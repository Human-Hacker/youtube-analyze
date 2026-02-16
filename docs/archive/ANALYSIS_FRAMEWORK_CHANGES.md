# 分析フレームワーク改定仕様書

> **目的**: この文書に記載された全変更をyoutube-analyze配下のファイルに反映すること。
> **対象リポジトリ**: `/Users/user/タスク/youtube-analyze/`
> **関連リポジトリ**: `/Users/user/タスク/youtube-long/`（Step 1 selection.mdへの将来的反映あり）

---

## 0. 改定の全体方針

### 0.1 分析の目的（最重要 — 全ファイルの根底に据える）
**伸びた動画の共通点と伸びていない動画の共通点を明らかにし、「伸びる動画の黄金理論」を構築すること。**

- 「黄金理論」とは、単なる統計モデル（相関係数＋閾値）ではなく、**上位原則（なぜ伸びるのか）＋実用チェックリスト（制作前に確認できる条件）の二層構造**
- 中心的な問い: **「伸びた動画全てに共通することは何か？」「伸びていない動画全てに共通することは何か？」**
- 問題の定義は常にこの中心的な問いから派生して設定する

> **W-23**: 0.1〜0.3 の内容は `data/analysis_fundamentals.json` に機械可読な形式で集約済み。fundamentals.json がマスター（正の情報源）であり、本文書の記述は変更履歴としての参考情報。不一致がある場合は fundamentals.json を優先すること。

### 0.2 HIT/MISSの新定義
- **HIT**: 15万回再生以上（旧: 10万）
- **MISS**: 15万回再生未満
- **根拠**: config.pyのHIT_THRESHOLDが150000に変更済み

### 0.3 分析手法（三本柱）

#### ■ 水平思考（Lateral Thinking）
あらゆる前提を疑い、見えていない変数を探す。Agent Cの分析フローに以下のフレームワークとして組み込む:
1. **前提列挙**: 「なぜそれが共通点なのか」「なぜそれが伸びる原因なのか」の前提を明示的に書き出す
2. **前提反転**: 各前提を「もし逆だったら？」で検証する。例: 「CTRが高いから伸びた」→「もしCTRが低くても伸びた動画があったら？」
3. **代替説生成**: 前提反転の結果から、従来の説明では捕捉できない新しい仮説を生成する

#### ■ 第一原理主義（First Principles Thinking）
YouTubeアルゴリズムの仕組み・視聴者心理・チャンネル固有特性から演繹的に考える。
前提知識は `agents/youtube_fundamentals.md` に明文化し、Agent C・Agent Eの両方が参照する。
（詳細は 2-10 を参照）

#### ■ 仮説駆動アプローチ（Hypothesis-Driven Approach）
McKinsey方式の「答えから始める」手法。中心的な問い（0.1）から派生した仮説のみを立てる。

**Agent Cの分析フロー（5ステップ）**:
```
① HIT/MISS共通点抽出（必須・最優先）
    ↓
② 前提列挙（「なぜそれが共通点なのか」の前提を書き出す）
    ↓
③ 前提反転・水平思考（各前提を「もし逆だったら？」で検証）
    ↓
④ 因果仮説生成（中心的な問いへのDay 1 Answerとして）
    ↓
⑤ 新仮説提示（Agent Eへ渡す）
```

**Agent Eの役割（レッドチーム）**:
- Agent Cから受け取った仮説をデータで検証する
- **確証バイアス防止**: Agent Cの仮説を支持するデータだけでなく、矛盾するデータを意図的に探す
- **アンカリング防止**: Agent Cが複数仮説を提示し、Agent Eは各仮説を独立に評価する
- 検証結果は「支持される / 修正される / 棄却される」の3状態で報告
- 棄却は失敗ではなく学習。「この方向ではない」と判明することで次サイクルの精度が上がる

**仮説の品質基準（良い仮説の3条件）**:
| 条件 | 説明 | チェック方法 |
|------|------|-------------|
| 具体的 | 検証可能な粒度まで落とし込まれている | 「どのデータで確認するか」が明確か |
| 反証可能 | データで覆せる可能性がある | 「何が起きたら棄却か」が定義されているか |
| 行動接続 | 正しければ黄金理論のどこに入るかが明確 | 「チェックリストのどの条件になるか」が言えるか |

**仮説ピラミッド（最終的な黄金理論の構造）**:
```
【最上位仮説 = 黄金理論の上位原則】
伸びる動画は〇〇の条件を満たしている
    │
    ├─【支持仮説1】HIT群の全件に共通する特徴Aが原因である
    │    ├─ 根拠: アナリティクスデータの分析
    │    └─ 根拠: 台本データの分析
    │
    ├─【支持仮説2】MISS群に共通する特徴Bの欠如が原因である
    │    ├─ 根拠: HIT群との差分分析
    │    └─ 根拠: メタデータの分析
    │
    └─【支持仮説3】特徴A+Bの組合せが閾値を超えるとHITになる
         ├─ 根拠: 統計モデルの検証
         └─ 根拠: 反例（エドシーラン等）の分析
```

---

## 1. 変更箇所一覧

