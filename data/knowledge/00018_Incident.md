# ADアカウントロック対応

## メタ情報

| 項目 | 値 |
|------|-----|
| **ナレッジID** | 00018 |
| **ITSMタイプ** | Incident |
| **作成日** | 2026-02-03 |
| **重要度** | High |
| **品質スコア** | 0.52 |
| **ITSM準拠度** | 35% |
| **ステータス** | 改善中 |

## タグ

`Active Directory` `アカウントロック` `認証` `セキュリティ` `ユーザー管理` `パスワード` `アクセス権限` `障害対応` `ヘルプデスク`

## 要約

### 3行要約
1. Active Directoryアカウントがロックされた際の対応手順です
2. 原因は複数回のパスワード入力ミスやセッション残存が主な要因です
3. ADUCまたはPowerShellでロック解除し、必要に応じてパスワードリセットを実施します

### 技術者向け要約
Incident: ADアカウントロック対応 / 関連技術: Active Directory, PowerShell, ADUC, ドメインコントローラー / ロック状態検知あり / 影響範囲: 単一ユーザー / 対応手順確定 / 自動化スクリプト利用可能

### 非技術者向け要約
【インシデント（障害対応）】ADアカウントロック対応 - 影響範囲: ログインできないユーザー / 重要度: 高（業務影響あり） / 状態: 対応可能 / 対応時間目安: 5-15分

---

## 問題の概要

Active Directoryアカウントがロックされ、ユーザーがWindowsログインやシステムアクセスができなくなる事象。

### 症状
- Windowsログイン時に「アカウントがロックされています」エラー
- 社内システムへのシングルサインオン失敗
- VPN接続時の認証エラー
- メールクライアントの認証失敗

### 影響範囲
- 対象ユーザーのすべてのAD認証依存サービス
- 業務遂行への直接的な影響

---

## 原因

**アカウントロックの主な原因**

| 原因 | 頻度 | 説明 |
|------|------|------|
| パスワード入力ミス | 高 | 連続したパスワード入力失敗（既定5回） |
| パスワード変更後のセッション残存 | 中 | 古いパスワードで認証を試みるアプリ |
| モバイルデバイス同期 | 中 | スマートフォンのメール同期設定 |
| サービスアカウント | 低 | 古い資格情報で実行されるサービス |
| 悪意あるアクセス試行 | 低 | 不正アクセスの可能性 |

### 確認方法
```powershell
# アカウント状態の確認
Get-ADUser -Identity "username" -Properties LockedOut, AccountLockoutTime, BadLogonCount

# ロックアウトイベントの確認（ドメインコントローラー）
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4740
} | Where-Object { $_.Properties[0].Value -eq "username" }
```

---

## 対応手順

### 1. 本人確認
- 社員番号または従業員IDで本人確認
- 上長への確認（必要に応じて）

### 2. アカウント状態確認
```powershell
# PowerShellでの確認
Get-ADUser -Identity "username" -Properties LockedOut, AccountLockoutTime, BadLogonCount, LastBadPasswordAttempt

# 結果例:
# LockedOut           : True
# AccountLockoutTime  : 2026-02-03 10:30:00
# BadLogonCount       : 5
```

### 3. ロック解除

#### 方法A: Active Directory Users and Computers (ADUC)
1. ADUCを起動（dsa.msc）
2. 対象ユーザーを検索
3. プロパティ → アカウントタブ
4. 「アカウントのロック解除」チェックボックスをオン
5. OK をクリック

#### 方法B: PowerShell
```powershell
# アカウントのロック解除
Unlock-ADAccount -Identity "username"

# 確認
Get-ADUser -Identity "username" -Properties LockedOut | Select-Object Name, LockedOut
```

### 4. パスワードリセット（必要な場合）
```powershell
# パスワードリセット（次回ログイン時に変更を強制）
Set-ADAccountPassword -Identity "username" -Reset -NewPassword (ConvertTo-SecureString "TempPass123!" -AsPlainText -Force)
Set-ADUser -Identity "username" -ChangePasswordAtLogon $true
```

### 5. 動作確認
- ユーザーにログイン確認を依頼
- 必要に応じてパスワード変更を案内

---

## 自動化スクリプト

