"""
Claude-Mem MCP Client
会話履歴メモリクライアント（cccmemory連携）

使い分け:
- memory (知識グラフ): エンティティ・関係管理、短期〜中期コンテキスト
- claude-mem (本クライアント): 会話履歴、セマンティック検索、決定追跡、長期記憶
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import os


class ClaudeMemClient:
    """Claude-Mem連携クライアント

    会話履歴、設計判断、過去の決定事項を記憶・検索する機能を提供
    cccmemory MCP サーバーと連携

    Features:
    - セマンティック検索（類似の会話/決定を検索）
    - 決定追跡（Decision Tracking）
    - Git統合（コミットとの関連付け）
    - 長期記憶（クロスセッション永続化）

    Note: 実際のMCP連携には、MCPツールを使用して
    mcp__claude-mem__* ツールを呼び出す必要があります
    """

    def __init__(self, db_path: Optional[str] = None):
        """初期化

        Args:
            db_path: データベースパス（省略時は環境変数から取得）
        """
        self.enabled = False  # MCP利用可能かどうか
        self.db_path = db_path or os.environ.get(
            "CCCMEMORY_DB_PATH",
            ".memory/claude-mem/conversations.db"
        )
        self._memory_cache = []  # ローカルキャッシュ
        self._decision_cache = []  # 決定追跡キャッシュ

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

        Example:
            memories = client.search_memories("データベース接続エラーの解決方法")
        """
        # TODO: 実際のMCP呼び出し
        # results = mcp_call("mcp__claude-mem__search", {
        #     "query": query,
        #     "limit": limit,
        #     "type": search_type
        # })

        # デモ実装
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
        # TODO: 実際のMCP呼び出し
        # results = mcp_call("mcp__claude-mem__search_similar", {
        #     "content": content,
        #     "threshold": threshold
        # })

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

        # TODO: 実際のMCP呼び出し
        # result = mcp_call("mcp__claude-mem__store_decision", decision_record)

        # ローカルキャッシュに保存
        self._decision_cache.append(decision_record)

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
        # TODO: 実際のMCP呼び出し

        # ローカルキャッシュから検索
        results = self._decision_cache

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
        """
        決定のステータスを更新

        Args:
            decision_id: 決定ID
            status: 新しいステータス（active, superseded, deprecated）
            notes: 更新メモ

        Returns:
            成功したかどうか
        """
        # TODO: 実際のMCP呼び出し

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
        """
        会話を保存

        Args:
            conversation_id: 会話ID
            messages: メッセージリスト [{"role": "user/assistant", "content": "..."}]
            metadata: メタデータ

        Returns:
            成功したかどうか
        """
        conversation = {
            "id": conversation_id,
            "messages": messages,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        # TODO: 実際のMCP呼び出し
        # result = mcp_call("mcp__claude-mem__store_conversation", conversation)

        self._memory_cache.append(conversation)
        return True

    def get_conversation_context(
        self,
        topic: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        トピックに関連する会話コンテキストを取得

        Args:
            topic: トピック
            limit: 最大結果数

        Returns:
            関連会話のリスト
        """
        # TODO: 実際のMCP呼び出し

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
        """
        決定をGitコミットにリンク

        Args:
            decision_id: 決定ID
            commit_hash: コミットハッシュ
            commit_message: コミットメッセージ

        Returns:
            成功したかどうか
        """
        # TODO: 実際のMCP呼び出し

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
        """
        コミットに関連する決定を取得

        Args:
            commit_hash: コミットハッシュ

        Returns:
            関連決定のリスト
        """
        # TODO: 実際のMCP呼び出し

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
        """
        ナレッジを過去の記憶で補強

        Args:
            knowledge_content: ナレッジ内容
            itsm_type: ITSMタイプ

        Returns:
            補強情報
        """
        # キーワード抽出
        keywords = self._extract_keywords(knowledge_content)

        # 関連記憶を検索
        all_memories = []
        for keyword in keywords[:3]:
            memories = self.search_memories(keyword, limit=2)
            all_memories.extend(memories)

        # 関連決定を検索
        related_decisions = self.get_decisions(
            tags=[itsm_type.lower()],
            limit=3
        )

        # 重複除去
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

    def _get_demo_memories(self, query: str) -> List[Dict[str, Any]]:
        """デモ用のメモリデータ"""
        demo_memories = [
            {
                "title": "データベース接続プール設定のベストプラクティス",
                "content": "各アプリケーションサーバーの接続プール最大数は、データベース側の max_connections を超えないように設定する必要がある。",
                "timestamp": "2025-12-15T10:00:00",
                "tags": ["database", "connection-pool", "best-practice"],
                "similarity": 0.85
            },
            {
                "title": "ITSMプロセスにおけるインシデント→問題管理の移行判断",
                "content": "同じ事象が3回以上発生した場合、または根本原因が不明な場合は、問題管理プロセスへエスカレーションする。",
                "timestamp": "2025-11-20T14:30:00",
                "tags": ["itsm", "incident", "problem", "escalation"],
                "similarity": 0.82
            },
            {
                "title": "証明書更新作業の標準手順",
                "content": "SSL/TLS証明書の更新は、期限の2週間前から計画し、ステージング環境で事前検証を行う。",
                "timestamp": "2025-10-05T09:00:00",
                "tags": ["security", "certificate", "procedure"],
                "similarity": 0.78
            },
            {
                "title": "ADアカウントロック対応の教訓",
                "content": "パスワード変更後のセッション残存が主な原因。モバイルデバイスのメール同期設定も確認が必要。",
                "timestamp": "2026-01-15T11:00:00",
                "tags": ["active-directory", "account", "troubleshooting"],
                "similarity": 0.75
            },
            {
                "title": "VPN接続障害の根本原因分析",
                "content": "証明書期限切れが最多の原因。自動更新の仕組みと30日前通知の設定を推奨。",
                "timestamp": "2026-02-01T09:30:00",
                "tags": ["vpn", "certificate", "rca"],
                "similarity": 0.72
            }
        ]

        # クエリに基づいたフィルタリングと類似度ソート
        query_lower = query.lower()
        filtered = []

        for m in demo_memories:
            # 簡易類似度計算
            score = 0.5  # ベーススコア
            if query_lower in m["title"].lower():
                score += 0.3
            if query_lower in m["content"].lower():
                score += 0.2
            for tag in m["tags"]:
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 0.1

            m["similarity"] = min(score, 1.0)
            filtered.append(m)

        # 類似度でソート
        filtered.sort(key=lambda x: x["similarity"], reverse=True)

        return filtered[:5]

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "total_memories": len(self._memory_cache),
            "total_decisions": len(self._decision_cache),
            "enabled": self.enabled,
            "db_path": self.db_path
        }


# グローバルインスタンス
claude_mem_client = ClaudeMemClient()
