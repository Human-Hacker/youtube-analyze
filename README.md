# YouTube Analytics Agent for ウタヨミ

## パイプライン実行順序

```
Step 1: python scripts/step1_fetch.py           # データ取得（YouTube API）
Step 2: python scripts/step2_build_model.py      # モデル構築（相関分析・フィルター）
  ┌─── 分析ループ（最大5回）─────────────────────────┐
  │ Step 3: python scripts/step3_analyze.py          # 分析準備（データ集計）
  │ Step 4: Agent C (agents/analyze-step4-hypothesis.md)  # 仮説生成
  │ Step 5: Agent E (agents/analyze-step5-verification.md) # 仮説検証
  │ Step 6: python scripts/step3_analyze.py --integrate    # 結果統合
  └─── 未収束なら Step 3 へ ─────────────────────────┘
Step 7: python scripts/step7_pdca.py VIDEO_ID    # PDCA評価（新動画）
```

## ディレクトリ構造

```
youtube-analyze/
├── commands/
│   └── analyze-pipeline.md          # パイプライン司令官（詳細仕様）
│
├── agents/
│   ├── analyze-step4-hypothesis.md  # Step 4: 仮説生成（メタ分析）
│   └── analyze-step5-verification.md # Step 5: 仮説検証（レッドチーム）
│
├── prompts/
│   ├── coordinator.md               # 分析サイクル仕様書
│   ├── youtube_fundamentals.md      # YouTube前提知識
│   └── scoring_criteria.md          # GI/CAスコアリング基準
│
├── scripts/
│   ├── auth.py                      # OAuth認証ユーティリティ
│   ├── step1_fetch.py               # Step 1: データ取得
│   ├── step2_build_model.py         # Step 2: モデル構築
│   ├── step2_filters.py             #   └─ 3段階フィルター
│   ├── step2_patterns.py            #   └─ パターン分析
│   ├── step2_history.py             #   └─ 履歴管理
│   ├── step2_report.py              #   └─ レポート生成
│   ├── step3_analyze.py             # Step 3/6: 分析準備 & 結果統合
│   ├── step7_pdca.py                # Step 7: PDCA評価
│   ├── data_summarizer.py           # データ集計ユーティリティ
│   ├── config.py                    # 設定（パス・閾値）
│   └── common/
│       ├── data_loader.py           # データ読み込み
│       └── metrics.py               # 統計計算
│
├── templates/
│   └── script_analysis_template.json # 台本分析テンプレート
│
├── data/
│   ├── input/                       # 入力データ
│   │   ├── videos/                  # 動画アナリティクスJSON（24本）
│   │   ├── scripts/                 # 台本構造分析JSON（24本）
│   │   ├── video_index.json         # 全動画一覧
│   │   ├── human_scores.json        # 人間評価スコア（GI/CA）
│   │   └── analysis_fundamentals.json # 分析の不変基盤
│   ├── output/                      # 現バージョンの全出力
│   │   ├── model.json               # 現在のモデル
│   │   ├── golden_theory.json       # 黄金理論（原則+チェックリスト）
│   │   ├── insights.md              # 採択/棄却仮説の全履歴
│   │   ├── analysis_report.md       # 分析レポート
│   │   ├── analysis_conclusion.md   # 分析結論（誰でも読める形式）
│   │   ├── data_summary.md          # 全動画指標サマリ
│   │   ├── new_hypotheses.md        # Agent C出力
│   │   ├── verification_report.md   # Agent E出力
│   │   └── prompt_modifications.md  # プロンプト改善提案
│   └── history/                     # 過去バージョンのスナップショット
│       ├── index.md                 # バージョン履歴
│       └── v{X.X}_{date}/           # スナップショット
│
├── projects/                        # アーティスト別手動データ（CSV）
├── client_secret.json               # Google Cloud認証（※Git管理外）
└── token.json                       # OAuthトークン（※Git管理外）
```

## 初回セットアップ

1. Google Cloud設定 → `client_secret.json` を配置
2. `python scripts/auth.py` で OAuth認証（`token.json` 生成）
3. `python scripts/step1_fetch.py` で全動画データ取得
4. YouTube Studio から手動CSV取得 → `python scripts/step1_fetch.py --merge`
5. 台本構造分析JSON を `data/input/scripts/` に配置
6. `python scripts/step2_build_model.py` でモデル構築

## 継続運用（新動画公開ごと）

1. `python scripts/step7_pdca.py VIDEO_ID` で予測 vs 実績を評価
2. 手動CSV追記 + 台本分析 → `python scripts/step7_pdca.py VIDEO_ID --skip-fetch --update-model`

## 分析サイクル

詳細は `commands/analyze-pipeline.md` を参照。
