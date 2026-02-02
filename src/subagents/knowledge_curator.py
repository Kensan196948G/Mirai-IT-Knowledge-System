"""
Knowledge Curator SubAgent
ナレッジ整理・分類を担当
"""

import re
from typing import Any, Dict, List

from .base import BaseSubAgent, SubAgentResult


class KnowledgeCuratorSubAgent(BaseSubAgent):
    """ナレッジキュレーター・サブエージェント"""

    def __init__(self):
        super().__init__(name="knowledge_curator", role="organization", priority="high")

    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        ナレッジの整理・分類・メタデータ付与

        Args:
            input_data: {
                'title': str,
                'content': str,
                'itsm_type': str
            }

        Returns:
            整理・分類結果
        """
        if not self.validate_input(input_data, ["title", "content"]):
            return SubAgentResult(
                status="failed", data={}, message="必須フィールドが不足しています"
            )

        title = input_data.get("title", "")
        content = input_data.get("content", "")
        itsm_type = input_data.get("itsm_type", "Other")

        # 1. タグ抽出
        tags = self._extract_tags(title, content, itsm_type)

        # 2. カテゴリ分類
        categories = self._classify_categories(content)

        # 3. キーワード抽出
        keywords = self._extract_keywords(content)

        # 4. 重要度評価
        importance = self._evaluate_importance(title, content, itsm_type)

        # 5. メタデータ生成
        metadata = self._generate_metadata(title, content, tags, categories)

        return SubAgentResult(
            status="success",
            data={
                "tags": tags,
                "categories": categories,
                "keywords": keywords,
                "importance": importance,
                "metadata": metadata,
            },
            message=f"{len(tags)}個のタグと{len(categories)}個のカテゴリを抽出しました",
        )

    def _extract_tags(self, title: str, content: str, itsm_type: str) -> List[str]:
        """タグを抽出"""
        tags = []
        text = (title + " " + content).lower()

        # 技術タグ
        tech_tags = {
            "ネットワーク": [
                "network",
                "ネットワーク",
                "lan",
                "wan",
                "vpn",
                "dns",
                "dhcp",
            ],
            "データベース": [
                "database",
                "db",
                "データベース",
                "sql",
                "mysql",
                "postgresql",
                "oracle",
            ],
            "サーバー": ["server", "サーバー", "サーバ", "apache", "nginx", "iis"],
            "セキュリティ": [
                "security",
                "セキュリティ",
                "脆弱性",
                "firewall",
                "ファイアウォール",
            ],
            "バックアップ": ["backup", "バックアップ", "restore", "リストア", "復元"],
            "パフォーマンス": [
                "performance",
                "パフォーマンス",
                "性能",
                "遅延",
                "レスポンス",
            ],
            "アクセス権限": [
                "permission",
                "権限",
                "access",
                "アクセス",
                "authentication",
                "認証",
            ],
            "ストレージ": ["storage", "ストレージ", "disk", "ディスク", "容量"],
            "メモリ": ["memory", "メモリ", "ram", "swap"],
            "CPU": ["cpu", "プロセッサ", "processor"],
            "OS": ["os", "linux", "windows", "unix", "centos", "ubuntu"],
            "アプリケーション": ["application", "アプリケーション", "app", "アプリ"],
            "クラウド": ["cloud", "クラウド", "aws", "azure", "gcp"],
            "仮想化": [
                "virtual",
                "仮想",
                "vm",
                "vmware",
                "hyper-v",
                "docker",
                "kubernetes",
            ],
            "ログ": ["log", "ログ", "logging", "syslog"],
        }

        for tag, keywords in tech_tags.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)

        # ITSMタイプ固有のタグ
        if itsm_type == "Incident":
            if any(
                word in text for word in ["緊急", "重大", "クリティカル", "critical"]
            ):
                tags.append("緊急対応")
            if any(word in text for word in ["障害", "エラー", "error", "failure"]):
                tags.append("障害対応")

        elif itsm_type == "Problem":
            if any(word in text for word in ["根本原因", "root cause", "再発"]):
                tags.append("根本原因分析")
            if any(word in text for word in ["対策", "防止", "改善"]):
                tags.append("再発防止")

        elif itsm_type == "Change":
            if any(word in text for word in ["計画", "定期", "scheduled"]):
                tags.append("計画停止")
            if any(word in text for word in ["メンテナンス", "maintenance"]):
                tags.append("定期メンテナンス")

        elif itsm_type == "Release":
            if any(
                word in text for word in ["デプロイ", "deploy", "リリース", "release"]
            ):
                tags.append("リリース")
            if any(word in text for word in ["ロールバック", "rollback", "巻き戻し"]):
                tags.append("ロールバック")

        return list(set(tags))  # 重複を除去

    def _classify_categories(self, content: str) -> List[str]:
        """カテゴリ分類"""
        categories = []
        content_lower = content.lower()

        category_patterns = {
            "インフラ": ["インフラ", "infrastructure", "サーバー", "ネットワーク"],
            "ミドルウェア": ["ミドルウェア", "middleware", "apache", "nginx", "tomcat"],
            "アプリケーション": ["アプリケーション", "application", "システム"],
            "ハードウェア": ["ハードウェア", "hardware", "機器", "デバイス"],
            "セキュリティ": ["セキュリティ", "security", "脆弱性", "認証"],
            "運用": ["運用", "operation", "オペレーション", "監視"],
            "開発": ["開発", "development", "デプロイ", "ビルド"],
        }

        for category, keywords in category_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.append(category)

        return categories if categories else ["その他"]

    def _extract_keywords(self, content: str) -> List[str]:
        """キーワード抽出（頻出単語）"""
        # 簡易的な実装: 3文字以上の単語で頻出するもの
        words = re.findall(r"[\w]+", content.lower())
        word_freq = {}

        # ストップワード（除外する一般的な単語）
        stop_words = {
            "の",
            "に",
            "を",
            "は",
            "が",
            "で",
            "と",
            "から",
            "まで",
            "より",
            "など",
            "この",
            "その",
            "あの",
            "どの",
            "ある",
            "いる",
            "する",
            "なる",
            "れる",
            "です",
            "ます",
            "した",
            "ました",
            "ている",
            "される",
            "として",
            "について",
        }

        for word in words:
            if len(word) >= 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 頻度順にソートして上位10件
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]

    def _evaluate_importance(
        self, title: str, content: str, itsm_type: str
    ) -> Dict[str, Any]:
        """重要度評価"""
        score = 0.5  # 基準スコア

        text = (title + " " + content).lower()

        # 緊急度による加点
        urgent_keywords = [
            "緊急",
            "重大",
            "クリティカル",
            "critical",
            "障害",
            "down",
            "ダウン",
        ]
        if any(keyword in text for keyword in urgent_keywords):
            score += 0.3

        # ITSMタイプによる加点
        if itsm_type == "Incident":
            score += 0.1
        elif itsm_type == "Problem":
            score += 0.2  # 問題管理は重要度高

        # 影響範囲による加点
        impact_keywords = ["全体", "システム全体", "全ユーザー", "本番", "production"]
        if any(keyword in text for keyword in impact_keywords):
            score += 0.2

        # 内容の充実度による加点
        if len(content) > 500:
            score += 0.1

        score = min(1.0, score)  # 最大1.0

        level = "low"
        if score >= 0.8:
            level = "critical"
        elif score >= 0.6:
            level = "high"
        elif score >= 0.4:
            level = "medium"

        return {"score": round(score, 2), "level": level}

    def _generate_metadata(
        self, title: str, content: str, tags: List[str], categories: List[str]
    ) -> Dict[str, Any]:
        """メタデータ生成"""
        return {
            "title_length": len(title),
            "content_length": len(content),
            "word_count": len(content.split()),
            "tag_count": len(tags),
            "category_count": len(categories),
            "has_code_block": "```" in content or "code" in content.lower(),
            "has_url": "http" in content.lower(),
            "has_list": "-" in content
            or "*" in content
            or re.search(r"\d+\.", content) is not None,
        }
