"""
Interactive Knowledge Creation Workflow
対話的ナレッジ生成ワークフロー

Claude Code Workflow Studio を活用した対話型インターフェース
AI駆動による自然言語理解と情報抽出
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.itsm_classifier import ITSMClassifier
from src.core.workflow import WorkflowEngine
from src.mcp.sqlite_client import SQLiteClient

logger = logging.getLogger(__name__)


class InteractiveKnowledgeCreationWorkflow:
    """対話的ナレッジ生成ワークフロー（AI駆動版）"""

    def __init__(self):
        self.conversation_history = []
        self.collected_info = {
            "title": None,
            "when": None,
            "system": None,
            "symptom": None,
            "impact": None,
            "response": None,
            "cause": None,
            "measures": None,
        }
        self.db_client = SQLiteClient()
        self.itsm_classifier = ITSMClassifier()

        # AI クライアント初期化
        self._ai_client = None
        self._init_ai_client()

    def _init_ai_client(self):
        """AIクライアントを初期化（Anthropicをプライマリとして使用）"""
        # プライマリ: Anthropic（Claude）- クォータ問題が少ない
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic

                self._ai_client = anthropic.Anthropic(api_key=anthropic_key)
                self._ai_provider = "anthropic"
                logger.info("対話AI（Anthropic）初期化完了")
                return
            except Exception as e:
                logger.warning(f"Anthropic初期化失敗: {e}")

        # フォールバック: OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import OpenAI

                self._ai_client = OpenAI(api_key=openai_key)
                self._ai_provider = "openai"
                logger.info("対話AI（OpenAI）初期化完了")
            except Exception as e:
                logger.warning(f"OpenAI初期化失敗: {e}")
                self._ai_provider = None

    def start_conversation(self, initial_input: str) -> Dict[str, Any]:
        """
        対話を開始

        Args:
            initial_input: ユーザーの最初の入力

        Returns:
            次の質問または完了メッセージ
        """
        self.conversation_history.append(
            {
                "role": "user",
                "content": initial_input,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 初期入力から情報を抽出
        self._extract_info_from_input(initial_input)

        # 次の質問を生成
        next_question = self._get_next_question()

        if next_question:
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": next_question,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return {
                "type": "question",
                "question": next_question,
                "progress": self._get_progress(),
            }
        else:
            # 情報収集完了、ナレッジ生成
            return self._generate_knowledge()

    def answer_question(self, answer: str) -> Dict[str, Any]:
        """
        質問への回答を処理

        Args:
            answer: ユーザーの回答

        Returns:
            次の質問またはナレッジ生成結果
        """
        # 直前の質問を保存（フォールバック用）
        previous_question = None
        if len(self.conversation_history) >= 1:
            for msg in reversed(self.conversation_history):
                if msg["role"] == "assistant":
                    previous_question = msg["content"]
                    break

        self.conversation_history.append(
            {"role": "user", "content": answer, "timestamp": datetime.now().isoformat()}
        )

        # 回答から情報を抽出
        self._extract_info_from_input(answer)

        # AI抽出が失敗した場合、直前の質問に基づいてフィールドを埋める
        self._fallback_save_answer(answer, previous_question)

        # 次の質問
        next_question = self._get_next_question()

        if next_question:
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": next_question,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return {
                "type": "question",
                "question": next_question,
                "progress": self._get_progress(),
            }
        else:
            return self._generate_knowledge()

    def _extract_info_from_input(self, text: str):
        """入力テキストから情報を抽出（AI駆動版）"""
        # AIが利用可能な場合はAI抽出を使用
        if self._ai_client:
            self._extract_info_with_ai(text)
        else:
            # フォールバック: キーワードベース
            self._extract_info_keyword_based(text)

    def _extract_info_with_ai(self, text: str):
        """AIを使って情報を抽出"""
        try:
            # 現在の会話履歴を整形
            context = "\n".join(
                [
                    f"{msg['role']}: {msg['content']}"
                    for msg in self.conversation_history[-5:]  # 直近5件
                ]
            )

            # 現在の収集状況
            current_info = json.dumps(
                {k: v for k, v in self.collected_info.items() if v},
                ensure_ascii=False,
                indent=2,
            )

            prompt = f"""あなたはITサポートの情報抽出アシスタントです。
ユーザーの入力からインシデント/ナレッジに必要な情報を抽出してください。

【会話履歴】
{context}

【最新の入力】
{text}

