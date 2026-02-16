# 分析パイプライン司令官

YouTube動画分析の全工程を管理・実行するオーケストレーター。

## パイプライン実行順序

```
Step 1: python scripts/step1_fetch.py           # データ取得（YouTube API）
Step 2: python scripts/step2_build_model.py      # モデル構築（相関分析・フィルター）
  ┌─── 分析ループ（最大5回）─────────────────────────┐
  │ Step 3: python scripts/step3_analyze.py          # 分析準備（データ集計 + ワークスペース作成）
  │ Step 4: Agent C (agents/analyze-step4-hypothesis.md)  # 仮説生成（メタ分析）
  │ Step 5: Agent E (agents/analyze-step5-verification.md) # 仮説検証（レッドチーム）
  │ Step 6: python scripts/step3_analyze.py --integrate    # 結果統合 + 収束判定
  └─── 未収束なら Step 3 へ ─────────────────────────┘
Step 7: python scripts/step7_pdca.py VIDEO_ID    # PDCA評価（新動画の予測 vs 実績）
```

## 各ステップの詳細

| Step | 種別 | 実行コマンド | 入力 | 出力 |
|------|------|-------------|------|------|
| 1 | script | `python scripts/step1_fetch.py` | YouTube API | `data/input/videos/*.json`, `data/input/video_index.json` |
| 2 | script | `python scripts/step2_build_model.py` | `data/input/videos/*.json`, `data/input/human_scores.json` | `data/output/model.json`, `data/output/analysis_report.md` |
| 3 | script | `python scripts/step3_analyze.py` | `data/output/model.json`, 全入力データ | `data/output/data_summary.md` |
| 4 | agent | `agents/analyze-step4-hypothesis.md` | `data/output/data_summary.md`, `data/output/insights.md`, `data/output/golden_theory.json` | `data/output/new_hypotheses.md` |
| 5 | agent | `agents/analyze-step5-verification.md` | `data/output/new_hypotheses.md`, 全入力データ | `data/output/verification_report.md` |
| 6 | script | `python scripts/step3_analyze.py --integrate` | `data/output/new_hypotheses.md`, `data/output/verification_report.md` | `data/output/insights.md`, `data/output/golden_theory.json`, `data/output/analysis_conclusion.md` |
| 7 | script | `python scripts/step7_pdca.py VIDEO_ID` | 新動画データ, `data/output/model.json` | `data/output/pdca_*.md` |

## ループ条件

- **正常終了**: 全仮説が「支持」or「修正」で、未解決矛盾がゼロ
- **成果ありで終了**: 一部採択・一部棄却だが、新たな手がかりがない
- **上限終了**: 5サイクル到達。残存矛盾を `data/output/insights.md` に記録して終了

## エージェント一覧

| エージェント | ファイル | 役割 |
|------------|---------|------|
| Agent C | `agents/analyze-step4-hypothesis.md` | メタ分析。HIT/MISS共通点抽出 → 水平思考 → 因果仮説生成 |
| Agent E | `agents/analyze-step5-verification.md` | レッドチーム。仮説を否定方向で検証し、確証バイアスを防止 |

## 参照プロンプト

| ファイル | 内容 | 参照元 |
|---------|------|--------|
| `prompts/coordinator.md` | 分析サイクル仕様書 | 本パイプライン |
| `prompts/youtube_fundamentals.md` | YouTube前提知識（アルゴリズム・視聴者心理） | Agent C, Agent E |
| `prompts/scoring_criteria.md` | GI/CAスコアリング定量基準 | Agent C, Agent E |

## ディレクトリ構造

```
youtube-analyze/
├── commands/
│   └── analyze-pipeline.md          # 本ファイル（パイプライン司令官）
├── agents/
│   ├── analyze-step4-hypothesis.md  # Step 4: 仮説生成
│   └── analyze-step5-verification.md # Step 5: 仮説検証
├── prompts/
│   ├── coordinator.md               # 分析サイクル仕様書
│   ├── youtube_fundamentals.md      # YouTube前提知識
│   └── scoring_criteria.md          # GI/CAスコアリング基準
├── scripts/
│   ├── auth.py                      # 認証ユーティリティ
│   ├── step1_fetch.py               # Step 1: データ取得
│   ├── step2_build_model.py         # Step 2: モデル構築
│   ├── step2_filters.py             #   └─ 内部: 3段階フィルター
│   ├── step2_patterns.py            #   └─ 内部: パターン分析
│   ├── step2_history.py             #   └─ 内部: 履歴管理
│   ├── step2_report.py              #   └─ 内部: レポート生成
│   ├── step3_analyze.py             # Step 3/6: 分析準備 & 結果統合
│   ├── step7_pdca.py                # Step 7: PDCA評価
│   ├── data_summarizer.py           # ユーティリティ: データ集計
│   ├── config.py                    # 設定
│   └── common/
│       ├── data_loader.py
│       └── metrics.py
├── data/
│   ├── input/                       # 入力データ（API取得・手動評価）
│   ├── output/                      # 出力データ（モデル・分析結果）
│   └── history/                     # 履歴（バージョン管理）
├── templates/                       # テンプレート
└── projects/                        # アーティスト別手動データ
```

## エラー時のリカバリ

| 状況 | 対応 |
|------|------|
| Step 1 でAPI認証エラー | `python scripts/auth.py` で再認証 |
| Step 2 でデータ不足 | `data/input/videos/` にJSONが存在するか確認 |
| Step 4/5 でAgent出力が不正 | `data/output/` の出力ファイルを確認し、JSONブロックのフォーマットを修正 |
| Step 6 でパースエラー | Agent出力のJSONブロックが正しい形式か確認 |
| ループが収束しない | 5サイクル上限で自動終了。`data/output/insights.md` に未解決問題を記録 |
