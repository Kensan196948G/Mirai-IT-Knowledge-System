"""
Documenter SubAgent
出力整形・要約を担当
"""

from typing import Dict, Any, List
from datetime import datetime
from .base import BaseSubAgent, SubAgentResult


class DocumenterSubAgent(BaseSubAgent):
    """ドキュメンター・サブエージェント"""

    def __init__(self):
        super().__init__(
            name="documenter",
            role="formatting",
            priority="medium"
        )

    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        ドキュメント整形と要約生成

        Args:
            input_data: {
                'title': str,
                'content': str,
                'itsm_type': str,
                'tags': list (オプション),
                'metadata': dict (オプション)
            }

        Returns:
            整形されたドキュメントと要約
        """
        if not self.validate_input(input_data, ['title', 'content']):
            return SubAgentResult(
                status='failed',
                data={},
                message="必須フィールドが不足しています"
            )

        title = input_data.get('title', '')
        content = input_data.get('content', '')
        itsm_type = input_data.get('itsm_type', 'Other')
        tags = input_data.get('tags', [])
        metadata = input_data.get('metadata', {})

        # 1. 技術者向け要約
        summary_technical = self._generate_technical_summary(title, content, itsm_type)

        # 2. 非技術者向け要約
        summary_non_technical = self._generate_non_technical_summary(title, content, itsm_type)

        # 3. 3行要約
        summary_3lines = self._generate_3line_summary(title, content)

        # 4. Markdown形式でフォーマット
        markdown_content = self._format_as_markdown(
            title, content, itsm_type, tags, summary_technical, summary_non_technical, metadata
        )

        # 5. HTML形式でフォーマット
        html_content = self._format_as_html(
            title, content, itsm_type, tags, summary_technical, summary_non_technical
        )

        return SubAgentResult(
            status='success',
            data={
                'summary_technical': summary_technical,
                'summary_non_technical': summary_non_technical,
                'summary_3lines': summary_3lines,
                'markdown': markdown_content,
                'html': html_content
            },
            message="要約とフォーマット生成が完了しました"
        )

    def _generate_technical_summary(self, title: str, content: str, itsm_type: str) -> str:
        """技術者向け要約を生成"""
        # 技術的なキーワードを抽出
        tech_keywords = self._extract_technical_keywords(content)

        # 主要な情報を抽出
        key_points = []

        # ITSMタイプに応じた情報抽出
        if itsm_type == 'Incident':
            key_points = self._extract_incident_summary(content)
        elif itsm_type == 'Problem':
            key_points = self._extract_problem_summary(content)
        elif itsm_type == 'Change':
            key_points = self._extract_change_summary(content)
        elif itsm_type == 'Release':
            key_points = self._extract_release_summary(content)
        else:
            key_points = self._extract_generic_summary(content)

        # 技術的な要約を構築
        summary_parts = [f"{itsm_type}: {title}"]
        if tech_keywords:
            summary_parts.append(f"関連技術: {', '.join(tech_keywords[:5])}")
        summary_parts.extend(key_points)

        return ' / '.join(summary_parts)

    def _generate_non_technical_summary(self, title: str, content: str, itsm_type: str) -> str:
        """非技術者向け要約を生成"""
        content_lower = content.lower()

        # 影響範囲
        impact = "システムの一部"
        if any(word in content_lower for word in ['全体', '全ユーザー', 'すべて']):
            impact = "システム全体"
        elif any(word in content_lower for word in ['一部', '特定', '限定']):
            impact = "システムの一部"

        # 状態
        status = "対応完了"
        if any(word in content_lower for word in ['対応中', '調査中', '進行中']):
            status = "対応中"
        elif any(word in content_lower for word in ['解決', '復旧', '完了']):
            status = "対応完了"

        # 重要度
        severity = "通常"
        if any(word in content_lower for word in ['緊急', '重大', 'クリティカル']):
            severity = "緊急"
        elif any(word in content_lower for word in ['重要', '高']):
            severity = "重要"

        # ITSMタイプの日本語化
        itsm_type_jp = {
            'Incident': 'インシデント（障害対応）',
            'Problem': '問題管理（根本原因対応）',
            'Change': '変更管理',
            'Release': 'リリース管理',
            'Request': 'サービスリクエスト',
            'Other': 'その他'
        }.get(itsm_type, itsm_type)

        return f"【{itsm_type_jp}】{title} - 影響範囲: {impact} / 重要度: {severity} / 状態: {status}"

    def _generate_3line_summary(self, title: str, content: str) -> List[str]:
        """3行要約を生成"""
        lines = []
        content_lower = content.lower()

        # 1行目: 何が起きたか / 何をするか
        first_sentence = content.split('。')[0] if '。' in content else content.split('\n')[0]
        lines.append(first_sentence.strip()[:100])

        # 2行目: 原因 or 対応内容
        if '原因' in content_lower:
            cause_idx = content_lower.find('原因')
            cause_text = content[cause_idx:cause_idx+100].split('。')[0]
            lines.append(cause_text.strip())
        elif '対応' in content_lower:
            response_idx = content_lower.find('対応')
            response_text = content[response_idx:response_idx+100].split('。')[0]
            lines.append(response_text.strip())
        else:
            # 2文目を使用
            sentences = [s.strip() for s in content.split('。') if s.strip()]
            if len(sentences) > 1:
                lines.append(sentences[1][:100])
            else:
                lines.append("詳細は本文を参照してください")

        # 3行目: 結果 or 対策
        if any(word in content_lower for word in ['解決', '復旧', '完了']):
            result_keywords = ['解決', '復旧', '完了']
            for keyword in result_keywords:
                if keyword in content_lower:
                    idx = content_lower.find(keyword)
                    result_text = content[idx:idx+100].split('。')[0]
                    lines.append(result_text.strip())
                    break
        elif '対策' in content_lower:
            measure_idx = content_lower.find('対策')
            measure_text = content[measure_idx:measure_idx+100].split('。')[0]
            lines.append(measure_text.strip())
        else:
            lines.append("対応状況は本文を参照してください")

        # 3行に調整
        while len(lines) < 3:
            lines.append("")

        return lines[:3]

    def _extract_technical_keywords(self, content: str) -> List[str]:
        """技術キーワードを抽出"""
        content_lower = content.lower()
        keywords = []

        tech_terms = [
            'linux', 'windows', 'apache', 'nginx', 'mysql', 'postgresql', 'redis',
            'docker', 'kubernetes', 'aws', 'azure', 'python', 'java', 'javascript',
            'cpu', 'メモリ', 'ディスク', 'ネットワーク', 'データベース', 'api'
        ]

        for term in tech_terms:
            if term in content_lower:
                keywords.append(term)

        return keywords

    def _extract_incident_summary(self, content: str) -> List[str]:
        """インシデント要約を抽出"""
        points = []
        content_lower = content.lower()

        # 発生時刻
        if any(word in content_lower for word in ['発生', '検知', '時刻']):
            points.append("発生時刻記録あり")

        # 影響
        if any(word in content_lower for word in ['影響', 'ユーザー', 'システム']):
            points.append("影響範囲記録あり")

        # 復旧
        if any(word in content_lower for word in ['復旧', '解決', '対応完了']):
            points.append("復旧済み")

        return points[:3]

    def _extract_problem_summary(self, content: str) -> List[str]:
        """問題管理要約を抽出"""
        points = []
        content_lower = content.lower()

        if '根本原因' in content_lower or 'root cause' in content_lower:
            points.append("根本原因分析済み")

        if any(word in content_lower for word in ['再発防止', '恒久対策']):
            points.append("再発防止策あり")

        if any(word in content_lower for word in ['インシデント', '関連']):
            points.append("関連インシデントあり")

        return points[:3]

    def _extract_change_summary(self, content: str) -> List[str]:
        """変更管理要約を抽出"""
        points = []
        content_lower = content.lower()

        if any(word in content_lower for word in ['変更内容', '対象', '範囲']):
            points.append("変更内容明記あり")

        if 'ロールバック' in content_lower or 'rollback' in content_lower:
            points.append("ロールバック計画あり")

        if 'テスト' in content_lower or 'test' in content_lower:
            points.append("テスト計画あり")

        return points[:3]

    def _extract_release_summary(self, content: str) -> List[str]:
        """リリース管理要約を抽出"""
        points = []
        content_lower = content.lower()

        if 'リリース' in content_lower or 'release' in content_lower:
            points.append("リリース内容記載あり")

        if any(word in content_lower for word in ['手順', 'ステップ', 'プロセス']):
            points.append("リリース手順あり")

        return points[:3]

    def _extract_generic_summary(self, content: str) -> List[str]:
        """汎用要約を抽出"""
        # 最初の3つの文を抽出
        sentences = [s.strip() for s in content.split('。') if s.strip()]
        return sentences[:3]

    def _format_as_markdown(
        self,
        title: str,
        content: str,
        itsm_type: str,
        tags: List[str],
        summary_technical: str,
        summary_non_technical: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Markdown形式でフォーマット"""
        md_parts = []

        # タイトル
        md_parts.append(f"# {title}\n")

        # メタ情報
        md_parts.append("## メタ情報\n")
        md_parts.append(f"- **ITSMタイプ**: {itsm_type}")
        md_parts.append(f"- **作成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if tags:
            md_parts.append(f"- **タグ**: {', '.join(tags)}")
        md_parts.append("")

        # 要約
        md_parts.append("## 要約\n")
        md_parts.append(f"**技術者向け**: {summary_technical}\n")
        md_parts.append(f"**非技術者向け**: {summary_non_technical}\n")

        # 本文
        md_parts.append("## 詳細\n")
        md_parts.append(content)
        md_parts.append("")

        # フッター
        md_parts.append("---")
        md_parts.append("*このナレッジは Mirai IT Knowledge Systems により生成されました*")

        return '\n'.join(md_parts)

    def _format_as_html(
        self,
        title: str,
        content: str,
        itsm_type: str,
        tags: List[str],
        summary_technical: str,
        summary_non_technical: str
    ) -> str:
        """HTML形式でフォーマット"""
        # 簡易的なMarkdown→HTML変換
        html_content = content.replace('\n', '<br>\n')

        # タグをバッジ風に
        tag_html = ' '.join([f'<span class="badge">{tag}</span>' for tag in tags])

        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .meta {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin-bottom: 20px; }}
        .badge {{ display: inline-block; background: #4CAF50; color: white; padding: 3px 8px;
                  border-radius: 3px; font-size: 0.9em; margin-right: 5px; }}
        .content {{ line-height: 1.6; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;
                   color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>

    <div class="meta">
        <p><strong>ITSMタイプ:</strong> {itsm_type}</p>
        <p><strong>作成日時:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>タグ:</strong> {tag_html}</p>
    </div>

    <div class="summary">
        <h2>要約</h2>
        <p><strong>技術者向け:</strong> {summary_technical}</p>
        <p><strong>非技術者向け:</strong> {summary_non_technical}</p>
    </div>

    <div class="content">
        <h2>詳細</h2>
        {html_content}
    </div>

    <div class="footer">
        <p><em>このナレッジは Mirai IT Knowledge Systems により生成されました</em></p>
    </div>
</body>
</html>
"""
        return html

