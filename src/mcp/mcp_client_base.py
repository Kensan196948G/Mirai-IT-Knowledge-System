"""
MCP Client Base - JSON-RPC over stdio adapter
MCPサーバーとsubprocess経由でJSON-RPC通信を行うベースクラス

MCP (Model Context Protocol) サーバーは stdio上のJSON-RPCプロトコルで通信します。
このモジュールは、Pythonアプリケーションから各MCPサーバーへの
接続・リクエスト送信・レスポンス受信を抽象化します。
"""

import json
import logging
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClientBase:
    """MCPサーバーとstdio JSON-RPCで通信するベースクライアント

    MCPサーバーをsubprocessで起動し、stdin/stdoutを通じてJSON-RPCメッセージを
    送受信します。サーバープロセスのライフサイクル管理も担当します。
    """

    def __init__(
        self,
        server_command: str,
        server_args: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        """
        Args:
            server_command: MCPサーバーコマンド (例: "npx")
            server_args: コマンド引数 (例: ["-y", "@upstash/context7-mcp"])
            env: 環境変数
            timeout: リクエストタイムアウト (秒)
            max_retries: 接続リトライ回数 (デフォルト: 2)
        """
        self.server_command = server_command
        self.server_args = server_args
        self.env = env or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._connected = False
        self._server_info: Optional[Dict[str, Any]] = None
        self._last_error: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """サーバーに接続中かどうか"""
        return self._connected and self._process is not None and self._process.poll() is None

    def connect(self) -> bool:
        """MCPサーバープロセスを起動して接続（リトライ付き）

        Returns:
            接続成功かどうか
        """
        if self.is_connected:
            return True

        for attempt in range(self.max_retries + 1):
            success = self._attempt_connect()
            if success:
                return True

            if attempt < self.max_retries:
                wait_time = (attempt + 1) * 1.0
                logger.info(
                    f"MCP接続リトライ ({attempt + 1}/{self.max_retries}): "
                    f"{wait_time}秒後に再試行..."
                )
                time.sleep(wait_time)

        return False

    def _attempt_connect(self) -> bool:
        """接続を1回試行する内部メソッド"""
        try:
            import os
            merged_env = os.environ.copy()
            merged_env.update(self.env)

            self._process = subprocess.Popen(
                [self.server_command] + self.server_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=merged_env,
                text=False,
            )

            # MCP initialize handshake
            init_result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mirai-knowledge-system",
                    "version": "1.0.0"
                }
            })

            if init_result is not None:
                # Send initialized notification
                self._send_notification("notifications/initialized", {})
                self._connected = True
                self._server_info = init_result
                self._last_error = None
                logger.info(
                    f"MCP server connected: {self.server_command} {' '.join(self.server_args)}"
                )
                return True
            else:
                self._last_error = "Handshake failed: no response from initialize"
                self.disconnect()
                return False

        except FileNotFoundError:
            self._last_error = f"Command not found: {self.server_command}"
            logger.warning(
                f"MCP server command not found: {self.server_command}"
            )
            return False
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"MCP server connection failed: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """MCPサーバープロセスを終了"""
        self._connected = False
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """MCPツールを呼び出す

        Args:
            tool_name: ツール名 (例: "resolve-library-id")
            arguments: ツール引数

        Returns:
            ツール実行結果、またはNone (エラー時)
        """
        if not self.is_connected:
            return None

        result = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """利用可能なツール一覧を取得

        Returns:
            ツール一覧
        """
        if not self.is_connected:
            return []

        result = self._send_request("tools/list", {})
        if result and "tools" in result:
            return result["tools"]
        return []

    def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """JSON-RPCリクエストを送信してレスポンスを受信

        Args:
            method: RPCメソッド名
            params: パラメータ

        Returns:
            result フィールドの値、またはNone
        """
        with self._lock:
            if not self._process or not self._process.stdin or not self._process.stdout:
                return None

            self._request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params,
            }

            try:
                request_bytes = json.dumps(request).encode("utf-8")
                # Content-Length header for JSON-RPC over stdio
                header = f"Content-Length: {len(request_bytes)}\r\n\r\n".encode("utf-8")
                self._process.stdin.write(header + request_bytes)
                self._process.stdin.flush()

                # Read response with timeout
                response = self._read_response()
                if response is None:
                    return None

                if "error" in response:
                    logger.error(f"MCP error: {response['error']}")
                    return None

                return response.get("result")

            except (BrokenPipeError, OSError) as e:
                logger.error(f"MCP communication error: {e}")
                self._connected = False
                return None

    def _send_notification(self, method: str, params: Dict[str, Any]):
        """JSON-RPC通知を送信 (レスポンスを待たない)"""
        with self._lock:
            if not self._process or not self._process.stdin:
                return

            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
            }

            try:
                notification_bytes = json.dumps(notification).encode("utf-8")
                header = f"Content-Length: {len(notification_bytes)}\r\n\r\n".encode("utf-8")
                self._process.stdin.write(header + notification_bytes)
                self._process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

    def _read_response(self) -> Optional[Dict[str, Any]]:
        """JSON-RPCレスポンスを読み取る (Content-Length header対応)

        select() を使ったノンブロッキングI/Oでタイムアウトを実現します。
        """
        import select

        if not self._process or not self._process.stdout:
            return None

        try:
            start_time = time.time()
            content_length = None
            fd = self._process.stdout.fileno()

            while time.time() - start_time < self.timeout:
                remaining = self.timeout - (time.time() - start_time)
                if remaining <= 0:
                    break

                # select() でデータが来るまで待機（タイムアウト付き）
                ready, _, _ = select.select([fd], [], [], min(remaining, 1.0))
                if not ready:
                    continue

                line = self._process.stdout.readline()
                if not line:
                    return None

                line_str = line.decode("utf-8").strip()

                if line_str.startswith("Content-Length:"):
                    content_length = int(line_str.split(":")[1].strip())
                elif line_str == "" and content_length is not None:
                    # ヘッダー終了、ボディを読む
                    body = self._process.stdout.read(content_length)
                    if body:
                        return json.loads(body.decode("utf-8"))
                    return None

            logger.warning("MCP response timeout")
            return None

        except Exception as e:
            logger.error(f"MCP response read error: {e}")
            return None

    def health_check(self) -> Dict[str, Any]:
        """接続の健全性を確認

        Returns:
            接続ステータス情報
        """
        status: Dict[str, Any] = {
            "connected": self.is_connected,
            "server_command": self.server_command,
            "server_args": self.server_args,
            "last_error": self._last_error,
        }

        if self._server_info:
            status["server_info"] = {
                "protocol_version": self._server_info.get("protocolVersion", "unknown"),
                "server_name": self._server_info.get("serverInfo", {}).get("name", "unknown"),
                "server_version": self._server_info.get("serverInfo", {}).get("version", "unknown"),
            }

        if self.is_connected:
            tools = self.list_tools()
            status["available_tools"] = len(tools)
            status["tool_names"] = [t.get("name", "") for t in tools]

        return status

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
