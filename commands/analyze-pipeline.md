# 分析パイプライン司令官

YouTube動画分析の全工程を管理・実行するオーケストレーター。
ユーザーとの対話で必要な情報を収集し、全ステップを自動実行する。

## 実行モード

ユーザーの指示に応じて適切なモードを選択する。

### モード A: 新動画のPDCA評価（動画公開後 Day7）

新しく公開した動画の事後分析。予測と実績を照合する。

### モード B: 分析モデルの再構築

全データを使ってモデルを更新し、仮説検証ループを回す。

### モード C: 次の動画候補の予測ロック

`next_26_artists.md` の予測をロックする（バイアス防止のため、データ収集前に実行）。

---

## モード A: 新動画のPDCA評価

### エージェントの対話フロー

```
エージェント → ユーザーに質問:
  1. 「評価する動画のIDを教えてください」
  2. 「YouTube Studio から以下のCSVをダウンロードして、パスを教えてください:
      - アナリティクス概要（過去7日）
      - トラフィックソース
      ※ 手元にない場合は "なし" と回答してください（API取得を試みます）」
```

### 自動実行フロー

```
Phase 1: データ準備
  1.1 ユーザーから video_id を取得
  1.2 台本分析JSONの自動生成:
      a. video_index.json からタイトルを取得 → アーティスト名を推定
      b. youtube-long/projects/{ARTIST}/ に script.md があるか確認
      c. script.md を読み、templates/script_analysis_template.json に沿って分析
      d. data/input/scripts/{VIDEO_ID}.json に保存
  1.3 スコア同期:
      python scripts/step_sync_scores.py --video-id VIDEO_ID
      → human_scores.json に GI/CA スコアが自動反映される
      ※ quantitativeソース（手動採点済み）は上書きしない

Phase 2: パイプライン実行
  2.1 python scripts/step1_fetch.py             # YouTube API データ取得
  2.2 python scripts/step2_build_model.py        # モデル再構築（新データ込み）
  2.3 python scripts/step7_pdca.py VIDEO_ID      # PDCA評価 + 予測照合

Phase 3: 結果報告
  3.1 data/output/pdca_{VIDEO_ID}_{DATE}.md の内容をユーザーに報告
  3.2 予測照合結果がある場合は特に強調して報告
  3.3 「モデルの更新が必要ですか？（分析ループに進みますか？）」と確認
```

### Phase 3 で「はい」の場合 → 分析ループ

```
  ┌─── 分析ループ（最大5回）─────────────────────────┐
  │ Step 3: python scripts/step3_analyze.py          # 分析準備
  │ Step 4: Agent C (agents/analyze-step4-hypothesis.md)  # 仮説生成
  │ Step 5: Agent E (agents/analyze-step5-verification.md) # 仮説検証
  │ Step 6: python scripts/step3_analyze.py --integrate    # 結果統合
  └─── 未収束なら Step 3 へ ─────────────────────────┘
```

---

## モード B: 分析モデルの再構築

```
Phase 1: データ更新
  1.1 python scripts/step1_fetch.py             # 最新データ取得
  1.2 python scripts/step2_build_model.py        # モデル再構築

Phase 2: 分析ループ（最大5回）
  2.1 python scripts/step3_analyze.py
  2.2 Agent C → 仮説生成
  2.3 Agent E → 仮説検証
  2.4 python scripts/step3_analyze.py --integrate
  → 収束判定 → 未収束ならループ

Phase 3: 結果報告
  3.1 data/output/analysis_conclusion.md をユーザーに報告
```

---

## モード C: 予測ロック

### 前提条件: 定量スコアリングの完了

予測をロックする前に、全アーティストのG1/G6/G_ST/G_YTスコアが `prompts/scoring_criteria.md` v1.0 の定量基準に基づいて算出されていなければならない。**概算・推定によるスコアは禁止**。

#### 必須手順（1件追加時も一括インポート時も同様）

1. **G1（ゴシップ露出度）**: `"{アーティスト名}" ワイドショー OR 特集 OR スキャンダル` でWeb検索し、独立記事数をカウント
2. **G6（楽曲知名度）**: `"{アーティスト名}" CM OR カラオケ OR ドラマ主題歌` でWeb検索し、日本でのCM/TV/カラオケ実績曲数をカウント
3. **G_ST（ストリーミング需要）**: `"{アーティスト名}" Spotify Japan` or `"{アーティスト名}" ストリーミング 日本` でWeb検索し、日本チャートでの実績を確認
4. **G_YT（YouTube解説需要）**: `"{アーティスト名}" 解説 OR まとめ OR 人生` でYouTube検索し、既存解説動画の本数・再生数を確認
5. 各スコアの**根拠（evidence）**を `next_*_artists.md` の選定理由に記録

#### スコアリング基準の詳細

