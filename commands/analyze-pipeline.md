# 分析パイプライン司令官

YouTube動画分析の全工程を管理・実行するオーケストレーター。
6フェーズ・13ステップのクリーンアーキテクチャで、動画成功要因を第一原理から解明する。

## 実行モード

ユーザーの指示に応じて適切なモードを選択する。

### モード A: フル分析パイプライン
全Phase（1〜5）を通して実行し、4軸モデルを構築する。

### モード B: PDCA評価（動画公開後 Day7）
新しく公開した動画の事後分析。予測と実績を照合する。

### モード C: 予測ロック
候補アーティストの事前予測をロックする（バイアス防止のため、データ収集前に実行）。

### モード D: 分析ループのみ
Phase 1-4完了後、Phase 5のモデル構築ループのみを回す。

---

## モード A: フル分析パイプライン

### Phase 1: Intelligence（情報収集）

```
Step 1: python scripts/step1_fetch.py
  → data/input/videos/*.json, data/input/video_index.json

Step 2: python scripts/step2_sync_scores.py
  → data/input/human_scores.json 更新

Step 3: python scripts/step3_summarize.py
  → data/output/data_summary.md
  → data/output/retention_data_pack.md
  → data/output/ctr_data_pack.md
```

**Phase 1 final出力**:
- `data/output/data_summary.md`（スクリプト向け全セクション）
- `data/output/retention_data_pack.md`（Step 4専用ドメインパック）
- `data/output/ctr_data_pack.md`（Step 5専用ドメインパック）

### Phase 2: Retention Analysis（維持率分析）

```
Step 4: Agent（agents/retention/step4_retention.md）
  skill: skills/retention_expertise.md
  入力: retention_data_pack.md + videos/*.json + scripts/*.json
  出力: data/output/retention_analysis.md（付録: 全動画維持率テーブル）
```

**Phase 2 final出力**: `data/output/retention_analysis.md`

### Phase 3: CTR Analysis（CTR分析）

```
Step 5: Agent（agents/ctr/step5_ctr.md）
  skill: skills/ctr_hook_expertise.md
  入力: ctr_data_pack.md + videos/*.json + human_scores.json
  出力: data/output/ctr_analysis.md（付録: 全動画CTRテーブル）
```

**Phase 3 final出力**: `data/output/ctr_analysis.md`

**注意**: Phase 2とPhase 3は独立しているため並列実行可能。

### Phase 4: Paired Comparison（ペア比較）

```
Step 6: Agent（agents/comparison/step6_pair_select.md）
  skill: skills/case_control_methodology.md
  入力: retention_analysis.md + ctr_analysis.md
  出力: data/output/pair_selection.md（全データ埋め込み済み）

Step 7: Agent（agents/comparison/step7_case_study.md）
  skill: skills/four_axis_analysis.md
  入力: pair_selection.md
  出力: data/output/case_studies.md（Phase総括Appendix含む）
```

**Phase 4 final出力**: `data/output/case_studies.md`

### Phase 5: Multi-Axis Model（多軸モデル構築）

```
Step 8: python scripts/step8_build_model.py
  → data/output/model.json（4軸モデル）

  ┌─── 分析ループ（最大5サイクル）─────────────────────────┐
  │ Step 9:  Agent（agents/model/step9_hypothesize.md）    │
  │   skill: skills/hypothesis_generation.md               │
  │   入力: case_studies.md + insights.md                  │
  │         + golden_theory.json                           │
  │   出力: data/output/new_hypotheses.md                   │
  │                                                         │
  │ Step 10: Agent（agents/model/step10_verify.md）         │
  │   skill: skills/verification_methodology.md            │
  │   入力: new_hypotheses.md + case_studies.md             │
  │         + human_scores.json + insights.md               │
  │         + golden_theory.json                            │
  │   出力: data/output/verification_report.md              │
  │                                                         │
  │ Step 11: python scripts/step11_integrate.py --integrate │
  │   入力: new_hypotheses.md + verification_report.md      │
  │   出力: insights.md, golden_theory.json 更新            │
  │   → 収束判定                                            │
  └─── 未収束なら Step 9 へ ────────────────────────────────┘

  収束後: data/output/analysis_conclusion.md 生成
```

