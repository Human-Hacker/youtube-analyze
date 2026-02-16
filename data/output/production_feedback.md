# 制作パイプラインへのフィードバック（数値差分）

> 生成日時: 2026-02-17 | 分析サイクル: 10+phase2回完了
> 本ファイルはW-22による自動生成。戦略的な変更分析はAgent F/G（youtube-feedback/）が担当。

---

## 1. 選定基準の数値差分（→ youtube-long/prompts/1. selection_report.md）

### 1-1. GI×CA判定基準
- 現在の閾値: GI×CA ≥ 16
- model.jsonの最新閾値精度: 45.8%（24本評価）

### 1-2. 回帰式
- 現在の記載値: 推定再生数 ≒ -306,908 + 38,970 × GIスコア
- model.json最新: GI×CA vs log(再生数) r=0.276, R²=0.076

> youtube-long が見つかりません。セクション1-3（差異比較）はスキップ。

---

> 自動生成: `python scripts/step3_analyze.py --integrate` (W-22)
> 戦略的変更分析は `youtube-feedback/` の Agent F/G を実行してください。