| # | 変更対象ファイル | 変更種別 | 概要 |
|---|-----------------|---------|------|
| 1-1 | `scripts/config.py` | 修正済み | HIT_THRESHOLD = 150000（変更済み） |
| 1-2 | `agents/coordinator.md` | 大幅書き換え | 分析目的・黄金理論の定義・中心的な問い・データ範囲を追加 |
| 1-3 | `agents/agent_c_meta_analysis.md` | 大幅書き換え | 分析目的・指標3分類・データ範囲・追加台本指標・感情曲線分析を反映 |
| 1-4 | `agents/agent_e_verification.md` | 修正 | 新HIT閾値・判定基準・黄金理論への貢献評価を追加 |
| 1-5 | `templates/script_analysis_template.json` | 拡張 | 新規台本分析指標5項目を追加 |
| 1-6 | `scripts/step1_fetch.py` | 機能追加 | Day別×トラフィックソース別クロス集計の取得を追加 |
| 1-7 | `scripts/data_summarizer.py` | 修正 | 新HIT閾値・新指標セクション追加 |
| 1-8 | `scripts/step3_build_model.py` | 修正 | 新HIT閾値・新指標の相関計算追加 |
| 1-9 | `IMPLEMENTATION_PLAN.md` | 追記 | 本改定の記録 |
| 1-10 | `agents/youtube_fundamentals.md` | **新規作成** | YouTube前提知識（アルゴリズム＋視聴者心理＋チャンネル固有データ） |
| 1-11 | `data/analysis_conclusion.md` | **新規出力** | サイクル完了時に自動生成される分析結論レポート（ゴースト・デック形式） |
| 1-12 | `agents/coordinator.md` | 追記 | 結論レポート生成ステップ・サイクル完了後の成果物一覧を追加 |
| 1-13 | `scripts/step2_analyze.py` | 機能追加 | generate_conclusion_report()を追加。--integrate完了時に結論レポートを自動生成 |
| 1-14 | `agents/agent_e_verification.md` | 入力追加 | 入力ファイルにgolden_theory.jsonを追加 |
| 1-15 | `scripts/data_summarizer.py` | セクション削除 | §6b「AI評価との乖離」テーブルを削除（判別力なし） |
| 1-16 | `scripts/step4_pdca.py` | 修正 | PDCA_DIR参照をworkspace/に変更（W-10のディレクトリ削除に対応） |
| 1-17 | `scripts/config.py` | 修正 | PDCA_DIR, MANUAL_DIR定義を削除 |
| 1-18 | `data/analysis_history/index.md` | 役割変更 | 棄却仮説テーブルを削除しバージョン履歴専用に縮小 |
| 1-19 | `scripts/step2_analyze.py` + `agents/agent_e_verification.md` | 機能追加 | 方法論レビュー自動化。Agent Eの「分析方法の評価」をパースしプロンプト改善提案を抽出・蓄積 |
| 1-20 | `scripts/step2_analyze.py` + `scripts/config.py` | 機能追加 | youtube-long接続。--integrate完了時にproduction_feedback.mdを自動生成（詳細はW-22参照） |
| 1-21 | `data/analysis_fundamentals.json` + 全スクリプト・全エージェント | **新規作成** | 分析の不変基盤（目的・HIT/MISS定義・共通点分析義務・指標体系・データ範囲・方法論）を単一JSONに集約。起動時整合性チェック強制（詳細はW-23参照） |

---

## 2. 各ファイルの詳細変更内容

---

### 2-1. `scripts/config.py`（変更済み）

```python
HIT_THRESHOLD = 150000   # 「伸びた」と判定する再生数の閾値（旧: 100000）
```

**追加定数**:
```python
# データ分析範囲
PRIMARY_ANALYSIS_WINDOW = 1    # 最重要: 最初の24時間（Day1）
SECONDARY_ANALYSIS_WINDOW = 7  # 重要: 最初の7日間
# 7日後に伸び始めた動画は、視聴回数が急増したポイントまで分析範囲を拡張する

# 指標分類
DATA_CATEGORIES = {
    "analytics": "アナリティクスデータ（YouTube API + Studio）",
    "script": "台本データ（台本構造分析JSON）",
    "meta": "メタデータ（人間評価・コンテキスト情報）"
}
```

---

### 2-2. `agents/coordinator.md` — 大幅書き換え

以下のセクションを**既存内容の先頭に追加**する（既存の「分析のゴール」セクションを置き換え）:

#### 追加・変更セクション:

```markdown
## 分析の最上位目的
**伸びた動画の共通点と伸びていない動画の共通点を明らかにし、「伸びる動画の黄金理論」を構築すること。**

### 中心的な問い（全分析はここから派生する）
1. **伸びた動画（15万回再生以上）全てに共通することは何か？**
2. **伸びていない動画（15万回再生未満）全てに共通することは何か？**
3. **1と2から導き出せる「伸びる動画の黄金理論」は何か？**

仮説はすべてこの3つの問いへの回答として設計すること。無関係な仮説は立てない。

### 分析手法（三本柱）
1. **水平思考**: 前提列挙→前提反転→代替説生成のフレームワークをAgent Cの分析フローに組み込む
2. **第一原理主義**: `agents/youtube_fundamentals.md` に明文化された前提知識から演繹的に考える
3. **仮説駆動アプローチ**: McKinsey方式の「答えから始める」手法。中心的な問いからDay 1 Answerを設定し、検証→進化させる

### Agent間の役割分担
- **Agent C（メタ分析）**: 共通点抽出 → 前提列挙 → 水平思考 → 因果仮説生成 → 仮説提示
- **Agent E（検証）**: レッドチームとしてAgent Cの仮説を反証データで検証。確証バイアス防止が主任務

### HIT/MISSの定義
- **HIT**: 15万回再生以上
- **MISS**: 15万回再生未満

### 黄金理論の形式
黄金理論は二層構造で構築する:

**第1層: 上位原則（なぜ伸びるのか）**
- YouTubeアルゴリズム・視聴者心理から演繹した「伸びるメカニズム」の説明
- 例: 「〇〇が△△を引き起こし、結果として再生数が伸びる」

**第2層: 実用チェックリスト（制作前に確認できる条件）**
- 制作者がコントロール可能な具体的条件のリスト
- 各条件にHIT群での充足率とMISS群での充足率を付記
- 例: 「条件X: HIT群 90%充足 / MISS群 20%充足」

### 分析に使用するデータの3分類

#### ■ アナリティクスデータ（YouTube API + Studioから取得）
| カテゴリ | 指標 | 取得元 |
|---------|------|--------|
| 基本指標 | 再生数, いいね数, コメント数, シェア数, 登録者獲得数 | API |
| トラフィック（7日合算） | ブラウジングIMP/CTR/視聴数, 関連動画IMP/CTR/視聴数, 検索IMP/CTR, 登録者視聴数 | Studio CSV |
| トラフィック（日別） | Day1-7のトラフィックソース別視聴数・CTR | API（day×trafficSource クロス集計） |
| 視聴維持 | 平均視聴時間(秒), 平均視聴率(%) | API |
| デモグラフィック | 年齢層別%, 性別%, コアターゲット(45-64歳)比率 | API |
| 日別推移 | Day1-7再生数, Day1→Day2変化率(%), 成長パターン分類 | API |
| 視聴者セグメント | コア視聴者%, ライト視聴者%, 新規視聴者% | Studio CSV |
| 関連動画ソース（※新規） | この動画への流入元となった関連動画のID・タイトル・視聴数・IMP・CTR（7日合算） | API（insightTrafficSourceDetail） |

#### ■ 台本データ（台本構造分析JSONから取得）
| カテゴリ | 指標 | 形式 |
|---------|------|------|
| 構造 | 一言テーマ有無, 敵役有無, 感情の底の数, エスカレーション有無, 救世主有無, 4要素完備フラグ | bool/num |
| フック | オープニング質問, 回答有無, 回答位置(%) | str/bool/num |
| MV | MV挿入数, 曲名リスト, 重要シーン配置フラグ | num/list/bool |
| 好奇心一致 | TOP1トピック, TOP1回答有無, TOP2トピック, TOP2回答有無, CAスコア(0-3) | str/bool/num |
| 感情曲線（※新規） | アップの数, ダウンの数, 合計転換数, 幕別パターン(Intro/1幕/2幕/3幕) | num/str |
| 導入30秒（※新規） | 開始タイプ(衝撃事実型/問いかけ型/エピソード導入型/データ提示型等), 引きの強さ(1-5) | str/num |
| 本人映像（※新規） | MV以外のYouTubeリンク総数, 可能なら種類分類(インタビュー/ライブ/ドキュメンタリー等) | num/list |
| 文字数 | 総文字数 | num |

#### ■ メタデータ（人間評価・コンテキスト情報）
| カテゴリ | 指標 | 形式 |
|---------|------|------|
| 人間GI評価 | G1(ゴシップ), G2(好奇心), G3(感情), G4(映画化), G6(楽曲知名度), GI_v3合計 | num(各1-5) |
| 人間CA評価 | CAスコア(0-3), GI×CA | num |
| コンテキスト | 公開日, 公開曜日, 公開時登録者数, 時事性（関連イベントの有無） | date/num/str |

### 重点的に見るべきデータ範囲

1. **最初の24時間（Day1）**: 最重要。ブラウジング推薦の初動を決定する
   - Day1の再生数、トラフィックソース別内訳（ブラウジング/関連/検索/登録者）
   - Day1のCTR

2. **最初の7日間（Day1-7）**: ほとんどの動画はここで伸びるかどうかが決まる
   - 日別推移パターン（成長型/減衰型/安定型）
   - Day1→Day2変化率（フック詐欺の検出: -50%以下で警告）
   - トラフィックソースの推移（ブラウジング比率の変化）

3. **遅延HIT（7日後に伸び始めた動画）**: 特殊ケースだが重要
   - 対象候補: ジャスティンビーバー（D1-7で8%、92%が7日後）、フレディーマーキュリー（D1→D7で631%成長）
   - 分析範囲: 視聴回数が急増したポイントまで拡張する
   - 遅延HIT発生時のトラフィックソース変化（何がトリガーになったか）を特定する
```