### ロック解除スクリプト（運用向け）
```powershell
<#
.SYNOPSIS
    ADアカウントロック解除スクリプト
.DESCRIPTION
    指定したユーザーのADアカウントロックを解除し、ログを記録します
.PARAMETER Username
    ロック解除対象のユーザー名（SAMAccountName）
.EXAMPLE
    .\Unlock-ADUserAccount.ps1 -Username "john.doe"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Username
)

$LogPath = "C:\Logs\ADUnlock_$(Get-Date -Format 'yyyyMMdd').log"

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Out-File -FilePath $LogPath -Append
    Write-Host $Message
}

try {
    # ユーザー存在確認
    $User = Get-ADUser -Identity $Username -Properties LockedOut, AccountLockoutTime -ErrorAction Stop

    if ($User.LockedOut) {
        Write-Log "ユーザー $Username はロックされています。ロック解除を実行します。"
        Unlock-ADAccount -Identity $Username
        Write-Log "ユーザー $Username のロック解除が完了しました。"
    } else {
        Write-Log "ユーザー $Username はロックされていません。"
    }
} catch {
    Write-Log "エラー: $_"
    throw
}
```

### 一括ロック解除スクリプト
```powershell
# 全ロックアカウントの確認と解除
$LockedUsers = Search-ADAccount -LockedOut

foreach ($User in $LockedUsers) {
    Write-Host "ロック解除: $($User.SamAccountName)"
    Unlock-ADAccount -Identity $User.SamAccountName
}
```

---

## 予防策

### 技術的対策
- ロックアウト閾値の適切な設定（推奨: 5-10回）
- ロックアウト期間の設定（推奨: 30分で自動解除）
- パスワード変更時の全デバイス再ログイン案内

### 運用的対策
- 証明書期限の30日前通知（関連: 00017_Incident）
- ユーザー向けセルフサービスパスワードリセット（SSPR）の導入
- 定期的なセキュリティ教育

### 監視スクリプト
```powershell
# ロックアカウント監視（定期実行用）
$LockedUsers = Search-ADAccount -LockedOut
if ($LockedUsers.Count -gt 5) {
    Send-MailMessage -To "it-alert@company.com" -Subject "警告: 大量のADアカウントロック検出" -Body "ロックアカウント数: $($LockedUsers.Count)"
}
```

---

## SubAgent分析結果

| SubAgent | 結果 | スコア |
|----------|------|--------|
| Architect | 条件付き承認、構造的問題指摘 | 0.81 |
| KnowledgeCurator | タグ・カテゴリ抽出完了 | 0.75 |
| ITSMExpert | Incident分類、準拠度35%（要改善） | 0.35 |
| DevOps | 自動化スコアHIGH、スクリプト提供 | 0.75 |
| QA | 品質スコアPOOR、改善必要 | 0.48 |
| Coordinator | 統合レビュー、公開却下 | 0.52 |
| Documenter | 要約生成完了 | 0.70 |

## Hooks実行結果

| Hook | 結果 | 詳細 |
|------|------|------|
| PreTask | PASS | 入力検証完了 |
| DuplicateCheck | PASS | 重複なし |
| DeviationCheck | WARNING | ITSM準拠度35%（改善推奨） |
| AutoSummary | PASS | 要約・キーワード生成完了 |
| PostTask | CONDITIONAL | 改善後の再レビュー必要 |

---

## 改善提案（必須対応）

### 高優先度
1. **初動対応フローの追加**: 発生検知から第一報までのフロー
2. **エスカレーションマトリックスの作成**: 誰に、いつ、どのようにエスカレーションするか
3. **影響範囲の明確化**: 対象ユーザー数、業務影響度の記録方法

### 中優先度
4. **復旧確認チェックリストの追加**: ロック解除後の動作検証方法
5. **PowerShellスクリプトのエラーハンドリング強化**: 監査証跡の確保
6. **構造化マークダウン形式への再編**: 見出し階層の整理

### 低優先度
7. **対応時間目標の明記**: SLA/OLA基準の追加

---

## 関連ナレッジ

- 00017_Incident: VPN接続エラー対応（証明書期限切れ）
- パスワードリセット対応（Request）- 作成予定
- 多要素認証(MFA)設定ガイド（Request）- 作成予定

---

*Generated by Mirai IT Knowledge System - Claude Code Workflow*
*SubAgents: 7 | Hooks: 5 | MCP Integrations: 5*
*Status: REQUIRES_IMPROVEMENT - 再レビュー後に公開予定*
