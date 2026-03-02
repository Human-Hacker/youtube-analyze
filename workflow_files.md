# ファイル構造定義

## 入力側（エージェント・スキル・スクリプト・コマンド）

```
youtube-analyze/
├── CLAUDE.md
├── commands/
│   └── analyze-pipeline.md              # 全ステップを実行するオーケストレーションコマンド
│
├── agents/
│   ├── retention/                       # Phase 2: 維持率分析
│   │   └── step4_retention.md           # Agent: 維持率曲線×台本構造マッピング
│   │
│   ├── ctr/                             # Phase 3: CTR分析
│   │   └── step5_ctr.md                 # Agent: CTR 4要因分析
│   │
│   ├── comparison/                      # Phase 4: ペア比較
│   │   ├── step6_pair_select.md         # Agent: HIT/MISSマッチドペア選定
│   │   └── step7_case_study.md          # Agent: 4軸差分深掘り分析
│   │
│   └── model/                           # Phase 5: 多軸モデル構築
│       ├── step9_hypothesize.md         # Agent: 4軸統合仮説生成
│       └── step10_verify.md             # Agent: レッドチーム検証
│
├── skills/                              # ドメイン知識（エージェントごとに専用化）
│   ├── retention_expertise.md           # Step 4専用: 維持率曲線理論
│   ├── ctr_hook_expertise.md            # Step 5専用: CTR理論 + GI/CA基準全文
│   ├── case_control_methodology.md      # Step 6専用: ケースコントロール研究法
│   ├── four_axis_analysis.md            # Step 7専用: 4軸フレームワーク完全定義
│   ├── hypothesis_generation.md         # Step 9専用: 仮説生成方法論
│   └── verification_methodology.md      # Step 10専用: レッドチーム検証方法論
│
├── scripts/                             # Python実行スクリプト
│   ├── common/
│   │   ├── __init__.py
│   │   ├── data_loader.py               # 共通データ読込ユーティリティ
│   │   └── metrics.py                   # 共通メトリクス計算
│   │
│   │  # --- Phase 1: Intelligence ---
│   ├── step1_fetch.py                   # Step 1: YouTube APIデータ取得
│   ├── step2_sync_scores.py             # Step 2: 人間評価スコア同期
│   ├── step3_summarize.py               # Step 3: data_summary + domain packs 生成
│   │
│   │  # --- Phase 5: Model ---
│   ├── step8_build_model.py             # Step 8: 相関モデル構築（4軸対応）
│   ├── step8_filters.py                 #   └─ サブモジュール: フィルター
│   ├── step8_patterns.py                #   └─ サブモジュール: パターン分析
│   ├── step8_report.py                  #   └─ サブモジュール: レポート生成
│   ├── step8_history.py                 #   └─ サブモジュール: 履歴管理
│   ├── step11_integrate.py              # Step 11: 結果統合・収束判定
│   │
│   │  # --- Phase 6: PDCA ---
│   ├── step12_predict.py                # Step 12: 予測ロック
│   ├── step13_pdca.py                   # Step 13: PDCA評価
│   │
│   ├── auth.py                          # YouTube API認証
│   └── config.py                        # 共通設定
│
└── studio_exports/                      # YouTube Studio手動エクスポートデータ
    └── {アーティスト名}/
        └── manual_analytics/
            ├── traffic_source.csv       # トラフィックソース別データ
            └── viewer_segments.csv      # 視聴者セグメント別データ
```

## 出力側（データ）

```
youtube-analyze/data/
├── input/                               # 不変データ（Phase 1で取得・更新）
│   ├── analysis_fundamentals.json       # 不変の分析仕様（手動管理）
│   ├── video_index.json                 # 全動画インデックス
│   ├── human_scores.json                # GI×CA人間評価スコア
│   ├── videos/
│   │   └── {VIDEO_ID}.json              # 各動画のアナリティクスデータ（24本+）
│   └── scripts/
│       └── {VIDEO_ID}.json              # 各動画の台本構造分析データ
│
├── output/                              # 分析出力（Phase 1-6で生成・更新）
│   │
│   │  # === Phase 1: Intelligence 出力 ===
│   ├── data_summary.md                  # Step 3: 全動画の構造化サマリ（スクリプト向け全13セクション）
│   ├── retention_data_pack.md           # Step 3: 維持率分析用ドメインパック（Step 4専用）
│   ├── ctr_data_pack.md                 # Step 3: CTR分析用ドメインパック（Step 5専用）
│   │
│   │  # === Phase 2: Retention final出力 ===
│   ├── retention_analysis.md            # Step 4: 維持率×台本構造分析（付録: 全動画テーブル）
│   │
│   │  # === Phase 3: CTR final出力 ===
│   ├── ctr_analysis.md                  # Step 5: CTR 4要因分析（付録: 全動画テーブル）
│   │
│   │  # === Phase 4: Comparison final出力 ===
│   ├── pair_selection.md                # Step 6: ペア選定結果（全データ埋め込み済み）
│   ├── case_studies.md                  # Step 7: ケーススタディ分析（Phase総括Appendix付き）
│   │
│   │  # === Phase 5: Model ===
│   ├── model.json                       # Step 8: 4軸モデル定義
│   ├── analysis_report.md               # Step 8: モデル構築レポート（人間用参考資料）
│   ├── new_hypotheses.md                # Step 9: 仮説レポート（ループ内中間出力）
│   ├── verification_report.md           # Step 10: 検証レポート（ループ内中間出力）
│   ├── insights.md                      # Step 11: 累積知見（ループ状態・毎サイクル更新）
│   ├── golden_theory.json               # Step 11: 黄金理論（ループ状態・毎サイクル更新）
│   ├── analysis_conclusion.md           # Step 11: 分析結論（ループ収束後のみ生成）
│   │
│   │  # === Phase 6: PDCA ===
│   ├── predictions/
│   │   ├── pred_{ARTIST}.md             # Step 12: アーティスト別予測カード
│   │   └── .gitkeep
│   ├── predictions.jsonl                # Step 12: 予測ログ（追記専用）
│   ├── next_33_artists.md               # Step 12: 入力用候補リスト（手動管理）
│   └── pdca_{VIDEO_ID}_{DATE}.md        # Step 13: PDCA評価レポート
│
└── history/                             # バージョン管理
    ├── index.md                         # バージョン履歴 + 棄却仮説アーカイブ
    └── v{X.X}_{DATE}/                   # スナップショット
```

