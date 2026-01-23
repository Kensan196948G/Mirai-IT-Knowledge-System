---
description: Created with Workflow Studio
allowed-tools: Task,AskUserQuestion
---
```mermaid
flowchart TD
    start_node_default([開始])
    end_node_default([終了])

```

## ワークフロー実行ガイド

上記のMermaidフローチャートに従ってワークフローを実行してください。各ノードタイプの実行方法は以下の通りです。

### ノードタイプ別実行方法

- **四角形のノード**: Taskツールを使用してSub-Agentを実行します
- **ひし形のノード(AskUserQuestion:...)**: AskUserQuestionツールを使用してユーザーに質問し、回答に応じて分岐します
- **ひし形のノード(Branch/Switch:...)**: 前処理の結果に応じて自動的に分岐します(詳細セクション参照)
- **四角形のノード(Promptノード)**: 以下の詳細セクションに記載されたプロンプトを実行します