#### 既存セクション「分析のゴール（F4対策）」の変更:
- 削除して上記「分析の最上位目的」に置き換える
- 既存のサイクルフロー、差分モード、ループ制限、方法論レビューはそのまま維持

---

### 2-3. `agents/agent_c_meta_analysis.md` — 大幅書き換え

#### 「## 役割」セクションを以下に置き換え:

```markdown
## 役割
全データとインサイトを俯瞰し、**伸びた動画の共通点と伸びていない動画の共通点**を明らかにする。
水平思考×第一原理×仮説駆動で新仮説を生成する。あらゆる前提を疑い、あらゆる可能性を考える。

### 前提知識
`agents/youtube_fundamentals.md` を必ず参照すること。YouTubeアルゴリズム・視聴者心理・チャンネル固有データの前提知識が記載されている。

### 中心的な問い（Issue Statement — 全仮説はここから派生させる）
1. 伸びた動画（15万回再生以上）全てに共通することは何か？
2. 伸びていない動画（15万回再生未満）全てに共通することは何か？
3. 上記から導き出せる「伸びる動画の黄金理論」は何か？

仮説を立てる前に必ず「この仮説は中心的な問いのどれに対する回答か？」を自問すること。

### 分析フロー（5ステップ — この順序で実行すること）

**① HIT/MISS共通点抽出（必須・最優先）**
- HIT群の全動画に共通する特徴をアナリティクス・台本・メタの3分類で探す
- MISS群も同様に実施
- HIT群にのみ共通する特徴を特定する

**② 前提列挙（水平思考ステップ1）**
- ①で見つけた共通点に対し「なぜそれが共通点なのか」の前提を明示的に書き出す
- 例: 「HIT群はDay1ブラウジング比率が高い」→前提:「ブラウジング推薦がDay1の伸びを決める」

**③ 前提反転・水平思考（水平思考ステップ2）**
- 各前提を「もし逆だったら？」で検証する
- 例: 「もしブラウジングが低くても伸びた動画があったら？」→データで確認
- 反転の結果、前提が覆れば代替説を生成する

**④ 因果仮説生成（Day 1 Answer）**
- ①②③を踏まえ、中心的な問いへの回答として因果仮説を生成する
- 仮説は必ず複数（2〜3パターン）立てること（アンカリング防止）
- 各仮説に「何が証明されれば正しいと言えるか」の検証条件を付記する
- 仮説の品質基準: 具体的 / 反証可能 / 行動接続（黄金理論のどこに入るか）

**⑤ 新仮説提示（Agent Eへ渡す）**
- 仮説ピラミッド形式で出力する（最上位仮説 → 支持仮説 → 根拠）
- Agent Eがレッドチームとしてデータ検証を行う
- Agent Eの検証結果（支持/修正/棄却）を受けて次サイクルで仮説を進化させる
```

#### 「## 入力ファイル」セクションに以下を追加:

```markdown
### データの3分類を意識すること
- **アナリティクスデータ**: videos/*.jsonのanalytics_overview, traffic_sources, demographics, daily_data, manual_data
- **台本データ**: videos/*.jsonのscript_analysis（またはdata/scripts/*.json）
- **メタデータ**: human_scores.json（GI×CA人間評価）、video_index.jsonの公開日・登録者数
```

#### 「### 分析の方向性（重要）」セクションの冒頭に以下を追加:

```markdown
**最重要: HIT群全体・MISS群全体の共通点分析**
仮説を立てる前に、まず以下の作業を必ず行うこと:
1. HIT群（15万回以上）の全動画をリストアップし、全動画に共通する特徴を探す
2. MISS群（15万回未満）の全動画をリストアップし、全動画に共通する特徴を探す
3. 「HIT群には共通するがMISS群には共通しない」特徴を特定する
4. 上記をアナリティクスデータ・台本データ・メタデータの3分類それぞれで行う

**データ範囲の重点**:
- 最初の24時間（Day1）: 最重要。日別×トラフィックソース別のクロスデータを特に注視
- 最初の7日間（Day1-7）: Day1→Day2変化率、成長パターン、トラフィック構成推移
- 遅延HIT: 7日後に伸び始めた動画は、急増ポイントまでのデータを分析
```

#### 「### 分析の方向性」の既存項目A-Dの**前に**以下を新規追加:

