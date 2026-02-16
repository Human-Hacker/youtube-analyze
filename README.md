# YouTube Analytics Agent for ウタヨミ

## ファイル一覧

```
youtube-analytics/
│
├── README.md                              ← このファイル
│
├── scripts/
│   ├── config.py                          ← 共通設定（直接実行しない）
│   ├── step0_setup.md                     ← Google Cloud初期設定ガイド（手動で読む）
│   ├── step1_auth.py                      ← OAuth認証
│   ├── step2_test.py                      ← API接続テスト
│   ├── step3_fetch_all.py                 ← 全動画データ一括取得
│   ├── step4_merge_manual.py              ← 手動CSVとAPIデータの結合
│   ├── step5_build_model.py               ← 「伸びる動画モデル」構築
│   └── step6_pdca_update.py               ← 新動画PDCA評価・モデル更新
│
├── data/
│   ├── videos/                            ← 動画ごとのJSON（step3で自動生成）
│   ├── scripts/                           ← 台本構造分析JSON（Claude Codeで生成）
│   ├── manual_exports/
│   │   └── manual_export.csv              ← YouTube Studioから手動取得データ
│   ├── pdca_reports/                      ← PDCAレポート（step6で自動生成）
│   ├── model_history/                     ← モデルバージョン履歴（自動生成）
│   ├── video_index.json                   ← 全動画一覧（step3で自動生成）
│   ├── model.json                         ← 現在のモデル（step5で自動生成）
│   └── analysis_report.md                 ← 分析レポート（step5で自動生成）
│
├── templates/
│   └── script_analysis_template.json      ← 台本分析のテンプレート
│
├── client_secret.json                     ← Google Cloudからダウンロード（※Git管理しない）
└── token.json                             ← 初回認証で自動生成（※Git管理しない）
```

---

## 実行手順 & Claude Codeでのコマンド

---

### ━━━ 初回セットアップ（1回だけ） ━━━

---

### Step 0: Google Cloud設定（手動作業）

`scripts/step0_setup.md` を読んで設定を完了させてください。
完了後、`client_secret.json` を `youtube-analytics/` 直下に配置。

---

### Step 1: OAuth認証

**Claude Codeで以下をコピペ:**
```
youtube-analytics/scripts/step1_auth.py を実行して
```

→ ブラウザが開く → Googleアカウントでログイン → `token.json` が生成される

---

### Step 2: API接続テスト

**Claude Codeで以下をコピペ:**
```
youtube-analytics/scripts/step2_test.py を実行して
```

→ チャンネル名・登録者数・最新動画・直近7日分データが表示されれば成功

---

### ━━━ モデル構築（初回） ━━━

---

### Step 3: 全動画のAPIデータ一括取得

**Claude Codeで以下をコピペ:**
```
youtube-analytics/scripts/step3_fetch_all.py を実行して
```

→ 全長編動画のアナリティクスを取得 → `data/videos/{video_id}.json` に保存
→ `data/video_index.json` に全動画の一覧が保存される

**※ 1動画だけ取得したい場合:**
```
youtube-analytics/scripts/step3_fetch_all.py を引数 VIDEO_ID で実行して
```

---

### Step 4-A: YouTube Studioから手動データ取得（手動作業）

YouTube Studio (https://studio.youtube.com) で各動画の以下を確認し、
`data/manual_exports/manual_export.csv` に記入してください:

| 取得するデータ | YouTube Studioでの場所 |
|---------------|----------------------|
| ブラウジングIMP数 | アナリティクス → トラフィックソース → ブラウジング機能 → インプレッション数 |
| ブラウジングCTR | 同上 → クリック率 |
| 関連動画IMP数 | アナリティクス → トラフィックソース → 関連動画 → インプレッション数 |
| 関連動画CTR | 同上 → クリック率 |
| コア視聴者率 | アナリティクス → 視聴者 → コア視聴者の% |
| 新規視聴者率 | アナリティクス → 視聴者 → 新しい視聴者の% |

**video_id は `data/video_index.json` を見て確認してください。**

CSVの形式:
```csv
video_id,artist_name,browsing_impressions,browsing_ctr,related_impressions,related_ctr,core_viewer_pct,new_viewer_pct
XXXXX,ジャスティン・ビーバー,1500000,7.8,300000,4.5,8.5,47.5
YYYYY,マイケル・ジャクソン,800000,5.4,200000,3.2,12.0,35.0
```

---

### Step 4-B: 手動データのマージ

**Claude Codeで以下をコピペ:**
```
youtube-analytics/scripts/step4_merge_manual.py を実行して
```

→ CSVのデータが各動画のJSONの `manual_data` フィールドに結合される

---

### Step 4-C: 台本の構造分析

**Claude Codeで以下をコピペ:**
```
/Users/user/タスク/youtube-long/projects/{アーティスト名}/script 配下の台本を読み込んで、
youtube-analyze/templates/script_analysis_template.json の形式で分析し、
youtube-analyze/data/scripts/{video_id}.json として保存して。

youtube-analyze/data/video_index.json でアーティスト名とvideo_idの対応を確認して。

各台本について以下を判定:
1. 一言テーマがあるか（台本全体を貫く一言）
2. 明確な加害者がいるか（視聴者が「許せない」と感じる存在）
3. 感情の底が3回以上あり、エスカレートしているか
4. 救済者がいるか
5. 冒頭のフック（問い）に台本内で答えているか
6. MVの挿入箇所と曲名
7. 好奇心マップTOP1-2に台本が答えているか（CAスコア 0-3）
8. GIスコアの各項目（G1-G6、各1-5）
```

---

### Step 5: モデル構築

**Claude Codeで以下をコピペ:**
```
youtube-analytics/scripts/step5_build_model.py を実行して
```

→ `data/model.json`（モデル定義）と `data/analysis_report.md`（分析レポート）が生成される

**構築後の確認:**
```
youtube-analytics/data/analysis_report.md を読んで、モデルの内容を要約して
```

---

### ━━━ 継続運用（新動画公開ごと） ━━━

---

### Step 6: PDCA評価

#### 6-A: 新動画のデータ取得 + 評価

**Claude Codeで以下をコピペ（VIDEO_IDを実際のIDに置換）:**
```
youtube-analytics/scripts/step6_pdca_update.py を引数 VIDEO_ID で実行して
```

→ データ取得 → 予測vs実績の比較 → `data/pdca_reports/` にレポート出力

#### 6-B: 手動CSV更新 + 台本分析（Step 4-A, 4-B, 4-C と同じ）

新動画分のデータを `manual_export.csv` に追記 → マージ → 台本分析

#### 6-C: モデル更新

**Claude Codeで以下をコピペ（VIDEO_IDを実際のIDに置換）:**
```
youtube-analytics/scripts/step6_pdca_update.py を引数 VIDEO_ID --skip-fetch --update-model で実行して
```

→ モデル再構築 → `data/model.json` 更新 → 旧モデルは `data/model_history/` にバックアップ

---

## 全体フロー図

```
[初回のみ]
  Step 0（手動）
    ↓
  Step 1 → Step 2 → Step 3
    ↓
  Step 4-A（手動） → Step 4-B → Step 4-C
    ↓
  Step 5
    ↓
  model.json + analysis_report.md 完成
    ↓
  selection.md / selection_report.md に反映


[新動画公開ごと]
  Step 6-A（データ取得+評価）
    ↓
  Step 4-A（手動CSV追記） → Step 4-B → Step 4-C（台本分析）
    ↓
  Step 6-C（モデル更新）
    ↓
  model.json 更新 → selection.md に反映
```

---

## .gitignore

```
client_secret.json
token.json
```