【現在の収集済み情報】
{current_info if current_info != '{{}}' else 'なし'}

以下のフィールドについて、入力から抽出できる情報をJSON形式で返してください。
抽出できない場合はnullを設定してください。既に収集済みのフィールドは上書きしないでください。

フィールド:
- title: 問題のタイトル（簡潔に）
- when: いつ発生したか（日時）
- system: どのシステム/サービスで発生したか（※任意のシステム名を認識してください。例: Windows11, AresStandard2025, 社内ポータルなど）
- symptom: 具体的な症状やエラー内容
- impact: 影響範囲
- response: 実施した対応内容
- cause: 原因（判明している場合）
- measures: 今後の対策

JSON形式で回答してください（説明文は不要）:"""

            # プロバイダーに応じたAPI呼び出し
            if getattr(self, "_ai_provider", None) == "anthropic":
                # Anthropic API
                response = self._ai_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text
            else:
                # OpenAI API
                response = self._ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "あなたはITサポートの情報抽出アシスタントです。JSON形式で回答してください。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                )
                content = response.choices[0].message.content

            # JSON抽出
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            extracted = json.loads(content.strip())

            # 抽出した情報をマージ（既存情報は上書きしない）
            for key, value in extracted.items():
                if (
                    key in self.collected_info
                    and value
                    and not self.collected_info[key]
                ):
                    self.collected_info[key] = value
                    logger.info(
                        f"AI抽出: {key} = {value[:50]}..."
                        if len(str(value)) > 50
                        else f"AI抽出: {key} = {value}"
                    )

        except Exception as e:
            logger.error(f"AI情報抽出エラー: {e}")
            # フォールバック
            self._extract_info_keyword_based(text)

    def _fallback_save_answer(self, answer: str, previous_question: Optional[str]):
        """
        直前の質問に基づいて回答を保存（フォールバック）

        AI抽出が失敗した場合や、抽出結果が空の場合に、
        直前の質問内容からフィールドを特定して回答を保存する
        """
        if not previous_question or not answer or len(answer.strip()) < 2:
            return

        # 質問とフィールドのマッピング
        question_field_map = {
            "いつ": "when",
            "日時": "when",
            "発生": "when",
            "システム": "system",
            "サービス": "system",
            "症状": "symptom",
            "エラー": "symptom",
            "影響": "impact",
            "範囲": "impact",
            "対応": "response",
            "原因": "cause",
            "対策": "measures",
            "防止": "measures",
        }

        # 直前の質問からフィールドを特定
        target_field = None
        for keyword, field in question_field_map.items():
            if keyword in previous_question:
                target_field = field
                break

        # フィールドが特定でき、まだ値が設定されていない場合は保存
        if target_field and not self.collected_info.get(target_field):
            self.collected_info[target_field] = answer.strip()
            logger.info(f"フォールバック保存: {target_field} = {answer[:50]}...")

    def _extract_info_keyword_based(self, text: str):
        """キーワードベースの情報抽出（フォールバック）"""
        text_lower = text.lower()

        # タイトル推定
        if not self.collected_info["title"]:
            first_sentence = text.split("。")[0].split("\n")[0]
            if len(first_sentence) > 10:
                self.collected_info["title"] = first_sentence[:100]

        # 時間情報
        if any(word in text_lower for word in ["昨日", "今日", "先週", "時", "分"]):
            if not self.collected_info["when"]:
                self.collected_info["when"] = text[:200]

        # システム情報（任意のシステム名も受け入れる）
        systems = ["web", "db", "データベース", "サーバー", "ネットワーク", "メール"]
        if any(sys in text_lower for sys in systems):
            if not self.collected_info["system"]:
                self.collected_info["system"] = text[:200]
        # キーワードがなくても、システムに関する質問への回答として扱う
        elif not self.collected_info["system"] and len(text) > 2:
            # 直前の質問がシステムについてだった場合、回答をシステムとして記録
            if self.conversation_history:
                last_msg = self.conversation_history[-1]
                if (
                    last_msg["role"] == "assistant"
                    and "システム" in last_msg["content"]
                ):
                    self.collected_info["system"] = text[:200]

        # 症状
        if any(
            word in text_lower for word in ["エラー", "障害", "遅い", "停止", "ダウン"]
        ):
            if not self.collected_info["symptom"]:
                self.collected_info["symptom"] = text[:200]

        # 対応内容
        if any(word in text_lower for word in ["対応", "復旧", "再起動", "設定"]):
            if not self.collected_info["response"]:
                self.collected_info["response"] = text[:200]

    def _get_next_question(self) -> Optional[str]:
        """次の質問を生成"""
        # 不足している情報を確認
        if not self.collected_info["when"]:
            variants = [
                "いつ頃発生しましたか？（例: 1/27 14:30、昨日の朝など）",
                "発生した日時は分かりますか？（分からなければ「不明」でOKです）",
                "発生タイミングを教えてください。（だいたいの時間帯でも可）",
            ]
            return variants[len(self.conversation_history) % len(variants)]

        if not self.collected_info["system"]:
            variants = [
                "どのシステム・サービスで発生しましたか？（例: メール、VPN、社内ポータル、基幹システム など）",
                "対象のシステム名は分かりますか？（不明なら「不明」や「おそらく〜」でもOK）",
                "どの画面・機能で起きましたか？（分かる範囲で構いません）",
            ]
            return variants[len(self.conversation_history) % len(variants)]

        if not self.collected_info["symptom"]:
            variants = [
                "具体的にどんな症状・エラーでしたか？（表示された文言があれば教えてください）",
                "現象を教えてください。（例: ログイン不可、遅い、エラーコードなど）",
                "どんな問題が起きましたか？（スクリーンショットがあれば内容だけでOK）",
            ]
            return variants[len(self.conversation_history) % len(variants)]

        if not self.collected_info["impact"]:
            variants = [
                "影響範囲を教えてください。（ユーザー数、部門、システム範囲など）",
                "誰に影響しましたか？（全員/一部/特定部門 など）",
                "影響の大きさはどの程度でしたか？（軽微/重大/業務停止 など）",
            ]
            return variants[len(self.conversation_history) % len(variants)]

        if not self.collected_info["response"]:
            variants = [
                "どのように対応しましたか？（実施した手順を教えてください）",
                "対処内容を教えてください。（再起動/設定変更/連絡先 など）",
                "暫定対応や回避策はありましたか？",
            ]
            return variants[len(self.conversation_history) % len(variants)]

        if not self.collected_info["cause"]:
            variants = [
                "原因は特定できましたか？（分かる範囲でOK／不明でも可）",
                "原因の見当はありますか？（例: 設定変更、負荷増加 など）",
                "原因が分かれば教えてください。分からなければ「不明」で大丈夫です。",
            ]
            return variants[len(self.conversation_history) % len(variants)]

        if not self.collected_info["measures"]:
            variants = [
                "今後の対策や再発防止策はありますか？",
                "同様の問題を防ぐために考えていることはありますか？",
                "再発防止のためにやっておきたいことはありますか？",
            ]
            return variants[len(self.conversation_history) % len(variants)]

        # 全ての情報が揃った
        return None

    def _get_progress(self) -> Dict[str, Any]:
        """進捗状況を取得"""
        total_fields = len(self.collected_info)
        filled_fields = sum(1 for v in self.collected_info.values() if v is not None)

        return {
            "filled": filled_fields,
            "total": total_fields,
            "percentage": int(filled_fields / total_fields * 100),
            "collected": {k: bool(v) for k, v in self.collected_info.items()},
        }

    def _generate_knowledge(self) -> Dict[str, Any]:
        """収集した情報からナレッジを生成（AI強化版）"""
        # AI駆動でナレッジコンテンツを生成
        if self._ai_client:
            return self._generate_knowledge_with_ai()
        else:
            return self._generate_knowledge_basic()

    def _generate_knowledge_with_ai(self) -> Dict[str, Any]:
        """AIを使ってナレッジを生成"""
        try:
            # 収集情報をJSON形式で整形
            collected_json = json.dumps(
                self.collected_info, ensure_ascii=False, indent=2
            )

            # 会話履歴を整形
            conversation_context = "\n".join(
                [
                    f"{msg['role']}: {msg['content']}"
                    for msg in self.conversation_history
                ]
            )

            prompt = f"""あなたはITサポートのナレッジ作成エキスパートです。
