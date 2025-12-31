# Hooks Implementation Templates
# フック実装テンプレート

## 概要

このディレクトリには、Claude Code Workflow Studio で使用する
Hooks の実装テンプレートが含まれています。

## Hooks の役割

| Hook | タイプ | 役割 | 実装ファイル |
|------|--------|------|------------|
| pre-task | 並列制御 | SubAgent割り当て | pre_task_template.py |
| on-change | 並列制御 | 影響分析 | on_change_template.py |
| post-task | 並列制御 | 統合レビュー | post_task_template.py |
| duplicate-check | 品質保証 | 重複検知 | duplicate_check_template.py |
| deviation-check | 品質保証 | 逸脱検知 | deviation_check_template.py |
| auto-summary | 品質保証 | 要約生成 | auto_summary_template.py |

## 使用方法

### Workflow Studio での参照

```.workflow
hooks:
  pre-task:
    script: config/hooks_templates/pre_task_template.py
    enabled: true
```

### Python実装との対応

実際の実装: `src/hooks/*.py`
テンプレート: `config/hooks_templates/*.py`

## Hooks の原則

1. **自動修正しない** - 警告・可視化のみ
2. **判断は人が行う** - 最終決定権は人間
3. **実行をブロックしない** - フローを止めない

## カスタマイズ

各Hookはパラメータでカスタマイズ可能:

```yaml
duplicate-check:
  threshold: 0.85  # 類似度閾値
  enabled: true

deviation-check:
  itsm_rules: config/itsm_rules.yaml
  severity_levels: [error, warning, info]
```