```markdown
#### ★ 共通点分析（最優先 — 他の方向性より先に実施）
0. **HIT群の全件共通特徴**: 15万回以上の全動画に例外なく共通する特徴は何か？（アナリティクス・台本・メタの各分類で）
0b. **MISS群の全件共通特徴**: 15万回未満の全動画に例外なく共通する特徴は何か？
0c. **差分特徴**: HIT群には共通するがMISS群には共通しない特徴の抽出
```

#### 出力フォーマットに以下のセクションを追加（「## 新仮説」の前に）:

```markdown
## HIT/MISS共通点分析（必須）
### HIT群（15万回以上）全件の共通特徴
- アナリティクス面: ...
- 台本面: ...
- メタデータ面: ...

### MISS群（15万回未満）全件の共通特徴
- アナリティクス面: ...
- 台本面: ...
- メタデータ面: ...

### HIT群にのみ共通する特徴
（HIT群には共通するがMISS群には共通しない特徴）

### 黄金理論への示唆
（上記から導き出せる「伸びる動画の条件」の候補）
```

---

### 2-4. `agents/agent_e_verification.md` — 修正

#### 「## 役割」に以下を追加:

```markdown
### 前提知識
`agents/youtube_fundamentals.md` を必ず参照すること。YouTubeアルゴリズム・視聴者心理・チャンネル固有データの前提知識が記載されている。

### レッドチームとしての役割（確証バイアス防止）
Agent Cの仮説に対して**意図的に反証データを探す**ことが最重要の役割である。
- 仮説を支持するデータだけでなく、矛盾するデータを積極的に探す
- Agent Cが複数仮説を提示した場合、各仮説を独立に評価する（アンカリング防止）
- 仮説の検証結果は以下の3状態で報告する:
  | 状態 | 説明 |
  |------|------|
  | 支持される | データが仮説と整合する |
  | 修正される | 方向性は合っているが詳細が異なる → 修正案を提示 |
  | 棄却される | データが仮説と矛盾する → 棄却理由と学びを記録 |
- 棄却は失敗ではなく学習。「この方向ではない」と判明することで次サイクルの精度が上がる

### 黄金理論構築への貢献
検証の最終目的は「伸びる動画の黄金理論」の精度を高めること。
仮説を棄却する場合でも、「黄金理論のどの部分を修正すべきか」を必ず提案する。
```

#### 判定基準テーブルの閾値は変更なし（採択≥90%, 条件付き≥75%, 棄却<75%）だが、以下の注記を追加:

```markdown
#### HIT群/MISS群の完全共通点に対する特別判定
Agent Cが「HIT群全件に共通」「MISS群全件に共通」と報告した特徴については、
通常の精度基準ではなく**例外ゼロかどうか**を厳密に検証する。
1例でも例外があれば「全件共通」は棄却し、精度ベースの条件付き採択に格下げする。
```

#### 出力フォーマットに以下を追加:

```markdown
## 黄金理論チェックリスト更新提案
（現時点で確立できる「伸びる動画の条件」のチェックリスト案）
- 条件: {内容}
- HIT群充足率: X/Y本（Z%）
- MISS群充足率: X/Y本（Z%）
- 判別力: {高/中/低}
```

---

### 2-5. `templates/script_analysis_template.json` — 拡張

以下のフィールドを**既存構造に追加**する:

```json
{
  "...既存フィールドはすべて維持...",

  "emotional_curve": {
    "_comment": "感情曲線のアップダウン分析。台本の物語としての感情曲線の作り方を記録する",
    "total_ups": 0,
    "total_downs": 0,
    "total_transitions": 0,
    "pattern_by_act": {
      "intro": "",
      "first_act": "",
      "second_act": "",
      "third_act": ""
    },
    "_pattern_format": "U=上昇, D=下降 を連結。例: 'UDU'=上昇→下降→上昇",
    "balance_description": ""
  },

  "opening_30sec": {
    "_comment": "最初の30秒（導入〜第一幕の始まり）の分析",
    "opening_type": "",
    "_opening_type_options": "衝撃事実型 / 問いかけ型 / エピソード導入型 / データ提示型 / 感情訴求型 / その他",
    "hook_strength": 0,
    "_hook_strength_scale": "1-5。1=弱い引き、5=非常に強い引き",
    "description": ""
  },

  "non_mv_media": {
    "_comment": "MV以外の本人映像（インタビュー、ライブ、ドキュメンタリー等）のYouTubeリンク",
    "total_links": 0,
    "links_by_type": {
      "interview": 0,
      "live": 0,
      "documentary": 0,
      "other": 0
    },
    "_note": "種類分類が困難な場合はtotal_linksのみ記入し、links_by_typeは空でよい"
  }
}
```

---

### 2-6. `scripts/step1_fetch.py` — 機能追加

#### 変更内容: Day別×トラフィックソース別クロス集計の取得を追加

**変更1: 既存の `_get_daily()` メソッドに追加**:

```python
# 追加取得: Day別×トラフィックソース別クロス集計
# YouTube Analytics API v2:
#   dimensions: "day,insightTrafficSourceType"
#   metrics: "views,estimatedMinutesWatched"
#   startDate: 公開日
#   endDate: 公開日+6日（7日間）
```

**変更2: 関連動画ソース詳細の取得メソッドを新規追加**:

```python
# 新規取得: 関連動画ソースの詳細（どの動画から流入したか）
# YouTube Analytics API v2:
#   dimensions: "insightTrafficSourceDetail"
#   metrics: "views,estimatedMinutesWatched"
#   filters: "insightTrafficSourceType==RELATED_VIDEO;video=={video_id}"
#   startDate: 公開日
#   endDate: 公開日+6日（7日間）
# 返却データ: 流入元の動画ID/タイトル、視聴数、視聴時間
```

**videos/{video_id}.json の daily_data に追加するフィールド**:

```json
"daily_data": {
  "daily": [
    {
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "views": 0,
      "avg_view_duration": 0,
      "subs_gained": 0,
      "traffic_breakdown": {
        "BROWSE": {"views": 0, "minutes_watched": 0},
        "RELATED": {"views": 0, "minutes_watched": 0},
        "SEARCH": {"views": 0, "minutes_watched": 0},
        "SUBSCRIBER": {"views": 0, "minutes_watched": 0},
        "OTHER": {"views": 0, "minutes_watched": 0}
      }
    }
  ],
  "day1_to_day2_change_percent": 0,
  "related_video_sources": [
    {
      "source_video_id": "xxxxx",
      "source_video_title": "元動画のタイトル",
      "views": 0,
      "estimated_minutes_watched": 0.0
    }
  ]
}
```

