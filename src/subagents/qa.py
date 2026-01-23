"""
QA SubAgent
品質保証・重複検知を担当
"""

from typing import Dict, Any, List
from .base import BaseSubAgent, SubAgentResult


class QASubAgent(BaseSubAgent):
    """品質保証・サブエージェント"""

    def __init__(self):
        super().__init__(
            name="qa",
            role="quality_validation",
            priority="high"
        )

    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        品質チェックと重複検知

        Args:
            input_data: {
                'title': str,
                'content': str,
                'existing_knowledge': list (オプション)
            }

        Returns:
            品質評価結果
        """
        if not self.validate_input(input_data, ['title', 'content']):
            return SubAgentResult(
                status='failed',
                data={},
                message="必須フィールドが不足しています"
            )

        title = input_data.get('title', '')
        content = input_data.get('content', '')
        existing_knowledge = input_data.get('existing_knowledge', [])

        # 1. 内容の完全性チェック
        completeness = self._check_completeness(title, content)

        # 2. 重複検知
        duplicates = self._detect_duplicates(title, content, existing_knowledge)

        # 3. 品質スコア算出
        quality_score = self._calculate_quality_score(title, content, completeness)

        # 4. 改善提案
        improvements = self._suggest_quality_improvements(completeness, quality_score)

        # ステータス判定
        if duplicates['high_similarity_count'] > 0:
            status = 'warning'
            message = f"重複の可能性がある類似ナレッジが{duplicates['high_similarity_count']}件見つかりました"
        elif quality_score['score'] < 0.5:
            status = 'warning'
            message = f"品質スコアが低いです: {quality_score['score']:.0%}"
        else:
            status = 'success'
            message = f"品質チェック完了: {quality_score['score']:.0%}"

        return SubAgentResult(
            status=status,
            data={
                'completeness': completeness,
                'duplicates': duplicates,
                'quality_score': quality_score,
                'improvements': improvements
            },
            message=message
        )

    def _check_completeness(self, title: str, content: str) -> Dict[str, Any]:
        """内容の完全性をチェック"""
        checks = []

        # 1. タイトルの適切性
        title_check = {
            'item': 'タイトル',
            'passed': 10 <= len(title) <= 100,
            'message': 'タイトルの長さが適切' if 10 <= len(title) <= 100 else
                      'タイトルが短すぎるか長すぎます（推奨: 10-100文字）'
        }
        checks.append(title_check)

        # 2. 内容の十分性
        content_check = {
            'item': '内容',
            'passed': len(content) >= 100,
            'message': '内容が十分に記載されています' if len(content) >= 100 else
                      '内容が不足しています（最低100文字を推奨）'
        }
        checks.append(content_check)

        # 3. 構造化されているか
        has_structure = any(marker in content for marker in ['##', '- ', '* ', '1.', '2.'])
        structure_check = {
            'item': '構造化',
            'passed': has_structure,
            'message': '見出しやリストで構造化されています' if has_structure else
                      '見出しやリストを使って構造化することを推奨します'
        }
        checks.append(structure_check)

        # 4. 具体性
        has_specifics = any(word in content.lower() for word in [
            '時刻', '日時', 'ユーザー', 'システム', 'サーバー', 'エラー', 'コマンド'
        ])
        specifics_check = {
            'item': '具体性',
            'passed': has_specifics,
            'message': '具体的な情報が含まれています' if has_specifics else
                      '時刻、対象システム、エラーメッセージなど具体的な情報を追加してください'
        }
        checks.append(specifics_check)

        # 5. 対応結果の記載
        has_result = any(word in content.lower() for word in [
            '解決', '対応', '復旧', '完了', '実施', '確認'
        ])
        result_check = {
            'item': '対応結果',
            'passed': has_result,
            'message': '対応結果が記載されています' if has_result else
                      '対応結果を明記してください'
        }
        checks.append(result_check)

        passed_count = sum(1 for check in checks if check['passed'])
        completeness_rate = passed_count / len(checks)

        return {
            'checks': checks,
            'passed_count': passed_count,
            'total_count': len(checks),
            'rate': round(completeness_rate, 2)
        }

    def _detect_duplicates(
        self,
        title: str,
        content: str,
        existing_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """重複を検知"""
        similarities = []

        for knowledge in existing_knowledge:
            existing_title = knowledge.get('title', '')
            existing_content = knowledge.get('content', '')

            # タイトルの類似度
            title_similarity = self._calculate_text_similarity(title, existing_title)

            # 内容の類似度
            content_similarity = self._calculate_text_similarity(content, existing_content)

            # 総合類似度（タイトルを重視）
            overall_similarity = (title_similarity * 0.6) + (content_similarity * 0.4)

            if overall_similarity > 0.5:  # 50%以上の類似度で記録
                similarities.append({
                    'knowledge_id': knowledge.get('id'),
                    'title': existing_title,
                    'title_similarity': round(title_similarity, 2),
                    'content_similarity': round(content_similarity, 2),
                    'overall_similarity': round(overall_similarity, 2)
                })

        # 類似度順にソート
        similarities.sort(key=lambda x: x['overall_similarity'], reverse=True)

        # 高類似度（80%以上）をカウント
        high_similarity_count = sum(1 for s in similarities if s['overall_similarity'] >= 0.8)

        return {
            'similar_knowledge': similarities[:5],  # 上位5件
            'high_similarity_count': high_similarity_count,
            'total_similar_count': len(similarities)
        }

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """2つのテキストの類似度を計算（Jaccard係数）"""
        if not text1 or not text2:
            return 0.0

        # 単語セットを作成
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Jaccard係数 = 積集合 / 和集合
        intersection = words1 & words2
        union = words1 | words2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _calculate_quality_score(
        self,
        title: str,
        content: str,
        completeness: Dict[str, Any]
    ) -> Dict[str, Any]:
        """品質スコアを算出"""
        score = 0.0
        factors = []

        # 1. 完全性スコア（40%）
        completeness_score = completeness['rate'] * 0.4
        score += completeness_score
        factors.append({
            'factor': '完全性',
            'weight': 0.4,
            'contribution': round(completeness_score, 2)
        })

        # 2. 内容の充実度（30%）
        content_richness = min(1.0, len(content) / 500)  # 500文字を満点とする
        content_score = content_richness * 0.3
        score += content_score
        factors.append({
            'factor': '内容の充実度',
            'weight': 0.3,
            'contribution': round(content_score, 2)
        })

        # 3. 可読性（20%）
        readability = self._evaluate_readability(content)
        readability_score = readability * 0.2
        score += readability_score
        factors.append({
            'factor': '可読性',
            'weight': 0.2,
            'contribution': round(readability_score, 2)
        })

        # 4. 有用性（10%）
        usefulness = self._evaluate_usefulness(content)
        usefulness_score = usefulness * 0.1
        score += usefulness_score
        factors.append({
            'factor': '有用性',
            'weight': 0.1,
            'contribution': round(usefulness_score, 2)
        })

        # レベル判定
        if score >= 0.8:
            level = 'excellent'
        elif score >= 0.6:
            level = 'good'
        elif score >= 0.4:
            level = 'acceptable'
        else:
            level = 'needs_improvement'

        return {
            'score': round(score, 2),
            'level': level,
            'factors': factors
        }

    def _evaluate_readability(self, content: str) -> float:
        """可読性を評価"""
        score = 0.5  # 基準値

        # 改行が適切に入っているか
        lines = content.split('\n')
        if len(lines) > 3:
            score += 0.2

        # 箇条書きや見出しがあるか
        if any(marker in content for marker in ['##', '- ', '* ', '1.', '2.']):
            score += 0.2

        # 過度に長い行がないか
        max_line_length = max(len(line) for line in lines) if lines else 0
        if max_line_length < 200:
            score += 0.1

        return min(1.0, score)

    def _evaluate_usefulness(self, content: str) -> float:
        """有用性を評価"""
        score = 0.5  # 基準値
        content_lower = content.lower()

        # 具体的な手順やコマンドがあるか
        if any(marker in content for marker in ['```', '`', '$', '#']):
            score += 0.2

        # 対策や解決方法が記載されているか
        if any(word in content_lower for word in ['対策', '解決', '方法', '手順']):
            score += 0.2

        # 原因分析があるか
        if any(word in content_lower for word in ['原因', '理由', 'なぜ', 'why']):
            score += 0.1

        return min(1.0, score)

    def _suggest_quality_improvements(
        self,
        completeness: Dict[str, Any],
        quality_score: Dict[str, Any]
    ) -> List[str]:
        """品質改善提案"""
        improvements = []

        # 完全性の改善
        failed_checks = [c for c in completeness['checks'] if not c['passed']]
        for check in failed_checks:
            improvements.append(check['message'])

        # 品質スコアに基づいた提案
        if quality_score['score'] < 0.6:
            improvements.append('内容をより詳細に記載し、具体的な情報を追加してください')

        if quality_score['score'] < 0.8:
            # 低スコアの要因を特定
            low_factors = [f for f in quality_score['factors'] if f['contribution'] < f['weight'] * 0.5]
            for factor in low_factors:
                if factor['factor'] == '可読性':
                    improvements.append('見出しや箇条書きを使って読みやすく構造化してください')
                elif factor['factor'] == '有用性':
                    improvements.append('具体的な手順やコマンド例を追加してください')

        return improvements
