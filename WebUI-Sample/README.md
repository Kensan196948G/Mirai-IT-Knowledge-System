# WebUI-Sample - 使い方ガイド

## 概要

Mirai IT Knowledge SystemsのWebUI-Sampleは、HTML5ベースのフロントエンドサンプル実装です。
セマンティックHTML、モダンCSS、バニラJavaScriptを使用した、アクセシブルでレスポンシブなWebアプリケーションのサンプルです。

## 📁 ファイル構成

```
WebUI-Sample/
├── index.html          # ダッシュボード（統計カード、最近のナレッジ一覧）
├── search.html         # ナレッジ検索（検索ボックス、フィルターパネル、結果表示）
├── create.html         # ナレッジ作成フォーム（タイトル、内容、ITSM自動判定）
├── detail.html         # ナレッジ詳細表示（全文表示、関連ナレッジ）
├── sf-browser.html     # Server Fault質問ブラウジング
├── README.md           # このファイル
├── css/
│   ├── base.css        # ベーススタイル、CSS変数、リセット
│   ├── components.css  # 再利用可能なUIコンポーネント
│   ├── layout.css      # ページレイアウト、ヘッダー、フッター
│   └── responsive.css  # レスポンシブデザイン
├── js/
│   └── components/     # JavaScriptモジュール（将来の拡張用）
├── assets/             # 画像、アイコンなど
└── data/               # サンプルデータ（JSON）
```

## 🚀 使い方

### 1. ローカルでの起動

#### 方法A: シンプルなHTTPサーバー（Python）

```bash
# WebUI-Sampleディレクトリに移動
cd Z:\Mirai-IT-Knowledge-Systems\WebUI-Sample

# Python 3でHTTPサーバーを起動
python -m http.server 8000

# ブラウザで開く
# http://localhost:8000
```

#### 方法B: Node.jsのhttp-server

```bash
# http-serverをグローバルインストール（初回のみ）
npm install -g http-server

# WebUI-Sampleディレクトリに移動
cd Z:\Mirai-IT-Knowledge-Systems\WebUI-Sample

# サーバーを起動
http-server -p 8000

# ブラウザで開く
# http://localhost:8000
```

#### 方法C: Live Server（VS Code拡張機能）

1. VS Codeで「Live Server」拡張機能をインストール
2. `index.html`を右クリック
3. "Open with Live Server"を選択

### 2. ページ一覧

#### ダッシュボード（index.html）
- **URL**: `http://localhost:8000/index.html`
- **機能**:
  - 統計カード（総ナレッジ数、ITSMタイプ別件数）
  - クイックアクション（作成、検索、Server Fault参照）
  - 最近のナレッジ一覧（カード形式）
  - クイックガイド（キーボードショートカット、使い方ヒント）

#### ナレッジ検索（search.html）
- **URL**: `http://localhost:8000/search.html`
- **機能**:
  - 検索ボックス（リアルタイム検索対応）
  - フィルターパネル（ITSMタイプ、タグ、作成日）
  - 検索結果一覧（カード形式）
  - 並び替え（新しい順、古い順、関連度順）
  - ページネーション

#### ナレッジ作成（create.html）
- **URL**: `http://localhost:8000/create.html`
- **機能**:
  - タイトル入力
  - 内容入力（Markdown対応）
  - ITSM自動判定（AI推奨表示）
  - タグ入力（推奨タグ表示）
  - プレビュー機能
  - 下書き自動保存（localStorage）

#### ナレッジ詳細（detail.html）
- **URL**: `http://localhost:8000/detail.html?id=1`
- **機能**:
  - ナレッジ全文表示
  - メタデータ（作成日時、更新日時、作成者）
  - AI要約（技術者向け、非技術者向け）
  - タグ一覧
  - 抽出された知見
  - 関連ナレッジ一覧
  - 編集、共有、印刷機能