**Phase 5 final出力**: `data/output/analysis_conclusion.md`

### ループ終了条件
- **正常終了**: 全仮説が「支持」or「修正」で、未解決矛盾がゼロ
- **成果ありで終了**: 一部採択・一部棄却だが、新たな手がかりがない
- **上限終了**: 5サイクル到達。残存矛盾を記録して終了

---

## モード B: PDCA評価

### エージェントの対話フロー

```
エージェント → ユーザーに質問:
  1. 「評価する動画のIDを教えてください」
  2. 「YouTube Studio CSVがあればパスを教えてください（なければAPIで取得）」
```

### 自動実行フロー

```
Phase 1: データ準備
  1.1 video_id 取得
  1.2 台本分析JSONの自動生成（youtube-long連携）
  1.3 python scripts/step2_sync_scores.py --video-id VIDEO_ID

Phase 6: PDCA評価
  Step 12: python scripts/step1_fetch.py
  Step 13: python scripts/step13_pdca.py VIDEO_ID
    → data/output/pdca_{VIDEO_ID}_{DATE}.md

結果報告: pdca レポートをユーザーに報告
  → 「モデル更新が必要ですか？」確認
  → Yes → モード D（分析ループ）へ
```

---

## モード C: 予測ロック

### 前提条件
全アーティストのスコアが `skills/ctr_hook_expertise.md` 内のGI/CA定量基準に基づいて算出済みであること。

### 実行

```
python scripts/step12_predict.py              # 全件インポート
python scripts/step12_predict.py --dry-run     # 実行せず確認
python scripts/step12_predict.py --artist "名前" --G1 N --G6 N  # 1件追加
```

**重要**: 予測ロックはデータ収集（モードB）の前に実行すること（バイアス防止）。

---

## モード D: 分析ループのみ

Phase 1-4が完了している前提で、Phase 5のループのみを回す。

```
Step 8:  python scripts/step8_build_model.py
Step 9:  Agent（agents/model/step9_hypothesize.md）
Step 10: Agent（agents/model/step10_verify.md）
Step 11: python scripts/step11_integrate.py --integrate
→ 収束判定 → 未収束ならStep 9へ
```

---

## 各ステップの詳細

| Step | Phase | 種別 | 実行 | 入力 | 出力 |
|------|-------|------|------|------|------|
| 1 | 1 | script | `step1_fetch.py` | YouTube API | `videos/*.json`, `video_index.json` |
| 2 | 1 | script | `step2_sync_scores.py` | `scripts/*.json` | `human_scores.json` 更新 |
| 3 | 1 | script | `step3_summarize.py` | Phase 1全データ | `data_summary.md`, `retention_data_pack.md`, `ctr_data_pack.md` |
| 4 | 2 | agent | `step4_retention.md` | `retention_data_pack.md` + 生データ | `retention_analysis.md` |
| 5 | 3 | agent | `step5_ctr.md` | `ctr_data_pack.md` + 生データ | `ctr_analysis.md` |
| 6 | 4 | agent | `step6_pair_select.md` | `retention_analysis.md` + `ctr_analysis.md` | `pair_selection.md` |
| 7 | 4 | agent | `step7_case_study.md` | `pair_selection.md` | `case_studies.md` |
| 8 | 5 | script | `step8_build_model.py` | Phase 1-4全出力 | `model.json` |
| 9 | 5 | agent | `step9_hypothesize.md` | `case_studies.md` + ループ状態 | `new_hypotheses.md` |
| 10 | 5 | agent | `step10_verify.md` | `new_hypotheses.md` + `case_studies.md` + `human_scores.json` + ループ状態 | `verification_report.md` |
| 11 | 5 | script | `step11_integrate.py --integrate` | 仮説+検証結果 | `insights.md`, `golden_theory.json` |
| 12 | 6 | script | `step12_predict.py` | 候補リスト | `predictions.jsonl`, `pred_*.md` |
| 13 | 6 | script | `step13_pdca.py` | 新動画データ + model.json | `pdca_*.md` |

