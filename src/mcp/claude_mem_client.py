"""
Claude-Mem MCP Client
会話履歴メモリクライアント (実MCP接続対応)

cccmemory MCPサーバーと連携して、会話履歴の永続化、
セマンティック検索、決定追跡を提供します。

使い分け:
- memory (知識グラフ): エンティティ・関係管理、短期〜中期コンテキスト
- claude-mem (本クライアント): 会話履歴、セマンティック検索、決定追跡、長期記憶
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .mcp_client_base import MCPClientBase

logger = logging.getLogger(__name__)


class ClaudeMemClient:
    """Claude-Mem連携クライアント

    cccmemory MCPサーバーと実接続して記憶管理を行います。
    MCP未検出時はデモデータにフォールバックします。
    """

    # .mcp.json の claude-mem 設定に準拠
    DEFAULT_COMMAND = "npx"
    DEFAULT_ARGS = ["-y", "cccmemory"]
    DEFAULT_DB_PATH = ".memory/claude-mem/conversations.db"

    def __init__(self, db_path: Optional[str] = None, auto_enable: bool = True):
        """初期化

        Args:
            db_path: データベースパス（省略時は環境変数から取得）
            auto_enable: MCP自動接続（デフォルト: True）
        """
        self.db_path = db_path or os.environ.get(
            "CCCMEMORY_DB_PATH", self.DEFAULT_DB_PATH
        )
        self._memory_cache: List[Dict[str, Any]] = []
        self._decision_cache: List[Dict[str, Any]] = []
        self._mcp_client: Optional[MCPClientBase] = None
        self.enabled = False

        if auto_enable:
            self.enabled = self._try_connect()

    def _try_connect(self) -> bool:
        """MCPサーバーへの接続を試行"""
        try:
            self._mcp_client = MCPClientBase(
                server_command=self.DEFAULT_COMMAND,
                server_args=self.DEFAULT_ARGS,
                env={"CCCMEMORY_DB_PATH": self.db_path},
                timeout=30.0,
            )
            connected = self._mcp_client.connect()
            if connected:
                logger.info("Claude-Mem MCP: 実接続成功")
                return True
            else:
                logger.info("Claude-Mem MCP: 接続失敗、スタブモードで動作")
                self._mcp_client = None
                return False
        except Exception as e:
            logger.warning(f"Claude-Mem MCP: 接続エラー ({e})、スタブモードで動作")
            self._mcp_client = None
            return False

    def disconnect(self):
        """MCP接続を切断"""
        if self._mcp_client:
            self._mcp_client.disconnect()
            self._mcp_client = None
        self.enabled = False

    # =========================================
    # セマンティック検索機能
    # =========================================

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        search_type: str = "semantic"
    ) -> List[Dict[str, Any]]:
        """
        過去の記憶をセマンティック検索

        Args:
            query: 検索クエリ
            limit: 最大結果数
            search_type: 検索タイプ（semantic, keyword, hybrid）

        Returns:
            検索結果のリスト
        """
        if not self.enabled or not self._mcp_client:
            return self._get_demo_memories(query)

        try:
            result = self._mcp_client.call_tool("search_conversations", {
                "query": query,
                "limit": limit,
                "scope": "all",
            })

            if result is None:
                return self._get_demo_memories(query)

            return self._format_search_results(result)

        except Exception as e:
            logger.warning(f"Claude-Mem search failed: {e}")
            return self._get_demo_memories(query)

    def search_similar_conversations(
        self,
        content: str,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        類似の会話を検索

        Args:
            content: 検索対象のコンテンツ
            threshold: 類似度閾値（0.0-1.0）

        Returns:
            類似会話のリスト
        """
        if not self.enabled or not self._mcp_client:
            return []

        try:
            result = self._mcp_client.call_tool("search_conversations", {
                "query": content[:200],
                "limit": 10,
                "scope": "all",
            })

            if result is None:
                return []

            # テキストから結果を抽出
            results = self._format_search_results(result)
            return [r for r in results if r.get("similarity", 0) >= threshold]

        except Exception as e:
            logger.warning(f"Similar conversation search failed: {e}")
            return []

    # =========================================
    # 決定追跡機能（Decision Tracking）
    # =========================================

    def store_decision(
        self,
        title: str,
        decision: str,
        rationale: str,
        context: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        knowledge_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        決定を記録

        Args:
            title: 決定のタイトル
            decision: 決定内容
            rationale: 決定理由
            context: コンテキスト/背景
            alternatives: 検討した代替案
            tags: タグ
            knowledge_id: 関連ナレッジID

        Returns:
            保存結果
        """
        decision_record = {
            "id": f"dec_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "decision": decision,
            "rationale": rationale,
            "context": context,
            "alternatives": alternatives or [],
            "tags": tags or [],
            "knowledge_id": knowledge_id,
            "timestamp": datetime.now().isoformat(),
            "status": "active"
        }

        self._decision_cache.append(decision_record)

        # MCP経由で永続化
        if self.enabled and self._mcp_client:
            try:
                self._mcp_client.call_tool("remember", {
                    "text": f"Decision: {title} - {decision} (Rationale: {rationale})",
                })
            except Exception as e:
                logger.warning(f"Decision storage to MCP failed: {e}")

        return {"success": True, "decision_id": decision_record["id"]}

    def get_decisions(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        knowledge_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        決定を検索・取得

        Args:
            query: 検索クエリ
            tags: フィルタタグ
            knowledge_id: ナレッジID
            limit: 最大結果数

        Returns:
            決定のリスト
        """
        # MCP経由で検索
        if self.enabled and self._mcp_client and query:
            try:
                result = self._mcp_client.call_tool("get_decisions", {
                    "query": query,
                    "limit": limit,
                    "scope": "all",
                })

                if result is not None:
                    decisions = self._format_search_results(result)
                    decisions.extend(self._decision_cache)
                    return decisions[:limit]

            except Exception as e:
                logger.warning(f"MCP decision search failed: {e}")

        # ローカルキャッシュから検索
        results = list(self._decision_cache)

        if knowledge_id:
            results = [d for d in results if d.get("knowledge_id") == knowledge_id]

        if tags:
            results = [
                d for d in results
                if any(t in d.get("tags", []) for t in tags)
            ]

        if query:
            query_lower = query.lower()
            results = [
                d for d in results
                if query_lower in d.get("title", "").lower()
                or query_lower in d.get("decision", "").lower()
                or query_lower in d.get("rationale", "").lower()
            ]

        return results[:limit]

    def update_decision_status(
        self,
        decision_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """決定のステータスを更新"""
        for decision in self._decision_cache:
            if decision.get("id") == decision_id:
                decision["status"] = status
                decision["status_notes"] = notes
                decision["updated_at"] = datetime.now().isoformat()
                return True
        return False

    # =========================================
    # 会話履歴機能
    # =========================================

    def store_conversation(
        self,
        conversation_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """会話を保存"""
        conversation = {
            "id": conversation_id,
            "messages": messages,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        self._memory_cache.append(conversation)

        if self.enabled and self._mcp_client:
            try:
                self._mcp_client.call_tool("index_conversations", {
                    "session_id": conversation_id,
                })
            except Exception as e:
                logger.warning(f"Conversation indexing to MCP failed: {e}")

        return True

    def get_conversation_context(
        self,
        topic: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """トピックに関連する会話コンテキストを取得"""
        if self.enabled and self._mcp_client:
            try:
                result = self._mcp_client.call_tool("search_project_conversations", {
                    "query": topic,
                    "limit": limit,
                    "include_claude_code": True,
                    "include_codex": True,
                })

                if result is not None:
                    return self._format_search_results(result)

            except Exception as e:
                logger.warning(f"Conversation context retrieval failed: {e}")

        return self.search_memories(topic, limit=limit)

    # =========================================
    # Git統合機能
    # =========================================

    def link_to_commit(
        self,
        decision_id: str,
        commit_hash: str,
        commit_message: Optional[str] = None
    ) -> bool:
        """決定をGitコミットにリンク"""
        if self.enabled and self._mcp_client:
            try:
                self._mcp_client.call_tool("link_commits_to_conversations", {
                    "query": commit_hash,
                    "limit": 1,
                    "scope": "all",
                })
            except Exception as e:
                logger.warning(f"Commit linking to MCP failed: {e}")

        for decision in self._decision_cache:
            if decision.get("id") == decision_id:
                if "git_links" not in decision:
                    decision["git_links"] = []
                decision["git_links"].append({
                    "commit_hash": commit_hash,
                    "commit_message": commit_message,
                    "linked_at": datetime.now().isoformat()
                })
                return True
        return False

    def get_decisions_by_commit(self, commit_hash: str) -> List[Dict[str, Any]]:
        """コミットに関連する決定を取得"""
        if self.enabled and self._mcp_client:
            try:
                result = self._mcp_client.call_tool("link_commits_to_conversations", {
                    "query": commit_hash,
                    "limit": 10,
                    "scope": "all",
                })

                if result is not None:
                    return self._format_search_results(result)

            except Exception as e:
                logger.warning(f"Commit-related decisions retrieval failed: {e}")

        results = []
        for decision in self._decision_cache:
            for link in decision.get("git_links", []):
                if link.get("commit_hash") == commit_hash:
                    results.append(decision)
                    break
        return results

    # =========================================
    # ナレッジ補強機能
    # =========================================

    def enhance_knowledge_with_memory(
        self,
        knowledge_content: str,
        itsm_type: str
    ) -> Dict[str, Any]:
        """ナレッジを過去の記憶で補強"""
        keywords = self._extract_keywords(knowledge_content)

        all_memories = []
        for keyword in keywords[:3]:
            memories = self.search_memories(keyword, limit=2)
            all_memories.extend(memories)

        related_decisions = self.get_decisions(
            tags=[itsm_type.lower()],
            limit=3
        )

        unique_memories = []
        seen_titles = set()
        for memory in all_memories:
            title = memory.get("title", "")
            if title not in seen_titles:
                unique_memories.append(memory)
                seen_titles.add(title)

        return {
            "related_memories": unique_memories[:5],
            "related_decisions": related_decisions,
            "keywords_used": keywords[:3],
            "enhancement_timestamp": datetime.now().isoformat()
        }

    # =========================================
    # ヘルパーメソッド
    # =========================================

    def _extract_keywords(self, content: str) -> List[str]:
        """キーワード抽出（簡易版）"""
        important_terms = [
            "データベース", "サーバー", "ネットワーク", "証明書",
            "バックアップ", "接続", "プール", "エラー", "障害",
            "問題", "変更", "リリース", "セキュリティ", "パフォーマンス",
            "監視", "アラート", "認証", "ログイン", "アカウント",
            "VPN", "AD", "Active Directory", "ロック", "権限"
        ]

        content_lower = content.lower()
        found_keywords = []

        for term in important_terms:
            if term.lower() in content_lower:
                found_keywords.append(term)

        return found_keywords[:5]

    def _format_search_results(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """MCP tools/call結果を標準フォーマットに変換"""
        formatted = []
        content_list = result.get("content", [])
        for item in content_list:
            text = item.get("text", "")
            if text:
                formatted.append({
                    "title": text[:100],
                    "content": text,
                    "timestamp": datetime.now().isoformat(),
                    "tags": [],
                    "similarity": 0.8,
                    "source": "Claude-Mem",
                })
        return formatted

    def _get_demo_memories(self, query: str) -> List[Dict[str, Any]]:
        """デモ用のメモリデータ（スタブモード）"""
        demo_memories = [
            {
                "title": "データベース接続プール設定のベストプラクティス",
                "content": "各アプリケーションサーバーの接続プール最大数は、データベース側の max_connections を超えないように設定する必要がある。",
                "timestamp": "2025-12-15T10:00:00",
                "tags": ["database", "connection-pool", "best-practice"],
                "similarity": 0.85,
                "source": "Claude-Mem-stub",
            },
            {
                "title": "ITSMプロセスにおけるインシデント→問題管理の移行判断",
                "content": "同じ事象が3回以上発生した場合、または根本原因が不明な場合は、問題管理プロセスへエスカレーションする。",
                "timestamp": "2025-11-20T14:30:00",
                "tags": ["itsm", "incident", "problem", "escalation"],
                "similarity": 0.82,
                "source": "Claude-Mem-stub",
            },
            {
                "title": "証明書更新作業の標準手順",
                "content": "SSL/TLS証明書の更新は、期限の2週間前から計画し、ステージング環境で事前検証を行う。",
                "timestamp": "2025-10-05T09:00:00",
                "tags": ["security", "certificate", "procedure"],
                "similarity": 0.78,
                "source": "Claude-Mem-stub",
            },
            {
                "title": "ADアカウントロック対応の教訓",
                "content": "パスワード変更後のセッション残存が主な原因。モバイルデバイスのメール同期設定も確認が必要。",
                "timestamp": "2026-01-15T11:00:00",
                "tags": ["active-directory", "account", "troubleshooting"],
                "similarity": 0.75,
                "source": "Claude-Mem-stub",
            },
            {
                "title": "VPN接続障害の根本原因分析",
                "content": "証明書期限切れが最多の原因。自動更新の仕組みと30日前通知の設定を推奨。",
                "timestamp": "2026-02-01T09:30:00",
                "tags": ["vpn", "certificate", "rca"],
                "similarity": 0.72,
                "source": "Claude-Mem-stub",
            }
        ]

        query_lower = query.lower()
        for m in demo_memories:
            score = 0.5
            if query_lower in m["title"].lower():
                score += 0.3
            if query_lower in m["content"].lower():
                score += 0.2
            for tag in m["tags"]:
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 0.1
            m["similarity"] = min(score, 1.0)

        demo_memories.sort(key=lambda x: x["similarity"], reverse=True)
        return demo_memories[:5]

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "total_memories": len(self._memory_cache),
            "total_decisions": len(self._decision_cache),
            "enabled": self.enabled,
            "mode": "live" if self.enabled else "stub",
            "db_path": self.db_path,
        }

    def get_status(self) -> Dict[str, Any]:
        """接続ステータスを返す"""
        return {
            "enabled": self.enabled,
            "mode": "live" if self.enabled else "stub",
            "db_path": self.db_path,
            "cached_memories": len(self._memory_cache),
            "cached_decisions": len(self._decision_cache),
        }


# グローバルインスタンス
claude_mem_client = ClaudeMemClient(auto_enable=False)