**実行要件**: 既存24本すべてを再取得する（`--force-refetch` フラグを新設）

```bash
python scripts/step1_fetch.py --force-refetch     # 全24本を再取得（クロス集計含む）
python scripts/step1_fetch.py --force-refetch VID  # 特定動画のみ再取得
```

---

### 2-7. `scripts/data_summarizer.py` — 修正

#### 変更1: HIT閾値を config.HIT_THRESHOLD から読む（ハードコードしない）

#### 変更2: 新セクション追加

既存8セクションに加えて以下を追加:

```
§9 感情曲線テーブル（※新規）
  列: #, アーティスト, UP数, DOWN数, 転換合計, Intro, 1幕, 2幕, 3幕, HIT

§10 導入30秒テーブル（※新規）
  列: #, アーティスト, 開始タイプ, 引きの強さ(1-5), HIT

§11 本人映像テーブル（※新規）
  列: #, アーティスト, MV数, 非MVリンク数, 合計メディア数, HIT

§12 Day1トラフィック内訳テーブル（※新規）
  列: #, アーティスト, D1合計, D1_BROWSE, D1_RELATED, D1_SEARCH, D1_SUB, HIT

§13 関連動画ソーステーブル（※新規）
  列: #, アーティスト, 関連動画ソース上位3件（動画タイトル+視聴数）, 関連動画合計視聴数, HIT
  ※各動画について、流入元の上位3件のソース動画を表示
```

---

### 2-8. `scripts/step3_build_model.py` — 修正

#### 変更1: HIT閾値を config.HIT_THRESHOLD から読む

#### 変更2: `compute_derived_metrics()` に新指標を追加

```python
# 新規台本指標
"emotional_ups": script.get("emotional_curve", {}).get("total_ups"),
"emotional_downs": script.get("emotional_curve", {}).get("total_downs"),
"emotional_transitions": script.get("emotional_curve", {}).get("total_transitions"),
"opening_type": script.get("opening_30sec", {}).get("opening_type"),
"hook_strength": script.get("opening_30sec", {}).get("hook_strength"),
"non_mv_links": script.get("non_mv_media", {}).get("total_links"),
"total_media_count": mv_count + non_mv_links,  # MV数 + 非MVリンク数

# Day1トラフィック内訳
"day1_browse_views": daily[0].get("traffic_breakdown", {}).get("BROWSE", {}).get("views"),
"day1_related_views": daily[0].get("traffic_breakdown", {}).get("RELATED", {}).get("views"),
"day1_search_views": daily[0].get("traffic_breakdown", {}).get("SEARCH", {}).get("views"),
"day1_subscriber_views": daily[0].get("traffic_breakdown", {}).get("SUBSCRIBER", {}).get("views"),

# 関連動画ソース
"related_source_count": len(daily_data.get("related_video_sources", [])),  # 流入元の関連動画数
"top_related_source_views": max([s["views"] for s in related_sources], default=0),  # 最大流入元の視聴数
```

#### 変更3: cause_metrics / effect_metrics の再分類

新規指標の分類:
- **cause_metrics（制作者コントロール可能）に追加**:
  - `emotional_transitions`（感情曲線の転換数）
  - `hook_strength`（導入30秒の引きの強さ）
  - `non_mv_links`（非MVリンク数）
  - `total_media_count`（総メディア数 = MV + 非MV）

- **effect_metrics（結果指標）に追加**:
  - `day1_browse_views`（Day1ブラウジング視聴数）
  - `day1_related_views`（Day1関連動画視聴数）
  - `related_source_count`（流入元の関連動画数）
  - `top_related_source_views`（最大流入元の視聴数）

---

### 2-10. `agents/youtube_fundamentals.md` — **新規作成**

Agent CとAgent Eの両方が参照する前提知識ファイル。3つのセクションで構成する。

```markdown
# YouTube前提知識（YouTube Fundamentals）

> このファイルはAgent C（メタ分析）とAgent E（検証）が第一原理思考を行う際の前提知識である。
> 分析時に必ず参照し、ここに記載された仕組みから演繹的に考えること。

---

## 1. YouTubeアルゴリズムの仕組み

### 1.1 ブラウジング推薦（ホームフィード）
- YouTube のホームフィードに表示されるかどうかは、主に**CTR（クリック率）× 視聴維持率**で決まる
- 新規動画はまず登録者のフィードに表示され、初動のCTRと視聴維持が良ければ非登録者にも拡大される
- Day1のブラウジング推薦の量がその後の伸びを大きく左右する
- サムネイルとタイトルがCTRを決定し、コンテンツの質が視聴維持率を決定する

### 1.2 関連動画推薦
- 現在視聴中の動画と「類似性が高い」と判断された動画が関連動画として表示される
- 類似性はトピック、視聴者の行動パターン（同じ人が見ている動画）、メタデータで判定される
- 関連動画からの流入は、特定のトピック（アーティスト名）への検索需要と連動する

### 1.3 YouTube検索
- 検索トラフィックは視聴者の能動的な意図を反映する
- 時事性のあるイベント（訃報、受賞、スキャンダル等）で検索需要が急増する
- 検索トラフィックの急増は遅延HITの主要トリガーの一つ

### 1.4 成長パターン
- **即時成長型**: Day1-2で大部分の視聴が発生（ブラウジング推薦が強い）
- **持続成長型**: Day1-7で安定的に成長（関連動画+検索が継続）
- **遅延成長型**: Day7以降に急伸（外部イベント or バイラル発生）
- **減衰型**: Day1をピークに急落（フック詐欺 or 需要ミスマッチ）

---

## 2. 視聴者心理の原則

### 2.1 好奇心ギャップ（Curiosity Gap）
- 人は「知りたいこと」と「現在知っていること」のギャップがあると、それを埋めようとする欲求が生じる
- タイトル・サムネイルでギャップを作り、動画内で段階的に解消することで視聴維持が上がる
- ギャップが大きすぎると「釣り」と判断されて離脱、小さすぎると「見なくてよい」と判断される

### 2.2 感情移入と物語構造
- 視聴者は主人公（アーティスト）の感情に同一化することで視聴を継続する
- 「逆境→努力→成功」「栄光→転落→再起」等の物語構造は感情移入を促進する
- 感情の「底」（最も辛い場面）が深いほど、その後の回復に対するカタルシスが大きい

### 2.3 ゴシップ欲求
- 有名人のスキャンダル、裏話、知られていない事実への関心は普遍的に強い
- 「みんなが知っているあの人の、みんなが知らない話」が最もクリック率が高い
- ゴシップ要素が強すぎるとネガティブな反応を招くリスクもある

### 2.4 楽曲の力（音楽チャンネル固有）
- 知名度の高い楽曲がMVとして挿入されると、感情のピークを人工的に作れる
- 「聴きたかった曲」が物語のクライマックスで流れる体験は視聴満足度を大きく左右する
- 楽曲を知らない視聴者にとってはMV挿入が離脱ポイントになり得る

---

## 3. 「うた詠み」チャンネル固有データ（24本の分析から抽出）

### 3.1 チャンネル概要
- **コンテンツ**: 海外音楽アーティストの伝記・物語形式の長尺動画（13〜22分）
- **動画数**: 24本（2025年7月〜2026年2月）
- **登録者推移**: 約20,000人 → 約47,000人（約136%成長）
- **公開頻度**: 週1〜2本

### 3.2 視聴者デモグラフィック
- **コア視聴者層**: 45〜64歳の女性（全視聴の30〜40%を占める）
- **サブ視聴者層**: 35〜44歳の男女、65歳以上の女性
- **最少視聴者層**: 13〜24歳（全視聴の3%未満）
- **含意**: 懐かしさ（ノスタルジア）への共感が視聴動機の中核にある

### 3.3 トラフィック構成
- **主要流入**: 登録者フィード（ブラウジング）38〜74% + 関連動画 22〜50%
- **この2つで全体の70〜96%**を占める。検索・外部は合計5%未満
- **含意**: アルゴリズム推薦への依存度が極めて高い

### 3.4 視聴維持パターン
- **平均視聴時間**: 5〜8分（動画長の29〜39%）
- **関連動画からの視聴者**は登録者より長く視聴する傾向（414〜582秒 vs 299〜464秒）
- **含意**: 新規視聴者ほど「期待を持ってクリック→満足すれば長く見る」パターン

### 3.5 視聴者セグメント
- **新規視聴者**: 53〜57%（過半数が初見）
- **ライト視聴者**: 40〜50%
- **コア視聴者**: 2〜3%
- **含意**: 毎回の動画で過半数が新規。アルゴリズム推薦による新規獲得が成長の鍵

### 3.6 GI×CA評価の傾向（14本評価済み）
- **高パフォーマンス**: GI_v3×CA > 40（例: ジャスティンビーバー 57、マイケルジャクソン①② 57.5）
- **低パフォーマンス**: GI_v3×CA < 15（例: ボブマーリー 5、アデル 7）
- **含意**: GI（物語の一般的関心度）とCA（好奇心一致度）の掛け算が性能を予測する可能性
```