`prompts/scoring_criteria.md` を参照。主要な閾値:
- G1: 独立記事10件以上→5, 5-9件→4, 3-4件→3, 1-2件→2, 0件→1
- G6: CM/TV/カラオケ実績3曲以上→5, 2曲→4, 1曲→3, カラオケのみ→2, なし→1
- G_ST: Spotify Japan月間リスナー/チャート実績で判定（1-5）
- G_YT: 日本語の解説動画の本数・合計再生数で判定（1-5）

### 実行

```
python scripts/step8_predict.py              # next_*_artists.md から全件インポート
python scripts/step8_predict.py --dry-run     # 実行せず確認
python scripts/step8_predict.py --artist "名前" --G1 N --G6 N --G_ST N --G_YT N  # 1件追加
```

**重要**: 予測ロックはデータ収集（モードA）の前に実行すること（バイアス防止）。

---

## 台本分析JSONの自動生成

モードA Phase 1.2 で、エージェントが youtube-long の台本を分析して JSON を生成する。

### アーティスト名の照合ルール

video_index.json のタイトルから推定 → youtube-long/projects/ のフォルダ名と照合:
- 完全一致を試行
- 部分一致（タイトルにフォルダ名が含まれる）を試行
- 見つからない場合はユーザーに確認

### 生成する JSON の構造

`templates/script_analysis_template.json` に準拠。主要フィールド:
- `gi_scores`: G1-G6 のスコア（台本の内容から採点）
- `curiosity_alignment`: ca_score（好奇心とタイトルの照合）
- `structure`: 統一テーマ、敵役、感情の底など
- `hook_analysis`: オープニングフック分析
- `emotional_curve`: 感情曲線パターン
- `opening_30sec`: 最初30秒の分析

### 採点基準

`prompts/scoring_criteria.md` の定量基準に従う。エージェントは:
1. 台本を通読し、各スコアを定量基準で採点
2. 根拠を `*_evidence` フィールドに記録
3. Web検索は不要（台本の内容のみで採点）

---

## 各ステップの詳細

| Step | 種別 | 実行コマンド | 入力 | 出力 |
|------|------|-------------|------|------|
| 1 | script | `python scripts/step1_fetch.py` | YouTube API | `data/input/videos/*.json`, `data/input/video_index.json` |
| 2 | script | `python scripts/step2_build_model.py` | `data/input/videos/*.json`, `data/input/human_scores.json` | `data/output/model.json`, `data/output/analysis_report.md` |
| 3 | script | `python scripts/step3_analyze.py` | `data/output/model.json`, 全入力データ | `data/output/data_summary.md` |
| 4 | agent | `agents/analyze-step4-hypothesis.md` | `data/output/data_summary.md`, `data/output/insights.md`, `data/output/golden_theory.json` | `data/output/new_hypotheses.md` |
| 5 | agent | `agents/analyze-step5-verification.md` | `data/output/new_hypotheses.md`, 全入力データ | `data/output/verification_report.md` |
| 6 | script | `python scripts/step3_analyze.py --integrate` | `data/output/new_hypotheses.md`, `data/output/verification_report.md` | `data/output/insights.md`, `data/output/golden_theory.json`, `data/output/analysis_conclusion.md` |
| 7 | script | `python scripts/step7_pdca.py VIDEO_ID` | 新動画データ, `data/output/model.json`, `data/predictions.jsonl` | `data/output/pdca_*.md` |
| 8 | script | `python scripts/step8_predict.py` | `data/output/next_26_artists.md` | `data/predictions.jsonl`, `data/output/predictions/pred_*.md` |
| sync | script | `python scripts/step_sync_scores.py` | `data/input/scripts/*.json` | `data/input/human_scores.json` 更新 |

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
| `prompts/scoring_criteria.md` | GI/CAスコアリング定量基準 | Agent C, Agent E, 台本分析JSON生成 |

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
│   ├── step7_pdca.py                # Step 7: PDCA評価 + 予測照合
│   ├── step8_predict.py             # Step 8: 事前予測の一括記録
│   ├── step_sync_scores.py          # 台本分析 → human_scores.json 同期
│   ├── data_summarizer.py           # ユーティリティ: データ集計
│   ├── config.py                    # 設定
│   └── common/
│       ├── data_loader.py
│       └── metrics.py
├── data/
│   ├── input/                       # 入力データ（API取得・手動評価）
│   │   └── scripts/                 # 台本分析JSON（自動生成 or 手動）
│   ├── output/                      # 出力データ（モデル・分析結果）
│   │   └── predictions/             # 予測カード
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
| 台本が youtube-long に見つからない | ユーザーにアーティスト名を確認 → 手動で script.md パスを指定 |
| 予測が見つからない (step7) | アーティスト名の表記揺れの可能性。部分一致で検索される |
