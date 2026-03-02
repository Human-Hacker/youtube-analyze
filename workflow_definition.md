# YouTube動画分析 ワークフロー定義書

## 概要

YouTube長編動画の成功要因を第一原理から解明し、再現可能な4軸予測モデルを構築するAIパイプライン。

### 第一原理

```
Views = Impressions × CTR × f(Retention)
```

この公式を分解し、各要素に影響する因子を4軸で体系化する:

| 軸 | 対応する公式要素 | 制作者がコントロール可能な因子 |
|----|----------------|---------------------------|
| Topic Power | Impressions（潜在需要） | アーティスト選定、タイミング、競合環境 |
| Hook Power | CTR | タイトル、サムネイル、好奇心ギャップ設計 |
| Retention Power | f(Retention) | 台本構造、感情曲線、MV配置、導入設計 |
| Virality Power | Impressions（拡散加速） | エンゲージメント誘発、共有性、コメント誘導 |

---

## アーキテクチャ原則

### 1エージェント = 1スキル + 最小入力
- 各エージェントは専用のskillファイルを1つだけ参照する
- 処理済みファイルの共有は原則禁止（checker例外のみ許可）

### Phase出力の自己完結性
- 各Phaseのfinal出力は後続Phaseが必要とする全情報を含む（付録テーブル）
- 後続エージェントが前Phaseの入力ファイルに遡る必要がない

### ドメインパック方式
- Phase 1はエージェント別に専用データパックを生成する
- data_summary.md はスクリプト専用（エージェントは参照しない）

---

## Phase構成

| Phase | 名前 | 目的 | ステップ |
|-------|------|------|----------|
| 1 | Intelligence | 全データの収集・同期・構造化 | Step 1-3 |
| 2 | Retention Analysis | 維持率曲線と台本構造の関係解明 | Step 4 |
| 3 | CTR Analysis | クリック率決定要因の解明 | Step 5 |
| 4 | Paired Comparison | 類似動画ペアの差分から因果特定 | Step 6-7 |
| 5 | Multi-Axis Model | 4軸モデル構築と仮説検証ループ | Step 8-11 |
| 6 | PDCA | 予測→検証→学習サイクル | Step 12-13 |

---

## Phase 1: Intelligence（情報収集）

**目的**: YouTubeから全データを取得し、分析用に構造化する