以下の情報から、情シス担当者が活用できる高品質なナレッジ記事を生成してください。

【収集した情報】
{collected_json}

【対話履歴】
{conversation_context}

以下のJSON形式で回答してください：
{{
  "title": "簡潔で分かりやすいタイトル（50文字以内）",
  "content": "Markdown形式のナレッジ本文（## セクション見出しを使用）",
  "summary": "要約（100文字以内）",
  "tags": ["タグ1", "タグ2", "タグ3"],
  "recommended_actions": ["推奨アクション1", "推奨アクション2"],
  "prevention_tips": ["再発防止策1", "再発防止策2"]
}}

ナレッジ本文には以下のセクションを含めてください：
- ## 概要
- ## 発生状況
- ## 影響範囲
- ## 対応手順
- ## 原因分析
- ## 再発防止策
- ## 参考情報（該当する場合）

JSON形式で回答してください（説明文は不要）:"""

            # API呼び出し
            if getattr(self, "_ai_provider", None) == "anthropic":
                response = self._ai_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text
            else:
                response = self._ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "あなたはITナレッジ作成のエキスパートです。JSON形式で回答してください。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=2000,
                    temperature=0.5,
                )
                content = response.choices[0].message.content

            # JSON抽出
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            ai_result = json.loads(content.strip())
            logger.info("AI駆動ナレッジ生成完了")

            # ITSM分類
            title = ai_result.get(
                "title", self.collected_info.get("title", "新規ナレッジ")
            )
            knowledge_content = ai_result.get("content", "")
            classification = self.itsm_classifier.classify(title, knowledge_content)

            # 類似ナレッジ検索
            similar_knowledge = self.db_client.search_knowledge(query=title, limit=5)

            return {
                "type": "knowledge_generated",
                "title": title,
                "content": knowledge_content,
                "summary": ai_result.get("summary", ""),
                "tags": ai_result.get("tags", []),
                "recommended_actions": ai_result.get("recommended_actions", []),
                "prevention_tips": ai_result.get("prevention_tips", []),
                "itsm_type": classification["itsm_type"],
                "confidence": classification["confidence"],
                "similar_knowledge": similar_knowledge,
                "conversation_history": self.conversation_history,
                "ai_generated": True,
                "action": "review_or_save",
            }

        except Exception as e:
            logger.error(f"AI駆動ナレッジ生成エラー: {e}")
            return self._generate_knowledge_basic()

    def _generate_knowledge_basic(self) -> Dict[str, Any]:
        """基本的なナレッジ生成（フォールバック）"""
        # 構造化された内容を生成
        content_parts = []

        content_parts.append("## 発生事象")
        if self.collected_info["when"]:
            content_parts.append(self.collected_info["when"])
        if self.collected_info["symptom"]:
            content_parts.append(self.collected_info["symptom"])
        content_parts.append("")

        if self.collected_info["system"]:
            content_parts.append("## 対象システム")
            content_parts.append(self.collected_info["system"])
            content_parts.append("")

        if self.collected_info["impact"]:
            content_parts.append("## 影響範囲")
            content_parts.append(self.collected_info["impact"])
            content_parts.append("")

        if self.collected_info["response"]:
            content_parts.append("## 対応内容")
            content_parts.append(self.collected_info["response"])
            content_parts.append("")

        if self.collected_info["cause"]:
            content_parts.append("## 原因")
            content_parts.append(self.collected_info["cause"])
            content_parts.append("")

        if self.collected_info["measures"]:
            content_parts.append("## 今後の対策")
            content_parts.append(self.collected_info["measures"])
            content_parts.append("")

        content = "\n".join(content_parts)
        title = self.collected_info["title"] or "新規ナレッジ"

        # ITSM分類
        classification = self.itsm_classifier.classify(title, content)

        # 類似ナレッジ検索
        similar_knowledge = self.db_client.search_knowledge(query=title, limit=5)

        return {
            "type": "knowledge_generated",
            "title": title,
            "content": content,
            "itsm_type": classification["itsm_type"],
            "confidence": classification["confidence"],
            "similar_knowledge": similar_knowledge,
            "conversation_history": self.conversation_history,
            "ai_generated": False,
            "action": "review_or_save",
        }

    def get_ai_answer(self, question: str) -> Dict[str, Any]:
        """
        AIを使って質問に回答（AIオーケストレーター連携）

        Args:
            question: ユーザーの質問

        Returns:
            AI生成の回答と根拠
        """
        try:
            # AIオーケストレーターを使用
            import asyncio

            from src.ai.orchestrator import get_orchestrator

            orchestrator = get_orchestrator()

            # 現在の会話コンテキストを追加
            context = {
                "conversation_history": self.conversation_history[-5:],
                "collected_info": {k: v for k, v in self.collected_info.items() if v},
            }

            # 非同期処理を実行（既存ループがあれば使用）
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Flask/Gunicornなど既存ループ内で実行中の場合
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run, orchestrator.process(question, context)
                        )
                        result = future.result(timeout=30)
                else:
                    result = loop.run_until_complete(
                        orchestrator.process(question, context)
                    )
            except RuntimeError:
                # ループがない場合は新規作成
                result = asyncio.run(orchestrator.process(question, context))

            return {
                "success": True,
                "answer": result.answer,
                "evidence": result.evidence,
                "sources": result.sources,
                "confidence": result.confidence,
                "ai_used": result.ai_used,
                "processing_time_ms": result.processing_time_ms,
            }

        except Exception as e:
            logger.error(f"AI回答生成エラー（オーケストレーター）: {e}")

            # フォールバック: 直接Anthropic APIを使用
            return self._get_ai_answer_direct(question)

    def _get_ai_answer_direct(self, question: str) -> Dict[str, Any]:
        """
        AIに直接質問（フォールバック）

        オーケストレーターが失敗した場合のフォールバック
        """
        try:
            if not self._ai_client:
                return {
                    "success": False,
                    "error": "AIクライアントが初期化されていません",
                    "answer": "AIサービスに接続できませんでした。",
                }

            # コンテキスト情報を整形
            context_info = ""
            if any(self.collected_info.values()):
                context_info = "\n【関連情報】\n" + "\n".join(
                    [f"- {k}: {v}" for k, v in self.collected_info.items() if v]
                )

            prompt = f"""あなたはIT情シスの専門家です。以下の質問に対して、実用的で分かりやすい回答を提供してください。

