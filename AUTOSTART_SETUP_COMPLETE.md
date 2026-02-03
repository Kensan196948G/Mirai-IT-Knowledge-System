# Mirai IT Knowledge System - 完全自動起動設定完了

## 📅 設定完了日時
2026-02-03

## ✅ 完了した設定

### 1. WSL systemdサービス登録
- **サービス名**: `mirai-knowledge-dev.service`
- **場所**: `/etc/systemd/system/mirai-knowledge-dev.service`
- **状態**: Active + Enabled
- **動作**: WSL起動時に自動起動

### 2. sudo パスワード不要設定
- **設定ファイル**: `/etc/sudoers.d/mirai-knowledge-nopasswd`
- **許可コマンド**:
  - `sudo systemctl start mirai-knowledge-dev`
  - `sudo systemctl stop mirai-knowledge-dev`
  - `sudo systemctl restart mirai-knowledge-dev`
  - `sudo systemctl status mirai-knowledge-dev`
  - `sudo journalctl -u mirai-knowledge-dev`

### 3. Windowsタスクスケジューラ登録
- **タスク名**: `Mirai-Knowledge-System-AutoStart`
- **トリガー**: ユーザーログオン時
- **動作**: WSL起動 → systemdサービス自動起動
- **状態**: Ready

---

## 🚀 動作フロー

```
1. Windows PC起動
   ↓
2. ユーザーログオン
   ↓
3. タスクスケジューラ起動
   ↓
4. WSL Ubuntu自動起動
   ↓
5. systemd起動
   ↓
6. mirai-knowledge-devサービス自動起動
   ↓
7. AI Orchestrator初期化（1-2分）
   ↓
8. WebUI完全起動
   → http://172.24.133.88:8888
```

---

## 🧪 動作確認（PC再起動後に実施）

### 1. サービス状態確認
```bash
sudo systemctl status mirai-knowledge-dev
```

期待結果: `Active: active (running)`

### 2. WebUIアクセス確認
- URL: http://172.24.133.88:8888
- チャット: http://172.24.133.88:8888/chat

### 3. タスク実行履歴確認（PowerShell）
```powershell
Get-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart' | Select-Object TaskName, State, LastRunTime, LastTaskResult
```

---

## 🔧 管理コマンド

### Windows側（PowerShell - 管理者権限）

```powershell
# タスク状態確認
Get-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart'

# 手動実行
Start-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart'

# 自動起動を無効化
Disable-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart'

# 自動起動を有効化
Enable-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart'

# タスク削除
Unregister-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart' -Confirm:$false
```

### WSL側（Linux）

```bash
# サービス状態確認
sudo systemctl status mirai-knowledge-dev

# サービス停止
sudo systemctl stop mirai-knowledge-dev

# サービス起動
sudo systemctl start mirai-knowledge-dev

# サービス再起動
sudo systemctl restart mirai-knowledge-dev

# リアルタイムログ表示
sudo journalctl -u mirai-knowledge-dev -f

# ログ確認（最新100行）
sudo journalctl -u mirai-knowledge-dev -n 100

# エラーログのみ表示
sudo journalctl -u mirai-knowledge-dev -p err
```

---

## 📊 システム構成

```
┌─────────────────────────────────────────────┐
│ Windows 11                                   │
│ ├─ タスクスケジューラ                       │
│ │  └─ Mirai-Knowledge-System-AutoStart ✅   │
│ │     (ログオン時に自動実行)                │
│ │                                            │
│ └─ WSL2 (Ubuntu)                             │
│    ├─ systemd                                │
│    │  └─ mirai-knowledge-dev.service ✅     │
│    │     (systemd起動時に自動実行)          │
│    │                                         │
│    └─ Mirai IT Knowledge System             │
│       ├─ Python 3.12 + venv                 │
│       ├─ Flask WebUI                        │
│       ├─ AI Orchestrator                    │
│       │  ├─ Claude (Anthropic)              │
│       │  ├─ Gemini (Google)                 │
│       │  └─ Perplexity                      │
│       ├─ DeepL Translation ✅               │
│       ├─ 7 SubAgents                        │
│       ├─ 5 Hooks (並列実行)                 │
│       └─ MCP Integrations                   │
└─────────────────────────────────────────────┘
```

---

## 🎯 アクセス情報

### WebUI
- **ベースURL**: http://172.24.133.88:8888
- **チャット**: http://172.24.133.88:8888/chat
- **インテリジェント検索**: http://172.24.133.88:8888/search/intelligent
- **Server Fault**: http://172.24.133.88:8888/serverfault
- **ナレッジ作成**: http://172.24.133.88:8888/knowledge/create
- **分析**: http://172.24.133.88:8888/analytics
- **設定**: http://172.24.133.88:8888/settings

### API
- **チャットAPI**: http://172.24.133.88:8888/api/chat/ai-answer
- **Server Fault API**: http://172.24.133.88:8888/api/serverfault/questions

---

## ⚠️ トラブルシューティング

### サービスが起動しない場合

1. **サービス状態確認**
   ```bash
   sudo systemctl status mirai-knowledge-dev
   ```

2. **エラーログ確認**
   ```bash
   sudo journalctl -u mirai-knowledge-dev -n 100
   ```

3. **手動起動テスト**
   ```bash
   sudo systemctl restart mirai-knowledge-dev
   ```

### タスクが実行されない場合

1. **タスク状態確認（PowerShell）**
   ```powershell
   Get-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart'
   ```

2. **手動実行テスト**
   ```powershell
   Start-ScheduledTask -TaskName 'Mirai-Knowledge-System-AutoStart'
   ```

3. **タスク履歴確認**
   - タスクスケジューラを開く
   - `Mirai-Knowledge-System-AutoStart`を選択
   - 「履歴」タブで実行履歴を確認

### WebUIにアクセスできない場合

1. **サービス起動確認**
   ```bash
   sudo systemctl status mirai-knowledge-dev
   ```

2. **プロセス確認**
   ```bash
   ps aux | grep python3 | grep app.py
   ```

3. **ポート確認**
   ```bash
   ss -tuln | grep 8888
   ```

4. **ログ確認**
   ```bash
   sudo journalctl -u mirai-knowledge-dev -f
   ```

---

## 📝 設定ファイル

### systemdサービスファイル
- 場所: `/etc/systemd/system/mirai-knowledge-dev.service`
- 元ファイル: `/mnt/d/Mirai-IT-Knowledge-System/scripts/systemd/mirai-knowledge-dev-current.service`

### sudoers設定
- 場所: `/etc/sudoers.d/mirai-knowledge-nopasswd`
- パーミッション: 440

### 環境設定
- 場所: `/mnt/d/Mirai-IT-Knowledge-System/.env.development`
- DeepL APIキー: 設定済み
- AI APIキー: 設定済み

---

## 🎊 完了

すべての設定が完了しました。Windows PC再起動後、自動的にMirai IT Knowledge Systemが起動します。

**起動完了まで約1-2分かかります（AI Orchestrator初期化時間）。**

---

## 📞 サポート

問題が発生した場合は、以下のログを確認してください：

```bash
# リアルタイムログ
sudo journalctl -u mirai-knowledge-dev -f

# エラーログのみ
sudo journalctl -u mirai-knowledge-dev -p err

# 最新1000行
sudo journalctl -u mirai-knowledge-dev -n 1000
```
