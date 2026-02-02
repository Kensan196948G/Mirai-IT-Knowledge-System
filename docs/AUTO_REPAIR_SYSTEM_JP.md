# 🤖 自動エラー検知・修復システム - 完全日本語解説
# Auto Error Detection & Repair System - Complete Japanese Guide

---

## 📖 目次

1. [システム概要](#システム概要)
2. [アーキテクチャの詳細説明](#アーキテクチャの詳細説明)
3. [実装されたコンポーネント](#実装されたコンポーネント)
4. [動作フローの詳細](#動作フローの詳細)
5. [使い方](#使い方)
6. [設定とカスタマイズ](#設定とカスタマイズ)
7. [トラブルシューティング](#トラブルシューティング)

---

## システム概要

### 🎯 このシステムは何をするのか？

このシステムは、**プロジェクトで発生するエラーを自動的に検知し、自動的に修復を試みる**システムです。

**具体例：**
- データベース接続エラーが発生 → 自動的にデータベースサービスを再起動
- Pythonモジュールが見つからない → 自動的に依存関係を再インストール
- ディスク容量不足 → 自動的に一時ファイルをクリーンアップ

### 💡 なぜこのシステムが必要なのか？

従来の開発では：
```
エラー発生 → 開発者が気づく → 原因調査 → 手動で修復 → テスト
```

このシステムでは：
```
エラー発生 → システムが自動検知 → 自動修復 → 自動テスト → (成功したら完了)
```

**メリット：**
- ⏰ 夜間や休日のエラーも自動対応
- 🚀 修復時間の大幅短縮
- 📊 エラーパターンの自動記録
- 🔄 同じエラーが再発しても自動対応

### 🏗️ システムの設計思想

本システムは **ITSM（IT Service Management）** および **SRE（Site Reliability Engineering）** の原則に基づいて設計されています。

**三位一体モデル：**
1. **GitHub Actions** = 無慈悲な進行管理者（判断のみ）
2. **ClaudeCode** = 賢い修復職人（実行のみ）
3. **state.json** = 申し送りノート（連携の要）

---

## アーキテクチャの詳細説明

### 📐 2層アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│  制御レイヤ (GitHub Actions)                    │
│  ・実行の開始/停止を決める                      │
│  ・何回修復を試みるか決める                     │
│  ・いつ諦めるか決める                           │
│  ・次の実行をスケジュールする                   │
└───────────────┬─────────────────────────────────┘
                │ 呼び出し
                ▼
┌─────────────────────────────────────────────────┐
│  修復レイヤ (ClaudeCode / Python)               │
│  ・ログを読んでエラーを見つける                 │
│  ・エラーの種類を判定する                       │
│  ・適切な修復方法を選ぶ                         │
│  ・修復アクションを実行する                     │
└─────────────────────────────────────────────────┘
```

### 🔑 重要な設計原則

#### 原則1: レイヤの完全分離

| レイヤ | やること | やらないこと |
|--------|----------|--------------|
| **制御レイヤ**<br>(GitHub Actions) | ・実行を開始する<br>・成功/失敗を判定する<br>・何回繰り返すか決める<br>・状態を保存する | ・エラーの内容を理解する<br>・修復方法を考える<br>・実際に修復する |
| **修復レイヤ**<br>(ClaudeCode) | ・エラーを検出する<br>・エラーの種類を判定する<br>・修復アクションを実行する<br>・修復結果を報告する | ・何回実行するか決める<br>・いつ諦めるか決める<br>・次の実行時刻を決める |

**なぜ分離するのか？**
- 混ぜると「無限ループ」や「暴走」が発生する危険がある
- それぞれの役割を明確にすることで、保守性が向上する
- テストやデバッグが容易になる

#### 原則2: Run（実行単位）は必ず終了する

GitHub Actions での1回の実行（Run）は：
- 最大15回の修復ループを回す
- どんな状況でも30分以内に終了する
- 問題が解決しない場合は、次のRunに引き継ぐ

**疑似無限ループの仕組み：**
```
Run #1 (最大15回修復) → 終了 → 5分待機
    ↓
Run #2 (最大15回修復) → 終了 → 5分待機
    ↓
Run #3 (最大15回修復) → 終了 → 5分待機
    ↓
... (テストが成功するまで継続)
```

これは「無限に見える」が、実際は：
- 各Runは必ず終了する
- GitHub Actionsの実行モデルとして健全
- リソースの暴走を防ぐ

#### 原則3: 状態は全てstate.jsonに集約

**Run間の情報伝達：**

```json
{
  "retry_required": true,           // 再試行が必要か？
  "run_count": 3,                   // これまでに何回実行したか？
  "last_error_id": "import_error",  // 最後に検出したエラーは？
  "last_error_summary": "Python Import Error",
  "last_attempt_at": "2026-02-02T06:00:00+00:00",
  "cooldown_until": "2026-02-02T06:05:00+00:00"  // いつまでクールダウン？
}
```

**なぜstate.jsonが重要なのか？**
- Run #1 で検出したエラーを Run #2 に伝える
- 同じエラーで無限ループしないよう制御する
- システム全体の状態を一箇所で管理する

---

## 実装されたコンポーネント

### 1️⃣ 制御レイヤ: GitHub Actions Workflow

**ファイル:** `.github/workflows/auto_repair.yml`

**主な機能：**

#### 🕐 スケジュール実行
```yaml
on:
  schedule:
    - cron: '*/5 * * * *'  # 5分ごとに実行
```

**解説：** 
- Cronジョブ形式で定期実行を設定
- `*/5` = 5分ごと
- `* * * *` = 毎時、毎日、毎月、全曜日

#### 🔄 修復ループ制御

```bash
# 疑似コード
MAX_ITERATIONS=15
ITERATION=0

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  # テスト実行
  run_tests
  
  if tests_passed; then
    echo "✅ 成功！"
    exit 0
  fi
  
  # エラー検知・修復
  auto_fix_daemon
  
  ITERATION=$((ITERATION + 1))
done

echo "⚠️ 15回試みましたが修復できませんでした"
exit 1
```

**解説：**
- 最大15回まで修復を試みる
- テストが成功したら即座に終了
- 15回失敗したら、次のRunに委ねる

#### 💾 状態管理

```bash
# state.json の更新
python3 << 'EOF'
import json
state = {
  "retry_required": not test_passed,
  "run_count": previous_count + 1,
  "last_run_at": datetime.now().isoformat()
}
# ... 保存処理
EOF
```

**解説：**
- Pythonスクリプトでstate.jsonを更新
- 次のRunが参照できるようにコミット・プッシュ
- Git履歴として状態変化が記録される

### 2️⃣ 修復レイヤ: auto_fix_daemon.py

**ファイル:** `scripts/auto_fix_daemon.py`

**クラス構造：**

```python
class AutoFixDaemon:
    def __init__(self):
        # 設定の読み込み
        self.error_patterns = self._load_error_patterns()
        self.state = self._load_state()
    
    def perform_health_checks(self):
        """ヘルスチェックを実行"""
        # データベースファイルは存在するか？
        # ディスク容量は十分か？
        # 必要なモジュールはインストールされているか？
        pass
    
    def scan_logs_for_errors(self, log_content):
        """ログからエラーを検出"""
        # 正規表現パターンマッチング
        # エラーの種類を特定
        pass
    
    def repair_error(self, error):
        """エラーを修復"""
        # 修復アクションの実行
        # 結果のログ記録
        pass
```

**主な機能の詳細：**

#### 🔍 エラー検出

```python
def scan_logs_for_errors(self, log_content):
    detected_errors = []
    
    for pattern_config in self.error_patterns['patterns']:
        # パターンマッチング
        if re.search(pattern_config['patterns'], log_content):
            # クールダウン中かチェック
            if not self.check_cooldown(pattern_config['id']):
                detected_errors.append(pattern_config)
    
    return detected_errors
```

**解説：**
- `config/error_patterns.json` で定義されたパターンと照合
- 正規表現を使って柔軟にマッチング
- クールダウン期間中のエラーはスキップ

#### 🔧 修復アクションの実行

```python
def execute_repair_action(self, action):
    action_type = action['type']
    
    if action_type == 'install_dependencies':
        # requirements.txt から依存関係をインストール
        subprocess.run([
            sys.executable, '-m', 'pip', 
            'install', '-r', 'requirements.txt'
        ])
    
    elif action_type == 'cleanup_temp_files':
        # /tmp 内の一時ファイルを削除
        # (安全性のため /tmp のみ)
        ...
    
    # その他のアクションタイプ...
```

**解説：**
- アクションタイプに応じて適切な処理を実行
- 安全性を考慮した実装（例: /tmp のみクリーンアップ）
- 実行結果をログに記録

#### ⏱️ クールダウン管理

```python
def check_cooldown(self, error_id, cooldown_seconds):
    """クールダウン期間中かチェック"""
    if self.state.get('last_error_id') != error_id:
        return False  # 違うエラーなのでOK
    
    cooldown_until = self.state.get('cooldown_until')
    if not cooldown_until:
        return False  # クールダウン設定なし
    
    return datetime.now() < datetime.fromisoformat(cooldown_until)

def set_cooldown(self, error_id, cooldown_seconds):
    """クールダウン期間を設定"""
    self.state['last_error_id'] = error_id
    self.state['cooldown_until'] = (
        datetime.now() + timedelta(seconds=cooldown_seconds)
    ).isoformat()
```

**解説：**
- 同じエラーに対して連続して修復しないよう制御
- デフォルトで300秒（5分）のクールダウン
- 無限ループの防止に必須の機能

### 3️⃣ 設定ファイル: error_patterns.json

**ファイル:** `config/error_patterns.json`

**構造：**

```json
{
  "patterns": [
    {
      "id": "database_connection_error",        // エラーの一意識別子
      "name": "Database Connection Error",      // 表示名
      "patterns": [                             // マッチさせる文字列パターン
        "sqlite3.OperationalError",
        "database is locked"
      ],
      "severity": "critical",                   // 重要度
      "auto_repair": true,                      // 自動修復を有効にするか
      "actions": [                              // 実行する修復アクション
        {
          "type": "restart_service",
          "service": "database",
          "wait_seconds": 5
        }
      ],
      "cooldown_seconds": 300                   // クールダウン期間
    }
  ],
  "health_checks": [
    {
      "name": "database",
      "type": "file_exists",
      "path": "db/knowledge.db",
      "required": true
    }
  ]
}
```

**定義済みのエラーパターン（6種類）：**

1. **database_connection_error** (critical)
   - データベース接続エラー
   - アクション: データベースサービスの再起動

2. **redis_connection_error** (high)
   - Redis接続エラー
   - アクション: Redisサービスの再起動

3. **disk_space_error** (critical)
   - ディスク容量不足
   - アクション: 一時ファイルのクリーンアップ、ログローテーション

4. **import_error** (high)
   - Pythonモジュールのインポートエラー
   - アクション: requirements.txt から依存関係を再インストール

5. **http_timeout** (medium)
   - HTTPリクエストのタイムアウト
   - アクション: 待機してリトライ

6. **test_failure** (medium)
   - テストの失敗
   - アクション: なし（情報記録のみ）

**定義済みのヘルスチェック（4種類）：**

1. **file_exists**: ファイルの存在確認
2. **file_writable**: ファイルの書き込み権限確認
3. **disk_space**: ディスク空き容量確認
4. **python_imports**: Pythonモジュールのインポート確認

### 4️⃣ 状態ファイル: state.json

**ファイル:** `data/state.json`

**フィールドの説明：**

```json
{
  "retry_required": true,
  // true = 次のRunで再試行が必要
  // false = 問題なし、次のRunは不要
  
  "run_count": 3,
  // これまでに何回Runを実行したか
  
  "last_error_id": "import_error",
  // 最後に検出したエラーのID
  
  "last_error_summary": "Python Import Error",
  // 最後に検出したエラーの概要
  
  "last_attempt_at": "2026-02-02T06:00:00+00:00",
  // 最後に修復を試みた日時
  
  "cooldown_until": "2026-02-02T06:05:00+00:00",
  // クールダウンがいつまで続くか
  
  "last_run_at": "2026-02-02T06:00:00+00:00",
  // 最後にRunを実行した日時
  
  "last_run_result": "failed",
  // 最後のRunの結果 ("success" or "failed")
  
  "last_iterations": 5,
  // 最後のRunで何回修復を試みたか
  
  "last_repairs_made": 2
  // 最後のRunで何個のエラーを修復したか
}
```

**使用例：**

```bash
# 状態を確認
cat data/state.json

# 状態をリセット（手動介入時）
cat > data/state.json << 'EOF'
{
  "retry_required": false,
  "run_count": 0,
  "last_error_id": null
}
EOF
```

### 5️⃣ 修復ログ: repair_log.json

**ファイル:** `data/repair_log.json`

**構造：**

```json
[
  {
    "timestamp": "2026-02-02T06:00:00+00:00",
    "action": {
      "error_id": "import_error",
      "error_name": "Python Import Error",
      "action": {
        "type": "install_dependencies",
        "file": "requirements.txt"
      },
      "result": {
        "success": true,
        "message": "Dependencies installed"
      }
    }
  }
]
```

**特徴：**
- 全ての修復アクションが記録される
- タイムスタンプ付きで時系列に並ぶ
- 成功/失敗の両方を記録
- 最新100件のみ保持（古いものは自動削除）

**使用例：**

```bash
# ログを確認
cat data/repair_log.json | python3 -m json.tool

# 最新のログのみ表示
tail -n 20 data/repair_log.json
```

---

## 動作フローの詳細

### 🎬 1回のRun内での処理フロー

```
【Step 1】Runの開始
   ↓
【Step 2】前回の状態を読み込み（state.json）
   ↓
【Step 3】テストを実行
   ↓
【Step 4】テスト成功？
   YES → 【Step 9】へ
   NO  → 【Step 5】へ
   ↓
【Step 5】auto_fix_daemon.py を呼び出し
   ├─ ヘルスチェック実行
   ├─ ログスキャン（エラー検出）
   ├─ エラーパターンマッチング
   ├─ クールダウンチェック
   └─ 修復アクション実行
   ↓
【Step 6】修復成功？
   YES → イテレーションカウント +1
   NO  → イテレーションカウント +1
   ↓
【Step 7】イテレーション < 15 かつ テスト失敗？
   YES → 【Step 3】へ戻る（ループ）
   NO  → 【Step 8】へ
   ↓
【Step 8】state.json を更新
   ├─ retry_required の設定
   ├─ run_count のインクリメント
   ├─ 最終実行結果の記録
   └─ Git コミット・プッシュ
   ↓
【Step 9】サマリー出力
   ├─ 実行回数
   ├─ イテレーション数
   ├─ 修復回数
   └─ 最終ステータス
   ↓
【Step 10】Run終了
```

### 🔄 複数Run間での連携

```
┌──────────────────────────────────────────────────────┐
│ Run #1 (06:00 開始)                                  │
│ ├─ テスト失敗検出                                    │
│ ├─ import_error を検出                               │
│ ├─ 依存関係を再インストール                          │
│ ├─ 再テスト → まだ失敗                               │
│ ├─ 15回試行 → 未解決                                 │
│ └─ state.json 更新: retry_required=true              │
│    cooldown_until=06:05                              │
└──────────────────────────────────────────────────────┘
         ↓ (5分待機)
┌──────────────────────────────────────────────────────┐
│ Run #2 (06:05 開始)                                  │
│ ├─ state.json 読み込み                               │
│ ├─ クールダウン期間終了を確認                        │
│ ├─ テスト実行 → まだ失敗                             │
│ ├─ import_error を再検出                             │
│ ├─ 別の修復方法を試行                                │
│ ├─ 再テスト → 成功！                                 │
│ └─ state.json 更新: retry_required=false             │
└──────────────────────────────────────────────────────┘
         ↓ (5分待機)
┌──────────────────────────────────────────────────────┐
│ Run #3 (06:10 開始)                                  │
│ ├─ state.json 読み込み                               │
│ ├─ retry_required=false を確認                       │
│ ├─ テスト実行 → 成功                                 │
│ └─ 何もせず終了（システム健全）                       │
└──────────────────────────────────────────────────────┘
```

### 📊 エラー検出から修復までの詳細

#### 例: Pythonインポートエラーの場合

**1. エラー発生**
```python
# テスト実行中
import some_module  # ModuleNotFoundError: No module named 'some_module'
```

**2. auto_fix_daemon による検出**
```python
def scan_logs_for_errors(self, log_content):
    # "ModuleNotFoundError" パターンを検出
    for pattern in error_patterns['patterns']:
        if pattern['id'] == 'import_error':
            if re.search("ModuleNotFoundError", log_content):
                return [pattern]  # マッチ！
```

**3. クールダウンチェック**
```python
def check_cooldown(self, error_id):
    # このエラーは最近修復したか？
    if self.state['last_error_id'] == 'import_error':
        cooldown_until = self.state['cooldown_until']
        if now < cooldown_until:
            return True  # クールダウン中、スキップ
    return False  # OK、修復可能
```

**4. 修復アクション実行**
```python
def execute_repair_action(self, action):
    if action['type'] == 'install_dependencies':
        # pip install を実行
        subprocess.run([
            sys.executable, '-m', 'pip', 
            'install', '-r', 'requirements.txt'
        ])
        # 成功！
```

**5. クールダウン設定**
```python
def set_cooldown(self, error_id, cooldown_seconds):
    self.state['last_error_id'] = 'import_error'
    self.state['cooldown_until'] = (now + 300秒).isoformat()
    self._save_state()
```

**6. ログ記録**
```python
def _log_repair_action(self, action):
    log_entry = {
        "timestamp": "2026-02-02T06:00:00",
        "action": {
            "error_id": "import_error",
            "result": {"success": True}
        }
    }
    # repair_log.json に追加
```

---

## 使い方

### 🚀 初回セットアップ

#### 1. リポジトリの確認

```bash
# 必要なファイルが存在するか確認
ls -la .github/workflows/auto_repair.yml
ls -la scripts/auto_fix_daemon.py
ls -la config/error_patterns.json
ls -la data/state.json

# 全て存在すればOK
```

#### 2. GitHub Actions の有効化

GitHubのリポジトリ設定で、GitHub Actionsが有効になっていることを確認：

```
リポジトリページ → Settings → Actions → General
→ "Allow all actions and reusable workflows" を選択
```

#### 3. ローカルテスト（オプション）

```bash
# 依存関係のインストール
pip install -r requirements.txt

# デーモンの動作確認
echo "Test log output" | python3 scripts/auto_fix_daemon.py

# テストスイートの実行
python3 scripts/test_auto_repair.py
```

### 🎮 手動実行（推奨：最初のテスト）

1. GitHubのリポジトリページを開く
2. 「**Actions**」タブをクリック
3. 左サイドバーから「**Auto Error Detection & Repair Loop**」を選択
4. 右上の「**Run workflow**」ボタンをクリック
5. ブランチを選択（通常は main）
6. （オプション）max_iterations を変更（デフォルト: 15）
7. 「**Run workflow**」をクリックして実行開始

**実行中の確認：**
- ワークフローが起動すると、リアルタイムでログが表示される
- 各ステップの進行状況が確認できる
- エラーがあれば赤色で表示される

**実行後の確認：**
- Summary セクションに詳細なレポートが表示される
- Run Count、Iterations、Repairs Made などの統計情報
- state.json と repair_log.json の内容

### 🤖 自動実行

特に設定不要。システムは自動的に5分ごとに実行されます。

**確認方法：**

```bash
# 次の実行予定時刻を確認
# GitHub Actions の画面で「Next run」を確認

# 実行履歴を確認
# Actions タブ → Auto Error Detection & Repair Loop
# → 実行履歴が時系列で表示される
```

**自動実行の停止：**

一時的に停止したい場合：
```
Actions タブ → Auto Error Detection & Repair Loop
→ 右上の「...」メニュー → Disable workflow
```

再開したい場合：
```
同じメニューから → Enable workflow
```

### 📊 モニタリング

#### GitHub Actions での監視

**リアルタイム監視：**
1. Actions タブを開く
2. 実行中のワークフローをクリック
3. 各ステップのログをリアルタイムで確認

**統計情報の確認：**
- Run Count: 累計実行回数
- Iterations: 今回のRunでの試行回数
- Repairs Made: 今回のRunでの修復回数
- Final Status: 最終結果（成功/失敗）

#### ローカルでの監視

```bash
# 状態ファイルを監視（5秒ごとに更新表示）
watch -n 5 cat data/state.json

# 修復ログを監視
tail -f data/repair_log.json

# 最近の修復履歴を表示
cat data/repair_log.json | python3 -m json.tool | tail -50
```

#### 通知の設定

GitHub Actions の通知を有効にする：
```
GitHub アカウント設定 → Notifications → Actions
→ 「Send notifications for failed workflows」にチェック
→ メールで失敗通知を受け取れる
```

---

## 設定とカスタマイズ

### 🎨 新しいエラーパターンの追加

#### 例: データベースロックエラーの追加

`config/error_patterns.json` に追加：

```json
{
  "id": "database_lock_error",
  "name": "Database Lock Error",
  "patterns": [
    "database is locked",
    "database table is locked",
    "SQLITE_BUSY"
  ],
  "severity": "high",
  "auto_repair": true,
  "actions": [
    {
      "type": "wait_and_retry",
      "wait_seconds": 10,
      "max_retries": 3
    },
    {
      "type": "restart_service",
      "service": "database",
      "wait_seconds": 5
    }
  ],
  "cooldown_seconds": 600
}
```

**フィールドの説明：**

- **id**: エラーの一意識別子（英数字、アンダースコア）
- **name**: エラーの表示名
- **patterns**: マッチングに使用する正規表現パターン（配列）
- **severity**: 重要度（critical, high, medium, low）
- **auto_repair**: 自動修復を有効にするか（true/false）
- **actions**: 実行する修復アクション（配列、順番に実行）
- **cooldown_seconds**: クールダウン期間（秒）

### 🔧 新しい修復アクションタイプの追加

`scripts/auto_fix_daemon.py` の `execute_repair_action` メソッドに追加：

```python
def execute_repair_action(self, action: Dict) -> Dict:
    action_type = action['type']
    
    # ... 既存のアクションタイプ ...
    
    elif action_type == 'clear_cache':
        # カスタムアクション: キャッシュのクリア
        cache_dir = self.project_root / action.get('cache_dir', '.cache')
        
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(exist_ok=True)
            
            result = {
                'success': True,
                'message': f"Cache cleared: {cache_dir}"
            }
        else:
            result = {
                'success': False,
                'message': f"Cache directory not found: {cache_dir}"
            }
    
    return result
```

**使用例:**

```json
{
  "id": "cache_corruption",
  "name": "Cache Corruption",
  "patterns": ["cache corrupted", "invalid cache"],
  "actions": [
    {
      "type": "clear_cache",
      "cache_dir": ".cache"
    }
  ]
}
```

### 🕐 実行間隔の変更

`.github/workflows/auto_repair.yml` の cron 式を変更：

```yaml
on:
  schedule:
    # 10分ごと
    - cron: '*/10 * * * *'
    
    # 1時間ごと
    - cron: '0 * * * *'
    
    # 毎日午前2時
    - cron: '0 2 * * *'
    
    # 平日の毎時0分と30分
    - cron: '0,30 * * * 1-5'
```

**Cron式の読み方：**
```
┌───────────── 分 (0 - 59)
│ ┌───────────── 時 (0 - 23)
│ │ ┌───────────── 日 (1 - 31)
│ │ │ ┌───────────── 月 (1 - 12)
│ │ │ │ ┌───────────── 曜日 (0 - 6, 0=日曜日)
│ │ │ │ │
* * * * *
```

### 🔢 最大イテレーション数の変更

`.github/workflows/auto_repair.yml` の環境変数を変更：

```yaml
env:
  MAX_ITERATIONS: 20  # 15 → 20 に変更
```

または、手動実行時にパラメータで指定：
```
Run workflow 画面 → max_iterations に 20 を入力
```

### 🏥 新しいヘルスチェックの追加

`config/error_patterns.json` の `health_checks` セクションに追加：

```json
{
  "name": "network_connectivity",
  "type": "http_request",
  "url": "https://api.example.com/health",
  "timeout": 5,
  "required": false
}
```

対応するチェック処理を `auto_fix_daemon.py` に追加：

```python
elif check_type == 'http_request':
    url = check.get('url')
    timeout = check.get('timeout', 5)
    
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code != 200:
            issues.append({
                'check': check_name,
                'issue': f"HTTP {response.status_code}: {url}",
                'severity': 'warning'
            })
    except requests.RequestException as e:
        issues.append({
            'check': check_name,
            'issue': f"Network error: {str(e)}",
            'severity': 'high' if check.get('required') else 'warning'
        })
```

---

## トラブルシューティング

### ❌ よくある問題と解決方法

#### 問題1: ワークフローが実行されない

**症状:**
- Actionsタブにワークフローが表示されない
- スケジュール実行が開始されない

**原因と解決方法:**

1. **GitHub Actions が無効化されている**
   ```
   Settings → Actions → General
   → "Allow all actions" が選択されているか確認
   ```

2. **ワークフローファイルにエラーがある**
   ```bash
   # YAMLファイルの構文チェック
   python3 -c "import yaml; yaml.safe_load(open('.github/workflows/auto_repair.yml'))"
   ```

3. **mainブランチにマージされていない**
   ```bash
   # ブランチを確認
   git branch
   
   # mainブランチにマージ
   git checkout main
   git merge your-branch
   git push
   ```

4. **リポジトリがフォークである**
   - フォークされたリポジトリではスケジュール実行が無効
   - 手動実行（workflow_dispatch）のみ使用可能

#### 問題2: 修復が動作しない

**症状:**
- エラーが検出されるが修復されない
- 修復アクションが実行されない

**原因と解決方法:**

1. **クールダウン期間中**
   ```bash
   # state.json を確認
   cat data/state.json | python3 -m json.tool
   
   # cooldown_until が未来の時刻なら、その時刻まで待つ
   
   # または、手動でリセット
   python3 << 'EOF'
   import json
   state = json.load(open('data/state.json'))
   state['cooldown_until'] = None
   state['last_error_id'] = None
   json.dump(state, open('data/state.json', 'w'), indent=2)
   EOF
   ```

2. **auto_repair が false に設定されている**
   ```json
   // config/error_patterns.json を確認
   {
     "id": "your_error",
     "auto_repair": false  // ← これを true に変更
   }
   ```

3. **エラーパターンがマッチしていない**
   ```bash
   # ローカルでテスト
   echo "Your error message" | python3 scripts/auto_fix_daemon.py
   
   # パターンが検出されるか確認
   ```

4. **修復アクションが失敗している**
   ```bash
   # repair_log.json で詳細を確認
   cat data/repair_log.json | python3 -m json.tool
   
   # result.success が false なら、result.message を確認
   ```

#### 問題3: 無限ループに陥っているように見える

**症状:**
- 同じエラーが何度も検出される
- 修復が成功しているのに再発する

**原因と解決方法:**

1. **修復が実際には失敗している**
   ```bash
   # repair_log.json で成功率を確認
   cat data/repair_log.json | grep '"success": false'
   ```

2. **テスト自体に問題がある**
   ```bash
   # テストを直接実行して確認
   python3 scripts/test_workflow.py
   
   # エラーメッセージを確認
   ```

3. **クールダウン期間が短すぎる**
   ```json
   // config/error_patterns.json
   {
     "cooldown_seconds": 300  // ← 600（10分）などに延長
   }
   ```

4. **根本原因が修復されていない**
   - 修復アクションは一時的な対処療法
   - 根本的な問題を手動で調査・修正する必要がある

#### 問題4: state.json が更新されない

**症状:**
- 修復を実行してもstate.jsonが古いまま
- Run間で情報が引き継がれない

**原因と解決方法:**

1. **Gitのプッシュ権限がない**
   ```yaml
   # .github/workflows/auto_repair.yml を確認
   # GITHUB_TOKEN が正しく設定されているか
   ```

2. **Gitの設定が不正**
   ```bash
   # ワークフロー内で確認
   git config --local user.email "action@github.com"
   git config --local user.name "GitHub Action"
   ```

3. **ファイルに変更がない**
   ```bash
   # ローカルで確認
   git status
   git diff data/state.json
   ```

#### 問題5: メモリ不足・タイムアウト

**症状:**
- ワークフローが途中で停止する
- 30分でタイムアウトする

**原因と解決方法:**

1. **イテレーション数が多すぎる**
   ```yaml
   # MAX_ITERATIONS を減らす
   env:
     MAX_ITERATIONS: 10  # 15 → 10
   ```

2. **修復アクションが重い**
   ```bash
   # 重い処理を最適化
   # 例: npm install → npm ci（高速）
   ```

3. **テストが遅い**
   ```bash
   # テストの実行時間を確認
   time python3 scripts/test_workflow.py
   
   # 遅いテストを最適化または分割
   ```

### 🔍 デバッグ方法

#### ローカルでのデバッグ

```bash
# 1. 詳細ログを有効にして実行
python3 -u scripts/auto_fix_daemon.py --test-output "エラーメッセージ" 2>&1 | tee debug.log

# 2. Pythonデバッガで実行
python3 -m pdb scripts/auto_fix_daemon.py

# 3. エラーパターンのテスト
python3 << 'EOF'
import re
pattern = "ModuleNotFoundError"
text = "エラー: ModuleNotFoundError: No module named 'foo'"
if re.search(pattern, text):
    print("マッチしました！")
else:
    print("マッチしませんでした")
EOF
```

#### GitHub Actions でのデバッグ

```yaml
# ワークフローに追加
- name: Debug Info
  run: |
    echo "=== Environment ==="
    env | sort
    
    echo "=== state.json ==="
    cat data/state.json || echo "Not found"
    
    echo "=== repair_log.json ==="
    cat data/repair_log.json || echo "Not found"
    
    echo "=== Disk Space ==="
    df -h
    
    echo "=== Python Version ==="
    python3 --version
    
    echo "=== Installed Packages ==="
    pip list
```

### 📞 サポート

問題が解決しない場合：

1. **GitHubのIssuesで質問**
   - リポジトリのIssuesタブで新しいIssueを作成
   - 問題の詳細、エラーメッセージ、環境情報を記載

2. **ログの提供**
   - GitHub Actionsのログをダウンロード
   - state.json と repair_log.json の内容を共有

3. **再現手順の提供**
   - どのような操作で問題が発生したか
   - 期待する動作と実際の動作

---

## 📚 参考情報

### システムの制限事項

| 項目 | 制限値 | 理由 |
|------|--------|------|
| 最大イテレーション | 15回/Run | リソース使用量の制限 |
| Run タイムアウト | 30分 | GitHub Actions の制限 |
| クールダウン期間 | 300秒（デフォルト） | 無限ループ防止 |
| 修復ログ保持数 | 100件 | ディスク容量の節約 |
| 実行間隔 | 5分（最小） | GitHub Actions の制限 |

### GitHub Actions の制限

- **並列実行数**: 無料プランは最大20並列
- **実行時間**: 無料プランは月2000分まで
- **ストレージ**: 無料プランは500MBまで
- **保持期間**: ログは90日間保持

### セキュリティ考慮事項

✅ **実装済みの安全機能:**
- ファイル削除は `/tmp` のみに制限
- システムコマンドは限定的な範囲で実行
- 依存関係のインストールは `requirements.txt` のみ
- ファイル権限チェックは読み取り専用

⚠️ **注意事項:**
- 本番環境では、修復アクションの内容を十分に検証してください
- 重要なデータがある場合は、事前にバックアップを取ってください
- 予期しない動作をした場合は、すぐにワークフローを無効化してください

### 推奨される運用方法

1. **段階的な導入**
   - まず手動実行でテスト
   - 問題がなければ自動実行を有効化
   - 最初は監視を強化

2. **定期的な見直し**
   - 月次でエラーパターンを見直し
   - 修復成功率をモニタリング
   - 不要なパターンは削除

3. **ドキュメント化**
   - カスタマイズ内容を記録
   - トラブル時の対応手順を整備
   - チーム内で知識を共有

4. **バックアップ**
   - state.json の定期バックアップ
   - error_patterns.json のバージョン管理
   - 重要な修復ログの保存

### 関連技術・概念

- **ITSM (IT Service Management)**: IT サービス管理のベストプラクティス
- **SRE (Site Reliability Engineering)**: サイトの信頼性を高めるエンジニアリング手法
- **ISO/IEC 20000**: IT サービスマネジメントの国際規格
- **自己修復システム (Self-Healing System)**: 障害を自動的に検知・修復するシステム

---

## 🎓 まとめ

### このシステムで実現できること

✅ **自動化されたエラー対応**
- 24時間365日、常時監視
- 人間の介入なしに修復を試行
- 対応履歴の自動記録

✅ **開発効率の向上**
- 単純なエラーは自動修復
- 開発者は本質的な問題に集中
- デバッグ時間の短縮

✅ **運用の安定化**
- 既知のエラーパターンに即座に対応
- エラーの再発防止（クールダウン）
- システム状態の可視化

### 今後の拡張可能性

🚀 **さらなる機能追加**
- Slack/Discord への通知連携
- より高度なエラー分析（AI活用）
- 複数プロジェクトでの横断的な運用
- カスタムダッシュボードの構築

### 最後に

このシステムは、**完全自動化を目指すものではなく、開発者をサポートするツール**です。

- 全てのエラーが自動修復できるわけではありません
- 根本的な問題解決には人間の判断が必要です
- システムの動作を定期的に確認することが重要です

**ただし、適切に設定・運用すれば、開発チームの強力な味方となります！**

---

**実装完了日**: 2026-02-02  
**ドキュメントバージョン**: 1.0.0  
**ライセンス**: Mirai IT Knowledge System に準拠

---

## 📮 お問い合わせ

ご質問、ご要望、バグ報告は GitHubの Issues までお願いします。

**Happy Auto-Repairing! 🤖✨**