#### Server Fault質問ブラウジング（sf-browser.html）
- **URL**: `http://localhost:8000/sf-browser.html`
- **機能**:
  - Server Fault質問一覧
  - フィルター（ステータス、タグ、スコア）
  - 統計情報（取得済み質問数、解決済み数）
  - インポート機能（質問をナレッジとして保存）
  - 外部リンク（Server Faultの元の質問へ）

## 🎨 デザインシステム

### CSS変数

プロジェクト全体で使用されるデザイントークンは`base.css`で定義されています。

```css
:root {
  /* Primary Colors */
  --color-primary: #667eea;
  --color-primary-dark: #5568d3;
  --color-primary-light: #8b9ef7;

  /* ITSM Type Colors */
  --color-incident: #f44336;
  --color-problem: #ff9800;
  --color-change: #2196F3;
  --color-release: #4CAF50;
  --color-request: #9C27B0;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* Shadows, Borders, Transitions... */
}
```

### ITSMタイプカラーコード

| ITSMタイプ | カラー | 用途 |
|-----------|--------|------|
| Incident | Red (#f44336) | インシデント管理 |
| Problem | Orange (#ff9800) | 問題管理 |
| Change | Blue (#2196F3) | 変更管理 |
| Release | Green (#4CAF50) | リリース管理 |
| Request | Purple (#9C27B0) | サービスリクエスト |
| Other | Gray (#607D8B) | その他 |

## ⌨️ キーボードショートカット

| キー | 機能 | 対応ページ |
|------|------|-----------|
| `/` | 検索ページへ移動 | 全ページ |
| `n` | 新規作成ページへ移動 | 全ページ |
| `?` | ヘルプを表示 | 全ページ |
| `e` | ナレッジを編集 | detail.html |
| `s` | ナレッジを共有 | detail.html |
| `p` | ナレッジを印刷 | detail.html |

## ♿ アクセシビリティ

### 実装されている機能

1. **セマンティックHTML**
   - 適切な見出し階層（`<h1>`〜`<h6>`）
   - `<article>`, `<section>`, `<nav>` などの構造化要素
   - `<main>`, `<header>`, `<footer>` によるランドマーク

2. **ARIA属性**
   - `role="banner"`, `role="navigation"`, `role="main"`, `role="contentinfo"`
   - `aria-label`, `aria-labelledby`, `aria-describedby`
   - `aria-current="page"` でアクティブページを明示
   - `aria-live="polite"` で動的コンテンツ変更を通知

3. **キーボード操作**
   - すべてのインタラクティブ要素がフォーカス可能
   - `tabindex="0"` で適切なフォーカス順序
   - `onkeypress` でEnterキーによるアクション実行

4. **視覚的配慮**
   - 十分なコントラスト比（WCAG AA準拠）
   - フォーカスインジケーターの視認性
   - アイコンに`aria-hidden="true"`を設定

## 📱 レスポンシブデザイン

### ブレークポイント

```css
/* Small devices (tablets, 576px and up) */
@media (min-width: 576px) { }

/* Medium devices (tablets, 768px and up) */
@media (min-width: 768px) { }

/* Large devices (desktops, 992px and up) */
@media (min-width: 992px) { }

/* Extra large devices (large desktops, 1200px and up) */
@media (min-width: 1200px) { }
```

### 対応デバイス

- ✅ スマートフォン（320px〜）
- ✅ タブレット（768px〜）
- ✅ デスクトップ（1024px〜）
- ✅ 大画面ディスプレイ（1920px〜）

## 🔧 カスタマイズ

### カラーテーマの変更

`base.css`のCSS変数を変更することで、全体のカラーテーマを簡単に変更できます。

```css
:root {
  --color-primary: #your-color;
  --color-primary-dark: #your-dark-color;
  --color-primary-light: #your-light-color;
}
```

### フォントの変更

```css
:root {
  --font-family: 'Your Font', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

### スペーシングの調整

```css
:root {
  --spacing-md: 1.5rem;  /* デフォルトは1rem */
  --spacing-lg: 2rem;    /* デフォルトは1.5rem */
}
```

## 🔌 API連携

現在のサンプルは静的なHTMLですが、本番環境では以下のAPIエンドポイントと連携します。

### エンドポイント例

```javascript
// ナレッジ一覧取得
GET /api/knowledge

// ナレッジ詳細取得
GET /api/knowledge/{id}

// ナレッジ作成
POST /api/knowledge

// ナレッジ検索
POST /api/knowledge/search

// ITSM自動判定
POST /api/classify

// Server Fault質問取得
GET /api/serverfault/questions
```

### 実装例

```javascript
// ナレッジ作成
async function createKnowledge(data) {
  const response = await fetch('/api/knowledge', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  });
  return await response.json();
}

// ナレッジ検索
async function searchKnowledge(query, filters) {
  const response = await fetch('/api/knowledge/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, filters })
  });
  return await response.json();
}
```

## 🧪 テスト

### 手動テスト項目

#### 機能テスト
- [ ] ダッシュボードの統計カードが正しく表示される
- [ ] 検索機能が動作する
- [ ] フィルター機能が動作する
- [ ] ナレッジ作成フォームが送信できる
- [ ] ナレッジ詳細が正しく表示される
- [ ] Server Fault質問一覧が表示される

#### レスポンシブテスト
- [ ] スマートフォン（320px）で正しく表示される
- [ ] タブレット（768px）で正しく表示される
- [ ] デスクトップ（1024px）で正しく表示される

#### アクセシビリティテスト
- [ ] キーボードのみで全機能が操作できる
- [ ] スクリーンリーダーで内容が読み上げられる
- [ ] コントラスト比が十分である

#### ブラウザ互換性テスト
- [ ] Chrome（最新版）
- [ ] Firefox（最新版）
- [ ] Safari（最新版）
- [ ] Edge（最新版）

## 📚 技術スタック

### フロントエンド
- **HTML5**: セマンティックHTML、ARIA属性
- **CSS3**: CSS Grid、Flexbox、CSS変数、アニメーション
- **JavaScript**: バニラJS、ES6+、非同期処理

### 開発ツール
- **エディタ**: Visual Studio Code
- **ブラウザ**: Chrome DevTools
- **バージョン管理**: Git

### 将来の拡張候補
- **フレームワーク**: React, Vue.js, Svelte
- **ビルドツール**: Vite, Webpack
- **テスト**: Jest, Playwright
- **Linter**: ESLint, Stylelint

## 🐛 トラブルシューティング

### ページが表示されない

**原因**: HTTPサーバーが起動していない、またはポートが使用されている

**解決策**:
```bash
# ポートを変更して再起動
python -m http.server 8080
```

### スタイルが適用されない

**原因**: CSSファイルのパスが正しくない

**解決策**: ブラウザのDevToolsでネットワークタブを確認し、404エラーがないかチェック

### JavaScriptが動作しない

**原因**: ブラウザのコンソールにエラーが表示されている

**解決策**: ブラウザのDevToolsでコンソールタブを確認し、エラーメッセージを確認

### レスポンシブデザインが動作しない

**原因**: `viewport`メタタグが設定されていない

**解決策**: HTMLの`<head>`に以下を追加
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

## 📖 参考リンク

### HTML/CSS/JavaScript
- [MDN Web Docs](https://developer.mozilla.org/)
- [Web.dev](https://web.dev/)
- [CSS-Tricks](https://css-tricks.com/)

### アクセシビリティ
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

### デザインシステム
- [Material Design](https://material.io/)
- [Tailwind CSS](https://tailwindcss.com/)

## 📝 ライセンス

このサンプルコードはMirai IT Knowledge Systemsプロジェクトの一部です。

## 🤝 コントリビューション

改善提案やバグ報告は、プロジェクトのIssueトラッカーまでお願いします。

---

**最終更新**: 2026-01-20
**バージョン**: 1.0.0
