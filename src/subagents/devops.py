"""
DevOps SubAgent
技術分析・自動化視点を担当
"""

import re
from typing import Any, Dict, List

from .base import BaseSubAgent, SubAgentResult


class DevOpsSubAgent(BaseSubAgent):
    """DevOps・サブエージェント"""

    def __init__(self):
        super().__init__(name="devops", role="technical_analysis", priority="medium")

    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        技術分析と自動化提案

        Args:
            input_data: {
                'title': str,
                'content': str,
                'itsm_type': str
            }

        Returns:
            技術分析結果と自動化提案
        """
        if not self.validate_input(input_data, ["content"]):
            return SubAgentResult(
                status="failed", data={}, message="必須フィールドが不足しています"
            )

        content = input_data.get("content", "")
        itsm_type = input_data.get("itsm_type", "Other")

        # 1. 技術要素の抽出
        tech_elements = self._extract_technical_elements(content)

        # 2. 自動化可能性の評価
        automation_potential = self._evaluate_automation_potential(content, itsm_type)

        # 3. 技術的リスクの分析
        technical_risks = self._analyze_technical_risks(content)

        # 4. コマンド・スクリプト抽出
        commands = self._extract_commands(content)

        # 5. 改善提案
        improvements = self._suggest_improvements(content, automation_potential)

        return SubAgentResult(
            status="success",
            data={
                "technical_elements": tech_elements,
                "automation_potential": automation_potential,
                "technical_risks": technical_risks,
                "commands": commands,
                "improvements": improvements,
            },
            message=f"技術要素{len(tech_elements)}件、自動化可能性{automation_potential['score']:.0%}を分析しました",
        )

    def _extract_technical_elements(self, content: str) -> List[Dict[str, str]]:
        """技術要素を抽出"""
        elements = []
        content_lower = content.lower()

        # 技術カテゴリ定義
        tech_categories = {
            "OS": ["linux", "windows", "unix", "centos", "ubuntu", "rhel", "debian"],
            "データベース": [
                "mysql",
                "postgresql",
                "oracle",
                "mongodb",
                "redis",
                "db",
                "database",
            ],
            "Webサーバー": ["apache", "nginx", "iis", "tomcat"],
            "プログラミング言語": [
                "python",
                "java",
                "javascript",
                "php",
                "ruby",
                "go",
                "c++",
            ],
            "クラウド": ["aws", "azure", "gcp", "cloud", "s3", "ec2", "lambda"],
            "コンテナ": ["docker", "kubernetes", "k8s", "container", "pod"],
            "CI/CD": ["jenkins", "gitlab", "github actions", "circleci", "travis"],
            "モニタリング": ["prometheus", "grafana", "zabbix", "nagios", "datadog"],
            "ネットワーク": [
                "vpn",
                "dns",
                "dhcp",
                "firewall",
                "load balancer",
                "proxy",
            ],
            "ストレージ": ["san", "nas", "nfs", "iscsi", "storage"],
            "バックアップ": ["backup", "restore", "snapshot", "replication"],
        }

        for category, keywords in tech_categories.items():
            matched_keywords = [kw for kw in keywords if kw in content_lower]
            if matched_keywords:
                elements.append({"category": category, "keywords": matched_keywords})

        return elements

    def _evaluate_automation_potential(
        self, content: str, itsm_type: str
    ) -> Dict[str, Any]:
        """自動化可能性を評価"""
        score = 0.0
        reasons = []
        content_lower = content.lower()

        # 繰り返し作業の検出
        repetitive_keywords = [
            "定期",
            "毎日",
            "毎週",
            "毎月",
            "繰り返し",
            "daily",
            "weekly",
        ]
        if any(keyword in content_lower for keyword in repetitive_keywords):
            score += 0.3
            reasons.append("定期的な作業である")

        # 手順が明確
        if any(
            pattern in content for pattern in ["1.", "2.", "3.", "手順", "ステップ"]
        ):
            score += 0.2
            reasons.append("手順が明確に定義されている")

        # コマンドが含まれる
        if re.search(r"```|`[^`]+`|\$\s+\w+|#\s+\w+", content):
            score += 0.3
            reasons.append("実行コマンドが記載されている")

        # スクリプト化可能な操作
        scriptable_keywords = [
            "コマンド",
            "command",
            "スクリプト",
            "script",
            "api",
            "curl",
            "ssh",
        ]
        if any(keyword in content_lower for keyword in scriptable_keywords):
            score += 0.2
            reasons.append("スクリプト化可能な操作を含む")

        # ITSMタイプによる調整
        if itsm_type == "Change" and "デプロイ" in content_lower:
            score += 0.1
            reasons.append("デプロイ作業は自動化の効果が高い")

        score = min(1.0, score)

        # レベル判定
        if score >= 0.7:
            level = "high"
            recommendation = "自動化を強く推奨します"
        elif score >= 0.4:
            level = "medium"
            recommendation = "自動化を検討する価値があります"
        else:
            level = "low"
            recommendation = "現時点では手動対応が適切です"

        return {
            "score": round(score, 2),
            "level": level,
            "reasons": reasons,
            "recommendation": recommendation,
        }

    def _analyze_technical_risks(self, content: str) -> List[Dict[str, str]]:
        """技術的リスクを分析"""
        risks = []
        content_lower = content.lower()

        # リスクパターン定義
        risk_patterns = [
            {
                "keywords": ["削除", "delete", "drop", "rm -rf", "truncate"],
                "risk": "データ削除リスク",
                "severity": "high",
                "mitigation": "バックアップ取得後に実施してください",
            },
            {
                "keywords": ["本番", "production", "prod"],
                "risk": "本番環境への影響",
                "severity": "high",
                "mitigation": "事前に十分なテストと承認プロセスを経てください",
            },
            {
                "keywords": ["停止", "stop", "shutdown", "ダウン"],
                "risk": "サービス停止リスク",
                "severity": "medium",
                "mitigation": "停止時間の最小化と関係者への事前通知を行ってください",
            },
            {
                "keywords": ["権限", "permission", "chmod 777", "sudo"],
                "risk": "セキュリティリスク",
                "severity": "medium",
                "mitigation": "最小権限の原則に従ってください",
            },
            {
                "keywords": ["パスワード", "password", "認証情報", "credential"],
                "risk": "認証情報の取り扱い",
                "severity": "high",
                "mitigation": "認証情報を平文で保存・送信しないでください",
            },
        ]

        for pattern in risk_patterns:
            if any(keyword in content_lower for keyword in pattern["keywords"]):
                risks.append(
                    {
                        "risk": pattern["risk"],
                        "severity": pattern["severity"],
                        "mitigation": pattern["mitigation"],
                    }
                )

        return risks

    def _extract_commands(self, content: str) -> List[Dict[str, str]]:
        """コマンドやスクリプトを抽出"""
        commands = []

        # コードブロック（```で囲まれた部分）を抽出
        code_blocks = re.findall(r"```(?:\w+)?\n?(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            commands.append({"type": "code_block", "content": block.strip()})

        # インラインコマンド（`で囲まれた部分）を抽出
        inline_commands = re.findall(r"`([^`]+)`", content)
        for cmd in inline_commands:
            if len(cmd) > 5:  # 短すぎるものは除外
                commands.append({"type": "inline_command", "content": cmd})

        # シェルコマンドパターン（$ や # で始まる行）
        shell_commands = re.findall(r"[$#]\s+(.+)", content)
        for cmd in shell_commands:
            commands.append({"type": "shell_command", "content": cmd.strip()})

        return commands

    def _suggest_improvements(
        self, content: str, automation_potential: Dict[str, Any]
    ) -> List[str]:
        """改善提案を生成"""
        improvements = []
        content_lower = content.lower()

        # 自動化提案
        if automation_potential["score"] >= 0.4:
            improvements.append(
                f"自動化の検討: {automation_potential['recommendation']}"
            )

        # ドキュメント改善
        if "エラー" in content_lower and "ログ" not in content_lower:
            improvements.append("エラー内容の詳細ログを記録することを推奨します")

        if "コマンド" in content_lower and "```" not in content:
            improvements.append(
                "コマンドはコードブロック（```）で記載すると可読性が向上します"
            )

        # 監視・アラート
        if (
            any(word in content_lower for word in ["障害", "エラー", "ダウン"])
            and "監視" not in content_lower
        ):
            improvements.append(
                "同様の事象を早期検知するための監視・アラート設定を検討してください"
            )

        # テスト
        if (
            any(word in content_lower for word in ["変更", "リリース", "デプロイ"])
            and "テスト" not in content_lower
        ):
            improvements.append("変更前にテスト環境での検証を実施することを推奨します")

        # バックアップ
        if (
            any(word in content_lower for word in ["削除", "変更", "更新"])
            and "バックアップ" not in content_lower
        ):
            improvements.append("作業前にバックアップを取得することを推奨します")

        return improvements
