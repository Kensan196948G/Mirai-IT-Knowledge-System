#!/usr/bin/env python3
"""
AI Client - マルチプロバイダーAIクライアント
OpenAI、Anthropic、Gemini APIを統一インターフェースで利用
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """AIプロバイダー"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class AIResponse:
    """AI応答データクラス"""

    content: str
    provider: AIProvider
    model: str
    usage: Dict[str, int]
    raw_response: Optional[Dict[str, Any]] = None


class AIClient:
    """
    マルチプロバイダーAIクライアント

    Usage:
        client = AIClient()
        response = client.chat("質問内容")
    """

    def __init__(
        self,
        provider: AIProvider = AIProvider.ANTHROPIC,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        """
        Args:
            provider: 使用するAIプロバイダー
            openai_api_key: OpenAI APIキー
            anthropic_api_key: Anthropic APIキー
            gemini_api_key: Gemini APIキー
        """
        self.provider = provider

        # APIキーの設定（引数 > 環境変数）
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

        # クライアントの初期化
        self._openai_client = None
        self._anthropic_client = None
        self._gemini_model = None

        self._initialize_client()

    def _initialize_client(self):
        """プロバイダーに応じたクライアントを初期化"""
        if self.provider == AIProvider.OPENAI and self.openai_api_key:
            try:
                from openai import OpenAI

                self._openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI クライアント初期化完了")
            except ImportError:
                logger.warning("openai パッケージがインストールされていません")
            except Exception as e:
                logger.error(f"OpenAI クライアント初期化エラー: {e}")

        elif self.provider == AIProvider.ANTHROPIC and self.anthropic_api_key:
            try:
                import anthropic

                self._anthropic_client = anthropic.Anthropic(
                    api_key=self.anthropic_api_key
                )
                logger.info("Anthropic クライアント初期化完了")
            except ImportError:
                logger.warning("anthropic パッケージがインストールされていません")
            except Exception as e:
                logger.error(f"Anthropic クライアント初期化エラー: {e}")

        elif self.provider == AIProvider.GEMINI and self.gemini_api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.gemini_api_key)
                self._gemini_model = genai.GenerativeModel("gemini-pro")
                logger.info("Gemini クライアント初期化完了")
            except ImportError:
                logger.warning(
                    "google-generativeai パッケージがインストールされていません"
                )
            except Exception as e:
                logger.error(f"Gemini クライアント初期化エラー: {e}")

    def is_available(self) -> bool:
        """クライアントが利用可能か確認"""
        if self.provider == AIProvider.OPENAI:
            return self._openai_client is not None
        elif self.provider == AIProvider.ANTHROPIC:
            return self._anthropic_client is not None
        elif self.provider == AIProvider.GEMINI:
            return self._gemini_model is not None
        return False

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> AIResponse:
        """
        チャットメッセージを送信

        Args:
            message: ユーザーメッセージ
            system_prompt: システムプロンプト
            conversation_history: 会話履歴 [{"role": "user/assistant", "content": "..."}]
            max_tokens: 最大トークン数
            temperature: 温度パラメータ

        Returns:
            AIResponse オブジェクト
        """
        if not self.is_available():
            raise RuntimeError(f"{self.provider.value} クライアントが利用できません")

        if self.provider == AIProvider.OPENAI:
            return self._chat_openai(
                message, system_prompt, conversation_history, max_tokens, temperature
            )
        elif self.provider == AIProvider.ANTHROPIC:
            return self._chat_anthropic(
                message, system_prompt, conversation_history, max_tokens, temperature
            )
        elif self.provider == AIProvider.GEMINI:
            return self._chat_gemini(
                message, system_prompt, conversation_history, max_tokens, temperature
            )

    def _chat_openai(
        self,
        message: str,
        system_prompt: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
        max_tokens: int,
        temperature: float,
    ) -> AIResponse:
        """OpenAI APIでチャット"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return AIResponse(
            content=response.choices[0].message.content,
            provider=AIProvider.OPENAI,
            model="gpt-4o-mini",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            raw_response=response.model_dump(),
        )

    def _chat_anthropic(
        self,
        message: str,
        system_prompt: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
        max_tokens: int,
        temperature: float,
    ) -> AIResponse:
        """Anthropic APIでチャット"""
        messages = []

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self._anthropic_client.messages.create(**kwargs)

        return AIResponse(
            content=response.content[0].text,
            provider=AIProvider.ANTHROPIC,
            model="claude-sonnet-4-20250514",
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
            },
            raw_response=None,
        )

    def _chat_gemini(
        self,
        message: str,
        system_prompt: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
        max_tokens: int,
        temperature: float,
    ) -> AIResponse:
        """Gemini APIでチャット"""
        # Geminiはシステムプロンプトをメッセージの先頭に追加
        full_message = ""
        if system_prompt:
            full_message = f"[System Instructions]\n{system_prompt}\n\n"

        if conversation_history:
            for msg in conversation_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                full_message += f"{role}: {msg['content']}\n\n"

        full_message += f"User: {message}"

        response = self._gemini_model.generate_content(
            full_message,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        return AIResponse(
            content=response.text,
            provider=AIProvider.GEMINI,
            model="gemini-pro",
            usage={"total_tokens": 0},  # Geminiは使用量情報が異なる
            raw_response=None,
        )

    def extract_json(
        self, message: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        AIにJSON形式で回答させる

        Args:
            message: ユーザーメッセージ
            system_prompt: システムプロンプト

        Returns:
            パースされたJSONデータ
        """
        json_system = (
            system_prompt or ""
        ) + "\n\n必ずJSON形式で回答してください。説明文は不要です。"

        response = self.chat(message, system_prompt=json_system, temperature=0.3)

        # JSON部分を抽出
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSONパースエラー: {e}\n内容: {content}")
            return {}

    def switch_provider(self, provider: AIProvider):
        """プロバイダーを切り替え"""
        self.provider = provider
        self._initialize_client()


# ファクトリー関数
def create_ai_client(provider: str = "anthropic") -> AIClient:
    """
    AIクライアントを作成

    Args:
        provider: "openai", "anthropic", "gemini"

    Returns:
        AIClient インスタンス
    """
    provider_enum = AIProvider(provider.lower())
    return AIClient(provider=provider_enum)