## .claude エイリアス設定

```
/Users/user/タスク/.claude/
├── agents/
│   └── analyze → youtube-analyze/agents（シンボリックリンク）
│
└── commands/
    └── analyze-pipeline.md → youtube-analyze/commands/analyze-pipeline.md（シンボリックリンク）
```

※ .claude/agents/ にシンボリックリンクを設置。
  これにより Claude Code 上で各エージェントを `analyze/retention/step4_retention` のように参照可能。

## エージェント別 入出力・スキル対応

| Agent | Phase | 専用Skill | 入力ファイル | 出力ファイル |
|-------|-------|-----------|------------|------------|
| Step 4 | 2 | `retention_expertise.md` | retention_data_pack.md + videos/*.json + scripts/*.json | retention_analysis.md |
| Step 5 | 3 | `ctr_hook_expertise.md` | ctr_data_pack.md + videos/*.json + human_scores.json | ctr_analysis.md |
| Step 6 | 4 | `case_control_methodology.md` | retention_analysis.md + ctr_analysis.md | pair_selection.md |
| Step 7 | 4 | `four_axis_analysis.md` | pair_selection.md | case_studies.md |
| Step 9 | 5 | `hypothesis_generation.md` | case_studies.md + insights.md + golden_theory.json | new_hypotheses.md |
| Step 10 | 5 | `verification_methodology.md` | new_hypotheses.md + case_studies.md + human_scores.json + insights.md + golden_theory.json | verification_report.md |

## Phase別データフロー

```
Phase 1 (Intelligence)
  入力: YouTube API, CSV, scripts/*.json
  出力: data_summary.md（スクリプト向け）
        retention_data_pack.md（Step 4向け）
        ctr_data_pack.md（Step 5向け）
         ↓
Phase 2 (Retention)              Phase 3 (CTR)
  入力: retention_data_pack.md     入力: ctr_data_pack.md
      + videos/*.json                 + videos/*.json
      + scripts/*.json                + human_scores.json
  出力: retention_analysis.md     出力: ctr_analysis.md
  （付録: 全動画テーブル）          （付録: 全動画テーブル）
         ↓                            ↓
         └──────────┬─────────────────┘
                    ↓
Phase 4 (Comparison)
  入力: retention_analysis.md + ctr_analysis.md
  出力: pair_selection.md（全データ埋め込み）
        → case_studies.md（Phase総括Appendix付き）
         ↓
Phase 5 (Model)                    ┐
  入力: case_studies.md + ループ状態 │
  Step 8: model.json構築           │
  Step 9: 仮説生成                 │ 分析ループ
  Step 10: 仮説検証                │ （最大5サイクル）
  Step 11: 知見統合・収束判定       │
  → 収束判定 → 未収束なら Step 9へ  ┘
  → 収束なら analysis_conclusion.md
         ↓
Phase 6 (PDCA)
  Step 12: 予測ロック
  Step 13: PDCA評価 → モデル更新要 → Phase 5 Step 9へ
```

## 処理済みファイルの共有ルール

| ファイル | 参照元Agent | 備考 |
|---------|------------|------|
| data_summary.md | スクリプトのみ (step8, step11) | エージェントは参照しない |
| retention_data_pack.md | Step 4 のみ | 専用ドメインパック |
| ctr_data_pack.md | Step 5 のみ | 専用ドメインパック |
| retention_analysis.md | Step 6 のみ | Phase 2 出力 → Phase 4 入力 |
| ctr_analysis.md | Step 6 のみ | Phase 3 出力 → Phase 4 入力 |
| pair_selection.md | Step 7 のみ | 全データ埋め込み済み |
| case_studies.md | Step 9, 10 | generator + checker（設計上必要） |
| human_scores.json | Step 5, 10 | 生データ + checker例外（独立検証用） |
| insights.md | Step 9, 10 | ループ状態（設計上必要） |
| golden_theory.json | Step 9, 10 | ループ状態（設計上必要） |
