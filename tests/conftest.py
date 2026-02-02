"""
Pytest共通設定とフィクスチャ
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


@pytest.fixture(scope="session")
def project_root_path():
    """プロジェクトルートパスを返す"""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_knowledge_data():
    """テスト用のサンプルナレッジデータ"""
    return {
        "title": "Webサーバー障害対応手順",
        "content": """
本番環境のWebサーバーがダウンした際の対応手順です。
1. サーバーの状態確認
2. エラーログの確認
3. サービスの再起動
4. 動作確認
緊急時は管理者に連絡してください。
        """.strip(),
        "itsm_type": "Incident",
        "tags": ["Webサーバー", "障害対応", "運用手順"],
        "created_by": "test_user"
    }


@pytest.fixture
def sample_subagent_results():
    """テスト用のサブエージェント実行結果"""
    return {
        "architect": {
            "status": "success",
            "message": "設計整合性チェック完了",
            "data": {
                "consistency_score": 0.9
            }
        },
        "knowledge_curator": {
            "status": "success",
            "message": "ナレッジ分類完了",
            "data": {
                "tags": ["Webサーバー", "障害対応"],
                "keywords": ["障害", "対応", "手順"],
                "importance": {
                    "score": 0.8,
                    "level": "high"
                }
            }
        },
        "itsm_expert": {
            "status": "success",
            "message": "ITSM妥当性チェック完了",
            "data": {
                "deviations": [],
                "compliance_score": 0.95,
                "recommendations": [
                    "影響範囲の記載を追加することを推奨します"
                ]
            }
        },
        "qa": {
            "status": "success",
            "message": "品質チェック完了",
            "data": {
                "duplicates": {
                    "similar_knowledge": [],
                    "high_similarity_count": 0
                },
                "quality_score": 0.85
            }
        },
        "documenter": {
            "status": "success",
            "message": "ドキュメント生成完了",
            "data": {
                "summary_technical": "Webサーバーダウン時の標準対応手順",
                "summary_non_technical": "Webサービスが停止した時の復旧方法",
                "summary_3lines": [
                    "Webサーバー障害発生時の対応手順",
                    "状態確認、ログ確認、再起動の流れ",
                    "緊急時は管理者へエスカレーション"
                ],
                "markdown": "# Webサーバー障害対応手順\n...",
                "html": "<h1>Webサーバー障害対応手順</h1>..."
            }
        }
    }


@pytest.fixture
def sample_hook_results():
    """テスト用のフック実行結果"""
    return [
        {
            "hook_name": "duplicate_check",
            "result": "pass",
            "message": "重複するナレッジは検出されませんでした",
            "details": {"threshold": 0.85}
        },
        {
            "hook_name": "deviation_check",
            "result": "pass",
            "message": "ITSM原則に準拠しています",
            "details": {"compliance_score": 0.95}
        },
        {
            "hook_name": "auto_summary",
            "result": "pass",
            "message": "3行要約が正常に生成されました",
            "details": {"line_count": 3}
        }
    ]
