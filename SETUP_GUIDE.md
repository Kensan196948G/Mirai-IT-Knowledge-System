# 🚀 Mirai IT Knowledge Systems - セットアップガイド

**バージョン**: 2.0.0
**最終更新**: 2025-12-31

---

## 📋 システム要件

- **OS**: Linux（ネイティブ）
- **Python**: 3.8以上
- **ネットワーク**: IPアドレス割り当て済み
- **ストレージ**: 最低1GB

---

## ⚡ クイックスタート

### 1. データベース初期化

```bash
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-Systems

# データベースを初期化
python3 scripts/init_db.py

# フィードバック機能を有効化
python3 scripts/apply_feedback_schema.py
```

### 2. サンプルデータ生成（オプション）

```bash
# 7件のリアルなサンプルナレッジを生成
python3 scripts/generate_sample_data.py
```

### 3. WebUI起動

```bash
# 簡単起動（推奨）
./start.sh

# または直接起動
python3 src/webui/app.py
```

**アクセス方法:**
- ネットワーク経由: `http://192.168.0.187:8888`
- ローカル: `http://localhost:8888`
- ポート番号: 8888（他プロジェクトと競合なし）

---

## 🔧 詳細セットアップ

### IPアドレスの確認

```bash
# 割り当てられたIPアドレスを確認
hostname -I
```

現在のIPアドレス: **192.168.0.187**

### 依存パッケージのインストール

```bash
# 必要なパッケージをインストール
pip install flask

# オプション: requirements.txtから一括インストール
pip install -r requirements.txt
```

### データベース構造の確認

```bash
# データベースの内容を確認
python3 -c "
from src.mcp.sqlite_client import SQLiteClient
client = SQLiteClient()
stats = client.get_statistics()
print(f'総ナレッジ数: {stats[\"total_knowledge\"]}')
"
```

---

## 🌐 MCP連携の設定

### Context7統合（技術ドキュメント）

Context7 MCPは自動的に初期化されます。

**使用例:**
```python
from src.mcp.mcp_integration import mcp_integration

# 技術ドキュメント検索
docs = mcp_integration.query_context7_docs("flask", "routing")
```

### Claude-Mem統合（設計記憶）

Claude-Mem MCPも自動的に初期化されます。

**使用例:**
```python
# 過去の記憶を検索
memories = mcp_integration.search_claude_mem("データベース接続プール")
```

### GitHub統合（バージョン管理）

詳細は [docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md) を参照してください。

**簡易セットアップ:**
```bash
# GitHubリポジトリを作成（Web UIまたはCLI）
gh repo create Mirai-IT-Knowledge-System --public

# リモート追加
git remote add origin git@github.com:YOUR_USERNAME/Mirai-IT-Knowledge-System.git

# 初回プッシュ
git add .
git commit -m "🎉 Initial commit"
git push -u origin main
```

---

## 📊 機能確認

### 1. ナレッジ作成のテスト

```bash
# テストワークフローを実行
python3 scripts/test_workflow.py
```

**確認事項:**
- ✅ 7つのSubAgentが正常動作
- ✅ 品質スコアが算出される
- ✅ Markdownファイルが生成される

### 2. WebUIの確認

ブラウザで `http://192.168.0.187:8888` にアクセスし、以下を確認:

- ✅ ホームページの統計情報
- ✅ ナレッジ一覧表示
- ✅ 検索機能
- ✅ 新規作成フォーム
- ✅ ダッシュボード
- ✅ 分析ページ（`/analytics`）
- ✅ フィードバックページ（`/feedback`）

### 3. MCP連携の確認

```python
from src.mcp.mcp_integration import mcp_integration

# ステータス確認
status = mcp_integration.get_status()
print(status)
# => {'context7': True, 'claude_mem': True, 'github': True}
```

---

## 🎯 運用開始

### 日常的な使用方法

#### 1. ナレッジの作成

**WebUIから:**
1. `http://192.168.0.187:8888/knowledge/create` にアクセス
2. タイトルと内容を入力
3. ITSMタイプを選択（または自動判定）
4. 「ナレッジを作成」をクリック

**Pythonから:**
```python
from src.core.workflow import WorkflowEngine

engine = WorkflowEngine()
result = engine.process_knowledge(
    title="障害対応記録",
    content="...",
    itsm_type="Incident",
    created_by="ops_team"
)
```

