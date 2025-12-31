"""
Interactive Knowledge Creation Workflow
対話的ナレッジ生成ワークフロー

Claude Code Workflow Studio を活用した対話型インターフェース
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.workflow import WorkflowEngine
from src.core.itsm_classifier import ITSMClassifier
from src.mcp.sqlite_client import SQLiteClient


class InteractiveKnowledgeCreationWorkflow:
    """対話的ナレッジ生成ワークフロー"""

    def __init__(self):
        self.conversation_history = []
        self.collected_info = {
            'title': None,
            'when': None,
            'system': None,
            'symptom': None,
            'impact': None,
            'response': None,
            'cause': None,
            'measures': None
        }
        self.db_client = SQLiteClient()
        self.itsm_classifier = ITSMClassifier()

    def start_conversation(self, initial_input: str) -> Dict[str, Any]:
        """
        対話を開始

        Args:
            initial_input: ユーザーの最初の入力

        Returns:
            次の質問または完了メッセージ
        """
        self.conversation_history.append({
            'role': 'user',
            'content': initial_input,
            'timestamp': datetime.now().isoformat()
        })

        # 初期入力から情報を抽出
        self._extract_info_from_input(initial_input)

        # 次の質問を生成
        next_question = self._get_next_question()

        if next_question:
            self.conversation_history.append({
                'role': 'assistant',
                'content': next_question,
                'timestamp': datetime.now().isoformat()
            })
            return {
                'type': 'question',
                'question': next_question,
                'progress': self._get_progress()
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
        self.conversation_history.append({
            'role': 'user',
            'content': answer,
            'timestamp': datetime.now().isoformat()
        })

        # 回答から情報を抽出
        self._extract_info_from_input(answer)

        # 次の質問
        next_question = self._get_next_question()

        if next_question:
            self.conversation_history.append({
                'role': 'assistant',
                'content': next_question,
                'timestamp': datetime.now().isoformat()
            })
            return {
                'type': 'question',
                'question': next_question,
                'progress': self._get_progress()
            }
        else:
            return self._generate_knowledge()

    def _extract_info_from_input(self, text: str):
        """入力テキストから情報を抽出（簡易版）"""
        text_lower = text.lower()

        # タイトル推定
        if not self.collected_info['title']:
            # 最初の文をタイトルとして使用
            first_sentence = text.split('。')[0].split('\n')[0]
            if len(first_sentence) > 10:
                self.collected_info['title'] = first_sentence[:100]

        # 時間情報
        if any(word in text_lower for word in ['昨日', '今日', '先週', '時', '分']):
            if not self.collected_info['when']:
                self.collected_info['when'] = text[:200]

        # システム情報
        systems = ['web', 'db', 'データベース', 'サーバー', 'ネットワーク', 'メール']
        if any(sys in text_lower for sys in systems):
            if not self.collected_info['system']:
                self.collected_info['system'] = text[:200]

        # 症状
        if any(word in text_lower for word in ['エラー', '障害', '遅い', '停止', 'ダウン']):
            if not self.collected_info['symptom']:
                self.collected_info['symptom'] = text[:200]

        # 対応内容
        if any(word in text_lower for word in ['対応', '復旧', '再起動', '設定']):
            if not self.collected_info['response']:
                self.collected_info['response'] = text[:200]

    def _get_next_question(self) -> Optional[str]:
        """次の質問を生成"""
        # 不足している情報を確認
        if not self.collected_info['when']:
            return "いつ発生しましたか？（日時を教えてください）"

        if not self.collected_info['system']:
            return "どのシステム・サービスで発生しましたか？"

        if not self.collected_info['symptom']:
            return "具体的にどんな症状・エラーでしたか？"

        if not self.collected_info['impact']:
            return "影響範囲を教えてください。（ユーザー数、システム範囲など）"

        if not self.collected_info['response']:
            return "どのように対応しましたか？"

        if not self.collected_info['cause']:
            return "原因は特定できましたか？（分かる範囲で）"

        if not self.collected_info['measures']:
            return "今後の対策や再発防止策はありますか？"

        # 全ての情報が揃った
        return None

    def _get_progress(self) -> Dict[str, Any]:
        """進捗状況を取得"""
        total_fields = len(self.collected_info)
        filled_fields = sum(1 for v in self.collected_info.values() if v is not None)

        return {
            'filled': filled_fields,
            'total': total_fields,
            'percentage': int(filled_fields / total_fields * 100),
            'collected': {k: bool(v) for k, v in self.collected_info.items()}
        }

    def _generate_knowledge(self) -> Dict[str, Any]:
        """収集した情報からナレッジを生成"""
        # 構造化された内容を生成
        content_parts = []

        content_parts.append("## 発生事象")
        if self.collected_info['when']:
            content_parts.append(self.collected_info['when'])
        if self.collected_info['symptom']:
            content_parts.append(self.collected_info['symptom'])
        content_parts.append("")

        if self.collected_info['system']:
            content_parts.append("## 対象システム")
            content_parts.append(self.collected_info['system'])
            content_parts.append("")

        if self.collected_info['impact']:
            content_parts.append("## 影響範囲")
            content_parts.append(self.collected_info['impact'])
            content_parts.append("")

        if self.collected_info['response']:
            content_parts.append("## 対応内容")
            content_parts.append(self.collected_info['response'])
            content_parts.append("")

        if self.collected_info['cause']:
            content_parts.append("## 原因")
            content_parts.append(self.collected_info['cause'])
            content_parts.append("")

        if self.collected_info['measures']:
            content_parts.append("## 今後の対策")
            content_parts.append(self.collected_info['measures'])
            content_parts.append("")

        content = '\n'.join(content_parts)
        title = self.collected_info['title'] or "新規ナレッジ"

        # ITSM分類
        classification = self.itsm_classifier.classify(title, content)

        # 類似ナレッジ検索
        similar_knowledge = self.db_client.search_knowledge(query=title, limit=5)

        return {
            'type': 'knowledge_generated',
            'title': title,
            'content': content,
            'itsm_type': classification['itsm_type'],
            'confidence': classification['confidence'],
            'similar_knowledge': similar_knowledge,
            'conversation_history': self.conversation_history,
            'action': 'review_or_save'
        }

    def save_knowledge(self, title: str, content: str, itsm_type: str, created_by: str = 'interactive_workflow') -> Dict[str, Any]:
        """ナレッジを保存"""
        engine = WorkflowEngine()
        result = engine.process_knowledge(
            title=title,
            content=content,
            itsm_type=itsm_type,
            created_by=created_by
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
        "max_connectionsの設定を見直します"
    ]

    for i, answer in enumerate(answers, 1):
        print(f"回答{i}: {answer}")
        result = workflow.answer_question(answer)

        if result['type'] == 'question':
            print(f"質問: {result['question']}")
            print(f"進捗: {result['progress']['percentage']}%")
            print()
        else:
            print("=" * 80)
            print("✅ ナレッジ生成完了！")
            print()
            print(f"タイトル: {result['title']}")
            print(f"ITSMタイプ: {result['itsm_type']} (信頼度: {result['confidence']:.0%})")
            print()
            print("--- 生成された内容 ---")
            print(result['content'])
            print()
            print(f"類似ナレッジ: {len(result['similar_knowledge'])}件")
            break