【質問】
{question}
{context_info}

以下の形式で回答してください：
1. 回答本文（簡潔に）
2. 推奨アクション（あれば）
3. 注意点（あれば）

日本語で回答してください。"""

            import time

            start_time = time.time()

            if getattr(self, "_ai_provider", None) == "anthropic":
                response = self._ai_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                )
                answer = response.content[0].text
            else:
                response = self._ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "あなたはIT情シスの専門家です。"},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=1500,
                    temperature=0.5,
                )
                answer = response.choices[0].message.content

            processing_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "answer": answer,
                "evidence": [],
                "sources": [],
                "confidence": 0.7,
                "ai_used": [self._ai_provider or "unknown"],
                "processing_time_ms": processing_time,
            }

        except Exception as e:
            logger.error(f"AI直接回答エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "AI回答の生成中にエラーが発生しました。しばらくしてからお試しください。",
            }

    def save_knowledge(
        self,
        title: str,
        content: str,
        itsm_type: str,
        created_by: str = "interactive_workflow",
    ) -> Dict[str, Any]:
        """ナレッジを保存"""
        engine = WorkflowEngine()
        result = engine.process_knowledge(
            title=title, content=content, itsm_type=itsm_type, created_by=created_by
        )
        return result


# 使用例
if __name__ == "__main__":
    workflow = InteractiveKnowledgeCreationWorkflow()

    print("🌸 対話的ナレッジ生成ワークフロー")
    print("=" * 80)
    print()

    # 初期入力
    initial = "昨日Webサーバーでエラーが出た"
    result = workflow.start_conversation(initial)

    print(f"質問: {result['question']}")
    print(f"進捗: {result['progress']['percentage']}%")
    print()

    # 対話シミュレーション
    answers = [
        "12月30日の14時頃です",
        "本番のWebサーバー3台全部です",
        "HTTP 503エラーが出て、ユーザーがアクセスできなくなりました",
        "全ユーザー約1000人に影響しました",
        "Apacheを再起動して復旧しました",
        "接続数の上限に達していたことが原因です",
        "max_connectionsの設定を見直します",
    ]

    for i, answer in enumerate(answers, 1):
        print(f"回答{i}: {answer}")
        result = workflow.answer_question(answer)

        if result["type"] == "question":
            print(f"質問: {result['question']}")
            print(f"進捗: {result['progress']['percentage']}%")
            print()
        else:
            print("=" * 80)
            print("✅ ナレッジ生成完了！")
            print()
            print(f"タイトル: {result['title']}")
            print(
                f"ITSMタイプ: {result['itsm_type']} (信頼度: {result['confidence']:.0%})"
            )
            print()
            print("--- 生成された内容 ---")
            print(result["content"])
            print()
            print(f"類似ナレッジ: {len(result['similar_knowledge'])}件")
            break