---

### 2-9. `IMPLEMENTATION_PLAN.md` — 追記

「### 次のステップ」セクションに以下を追加:

```markdown
### 分析フレームワーク改定（2026-02-16）
- ANALYSIS_FRAMEWORK_CHANGES.md に基づく全面改定
- HIT閾値: 10万→15万（config.py変更済み）
- 分析目的: 「黄金理論」構築を最上位目的に設定
- 分析手法: 水平思考フレームワーク + 第一原理（前提知識明文化）+ 仮説駆動（McKinsey方式）
- データ3分類: アナリティクス / 台本 / メタデータ
- データ範囲: Day1（最重要）→ Day1-7 → 遅延HIT拡張
- 台本指標追加: 感情曲線, 導入30秒, 非MVリンク
- step1_fetch.py: Day別×トラフィックソース別クロス集計追加 + 全24本再取得
- 新規ファイル: agents/youtube_fundamentals.md（YouTube前提知識）
- Agent C: 5ステップ分析フロー（共通点抽出→前提列挙→水平思考→仮説生成→提示）
- Agent E: レッドチーム役割の明確化（確証バイアス防止）
- Agent C/E/coordinator: 中心的な問い・HIT/MISS共通点分析・黄金理論チェックリストを追加
```

---

### 2-11. `data/analysis_conclusion.md` — サイクル完了時に自動生成

**目的**: 分析サイクル完了後、分析結果が `insights.md`・`golden_theory.json`・`model.json`・`analysis_report.md` に散在する問題を解決する。「結局、伸びる動画の黄金理論は何か？」という最上位の問いに対する統合的な結論を、誰にでも読める形式で出力する。

**設計方針（ゴースト・デック形式）**:
- 専門用語を使わない。統計用語（r値、R²等）には必ず平易な説明を付記
- 「結論→根拠→限界→次のアクション」のストーリーラインで構成
- 指標名は日本語の説明に変換（例: `total_media_count` → 「動画内に挿入した映像素材の総数」）
- 棄却された仮説は「試したが間違いだった仮説」として記載（学びを強調）

**生成タイミング**: `python scripts/step2_analyze.py --integrate` の最終ステップで自動生成。サイクル完了ごとに上書き更新される。

**レポート構成**:

```markdown
# 伸びる動画の黄金理論 — 分析結論レポート

> 最終更新: {date} | 分析サイクル: {cycle}回完了 | 対象動画: {n}本

---

## このレポートの読み方
この文書は、{n}本の動画データを分析した結果をまとめたものです。
「伸びる動画（15万再生以上）」と「伸びない動画」に分けて共通点を調べ、
制作前に確認できるチェックリストとして整理しました。

---

## 1. 結論: 伸びる動画の条件（黄金理論）

### なぜ伸びるのか（上位原則）
{golden_theory.json の principles から平易な文章で記述}

### 制作前チェックリスト
| # | チェック項目 | HITの中でクリアした割合 | MISSの中でクリアした割合 | 判別力 |
|---|------------|---------------------|----------------------|-------|

### この理論の信頼度
- 全動画への的中率: {accuracy}%（{correct}/{total}本）
- 反例（理論が外した動画）: {exceptions}
- まだ解明できていないこと: {open_questions}件

---

## 2. 発見の要約

### 伸びた動画（HIT）に共通していたこと
{insights.md の採択済みインサイトから}

### 伸びなかった動画（MISS）に共通していたこと
{insights.md + model.json から導出}

### 試したが間違いだった仮説
{insights.md の棄却仮説から。「〇〇が原因かと思ったが、△△だった」形式}

---

## 3. 統計サマリ

### 予測力の高い指標
| 指標 | 再生数との相関 | 意味 |
|------|-------------|------|

### モデルの精度推移
| バージョン | 日付 | R² | 主な変更点 |
|-----------|------|-----|-----------|

---

## 4. 次のアクション

### 未解決の問い
### 次に検証すべきこと
### データ品質の課題
```

**データソースと変換ルール**:

| レポートセクション | データソース | 変換処理 |
|-------------------|------------|---------|
| 上位原則 | `golden_theory.json` の `principles[]` | status が "established"/"supported" のみ抽出し平易な文に変換 |
| チェックリスト | `golden_theory.json` の `checklist[]` | status が "adopted" のみ。rate を %表記に変換 |
| 理論の信頼度 | `model.json` の prediction accuracy | correct/total を計算 |
| HIT共通点 | `insights.md` の「採択済みインサイト」 | 主要なもの（最新3〜5件）を抽出 |
| 棄却仮説 | `insights.md` の「棄却仮説と学び」 | 「学び」フィールドを「〇〇だと思ったが△△だった」形式に再構成 |
| 相関テーブル | `model.json` の cause_metrics 相関 | 上位5件を METRIC_DESCRIPTIONS で日本語化 |
| 精度推移 | `analysis_history/index.md` | バージョン履歴テーブルをパース |
| 未解決の問い | `insights.md` の「未解決の問い」 | そのまま転記 |

---

### 2-12. `agents/coordinator.md` — 結論レポート関連の追記

#### Phase 3 の手順に追加:

```markdown
  9. 結論レポート生成（analysis_conclusion.md を更新）
```

#### サイクル終了条件の後に追加:

```markdown
### サイクル完了後の成果物
サイクルが完了（正常終了・成果あり終了・上限終了のいずれか）すると、以下が更新される:
- `data/analysis_conclusion.md` — **分析の最終結論**（誰でも読める形式）
- `data/golden_theory.json` — 黄金理論の構造化データ
- `data/analysis_history/insights.md` — 採択/棄却の全履歴
- `data/model.json` — 統計モデル
```

---

### 2-13. `scripts/step2_analyze.py` — 結論レポート生成機能の追加

`integrate()` 関数の末尾（矛盾チェックの後、return の前）に以下を追加:

```python
# 8. 結論レポート生成
print("\n[統合] 結論レポート生成中...")
generate_conclusion_report()
print(f"  analysis_conclusion.md 生成完了")
```

**新規関数**:

```python
METRIC_DESCRIPTIONS = {
    "total_media_count": "動画内に挿入した映像素材の総数",
    "non_mv_links": "MV以外の映像（インタビュー・ライブ等）の数",
    "mv_count": "挿入したミュージックビデオの数",
    "word_count": "台本の文字数",
    "video_duration": "動画の長さ（秒）",
    "gi_x_ca": "関心度×好奇心一致度（GI×CA）スコア",
    "hook_strength": "最初の30秒の引きの強さ",
    "emotional_transitions": "感情曲線の転換回数",
    "ca_score": "好奇心一致度（CA）スコア",
}


def generate_conclusion_report():
    """
    golden_theory.json + insights.md + model.json + index.md を統合し、
    data/analysis_conclusion.md を生成する。

    設計方針:
    - ゴースト・デック形式: 専門用語を使わず、誰でも読めるドキュメント
    - 構造: 結論（黄金理論）→ 発見の要約 → 統計サマリ → 次のアクション
    - golden_theory.json の principles/checklist を平易な日本語に変換
    - model.json の相関テーブルに「意味」列を付加（METRIC_DESCRIPTIONS）
    - insights.md の棄却仮説を「試したが間違いだった仮説」として再構成
    """
    golden = load_golden_theory()
    frontmatter, body = load_insights()
    model = _load_model_json()

    report = _build_header(frontmatter)
    report += _build_conclusion_section(golden)
    report += _build_findings_section(body)
    report += _build_stats_section(model)
    report += _build_next_actions_section(body)
    report += _build_footer()

    output_path = os.path.join(DATA_DIR, "analysis_conclusion.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
```

---

### 2-14. `agents/agent_e_verification.md` — 入力ファイルにgolden_theory.jsonを追加

**問題**: Agent Eの入力ファイルにgolden_theory.jsonが含まれておらず、現在確立されている黄金理論を参照せずに検証を行っている。

**対応**: 入力ファイルリストの6番目に追加:

```markdown
6. `data/golden_theory.json` — 現在の黄金理論（原則+チェックリスト+棄却条件）
```

検証時の追加チェック項目:
- 新仮説と確立済み原則（principles）の整合性
- 新チェックリスト提案と既存条件の重複有無
- 棄却済み条件と同方向の仮説の排除

---

### 2-15. `scripts/data_summarizer.py` — §6b AI評価セクションの削除

**問題**: §6b「AI評価との乖離」テーブルが出力されているが、AI評価は系統的過大評価（G3=5, G2=4-5に集中）で判別力がない。Agent Cがこのデータを使うリスクがある。