| Step | 種別 | ファイル | 役割 | 入力 | 出力 |
|------|------|---------|------|------|------|
| 1 | script | step1_fetch.py | YouTube APIデータ取得 | YouTube API | videos/*.json, video_index.json |
| 2 | script | step2_sync_scores.py | 人間評価スコア同期 | scripts/*.json | human_scores.json更新 |
| 3 | script | step3_summarize.py | 構造化サマリ + ドメインパック生成 | Phase 1全データ | **data_summary.md**, **retention_data_pack.md**, **ctr_data_pack.md** |

### 制約
- Step 1→2→3 の順序実行（各ステップの出力が次の入力）
- data_summary.mdは13セクション構成（スクリプト専用。エージェントは参照しない）
- retention_data_pack.mdはStep 4専用（§1,2,4,9,10,11）
- ctr_data_pack.mdはStep 5専用（§1,2,3,5,6,7,12,13）

---

## Phase 2: Retention Analysis（維持率分析）

**目的**: 動画の維持率曲線と台本構造の対応関係を解明する

| Step | 種別 | ファイル | 専用skill | 入力 | 出力 |
|------|------|---------|-----------|------|------|
| 4 | agent | agents/retention/step4_retention.md | retention_expertise.md | retention_data_pack.md, videos/*.json, scripts/*.json | **retention_analysis.md**（付録: 全動画維持率テーブル） |

### 制約
- Phase 1完了後に実行可能
- Phase 3と並列実行可能（依存関係なし）
- 出力に全動画の維持率データテーブルを付録として含める

---

## Phase 3: CTR Analysis（CTR分析）

**目的**: クリック率を決定する4要因（トピック、タイトル、タイミング、競合）を解明する

| Step | 種別 | ファイル | 専用skill | 入力 | 出力 |
|------|------|---------|-----------|------|------|
| 5 | agent | agents/ctr/step5_ctr.md | ctr_hook_expertise.md | ctr_data_pack.md, videos/*.json, human_scores.json | **ctr_analysis.md**（付録: 全動画CTRテーブル） |

### 制約
- Phase 1完了後に実行可能
- Phase 2と並列実行可能（依存関係なし）
- 出力に全動画のCTRデータテーブルを付録として含める

---

## Phase 4: Paired Comparison（ペア比較）

**目的**: 条件が似ているのに結果が異なるペアを比較し、因果要因を特定する

| Step | 種別 | ファイル | 専用skill | 入力 | 出力 |
|------|------|---------|-----------|------|------|
| 6 | agent | agents/comparison/step6_pair_select.md | case_control_methodology.md | retention_analysis.md, ctr_analysis.md | pair_selection.md（全データ埋め込み済み） |
| 7 | agent | agents/comparison/step7_case_study.md | four_axis_analysis.md | pair_selection.md | **case_studies.md**（Phase総括Appendix付き） |

### 制約
- Phase 2, 3 両方完了後に実行可能
- Step 6→7 の順序実行
- Step 6出力にペアごとの全データを埋め込み（Step 7が他ファイルを参照する必要をなくす）
- Step 7出力にPhase 2-4の主要発見と全動画4軸統合テーブルを付録として含める

---

## Phase 5: Multi-Axis Model（多軸モデル構築）

**目的**: Phase 2-4の分析結果を統合し、4軸モデルで「伸びる動画の黄金理論」を構築する

| Step | 種別 | ファイル | 専用skill | 入力 | 出力 |
|------|------|---------|-----------|------|------|
| 8 | script | step8_build_model.py | — | data_summary.md | model.json |
| 9 | agent | agents/model/step9_hypothesize.md | hypothesis_generation.md | case_studies.md, insights.md, golden_theory.json | new_hypotheses.md |
| 10 | agent | agents/model/step10_verify.md | verification_methodology.md | new_hypotheses.md, case_studies.md, human_scores.json, insights.md, golden_theory.json | verification_report.md |
| 11 | script | step11_integrate.py --integrate | — | 仮説 + 検証結果 | insights.md, golden_theory.json |

### 分析ループ
```
Step 9 → Step 10 → Step 11 → 収束判定
  ↑                              │
  └──── 未収束 & サイクル<5 ──────┘
```

### ループ状態（累積ファイル）
- `data/output/insights.md` — 採択/棄却の全履歴（毎サイクル更新）
- `data/output/golden_theory.json` — 黄金理論のチェックリスト（毎サイクル更新）

### ループ終了条件
| 条件 | 名称 | 動作 |
|------|------|------|
| 全仮説が採択/修正、未解決矛盾ゼロ | 正常終了 | analysis_conclusion.md 生成 |
| 一部採択/棄却、新手がかりなし | 成果あり終了 | analysis_conclusion.md 生成 |
| 5サイクル到達 | 上限終了 | 残存矛盾を記録して終了 |

### 制約
- Phase 4完了後に実行可能
- Step 8→9→10→11 の順序実行（ループ内）
- Step 9はcase_studies.mdのPhase総括Appendixから全Phase 2-4の発見を参照（直接遡らない）
- Step 10はchecker例外としてhuman_scores.jsonに直接アクセス（パイプライン処理済みデータを信用せず独立検証）
- Phase 5 final出力: **analysis_conclusion.md**（ループ収束後のみ生成）

---

## Phase 6: PDCA（予測→検証→学習）

**目的**: モデルの予測精度を実データで検証し、継続的に改善する

| Step | 種別 | ファイル | 役割 | 入力 | 出力 |
|------|------|---------|------|------|------|
| 12 | script | step12_predict.py | 予測ロック | 候補リスト, golden_theory.json | predictions.jsonl, pred_*.md |
| 13 | script | step13_pdca.py | PDCA評価 | 新動画データ, model.json | pdca_*.md |

### 制約
- Step 12は独立実行可能（バイアス防止のため、Step 13より前に実行）
- Step 13はPhase 1（データ取得）後に実行可能
- PDCA結果で「モデル更新が必要」と判定された場合 → Phase 5 Step 9へ

---

## 依存関係図

```
Phase 1 ──→ Phase 2 ──┐
       └──→ Phase 3 ──┤
                       ↓
                 Phase 4 ──→ Phase 5（ループ）──→ Phase 6
                                    ↑                   │
                                    └───── PDCA更新 ─────┘
```

Phase 2とPhase 3は並列実行可能。それ以外は順序依存。

---

## エージェント一覧

| 名前 | Phase | ファイル | 専用skill | 役割 |
|------|-------|---------|-----------|------|
| Retention Analyst | 2 | agents/retention/step4_retention.md | retention_expertise.md | 維持率曲線×台本構造マッピング |
| CTR Analyst | 3 | agents/ctr/step5_ctr.md | ctr_hook_expertise.md | CTR 4要因分析（GI/CA基準内蔵） |
| Pair Selector | 4 | agents/comparison/step6_pair_select.md | case_control_methodology.md | HIT/MISSマッチドペア選定 |
| Case Researcher | 4 | agents/comparison/step7_case_study.md | four_axis_analysis.md | 4軸差分深掘り分析 |
| Hypothesis Generator | 5 | agents/model/step9_hypothesize.md | hypothesis_generation.md | 4軸統合仮説生成（水平思考×第一原理） |
| Red Team Verifier | 5 | agents/model/step10_verify.md | verification_methodology.md | 仮説の否定方向検証 |

---

## スキルファイル（エージェント専用化）

| ファイル | 対象Agent | 主な内容 |
|---------|-----------|---------|
| skills/retention_expertise.md | Step 4 | 維持率曲線理論、感情移入×物語構造、MV挿入効果 |
| skills/ctr_hook_expertise.md | Step 5 | CTR理論、好奇心ギャップ、GI/CAスコアリング基準全文 |
| skills/case_control_methodology.md | Step 6 | ケースコントロール研究法、マッチング基準設計 |
| skills/four_axis_analysis.md | Step 7 | 4軸フレームワーク完全定義、差分分析の因果推論 |
| skills/hypothesis_generation.md | Step 9 | 仮説生成方法論、反証可能性要件、N=24統計推論 |
| skills/verification_methodology.md | Step 10 | レッドチーム方法論、確証バイアス対策、検証閾値 |

---

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

---

## HIT/MISSの定義

| 区分 | 条件 |
|------|------|
| HIT | 15万回再生以上 |
| MISS | 15万回再生未満 |

---

## 4軸モデルの詳細

### Topic Power（トピック力）
「この人の話を聞きたい」という潜在需要の強さ。

構成要素:
- GIスコア（G1ゴシップ + G2好奇心 + G3感情 + G4映画 + G6楽曲知名度）
- Google Trends JP検索ボリューム
- 競合チャンネルの動画密度
- 公開タイミング（時事性との連動）

### Hook Power（フック力）
「このサムネイル/タイトルをクリックしたい」という衝動の強さ。

構成要素:
- CAスコア（好奇心TOP1-2とタイトルの一致度）
- ブラウジングCTR
- タイトルパターン（疑問型/対比型/事実提示型/エモーショナル型）
- 好奇心ギャップの設計

### Retention Power（維持力）
「最後まで見たい」という継続視聴動機の強さ。

構成要素:
- 平均視聴率
- 導入30秒の引き（開始タイプ、引きの強さ）
- 感情曲線設計（転換数、底の深さ、カタルシス）
- MV配置（挿入数、重要シーン配置）
- 台本構造（敵役、エスカレーション、フック回答位置）

### Virality Power（拡散力）
「誰かに教えたい」という共有動機の強さ。

構成要素:
- エンゲージメント率
- コメント率
- シェア数
- 登録者獲得効率

---

## データの3分類

### アナリティクスデータ（YouTube API + Studio）
再生数, CTR, トラフィック, 視聴維持, デモグラフィック, 日別推移, 視聴者セグメント

### 台本データ（台本構造分析JSON）
構造, フック, MV, 好奇心一致, 感情曲線, 導入30秒, 本人映像, 文字数

### メタデータ（定量評価・コンテキスト）
GI評価, CA評価, 好奇心TOP1-2, エビデンス, コンテキスト（公開日, 時事性）

---

## 命名規則

| 接頭辞 | 意味 | 例 |
|--------|------|-----|
| step{N}_ | ステップ番号に対応するファイル | step4_retention.md |
| data_ | データ関連 | data_summary.md |
| golden_ | 黄金理論関連 | golden_theory.json |
| analysis_ | 分析結果 | analysis_conclusion.md |
| pred_ | 予測 | pred_ビヨンセ.md |
| pdca_ | PDCA評価 | pdca_VIDEO_ID_DATE.md |
