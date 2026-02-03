# 🤝 Contributing to Mirai IT Knowledge Systems

Mirai IT Knowledge Systems への貢献に興味を持っていただきありがとうございます！

## 📋 貢献方法

### バグ報告

バグを見つけた場合:
1. [Issues](https://github.com/Kensan196948G/Mirai-IT-Knowledge-System/issues) で既存のissueを検索
2. 見つからない場合は、新しいissueを作成
3. バグ報告テンプレートに従って詳細を記載

### 機能リクエスト

新機能の提案:
1. [Issues](https://github.com/Kensan196948G/Mirai-IT-Knowledge-System/issues) で機能リクエストを作成
2. 機能の必要性と利点を説明
3. 可能であれば実装案を提示

### プルリクエスト

コードの貢献:

1. **フォーク**
   ```bash
   # リポジトリをフォーク
   gh repo fork Kensan196948G/Mirai-IT-Knowledge-System
   ```

2. **ブランチ作成**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **開発**
   - コードを記述
   - テストを追加
   - ドキュメントを更新

4. **コミット**
   ```bash
   git add .
   git commit -m "✨ Add: Your feature description"
   ```

5. **プッシュ**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **プルリクエスト作成**
   - GitHubでプルリクエストを作成
   - 変更内容を詳しく説明

## 📝 コーディング規約

### Python

- PEP 8に準拠
- 型ヒントを使用
- Docstringを記述

```python
def process_knowledge(
    title: str,
    content: str,
    itsm_type: str = 'Other'
) -> Dict[str, Any]:
    """
    ナレッジを処理

    Args:
        title: タイトル
        content: 内容
        itsm_type: ITSMタイプ

    Returns:
        処理結果
    """
    pass
```

### コミットメッセージ

絵文字プレフィックスを使用:
- ✨ `:sparkles:` - 新機能
- 🐛 `:bug:` - バグ修正
- 📝 `:memo:` - ドキュメント
- 🎨 `:art:` - コード構造改善
- ⚡ `:zap:` - パフォーマンス改善
- 🔧 `:wrench:` - 設定変更
- ✅ `:white_check_mark:` - テスト追加

例:
```
✨ Add: ナレッジ評価機能を追加
🐛 Fix: 検索結果の表示バグを修正
📝 Docs: セットアップガイドを更新
```

## 🧪 テスト

テストを実行:
```bash
# ワークフローテスト
python3 scripts/test_workflow.py

# データベーステスト
python3 scripts/init_db.py
```

## 📚 ドキュメント

ドキュメントの更新:
- 新機能を追加した場合は `docs/NEW_FEATURES.md` を更新
- APIを変更した場合は関連ドキュメントを更新

## 🔍 コードレビュー

プルリクエストは以下の点をレビューします:
- コードの品質
- テストの網羅性
- ドキュメントの完全性
- セキュリティ

## 📞 質問

質問がある場合:
- [Issues](https://github.com/Kensan196948G/Mirai-IT-Knowledge-System/issues) で質問
- [Discussions](https://github.com/Kensan196948G/Mirai-IT-Knowledge-System/discussions) で議論

## 📄 ライセンス

貢献することで、あなたの貢献が MIT License の下でライセンスされることに同意します。

---

**ご協力ありがとうございます！** 🎉