**対応**:
- §6b のテーブル生成コード（`### 6b. AI評価との乖離（参考）`セクション）を削除
- §6 の注記「AI評価は系統的に過大評価する」は維持
- AI評価の生データ（videos/*.json内）は将来の再較正用に保持

---

### 2-16. `scripts/step4_pdca.py` — PDCA_DIR参照の修正

**問題**: step4_pdca.pyがconfig.pyのPDCA_DIR（`data/pdca_reports/`）をインポートしているが、このディレクトリはファイル整理（W-10）で削除される。

**対応**:
- step4_pdca.py: `from config import PDCA_DIR` を削除し、出力先を `WORKSPACE_DIR` に変更
- config.py: `PDCA_DIR` と `MANUAL_DIR` の定義行を削除

---

### 2-17. `scripts/config.py` — 不要なパス定義の削除

W-10で削除されるディレクトリへの参照を削除:

```python
# 削除する行
MANUAL_DIR = os.path.join(DATA_DIR, "manual_exports")
PDCA_DIR = os.path.join(DATA_DIR, "pdca_reports")
```

---

### 2-18. `data/analysis_history/index.md` — 役割変更

**問題**: index.mdとinsights.mdの両方に棄却仮説が記録されており冗長。

**対応**: index.mdから「棄却仮説テーブル」を削除し、バージョン履歴専用に縮小:

```markdown
# 分析履歴

## バージョン履歴
| Ver | 日付 | R² | 主な変更点 |
|-----|------|-----|-----------|

## 未解決問題
（棄却仮説の参照はinsights.mdに統一）
```

---

### 2-19. `scripts/step2_analyze.py` + `agents/agent_e_verification.md` — 方法論レビュー自動化

**問題**: coordinator.md の Step 8「方法論レビュー」では、Agent Eの「分析方法の評価」セクションに基づいてAgent C/E定義ファイル（プロンプト）を改善すると規定されている。しかし step2_analyze.py の `integrate()` にはこの処理が未実装。Agent Eが毎回書く改善提案が放置されている。

**対応**:

1. **Agent E出力のJSONに `methodology_review` フィールドを追加**:
   - Agent Cの仮説生成品質（結果指標使用率、データ正確性、棄却仮説再提案、多様性）
   - Agent C/E定義ファイルへの具体的な修正提案（対象・種別・理由・優先度）
   - Agent E自身の自己評価

2. **step2_analyze.py に `apply_methodology_review()` を追加**:
   - 自動適用: insights.md へ品質メトリクス（結果指標使用率の推移等）を自動記録
   - 手動確認: `workspace/prompt_modifications.md` にプロンプト改善提案を出力
   - Agent C/E定義ファイルの直接編集は自動化しない（品質劣化リスク回避）

3. **agent_e_verification.md の「分析方法の評価」セクションに構造化データ対応を明記**

詳細な仕様は WORKFLOW_IMPROVEMENTS.md の W-21 を参照。

---

## 3. 実行順序

```
1. scripts/config.py              ← 変更済み（HIT_THRESHOLD=150000）
2. templates/script_analysis_template.json  ← 新指標3項目追加
3. scripts/step1_fetch.py         ← Day別×トラフィックソース クロス集計追加
4. scripts/step1_fetch.py --force-refetch  ← 全24本再取得（実行）
5. scripts/data_summarizer.py     ← 新セクション§9-12追加 + HIT閾値修正
6. scripts/step3_build_model.py   ← 新指標追加 + HIT閾値修正
7. agents/youtube_fundamentals.md ← 新規作成（YouTube前提知識: アルゴリズム＋心理＋チャンネル固有）
8. agents/coordinator.md          ← 分析目的・黄金理論・分析手法・データ分類・データ範囲を追加
9. agents/agent_c_meta_analysis.md ← 5ステップ分析フロー・水平思考・仮説駆動を追加
10. agents/agent_e_verification.md ← レッドチーム役割・確証バイアス防止・黄金理論チェックリストを追加
11. （IMPLEMENTATION_PLAN.mdは W-10 で削除予定のため、記録は insights.md の備考に残す）

--- 結論レポート機能追加 ---
12. scripts/step2_analyze.py に generate_conclusion_report() を追加
13. agents/coordinator.md に結論レポート手順・成果物一覧を追記

--- 監査対応 ---
14. agents/agent_e_verification.md に golden_theory.json を入力追加
15. scripts/data_summarizer.py から §6b セクションを削除
16. scripts/config.py から PDCA_DIR, MANUAL_DIR を削除
17. scripts/step4_pdca.py の出力先を workspace/ に変更
18. data/analysis_history/index.md を役割変更（棄却仮説テーブル削除）

--- 方法論レビュー自動化 ---
19. agents/agent_e_verification.md の構造化データに methodology_review フィールドを追加
20. scripts/step2_analyze.py に apply_methodology_review() を追加

--- 不変基盤ファイル（W-23: 他の全変更より先に実施することを推奨） ---
21. data/analysis_fundamentals.json      ← 新規作成（6要素を集約。詳細はW-23参照）
22. scripts/common/data_loader.py        ← load_fundamentals() + validate_fundamentals() を追加
23. 全スクリプト冒頭に validate_fundamentals() 呼び出しを追加
24. agents/coordinator.md + agent_c + agent_e ← 必読ファイルに analysis_fundamentals.json を追加

--- 実行後 ---
25. python scripts/step3_build_model.py  ← モデル再構築（新HIT閾値で、fundamentals整合性チェック含む）
26. python scripts/step2_analyze.py      ← 分析サイクル実行（新フレームワークで）
27. python scripts/step2_analyze.py --integrate ← 統合処理 + 方法論レビュー + 結論レポート生成確認
```

---

## 4. 将来的な変更（本改定のスコープ外だが記録）

### youtube-long への反映 → **W-22 で正式に設計済み**

以下の項目は WORKFLOW_IMPROVEMENTS.md W-22 で設計された `production_feedback.md` 自動生成で対応する:

- ~~GI×CA閾値を model.json の最新値に連動させる~~ → W-22 セクション1（選定基準の更新提案）で差異を自動検出
- ~~`youtube-long/agents/utayomi-step1-selection.md` の修正~~ → W-22 セクション2（台本設計への示唆）で提案生成

**W-22のスコープ外として残る項目**:
- 好奇心マップ作成時に、YouTubeで再生回数が高いその人物の動画・ショート動画の内容も取得する
  - 最終的な好奇心TOP1-2は、Web検索結果 + YouTube高再生動画の内容 の両方を根拠にする
  - これはutayomi-step1-selection.mdの機能拡張であり、youtube-long側の改修が必要

### 未評価10本のGI×CA人間評価
- エドシーラン、テイラースウィフト、レディーガガ、ブルーノマーズ等の人間評価を完了させる
- 特にエドシーラン（48万再生、旧GI=10）は黄金理論の潜在的反例として最優先

### 台本構造の24本再分析
- 新テンプレート（emotional_curve, opening_30sec, non_mv_media）で全24本を再分析する必要がある

---

## 5. 実装バグ・ギャップ一覧（2エージェント完全性検証で発見）

> Agent C + Agent E の2エージェントのみでワークフロー全体が機能するかを検証した結果。
> **結論: 追加エージェント不要。2エージェント + Python自動処理で完結する。ただしPythonコードに以下のバグ・ギャップあり。**
> 詳細は WORKFLOW_IMPROVEMENTS.md セクション5 を参照。

| ID | 種別 | 重大度 | 概要 | 対応先 |
|----|------|--------|------|--------|
| BUG-1 | バグ | 高 | `update_insights()` が "conditional" ステータスを処理せず、条件付き採択仮説が消失 | step2_analyze.py |
| BUG-2 | バグ | 中 | `update_golden_theory()` が principle の "modify"/"remove" アクションを処理しない | step2_analyze.py |
| BUG-3 | バグ | 中 | `validate_golden_theory()` がスタブ（pass）のまま。チェックリスト充足率が更新されない | step3_build_model.py |
| GAP-4 | 未実装 | 中 | W-21 方法論レビューが未実装（設計済み・コード未反映） | step2_analyze.py |
| GAP-5 | ギャップ | 低 | サイクル番号をAgent任せにしており、自動管理がない。ID重複リスク | step2_analyze.py |
| GAP-6 | ギャップ | 低 | Agent C出力の `hit_miss_commonalities` がstep2で未使用。共通点分析結果が記録されない | step2_analyze.py |

修正の実行順序・詳細な修正方針は WORKFLOW_IMPROVEMENTS.md セクション5 に記載。