#### 2. ナレッジの検索

**WebUIから:**
1. `/knowledge/search` にアクセス
2. キーワード、ITSMタイプ、タグで検索
3. 結果からナレッジを選択

**APIから:**
```bash
curl "http://192.168.0.187:8888/api/knowledge?query=データベース"
```

#### 3. フィードバックの収集

**ナレッジ評価:**
```python
from src.mcp.feedback_client import FeedbackClient

client = FeedbackClient()
client.add_knowledge_feedback(
    knowledge_id=1,
    rating=5,
    feedback_type="helpful",
    comment="とても参考になりました"
)
```

**システムフィードバック:**
- `/feedback` ページからフィードバック送信

#### 4. 分析レポートの確認

**WebUIから:**
- `/analytics` にアクセス

**Pythonから:**
```python
from src.core.analytics import AnalyticsEngine

engine = AnalyticsEngine()
report = engine.generate_comprehensive_report(days=30)
recommendations = engine.generate_recommendations()
```

### 定期メンテナンス

#### 週次タスク
```bash
# データベースバックアップ
cp db/knowledge.db backups/knowledge-$(date +%Y%m%d).db

# 分析レポート生成
python3 -c "
from src.core.analytics import AnalyticsEngine
engine = AnalyticsEngine()
report = engine.generate_comprehensive_report(days=7)
print('週次レポート:', report)
"
```

#### 月次タスク
- フィードバックのレビュー
- 低評価ナレッジの改善
- システムフィードバックの対応
- GitHubへのプッシュ確認

---

## 🔒 セキュリティ設定

### ファイアウォール設定

```bash
# ポート5000を開放（必要に応じて）
sudo ufw allow 5000/tcp
```

### アクセス制限

社内ネットワーク限定でアクセスを制限する場合:

```python
# src/webui/app.py の最後を編集
if __name__ == '__main__':
    # 特定のIPからのみアクセス可能
    app.run(host='192.168.0.187', port=5000, debug=False)
```

---

## 📚 ドキュメント

- [README.md](README.md) - プロジェクト概要
- [ARCHITECTURE.md](ARCHITECTURE.md) - システム設計
- [docs/NEW_FEATURES.md](docs/NEW_FEATURES.md) - 新機能詳細
- [docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md) - GitHub連携
- [RELEASE_NOTES_V2.md](RELEASE_NOTES_V2.md) - リリースノート

---

## 🆘 トラブルシューティング

### WebUIが起動しない

```bash
# Flaskがインストールされているか確認
python3 -c "import flask; print(flask.__version__)"

# ポートが使用中でないか確認
lsof -i:8888

# 別のポートで起動
python3 src/webui/app.py --port 8080
```

### データベースエラー

```bash
# データベースを再初期化
rm db/knowledge.db
python3 scripts/init_db.py
python3 scripts/apply_feedback_schema.py
```

### MCP連携エラー

```python
# MCPステータス確認
from src.mcp.mcp_integration import mcp_integration
print(mcp_integration.get_status())

# 再初期化
from src.mcp.mcp_integration import auto_initialize
auto_initialize()
```

---

## 📞 サポート

問題が解決しない場合:
1. ログを確認: `data/logs/`
2. GitHubでIssueを作成
3. ドキュメントを再確認

---

## ✅ チェックリスト

セットアップ完了の確認:

- [ ] データベース初期化完了
- [ ] フィードバックスキーマ適用完了
- [ ] サンプルデータ生成完了（オプション）
- [ ] WebUIが起動し、アクセス可能
- [ ] IPアドレス（192.168.0.187）でアクセス可能
- [ ] MCP連携が有効化されている
- [ ] GitHub連携設定完了（オプション）
- [ ] ナレッジ作成テスト成功
- [ ] フィードバック機能動作確認
- [ ] 分析機能動作確認

**全てチェックが付けば、運用開始準備完了です！** 🎉

---

## 🚀 次のステップ

1. 実際のインシデント・問題を登録
2. チームメンバーへの使い方説明
3. フィードバックの収集開始
4. 週次レポートの確認
5. 継続的な改善

---

**Mirai IT Knowledge Systems v2.0へようこそ！**