## エージェント一覧

| エージェント | ファイル | Phase | 専用skill | 役割 |
|------------|---------|-------|-----------|------|
| Retention Analyst | `step4_retention.md` | 2 | `retention_expertise.md` | 維持率曲線×台本構造マッピング |
| CTR Analyst | `step5_ctr.md` | 3 | `ctr_hook_expertise.md` | CTR 4要因分析（GI/CA基準内蔵） |
| Pair Selector | `step6_pair_select.md` | 4 | `case_control_methodology.md` | HIT/MISSマッチドペア選定 |
| Case Researcher | `step7_case_study.md` | 4 | `four_axis_analysis.md` | ペアごとの4軸差分分析 |
| Hypothesis Generator | `step9_hypothesize.md` | 5 | `hypothesis_generation.md` | 4軸統合仮説生成 |
| Red Team Verifier | `step10_verify.md` | 5 | `verification_methodology.md` | 仮説の否定方向検証 |

## 参照スキル（エージェントごとに専用化）

| ファイル | 対象Agent | 主な内容 |
|---------|-----------|---------|
| `skills/retention_expertise.md` | Step 4 | 維持率曲線理論、感情移入×物語構造、MV挿入効果 |
| `skills/ctr_hook_expertise.md` | Step 5 | CTR理論、好奇心ギャップ、GI/CAスコアリング基準全文 |
| `skills/case_control_methodology.md` | Step 6 | ケースコントロール研究法、マッチング基準設計 |
| `skills/four_axis_analysis.md` | Step 7 | 4軸フレームワーク完全定義、差分分析の因果推論 |
| `skills/hypothesis_generation.md` | Step 9 | 仮説生成方法論、反証可能性要件、N=24統計推論 |
| `skills/verification_methodology.md` | Step 10 | レッドチーム方法論、確証バイアス対策、検証閾値 |

## データフロー

```
Phase 1 (Intelligence)
  入力: YouTube API, CSV, scripts/*.json
  出力: data_summary.md（スクリプト向け）
        retention_data_pack.md（Step 4向け）
        ctr_data_pack.md（Step 5向け）
         ↓
Phase 2 (Retention)          Phase 3 (CTR)
  入力: retention_data_pack    入力: ctr_data_pack
  出力: retention_analysis.md  出力: ctr_analysis.md
  （付録: 全動画テーブル）      （付録: 全動画テーブル）
         ↓                      ↓
         └──────────┬───────────┘
                    ↓
Phase 4 (Comparison)
  入力: retention_analysis + ctr_analysis
  出力: pair_selection.md（全データ埋め込み）
        → case_studies.md（Phase総括Appendix付き）
         ↓
Phase 5 (Model) ← ループ（最大5サイクル）
  入力: case_studies.md + ループ状態
  出力: analysis_conclusion.md（★ Phase 5 final）
         ↓
Phase 6 (PDCA)
  予測ロック / PDCA評価
```

## エラー時のリカバリ

| 状況 | 対応 |
|------|------|
| Step 1 でAPI認証エラー | `python scripts/auth.py` で再認証 |
| Step 4/5 で分析データ不足 | Phase 1の出力を確認、data_packが正常か確認 |
| Step 6 でペアが見つからない | マッチング条件を緩和（GI差を5まで拡大） |
| Step 9/10 でAgent出力不正 | 出力ファイルのJSONブロックフォーマットを修正 |
| ループが収束しない | 5サイクル上限で自動終了。insights.mdに未解決問題を記録 |
