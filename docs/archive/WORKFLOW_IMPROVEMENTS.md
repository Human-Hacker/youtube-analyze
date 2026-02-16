# ワークフロー改善仕様書

> **目的**: ANALYSIS_FRAMEWORK_CHANGES.md（分析フレームワーク改定）と併せて実施する、パイプライン構造の改善。
> **対象リポジトリ**: `/Users/user/タスク/youtube-analyze/`
> **前提**: ANALYSIS_FRAMEWORK_CHANGES.md の変更が先に適用されていること。

---

## 0. 改善の全体方針

### 0.1 根本課題
現在のパイプラインは「データ処理（Python）」と「知見発見（Agent C/E in Claude Code）」が**完全に断絶**している。
Agent C/Eが発見した仮説・黄金理論チェックリストがmodel.jsonに反映されず、step3_build_model.pyはAgent出力を一切読まない。

### 0.2 改善方針
1. **golden_theory.json** を新設し、黄金理論の二層構造を構造化データとして格納する
2. **step2_analyze.py** を半自動オーケストレーターに改修し、Agent出力→insights更新→model更新を一気通貫で制御する
3. **insights.md** を構造化し、採択/棄却仮説をパース可能にする
4. **Agent C/E出力フォーマット** を規約化し、JSONブロックで構造化データを埋め込む
5. **step3_build_model.py** を機能別に分割し、golden_theory.jsonを読んでモデルに反映する
6. **フィードバックループ** を明確化し、棄却仮説の蓄積→次サイクルへの引き継ぎを自動化する

---

## 1. 変更箇所一覧

| # | 変更対象 | 変更種別 | 概要 |
|---|---------|---------|------|
| W-1 | `data/golden_theory.json` | **新規作成** | 黄金理論の二層構造を格納するJSONファイル |
| W-2 | `scripts/step2_analyze.py` | 大幅改修 | 半自動オーケストレーターに改修 |
| W-3 | `data/analysis_history/insights.md` | フォーマット変更 | YAML frontmatter + 構造化セクションに変更 |
| W-4 | `agents/agent_c_meta_analysis.md` | 出力フォーマット追加 | 出力にJSONブロック規約を追加 |
| W-5 | `agents/agent_e_verification.md` | 出力フォーマット追加 | 出力にJSONブロック規約を追加 |
| W-6 | `scripts/step3_build_model.py` | 機能分割 | 6モジュールに分割 |
| W-7 | `scripts/common/data_loader.py` | **新規作成** | 共通データ読み込みモジュール |
| W-8 | `scripts/common/metrics.py` | **新規作成** | 共通指標計算モジュール |
| W-9 | `agents/coordinator.md` | 修正 | Agentパス修正 + ループ制御の明確化 |
| W-10 | プロジェクト全体 | **ファイル整理** | 不要ファイルの削除・.gitignore更新・video_index.json整理 |
| W-11 | `agents/agent_c_meta_analysis.md` | 入力戦略変更 | 2フェーズ読み込み（概要→選択的深掘り）+ 読み込み計画の明示化 |
| W-12 | `scripts/step2_analyze.py` + 新規テンプレート | **機能追加** | サイクル完了時に分析結論レポート（analysis_conclusion.md）を自動生成 |
| W-13 | `data/analysis_history/index.md` | 役割変更 | 棄却仮説テーブルをinsights.mdに一本化。index.mdはバージョン履歴専用に縮小 |
| W-14 | `agents/agent_e_verification.md` | 入力追加 | 入力ファイルにgolden_theory.jsonを追加（現在の黄金理論を参照して検証） |
| W-15 | `scripts/data_summarizer.py` | セクション修正 | §6b「AI評価との乖離」セクションを削除（判別力なし・誤誘導リスク） |
| W-16 | `scripts/step4_pdca.py` + `scripts/config.py` | 修正 | PDCA_DIR参照をW-10の削除に合わせて修正。出力先をworkspace/に変更 |
| W-17 | `agents/coordinator.md` | 修正 | Phase 3の手動ステップ残存を削除 + IMPLEMENTATION_PLAN.md参照を削除 |
| W-18 | `scripts/step3_filters.py` | 検討事項 | 3段階フィルター（精度66.7%）の扱いを見直し。表示に注意喚起を追加 |
| W-19 | `scripts/step3_history.py` | 改修 | analysis_historyスナップショットの保持ポリシーを導入（最新5件+マイルストーン） |
| W-20 | `data/analysis_report.md` | 役割明確化 | 読み手をAgent C/E + 開発者に限定し、結論レポート（W-12）との棲み分けを明記 |
| W-21 | `scripts/step2_analyze.py` | **機能追加** | Agent Eの「分析方法の評価」セクションをパースし、プロンプト改善提案を抽出・蓄積。改善アクションを自動実行 |
| W-22 | `scripts/step2_analyze.py` + `youtube-long/` | **機能追加** | youtube-analyze → youtube-long パイプライン接続。分析結果を制作プロセスに自動フィードバック |
| W-23 | `data/analysis_fundamentals.json` + 全スクリプト・全エージェント | **新規作成** | 分析の不変基盤（目的・定義・指標・方法論）を単一ファイルに集約し、起動時整合性チェックを強制 |

---

## 2. 各変更の詳細

---

### W-1. `data/golden_theory.json` — 新規作成

黄金理論の二層構造を格納する。step3_build_model.pyが読み込んでモデルに反映する。
Agent Eのチェックリスト提案をstep2がパースしてここに書き込む。

**初期スキーマ**:

```json
{
  "version": "1.0",
  "last_updated": "YYYY-MM-DD",
  "last_cycle": 0,

  "principles": [
    {
      "id": "P1",
      "statement": "（上位原則の記述）",
      "mechanism": "（なぜ伸びるのかのメカニズム説明）",
      "status": "hypothesis",
      "established_cycle": null,
      "supporting_evidence": [],
      "contradicting_evidence": []
    }
  ],

  "checklist": [
    {
      "id": "C1",
      "condition": "（条件名）",
      "hit_fulfillment": {"count": 0, "total": 0, "rate": 0.0},
      "miss_fulfillment": {"count": 0, "total": 0, "rate": 0.0},
      "discriminative_power": "high",
      "status": "adopted",
      "established_cycle": 1,
      "linked_principle": "P1",
      "data_category": "analytics",
      "notes": ""
    }
  ],

  "rejected_conditions": [
    {
      "id": "R1",
      "condition": "（棄却された条件）",
      "rejection_reason": "（棄却理由）",
      "rejected_cycle": 1,
      "learning": "（この棄却から得た学び）"
    }
  ]
}
```

**ステータス定義**:
- `principles[].status`: `"hypothesis"` → `"supported"` → `"established"` （仮説→支持→確立）
- `checklist[].status`: `"proposed"` → `"adopted"` / `"conditional"` / `"rejected"`
- `checklist[].discriminative_power`: `"high"` (差>50%) / `"medium"` (差20-50%) / `"low"` (差<20%)

---

### W-2. `scripts/step2_analyze.py` — 半自動オーケストレーターに改修

**現状の問題**: data_summaryを生成して手順を表示するだけ。Agent出力は手動でClaude Codeが実行。出力のmodel.jsonへの反映は一切ない。

**改修後のフロー**:

```python
# step2_analyze.py の新フロー

def main(mode, diff_video_id=None):
    """
    Phase 1: データ準備（自動）
    Phase 2: Agent C/E 実行指示（手動 — Claude Codeで実行）
    Phase 3: Agent出力の統合（自動 — Agent完了後に再実行）
    """

    # === Phase 1: データ準備 ===
    run_data_summarizer(diff_video_id)
    prepare_workspace()
    print_agent_instructions(mode)  # Agent C/E の実行手順を表示
    # ここで一旦停止。ユーザーがClaude CodeでAgent C/Eを実行する。

    # === Phase 3: Agent出力の統合 ===
    # --integrate フラグで再実行すると、以下を自動実行
    if args.integrate:
        # 1. Agent出力ファイルの存在チェック
        check_agent_outputs()

        # 2. new_hypotheses.md からJSONブロックを抽出
        hypotheses = parse_agent_c_output("workspace/new_hypotheses.md")

        # 3. verification_report.md からJSONブロックを抽出
        verification = parse_agent_e_output("workspace/verification_report.md")

        # 4. insights.md を更新
        update_insights(hypotheses, verification)

        # 5. golden_theory.json を更新
        update_golden_theory(verification["checklist_proposal"])

        # 6. step3_build_model.py を実行
        run_step3()

        # 7. サイクルカウンターを進める
        increment_cycle()

        # 8. 次サイクルが必要か判定
        if verification["unresolved_contradictions"]:
            print("矛盾が残っています。次サイクルを実行してください。")
            print(f"現在のサイクル: {current_cycle}/{MAX_CYCLES}")
```

**新しいCLIインターフェース**:

```bash
# Phase 1: データ準備 + Agent実行指示を表示
python scripts/step2_analyze.py

# Phase 1 + 差分モード
python scripts/step2_analyze.py --diff VIDEO_ID

# Phase 3: Agent完了後に統合処理を実行
python scripts/step2_analyze.py --integrate

# 全フェーズ一気通貫（Agent出力が既に存在する場合）
python scripts/step2_analyze.py --integrate --auto
```

**新規関数**:

```python
def parse_agent_c_output(filepath: str) -> dict:
    """
    new_hypotheses.md から ```json ブロックを抽出し、
    仮説リストを返す。
    """
    pass

def parse_agent_e_output(filepath: str) -> dict:
    """
    verification_report.md から ```json ブロックを抽出し、
    検証結果・チェックリスト提案・残存矛盾を返す。
    """
    pass

def update_insights(hypotheses: dict, verification: dict):
    """
    insights.md のYAML frontmatterと本文を更新。
    - 採択仮説 → 「## 採択済みインサイト」に追加
    - 棄却仮説 → 「## 棄却仮説と学び」に追加
    """
    pass

def update_golden_theory(checklist_proposal: list):
    """
    golden_theory.json を更新。
    - 新規条件を checklist に追加
    - 棄却条件を rejected_conditions に移動
    - discriminative_power を再計算
    """
    pass
```

---

### W-3. `data/analysis_history/insights.md` — フォーマット変更

**現状の問題**: 自由記述でスキーマ未定義。パース不可能。

**新フォーマット**: YAML frontmatter + 構造化Markdownセクション

```markdown
---
version: 3
last_updated: "2026-02-16"
total_cycles: 2
adopted_count: 5
rejected_count: 3
open_questions: 2
---

# 分析インサイト

## 採択済みインサイト

### INS-001: {インサイトのタイトル}
- **サイクル**: 1
- **ステータス**: adopted
- **根拠**: {根拠の要約}
- **黄金理論チェックリストID**: C1
- **詳細**:
  {自由記述の詳細説明}

### INS-002: {インサイトのタイトル}
...

## 棄却仮説と学び

### REJ-001: {棄却された仮説}
- **サイクル**: 1
- **棄却理由**: {データとの矛盾点}
- **学び**: {この棄却から得た知見}

### REJ-002: ...

## 未解決の問い

### Q-001: {未解決の問い}
- **発見サイクル**: 1
- **関連データ**: {どのデータが関係するか}

## 探索的発見（次サイクルへの手がかり）

### EXP-001: {発見内容}
- **サイクル**: 1
- **次のアクション**: {次サイクルでどう扱うか}
```

**パース規約**:
- YAML frontmatterは `---` で囲まれた部分。メタデータの自動集計に使用
- 各セクション内の `### ` 見出しが1件のエントリー
- `- **キー**:` 形式の行が構造化属性
- 自由記述部分は `**詳細**:` 以降の段落

---

### W-4. `agents/agent_c_meta_analysis.md` — 出力フォーマット追加

**現状の問題**: 出力が自由記述Markdownで、step2がパースできない。

**追加規約**: ANALYSIS_FRAMEWORK_CHANGES.md で定義されたMarkdownセクション（HIT/MISS共通点分析、新仮説 等）は**そのまま維持**する。それに加えて、出力の**末尾に** `## 構造化データ` セクションを追加し、JSONブロックで機械パース用のデータを出力する。つまり人間用Markdownと機械用JSONが同じファイル内に共存する。

Agent Cの出力フォーマットの「## 新仮説」セクションの**後に**以下を追加:

```markdown
## 構造化データ（step2がパースする — このセクションのフォーマットを厳守すること）

```json
{
  "cycle": 1,
  "hit_miss_commonalities": {
    "hit_common": [
      {
        "feature": "（HIT群全件に共通する特徴）",
        "category": "analytics",
        "confidence": "all_match",
        "detail": "（詳細説明）"
      }
    ],
    "miss_common": [
      {
        "feature": "（MISS群全件に共通する特徴）",
        "category": "script",
        "confidence": "all_match",
        "detail": ""
      }
    ],
    "hit_only": [
      {
        "feature": "（HIT群にのみ共通する特徴）",
        "category": "meta",
        "detail": ""
      }
    ]
  },
  "hypotheses": [
    {
      "id": "H1",
      "statement": "（仮説の記述）",
      "central_question": 1,
      "verification_condition": "（何が証明されれば正しいと言えるか）",
      "rejection_condition": "（何が起きたら棄却か）",
      "checklist_candidate": "（正しければ黄金理論のどの条件になるか）",
      "supporting_data": ["（根拠データ1）", "（根拠データ2）"],
      "quality_check": {
        "specific": true,
        "falsifiable": true,
        "action_connected": true
      }
    },
    {
      "id": "H2",
      "statement": "...",
      "central_question": 2,
      "verification_condition": "...",
      "rejection_condition": "...",
      "checklist_candidate": "...",
      "supporting_data": [],
      "quality_check": {
        "specific": true,
        "falsifiable": true,
        "action_connected": true
      }
    }
  ],
  "lateral_thinking_log": {
    "premises_listed": ["（列挙した前提1）", "（列挙した前提2）"],
    "premises_inverted": [
      {
        "premise": "（反転した前提）",
        "result": "（反転の結果: 覆った / 維持された）",
        "alternative": "（覆った場合の代替説。維持ならnull）"
      }
    ]
  }
}
```（←閉じバッククォート）
```

---

### W-5. `agents/agent_e_verification.md` — 出力フォーマット追加

**現状の問題**: チェックリスト提案が自由記述で、golden_theory.jsonに自動反映できない。

Agent Eの出力フォーマットの「## 黄金理論チェックリスト更新提案」セクションの**後に**以下を追加:

```markdown
## 構造化データ（step2がパースする — このセクションのフォーマットを厳守すること）

```json
{
  "cycle": 1,
  "verification_results": [
    {
      "hypothesis_id": "H1",
      "status": "supported",
      "accuracy": 0.92,
      "detail": "（検証の詳細）",
      "contradicting_data": [],
      "modification": null
    },
    {
      "hypothesis_id": "H2",
      "status": "rejected",
      "accuracy": 0.45,
      "detail": "（棄却の詳細）",
      "contradicting_data": ["（矛盾データ1）"],
      "modification": null,
      "learning": "（この棄却から得た学び）"
    }
  ],
  "checklist_proposal": [
    {
      "condition": "（条件名）",
      "hit_fulfillment": {"count": 8, "total": 10, "rate": 0.8},
      "miss_fulfillment": {"count": 3, "total": 14, "rate": 0.21},
      "discriminative_power": "high",
      "status": "adopted",
      "linked_principle": "P1",
      "data_category": "analytics",
      "notes": ""
    }
  ],
  "principle_updates": [
    {
      "action": "add",
      "principle": {
        "statement": "（上位原則の記述）",
        "mechanism": "（メカニズム説明）"
      }
    }
  ],
  "unresolved_contradictions": [
    {
      "description": "（未解決の矛盾）",
      "related_hypotheses": ["H1"],
      "suggested_investigation": "（次サイクルでの調査方向）"
    }
  ],
  "exploratory_findings": [
    {
      "description": "（探索的発見）",
      "next_action": "（次サイクルへの提案）"
    }
  ]
}
```（←閉じバッククォート）
```

---

### W-6. `scripts/step3_build_model.py` — 機能分割

**現状の問題**: 1074行のモノリシックファイルに8つの異なる責務が詰め込まれている。

**分割後の構成**:

```
scripts/
├── common/
│   ├── __init__.py
│   ├── data_loader.py      ← W-7 で定義
│   └── metrics.py           ← W-8 で定義
├── step3_build_model.py     ← エントリーポイント（薄くする）
├── step3_filters.py         ← 3段階フィルタ分析（F1/F2/F3）
├── step3_patterns.py        ← パターン分析・グループ比較・ベンチマーク
├── step3_report.py          ← Markdownレポート生成
└── step3_history.py         ← バージョン管理・履歴保存
```

**step3_build_model.py（改修後）**: エントリーポイントとして全モジュールを呼び出す。**新規追加**: golden_theory.jsonの読み込みとモデルへの反映。

```python
# step3_build_model.py（改修後の骨格）

from common.data_loader import load_all_videos, load_human_scores, load_video_index
from common.metrics import compute_derived_metrics
from step3_filters import run_3stage_filter
from step3_patterns import analyze_patterns, compare_groups, benchmark
from step3_report import generate_report
from step3_history import save_history, update_index

def main():
    # 1. データ読み込み（共通モジュール）
    videos = load_all_videos()
    scores = load_human_scores()
    index = load_video_index()

    # 2. 指標計算（共通モジュール）
    metrics = compute_derived_metrics(videos, scores, index)

    # 3. 黄金理論の読み込み（★新規）
    golden = load_golden_theory()  # data/golden_theory.json

    # 4. 3段階フィルタ分析
    filter_results = run_3stage_filter(metrics)

    # 5. パターン分析
    patterns = analyze_patterns(metrics)
    groups = compare_groups(metrics)
    bench = benchmark(metrics)

    # 6. 黄金理論チェックリストの検証（★新規）
    #    golden_theory.json のチェックリスト条件を
    #    実データで再検証し、充足率を更新する
    validated_theory = validate_golden_theory(golden, metrics)

    # 7. モデル生成（golden_theoryを統合）
    model = build_model(filter_results, patterns, groups, validated_theory)

    # 8. レポート生成
    generate_report(model, metrics, validated_theory)

    # 9. 履歴保存
    save_history(model)
    update_index()
```

**新規関数 `validate_golden_theory()`**:
```python
def validate_golden_theory(golden: dict, metrics: list) -> dict:
    """
    golden_theory.json のチェックリスト条件を
    実データのmetricsで再検証する。
    - 各条件のHIT群充足率・MISS群充足率を再計算
    - discriminative_power を再判定
    - 条件が実データと矛盾すればフラグを立てる
    """
    pass
```

---

### W-7. `scripts/common/data_loader.py` — 新規作成

**現状の問題**: data_summarizer.py と step3_build_model.py が同一のデータ読み込みロジックを重複実装している。

```python
# common/data_loader.py

"""
全スクリプト共通のデータ読み込みモジュール。
data_summarizer.py、step2_analyze.py、step3_build_model.py が共有する。
"""

import json
from pathlib import Path
from scripts.config import VIDEOS_DIR, DATA_DIR, HUMAN_SCORES_FILE

def load_all_videos() -> list[dict]:
    """data/videos/*.json を全件読み込み、リストで返す"""
    pass

def load_video_index() -> dict:
    """data/video_index.json を読み込む"""
    pass

def load_human_scores() -> dict:
    """data/human_scores.json を読み込む"""
    pass

def load_golden_theory() -> dict:
    """data/golden_theory.json を読み込む。存在しなければ空の初期構造を返す"""
    pass

def save_golden_theory(data: dict):
    """data/golden_theory.json を書き込む"""
    pass

def load_insights() -> dict:
    """
    data/analysis_history/insights.md を読み込み、
    YAML frontmatter と 本文セクション を分離して返す
    """
    pass

def save_insights(frontmatter: dict, sections: dict):
    """insights.md を書き込む"""
    pass
```

---

### W-8. `scripts/common/metrics.py` — 新規作成

**現状の問題**: data_summarizer.py と step3_build_model.py で engagement_rate、gi_x_ca 等の計算が重複。

```python
# common/metrics.py

"""
全スクリプト共通の指標計算モジュール。
"""

from scripts.config import HIT_THRESHOLD

def compute_derived_metrics(video: dict, human_score: dict = None) -> dict:
    """
    1本の動画データから派生指標を計算する。
    data_summarizer.py と step3_build_model.py の両方がこれを呼ぶ。

    Returns:
        {
            "video_id": "...",
            "is_hit": bool,
            "engagement_rate": float,
            "avg_view_duration": float,
            "day1_day2_change": float,
            "gi_x_ca": float,
            # ... 台本指標、Day1トラフィック内訳 等
        }
    """
    pass

def classify_hit_miss(view_count: int) -> bool:
    """HIT_THRESHOLD に基づくHIT/MISS判定"""
    return view_count >= HIT_THRESHOLD

def classify_growth_pattern(daily_data: list) -> str:
    """日別推移から成長パターンを分類: immediate/sustained/delayed/decay"""
    pass
```

---

### W-9. `agents/coordinator.md` — 修正

#### 修正1: Agentパスの修正

**現状の問題**: coordinator.md内のAgentパスが実ファイルと不一致。

```markdown
<!-- 旧（不一致） -->
- Agent C: `.claude/agents/analyze-meta.md` のエイリアス経由
- Agent E: `.claude/agents/analyze-verify.md` のエイリアス経由

<!-- 新（実ファイルパスに修正） -->
- Agent C: `agents/agent_c_meta_analysis.md`
- Agent E: `agents/agent_e_verification.md`
```

#### 修正2: フィードバックループの明確化

Phase 2 の記述を以下に置き換え:

```markdown
## Phase 2: 仮説生成→検証ループ（最大5サイクル）

### サイクルの実行手順
1. `python scripts/step2_analyze.py` でデータ準備
2. Claude Code で Agent C を実行 → `workspace/new_hypotheses.md` 生成
3. Claude Code で Agent E を実行 → `workspace/verification_report.md` 生成
4. `python scripts/step2_analyze.py --integrate` で統合処理
   - Agent出力のJSONブロックをパース
   - insights.md を更新（採択/棄却/学びを追記）
   - golden_theory.json を更新（チェックリスト追加/棄却移動）
   - step3_build_model.py を実行（モデル再構築）
5. 矛盾チェック:
   - `unresolved_contradictions` が空 → 完了
   - 残存あり & サイクル < 5 → 手順1に戻る
   - 残存あり & サイクル = 5 → 強制終了。残存矛盾を `insights.md` に記録

### サイクル間の情報引き継ぎ
- Agent C は次サイクルで `insights.md` を読むことで、前サイクルの棄却仮説と学びを知る
- `insights.md` の「## 棄却仮説と学び」セクションに前サイクルの棄却理由が記録されている
- Agent C は棄却された仮説と同じ仮説を再生成してはならない（insights.mdで確認すること）
- `insights.md` の「## 探索的発見」セクションに、次サイクルへの手がかりが記録されている

### サイクルの終了条件
- **正常終了**: 全仮説が「支持」or「修正」で、未解決矛盾がゼロ
- **成果ありで終了**: 一部採択・一部棄却だが、新たな手がかりがない
- **上限終了**: 5サイクル到達。残存矛盾を記録して終了
```

---

### W-10. プロジェクト全体 — ファイル整理

現在使用されていないファイルの削除、.gitignoreの整備、データ不整合の修正を行う。

#### 10-a. 不要ファイルの削除

| 対象 | 理由 | アクション |
|------|------|-----------|
| `IMPLEMENTATION_PLAN.md` | Task 1-9は全て完了済み。今後の実装仕様は本ファイル（WORKFLOW_IMPROVEMENTS.md）とANALYSIS_FRAMEWORK_CHANGES.mdが担う。完了記録としての役割も`data/analysis_history/index.md`が代替する | **削除** |
| `workflow_diagram_v2.html` | 一時的な可視化用。仕様書2本（本ファイル + ANALYSIS_FRAMEWORK_CHANGES.md）にフローが記述されているため不要 | **削除** |
| `data/manual_exports/` | 空ディレクトリ。どのスクリプトからも参照されていない | **削除** |
| `data/pdca_reports/` | 空ディレクトリ。step4_pdca.pyはこのフォルダを使用していない | **削除** |
| `scripts/__pycache__/` | Python自動生成のバイトコード。.gitignoreに追加して削除 | **削除** |

> **注意**: `projects/`ディレクトリ（24アーティスト × 2 CSV）は**削除しない**。step1_fetch.pyの`--merge`でデータ統合済みだが、元データのアーカイブとして保持する。

#### 10-b. `.gitignore` の更新

現在の`.gitignore`（`client_secret.json`と`token.json`のみ）に以下を追加:

```gitignore
# 既存
client_secret.json
token.json

# 追加
__pycache__/
*.pyc
.DS_Store
```

#### 10-c. `data/video_index.json` の整理

**現状の問題**: video_index.jsonには35本が登録されているが、`data/videos/`に実データがあるのは24本。実データのない11本のエントリが残っている（短尺動画など、分析対象外として除外されたもの）。

**対応**: 実データのない11本のエントリを削除し、`total_count`を24に修正する。

削除対象のvideo_id:
- `9y8RHGuAIbc`, `8LsVTT2WzRM`, `IokXr014oZQ`, `ar-3-Jb6Iq4`, `hlES8bz2KWI`
- `Lrm81I5-GXc`, `dUeyTLjkgCw`, `H16hA5c_JQY`, `sfYXx-QoUBE`, `rEc1Yn5zWqI`, `ExR_HzX6iWs`

---

### W-11. `agents/agent_c_meta_analysis.md` — 入力戦略変更（2フェーズ読み込み）

**現状の問題**: Agent Cは毎サイクルで全24本のデータと台本を読み込む設計になっている。初回は全件読み込みが必要だが、2サイクル目以降は既にinsights.mdとgolden_theory.jsonに蓄積された知見があるため、全件再読み込みは非効率。また、仮説の方向性によって必要なデータの種類（analytics/script/meta）は異なるのに、一律で全データを読んでいる。

**改修方針**: 「何を読むか」自体をAgent Cの分析行為の一部とする。概要データから注目すべき動画とデータ種別を判断し、必要なものだけ深掘りする2フェーズ読み込みに変更する。

#### 変更1: 「入力ファイル」セクションの改修

現行の「## 入力ファイル（必ず全て読む）」を以下の2フェーズ構成に置換する。

現行の入力ファイル4件（data_summary.md, insights.md, model.json, index.md）は**Phase 1としてそのまま維持**。これにW-1で新設する `data/golden_theory.json` を追加する。

現行の「### 必要に応じて個別参照」セクション（videos/*.json, human_scores.json）を**Phase 2**に昇格させ、「必要に応じて」ではなく「⓪読み込み計画で選定したもののみ読む」に変更する:

```markdown
## 入力ファイル

### Phase 1: 概要読み込み（必ず全て読む）
1. `data/workspace/data_summary.md` — 全動画の指標サマリ（data_summarizer.py出力）
2. `data/analysis_history/insights.md` — 現在の確立されたインサイト集
3. `data/model.json` — 現在のモデル定義
4. `data/analysis_history/index.md` — 棄却済み仮説・未解決問題
5. `data/golden_theory.json` — 現在の黄金理論（原則+チェックリスト+棄却条件）★追加

### Phase 2: 選択的深掘り（⓪読み込み計画で選定したもののみ読む）
- `data/videos/{id}.json` — 注目動画のみ。全件読まない
- `data/scripts/{id}.json` — 台本データが仮説に関連する場合のみ
- `data/human_scores.json` — GIサブスコアの詳細が必要な場合のみ
```

> 「### data_summary.mdのセクション構成」テーブル、「### データの3分類を意識すること」はそのまま維持。

#### 変更2: 分析フローにステップ⓪を追加（5ステップ → 6ステップ）

現行の①〜⑤は変更なし。その**前に**ステップ⓪を追加する:

```markdown
**⓪ 読み込み計画（Phase 1完了後、①の前に実施）**
Phase 1の概要データを読んだ上で、以下を判断し「読み込み計画」として出力する:

1. **注目動画の選定**（最大8本）:
   - 黄金理論に反する動画（HITなのにチェックリスト未充足 / MISSなのに充足）
   - 前サイクルの探索的発見に関連する動画
   - 未解決の問いに関連する動画
   - 境界領域の動画（GI×CAが閾値付近でHIT/MISSが分かれている）
   ※ 初回サイクル（insights.mdが空 or cycle=0）の場合はこのステップをスキップし、
     全件をdata_summary.mdベースで分析する

2. **必要なデータ種別の選定**:
   - 仮説の方向性がアナリティクス寄り → videos/*.jsonのanalytics_overview, traffic_sources, daily_dataを読む
   - 仮説の方向性が台本寄り → scripts/*.json または videos/*.jsonのscript_analysisを読む
   - 仮説の方向性がメタデータ寄り → human_scores.jsonを読む
   - 複数の方向性がある場合は、最も有望な方向から優先

3. **読み込み計画の出力**（以下のフォーマットで明示する）:
   ### 読み込み計画
   - 注目動画: {video_id_1}（理由: ...）, {video_id_2}（理由: ...）, ...
   - 必要データ種別: analytics / script / meta
   - 読み込み理由: {なぜこれらの動画・データが必要か}
   - 読まない判断: {全件読み込みをしない理由 / 特定のデータ種別を読まない理由}
```

また、現行の**①**に以下の注記を追加:
```
- ①のHIT/MISS共通点抽出はdata_summary.mdの概要テーブルで全件カバーする
- ⓪で選定した注目動画のみ、videos/*.jsonで詳細を確認する
```

#### 変更3: 構造化データに `reading_plan` フィールドを追加

W-4で定義したAgent C出力のJSONブロックに `reading_plan` を追加する:

```json
{
  "cycle": 2,
  "reading_plan": {
    "focus_videos": [
      {
        "video_id": "xxx",
        "reason": "HITだがチェックリストC3未充足",
        "data_read": ["analytics", "script"]
      }
    ],
    "skipped_data": "台本データは今回の仮説方向（トラフィック構造）に無関係のため省略",
    "full_scan_used": false
  },
  "hit_miss_commonalities": { ... },
  "hypotheses": [ ... ],
  "lateral_thinking_log": { ... }
}
```

> **初回サイクルの扱い**: insights.mdが空（cycle=0）またはgolden_theory.jsonが初期状態の場合、⓪の選定はスキップし、`"full_scan_used": true` を設定する。2サイクル目以降から選択的読み込みが有効になる。

#### Agent Eとの対比

Agent Eは検証エージェントであり、**反例を1件でも見逃すと仮説を誤採択するリスクがある**ため、data_summary.mdの全件データで網羅的にスクリーニングを行う設計を維持する。ただし、Agent Eも詳細データ（videos/*.json）の読み込みは反例候補が見つかった動画に限定してよい。

---

### W-12. 分析結論レポートの自動生成 — `analysis_conclusion.md`

**現状の問題**: サイクル完了後、分析結果が `insights.md`・`golden_theory.json`・`model.json`・`analysis_report.md` の4ファイルに散在しており、「結局、伸びる動画の黄金理論は何か？」という最上位の問い（coordinator.md）に対する**統合的な結論ドキュメント**が存在しない。人間が4ファイルを横断的に読んで自分で結論を組み立てる必要がある。

**改修方針**: `step2_analyze.py --integrate` の最終ステップとして、全ソースを統合した結論レポートを自動生成する。このレポートは「ゴースト・デック」形式 — 専門用語を排除し、誰が読んでも分析の結論が理解できるドキュメントとして設計する。

#### 12-a. 出力ファイル

**パス**: `data/analysis_conclusion.md`（サイクル完了ごとに上書き更新）

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
{golden_theory.json の principles から、statusが"established"または"supported"のものを平易な文章で記述}

例:
- 「〇〇の条件を満たす動画は、YouTubeのアルゴリズムに推薦されやすい」
- 「視聴者の好奇心と、動画内容の一致度が高いほど伸びる」

### 制作前チェックリスト
{golden_theory.json の checklist から、statusが"adopted"のものを表形式で出力}

| # | チェック項目 | HITの中でクリアした割合 | MISSの中でクリアした割合 | 判別力 |
|---|------------|---------------------|----------------------|-------|
| {id} | {condition} | {hit_rate}% | {miss_rate}% | {power} |

### この理論の信頼度
- 全動画への的中率: {accuracy}%（{correct}/{total}本）
- 反例（理論が外した動画）: {exceptions}
- まだ解明できていないこと: {open_questions}件

---

## 2. 発見の要約

### 伸びた動画（HIT）に共通していたこと
{insights.md の採択済みインサイトから主要なものを箇条書き}

### 伸びなかった動画（MISS）に共通していたこと
{insights.md + model.jsonから導出}

### 試したが間違いだった仮説
{insights.md の棄却仮説から主要なものをピックアップ。「〇〇が原因かと思ったが、データを見ると△△だった」形式}

---

## 3. 統計サマリ

### 予測力の高い指標
{model.json の cause_metrics 相関テーブルから上位5件}

| 指標 | 再生数との相関 | 意味 |
|------|-------------|------|
| {metric} | r={value} | {plain_description} |

### モデルの精度推移
{analysis_history/index.md のバージョン履歴から、R²の推移を抽出}

| バージョン | 日付 | R² | 主な変更点 |
|-----------|------|-----|-----------|
| {ver} | {date} | {r2} | {change} |

---

## 4. 次のアクション

### 未解決の問い
{insights.md の「未解決の問い」セクションから}

### 次に検証すべきこと
{insights.md の「探索的発見」から}

### データ品質の課題
{既知の課題: AI評価の混在、サンプルサイズ等}

---

> このレポートは `python scripts/step2_analyze.py --integrate` の実行時に自動生成されます。
> 詳細データ: model.json / golden_theory.json / insights.md
```

#### 12-b. `step2_analyze.py` への変更

`integrate()` 関数の末尾（矛盾チェックの後、return の前）に以下を追加:

```python
# 8. 結論レポート生成
generate_conclusion_report()
```

**新規関数**:

```python
def generate_conclusion_report():
    """
    golden_theory.json + insights.md + model.json + index.md を統合し、
    data/analysis_conclusion.md を生成する。

    設計方針:
    - ゴースト・デック形式: 専門用語を使わず、誰でも読めるドキュメント
    - 構造: 結論（黄金理論）→ 発見の要約 → 統計サマリ → 次のアクション
    - golden_theory.json の principles/checklist を平易な日本語に変換
    - model.json の相関テーブルに「意味」列を付加（指標名→日本語説明）
    - insights.md の棄却仮説を「試したが間違いだった仮説」として再構成
    """
    pass
```

**指標名→日本語説明の変換テーブル**（レポート内で使用）:

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
```

#### 12-c. coordinator.md への変更

Phase 3 の手順に以下を追加:

```markdown
  9. 結論レポート生成（analysis_conclusion.md を更新）
```

また、サイクル終了条件の後に以下を追加:

```markdown
### サイクル完了後の成果物
サイクルが完了（正常終了・成果あり終了・上限終了のいずれか）すると、以下が更新される:
- `data/analysis_conclusion.md` — **分析の最終結論**（誰でも読める形式）
- `data/golden_theory.json` — 黄金理論の構造化データ
- `data/analysis_history/insights.md` — 採択/棄却の全履歴
- `data/model.json` — 統計モデル
```

---

### W-13. `data/analysis_history/index.md` — 役割変更（棄却仮説の一本化）

**現状の問題（A-1/B-1）**: index.mdとinsights.mdの両方に棄却仮説が記録されている。W-3でinsights.mdが構造化された後、index.mdの「棄却仮説テーブル」は冗長。Agent Cが両方を読むと同じ情報を二重に処理し、コンテキストを浪費する。

**対応**:
1. index.mdから「## 棄却仮説テーブル」セクションを削除
2. index.mdの役割を**バージョン履歴専用**に限定（モデルバージョン・R²推移・主な変更点のみ）
3. Agent Cの入力ファイルリスト（agent_c_meta_analysis.md）から、index.mdの説明を「バージョン履歴・未解決問題」に変更
4. 棄却仮説の参照はinsights.md一本に統一

**index.mdの新構成**:
```markdown
# 分析履歴

## バージョン履歴
| Ver | 日付 | R² | 主な変更点 |
|-----|------|-----|-----------|

## 未解決問題
（棄却仮説はinsights.mdを参照）
```

---

### W-14. `agents/agent_e_verification.md` — 入力ファイルにgolden_theory.jsonを追加

**現状の問題（A-2）**: Agent Eの入力ファイルにgolden_theory.jsonが含まれていない。現在の黄金理論（確立済みの原則・チェックリスト）を参照せずに仮説を検証しているため、既に確立された知見との整合性チェックができない。

**対応**: 入力ファイルリストに以下を追加:

```markdown
## 入力ファイル（必ず全て読む）
1. `data/workspace/new_hypotheses.md` — Agent Cの仮説レポート
2. `data/workspace/data_summary.md` — 全動画の指標サマリ
3. `data/videos/*.json` — 必要に応じて個別動画の詳細データ
4. `data/human_scores.json` — 人間評価スコア
5. `data/analysis_history/insights.md` — 現在のインサイト集
6. `data/golden_theory.json` — 現在の黄金理論（原則+チェックリスト）★追加
```

Agent Eは検証時に以下をチェックする:
- 新仮説が既存の確立済み原則（principles）と矛盾しないか
- 新チェックリスト提案が既存の採択済み条件（checklist）と重複しないか
- 棄却済み条件（rejected_conditions）と同じ方向の仮説が来ていないか

---

### W-15. `scripts/data_summarizer.py` — §6b AI評価セクションの削除

**現状の問題（A-3）**: §6b「AI評価との乖離（参考）」セクションが表示されている。AI評価は系統的過大評価（G3=5, G2=4-5に集中）であり判別力がないことが判明済み。Agent Cがこのセクションを見てAI評価を分析に使うリスクがある。

**対応**:
1. data_summarizer.pyから§6bセクション（「AI評価との乖離」テーブル生成部分）を削除
2. §6の注記「AI評価は系統的に過大評価する」はそのまま維持（警告として有用）
3. AI評価データ自体はvideos/*.json内に保持（将来の再較正用）。表示のみ削除

---

### W-16. `scripts/step4_pdca.py` + `scripts/config.py` — PDCA_DIR参照の修正

**現状の問題（A-4）**: step4_pdca.pyがconfig.pyのPDCA_DIR（`data/pdca_reports/`）を参照している。W-10でこのディレクトリを削除するため、W-10実行後にstep4がImportError or FileNotFoundErrorで壊れる。

**対応**:
1. config.pyの`PDCA_DIR`定義を`WORKSPACE_DIR`に統合（PDCAレポートはworkspace/に出力）
2. step4_pdca.pyの出力先を`data/workspace/pdca_{video_id}_{date}.md`に変更
3. step4_pdca.pyのdocstringを更新（出力先の変更を反映）
4. config.pyから`PDCA_DIR`行と`MANUAL_DIR`行を削除（両方とも参照先が削除される）

```python
# config.py から削除する行
MANUAL_DIR = os.path.join(DATA_DIR, "manual_exports")  # W-10で削除済み
PDCA_DIR = os.path.join(DATA_DIR, "pdca_reports")       # W-10で削除済み
```

---

### W-17. `agents/coordinator.md` — 手動ステップ残存とIMPLEMENTATION_PLAN参照の削除

**現状の問題（B-2/B-3）**: coordinator.mdのPhase 3に手動ステップが残存している（W-2で自動化済み）。また147行目付近でIMPLEMENTATION_PLAN.md（W-10で削除予定）を参照している。

**対応**:
1. Phase 3 の記述からW-2で自動化された手動ステップ（手動でinsights.md更新、手動でindex.md更新）を削除
2. `IMPLEMENTATION_PLAN.md` への参照をすべて削除
3. 方法論レビュー（Step 8）の「変更内容を`IMPLEMENTATION_PLAN.md`にも記録」を「変更内容を`insights.md`の備考に記録」に変更

---

### W-18. `scripts/step3_filters.py` — 3段階フィルター精度の注意喚起

**現状の問題（B-4）**: 3段階フィルター（F1: GI×CA閾値、F2: 台本構造、F3: 総合）の精度が66.7%で、ランダム（50%）とほぼ変わらない。Agent Cがこの数値を見て「フィルターが有効」と誤解するリスクがある。

**対応**:
1. analysis_report.md のフィルターセクションに以下の注意喚起を追加:

```markdown
> ⚠️ 3段階フィルターの精度は66.7%（24本中16本正解）であり、統計的に有意な判別力とは言えない。
> 黄金理論のチェックリスト（golden_theory.json）の方が信頼性が高い。
```

2. Agent Cの入力ファイル説明にmodel.jsonのフィルター精度に関する注記を追加:

```markdown
- model.json の3段階フィルター結果は参考値。精度が低い（66.7%）ため、
  黄金理論チェックリスト（golden_theory.json）を優先すること
```

---

### W-19. `scripts/step3_history.py` — スナップショット保持ポリシーの導入

**現状の問題（B-5）**: analysis_historyにv2.0〜v3.1（12バージョン）のスナップショットが蓄積されており、その多くはR²値が同一。サイクルを重ねるたびに無制限に増加する。

**対応**: step3_history.pyにスナップショットの保持ポリシーを追加:

```python
SNAPSHOT_POLICY = {
    "keep_latest": 5,           # 直近5バージョンは常に保持
    "keep_milestones": True,    # R²が0.05以上変化したバージョンはマイルストーンとして永久保持
    "auto_cleanup": True,       # save_history()実行時に自動でポリシーを適用
}
```

- save_history()の末尾でcleanup_old_snapshots()を呼び出す
- 削除対象のバージョンはindex.mdの履歴テーブルには残る（ディレクトリのみ削除）

---

### W-20. `data/analysis_report.md` — 読み手の明確化

**現状の問題（B-6）**: analysis_report.mdの読み手が不明確。W-12でanalysis_conclusion.md（人間向け）を新設したことで、analysis_report.mdの位置づけが曖昧になる。

**対応**: analysis_report.mdの冒頭に以下のヘッダーを追加:

```markdown
> **このファイルの読み手**: Agent C / Agent E / 開発者（デバッグ用）
> **一般向けの分析結論**: `data/analysis_conclusion.md` を参照してください
```

step3_report.pyのレポート生成関数にこのヘッダーを自動挿入するよう修正。

---

### W-21. `scripts/step2_analyze.py` — 方法論レビューの自動化（プロンプト改善）

**現状の問題**: coordinator.md の Step 8「方法論レビュー」では、Agent Eの「分析方法の評価」セクションに基づいてAgent C/Eの定義ファイル（プロンプト）を改善すると規定されている。しかし、step2_analyze.py の `integrate()` 関数にはこの処理が一切実装されていない。Agent Eが毎回 `verification_report.md` に改善提案を書いても、誰もそれを読まず、プロンプトは改善されない。

**改修方針**: `integrate()` 関数に方法論レビューのステップを追加する。Agent Eの評価セクションをパースし、改善提案を構造化して蓄積する。改善アクションの適用は、提案の種類に応じて「自動適用」と「手動確認用の出力」に分ける。

#### 21-a. Agent E出力の「分析方法の評価」セクションのパース

`verification_report.md` の末尾にある以下のセクションを抽出する:

```markdown
## 分析方法の評価
### Agent Cの仮説生成品質
- 結果指標を使った仮説の数: X/Y本
- データの正確性: ...
- 棄却済み仮説の再提案: ...
- 仮説の多様性: ...

### 分析プロセスの改善提案
- Agent C定義ファイルへの具体的な修正提案（あれば）
- Agent E自身の検証プロセスの改善点（あれば）
- コーディネーターのフロー改善点（あれば）
```

#### 21-b. Agent E出力のJSONブロックへの構造化データ追加

W-5で定義したAgent E出力のJSONブロックに `methodology_review` フィールドを追加:

```json
{
  "cycle": 1,
  "verification_results": [...],
  "checklist_proposal": [...],
  "methodology_review": {
    "agent_c_quality": {
      "result_metric_hypotheses": {"count": 0, "total": 5, "trend": "improving"},
      "data_accuracy_issues": [],
      "re_proposed_rejected": false,
      "diversity_assessment": "adequate"
    },
    "proposed_changes": [
      {
        "target": "agent_c",
        "type": "add_prohibition",
        "description": "結果指標XYZの使用を禁止リストに追加",
        "reason": "サイクル1-3で繰り返し結果指標を使用",
        "priority": "high"
      },
      {
        "target": "agent_e",
        "type": "add_guideline",
        "description": "相関分析時にサンプル外検証を追加",
        "reason": "過学習リスクの低減",
        "priority": "medium"
      }
    ],
    "self_assessment": {
      "missed_issues": [],
      "over_strict_judgments": [],
      "process_improvements": []
    }
  }
}
```

#### 21-c. `step2_analyze.py` への変更

`integrate()` 関数に Step 8 として以下を追加（結論レポート生成の前に挿入）:

```python
# 8. 方法論レビュー（プロンプト改善）
print("\n[統合] 方法論レビュー...")
review_result = apply_methodology_review(verification)
if review_result["changes_applied"]:
    print(f"  自動適用: {review_result['auto_applied']}件")
if review_result["manual_review_needed"]:
    print(f"  手動確認が必要: {review_result['manual_count']}件")
    print(f"  → data/workspace/prompt_modifications.md を確認してください")

# 9. 結論レポート生成（旧Step 8）
```

**新規関数**:

```python
def apply_methodology_review(verification: dict) -> dict:
    """
    Agent Eの方法論レビューに基づきプロンプト改善を実行する。

    自動適用される改善:
    - insights.md への品質メトリクスの記録（結果指標使用率の推移等）
    - 棄却済み仮説の再提案検出時の警告追記

    手動確認用に出力される改善:
    - Agent C/E定義ファイルへの具体的な修正提案
      → workspace/prompt_modifications.md に提案内容を出力
    - コーディネーターフローの変更提案

    Returns:
        {
            "changes_applied": bool,
            "auto_applied": int,
            "manual_review_needed": bool,
            "manual_count": int,
        }
    """
    pass
```

#### 21-d. `workspace/prompt_modifications.md` のフォーマット

手動確認が必要な改善提案を出力するファイル:

```markdown
# プロンプト改善提案 — サイクル {cycle}

> 生成日: {date}
> Agent Eの「分析方法の評価」に基づく自動生成

---

## Agent Cの仮説生成品質

| 指標 | 今回 | 前回 | 傾向 |
|------|------|------|------|
| 結果指標を使った仮説 | {count}/{total} | {prev} | {trend} |
| データ正確性の問題 | {issues} | - | - |
| 棄却済み仮説の再提案 | {re_proposed} | - | - |
| 仮説の多様性 | {diversity} | - | - |

---

## 改善提案（手動確認が必要）

### 提案1: {description}
- **対象ファイル**: `agents/{target}.md`
- **変更種別**: {type}
- **理由**: {reason}
- **優先度**: {priority}
- **適用方法**: 以下をファイルに追記/修正
```
{具体的な変更内容}
```

### 提案2: ...

---

## 自動適用済みの変更
- insights.md に品質メトリクス（サイクル{cycle}）を記録済み

---

> このファイルの提案を確認し、必要なものを手動で適用してください。
> 適用後、このファイルは次サイクルの --integrate で上書きされます。
```

#### 21-e. `insights.md` への品質メトリクス記録

insights.md の末尾に「## 方法論レビュー履歴」セクションを新設し、サイクルごとの品質メトリクスを自動追記する:

```markdown
## 方法論レビュー履歴

### サイクル1
- 結果指標使用率: 2/5本（40%）
- データ正確性: 問題なし
- 仮説多様性: 3方向（analytics/script/meta）

### サイクル2
- 結果指標使用率: 0/4本（0%） ← 改善
- データ正確性: 1件の誤認あり
- 仮説多様性: 2方向（analytics/script）
```

#### 21-f. `agents/agent_e_verification.md` への変更

現在の「分析方法の評価」セクション（必須）のフォーマットに、構造化データとの対応を明記:

```markdown
## 分析方法の評価（必須 — step2がパースする）
以下の内容を記載すること。JSON構造化データの `methodology_review` にも同内容を含めること。
```

---

### W-22. youtube-analyze → youtube-long パイプライン接続

#### 背景と目的

youtube-analyze（分析パイプライン）の成果物（golden_theory.json, model.json, insights.md, analysis_conclusion.md）は、youtube-long（制作パイプライン）に手動転記でしかフィードバックされていない。

現状の接続ポイント:
- model.jsonの回帰式・閾値 → selection_report.mdの判定基準（**手動転記**）
- QUANTITATIVE_SCORING_PLAN.md → scoring_criteria.md + selection_report.mdの定量基準（**実施済みだが一回限り**）
- golden_theory.jsonのチェックリスト → 台本レビュー基準（**未接続**）

**目的**: 分析サイクル完了時に、制作パイプラインへの更新提案を自動生成し、半自動で適用可能にする。

#### 設計方針

1. **自動生成 + 手動適用**: youtube-long側のファイルを直接編集するのはリスクが高い（regulationの整合性が崩れる）。代わりに「更新提案ドキュメント」を自動生成し、人間がレビュー後に適用する
2. **3つの接続レイヤー**: 選定段階・台本設計段階・レビュー段階のそれぞれにフィードバック
3. **トリガー**: `step2_analyze.py --integrate` 完了時に自動生成（結論レポートと同タイミング）

#### 22-a. 出力ファイル: `data/workspace/production_feedback.md`

`--integrate` 完了時に自動生成される。以下の3セクションで構成:

```markdown
# 制作パイプラインへのフィードバック
> 生成日時: YYYY-MM-DD | 分析サイクル: N回完了

---

## 1. 選定基準の更新提案（→ youtube-long/prompts/1. selection_report.md）

### 1-1. GI×CA判定基準
- 現在の閾値: GI×CA ≥ 16
- model.jsonの最新閾値精度: XX%（N本評価）
- 推奨閾値変更: {変更なし / 閾値をXに変更 / 理由}

### 1-2. 回帰式の更新
- 現在: 推定再生数 ≒ -306,908 + 38,970 × GIスコア
- model.jsonの最新回帰式: {更新があれば記載}

### 1-3. selection_report.mdに転記すべき数値
| 項目 | 現在の記載値 | model.json最新値 | 差異 |
|------|------------|-----------------|------|
| GI相関 r値 | +0.798 | {最新値} | {差分} |
| 閾値16精度 | 100%（12/12） | {最新値} | {差分} |
| CA=3平均再生数 | 47万 | {最新値} | {差分} |

→ 差異がある項目のみ、selection_report.mdの該当行を手動更新すること

---

## 2. 台本設計への示唆（→ youtube-long/prompts/ 各ステップ）

### 2-1. 黄金理論チェックリストから導出された制作ガイドライン
（golden_theory.jsonの adopted チェックリスト条件を、制作者が実行可能な形に変換）

| # | 黄金理論の条件 | 判別力 | 制作時のアクション | 対応する制作ステップ |
|---|--------------|--------|------------------|-------------------|
{golden_theory.json の checklist から自動生成}

### 2-2. 棄却された仮説（やっても意味がないこと）
（insights.mdの棄却仮説から、制作者が避けるべきことを抽出）

| # | 棄却された考え | 理由 | 対応するステップ |
|---|--------------|------|----------------|
{insights.md の rejected セクションから自動生成}

---

## 3. レビュー基準の強化提案（→ youtube-long/prompts/9_review_common.md）

### 3-1. 分析で発見したHIT/MISS差分に基づく新規チェック項目
（Agent C/Eが発見した共通点のうち、台本で制御可能なもの）

| # | チェック項目案 | 根拠データ | regulation追加先 |
|---|-------------|----------|----------------|
{hit_miss_commonalities + adopted insights から自動生成}

### 3-2. regulation_id_registry.md への追加候補
（分析結果から導出された新ルール案。feedback_regulation_mapping.mdのフォーマットに準拠）

---

## 適用チェックリスト

- [ ] セクション1の数値差異を selection_report.md に転記
- [ ] セクション2のガイドラインを該当プロンプトに反映
- [ ] セクション3のチェック項目を review_common.md に追加
- [ ] 変更後、次回のアーティスト選定で新基準を使用
```

#### 22-b. `step2_analyze.py` への追加: `generate_production_feedback()`

integrate() の結論レポート生成（Step 8）の直後に実行。

```python
def generate_production_feedback():
    """
    golden_theory.json + model.json + insights.md を読み込み、
    youtube-long 制作パイプラインへの更新提案を自動生成する。

    出力: data/workspace/production_feedback.md
    """
```

**処理の流れ**:
1. model.json から GI×CA閾値精度・回帰式・相関値を取得
2. `youtube-long/prompts/1. selection_report.md` を読み取り、現在記載されている数値を抽出（正規表現）
3. 差異がある項目をテーブルに出力（セクション1）
4. golden_theory.json の checklist（status=adopted）を読み取り、制作アクションに変換（セクション2-1）
5. insights.md の棄却仮説セクションをパースし、「やっても意味がないこと」を抽出（セクション2-2）
6. insights.md の採択インサイト + hit_miss_commonalities（GAP-6で記録予定）から、台本で制御可能な項目を抽出（セクション3）

**チェックリスト条件 → 制作アクション変換ルール**:

| data_category | 制作ステップ | 変換例 |
|---------------|------------|--------|
| meta（GI/CA関連） | Step 1: selection | 「GI×CA≥Xのアーティストを選ぶ」 |
| script（台本構造） | Step 7: 三幕構成設計 | 「感情の底を3回以上設計する」 |
| script（フック/導入） | Step 4: フック設計 | 「フック回答位置をX%以内にする」 |
| script（MV/メディア） | Step 7a: イベント配置 | 「MV挿入をX本以上にする」 |
| analytics（CTR関連） | Step 1: タイトル設計 | 「好奇心TOP1のキーワードをタイトルに含める」 |

#### 22-c. youtube-long 側の参照パス

youtube-long のエージェントが production_feedback.md を**直接参照する必要はない**。
代わりに、人間が以下の流れで適用する:

```
1. step2 --integrate 完了
    ↓
2. workspace/production_feedback.md が自動生成される
    ↓
3. 人間がレビューし、適用すべき項目を判断
    ↓
4-a. 選定基準の数値更新 → selection_report.md を手動編集
4-b. 台本ガイドライン → 該当prompts/*.mdに手動追記
4-c. レビュー基準 → regulation に反映（feedback_regulation_mapping.md のフローを使用）
```

**将来的な自動化の余地**:
- 4-a（数値転記）は自動化可能（selection_report.mdの特定行を正規表現で更新）
- 4-b, 4-c は regulation の整合性チェックが必要なため、自動化は慎重に行う
- youtube-long側の feedback_regulation_mapping.md に「分析結果フィードバック」カテゴリを追加すれば、既存のフィードバック恒久化エージェントで処理可能になる

#### 22-d. config.py への追加

```python
# youtube-long パイプラインのパス（production_feedback生成時に参照）
YOUTUBE_LONG_DIR = os.path.join(os.path.dirname(BASE_DIR), "youtube-long")
SELECTION_REPORT_TEMPLATE = os.path.join(YOUTUBE_LONG_DIR, "prompts", "1. selection_report.md")
```

**注意**: youtube-long が存在しない環境でもエラーにならないよう、パス存在チェックを入れる。存在しない場合はセクション1の差異比較をスキップし、セクション2-3のみ生成する。

#### 22-e. 既存の接続ポイントとの関係

| 既存の仕組み | W-22での扱い |
|-------------|-------------|
| README.mdのフロー図「model.json → selection.mdに反映」 | production_feedback.md セクション1で差異を可視化。手動転記を支援 |
| QUANTITATIVE_SCORING_PLAN.md | scoring_criteria.md の基準自体は変更しない。GI×CAの閾値・精度のみ更新対象 |
| ANALYSIS_FRAMEWORK_CHANGES.md セクション4「youtube-longへの反映」 | W-22で正式に設計。スコープ外→スコープ内に移行 |
| youtube-long/feedback_regulation_mapping.md | セクション3のregulation追加候補は、このマッピングのフォーマットに準拠して出力する |

---

### W-23. `data/analysis_fundamentals.json` — 不変基盤ファイル

#### 23-a. 問題

分析に不可欠な6つの基本要素（目的・HIT/MISS定義・全動画共通点分析の義務・指標体系・データ範囲・分析方法論）が、coordinator.md・agent_c_meta_analysis.md・config.py等に散在している。これらはmarkdownやPython設定ファイルであり、誰でも変更でき、変更しても他ファイルとの整合性チェックが行われない。

**具体的リスク**:
- config.pyの `HIT_THRESHOLD` を変更しても、coordinator.mdの「15万回再生」は自動更新されない（過去に10万→15万で実際に発生）
- Agent Cが水平思考ステップを飛ばしても検知する仕組みがない
- 分析目的の記述が coordinator.md / agent_c_meta_analysis.md / ANALYSIS_FRAMEWORK_CHANGES.md に重複しており、一方だけ編集するリスクがある

#### 23-b. 解決策: `data/analysis_fundamentals.json`

**分析の不変基盤を単一のJSONファイルに集約し、全スクリプト・全エージェントが起動時にこのファイルを参照する。**

このファイルは分析パイプラインの「憲法」であり、変更するには明示的な意思決定が必要。通常の分析サイクルでは絶対に変更されない。

**スキーマ**:

```json
{
  "schema_version": "1.0",
  "last_reviewed": "YYYY-MM-DD",

  "purpose": {
    "statement": "伸びた動画の共通点と伸びていない動画の共通点を明らかにし、「伸びる動画の黄金理論」を構築すること",
    "golden_theory_definition": "上位原則（なぜ伸びるのか）＋実用チェックリスト（制作前に確認できる条件）の二層構造",
    "central_questions": [
      "伸びた動画全てに共通することは何か？",
      "伸びていない動画全てに共通することは何か？"
    ],
    "constraint": "問題の定義は常にcentral_questionsから派生して設定すること"
  },

  "hit_miss_definition": {
    "hit_threshold": 150000,
    "hit_label": "15万回再生以上",
    "miss_label": "15万回再生未満",
    "unit": "views"
  },

  "commonality_analysis": {
    "requirement": "HIT群の全動画に共通する特徴とMISS群の全動画に共通する特徴を必ず抽出すること",
    "scope": "全動画を対象。サンプリングや代表例のみの分析は不可",
    "categories": ["analytics", "scripts", "meta"],
    "output_requirement": "hit_miss_commonalities JSON構造として必ず出力すること"
  },

  "metrics": {
    "analytics": {
      "description": "YouTube Analyticsから取得できるデータ",
      "groups": {
        "traffic_sources": ["ブラウジング機能", "YouTube検索", "関連動画", "外部", "チャンネルページ", "通知", "その他"],
        "engagement": ["総再生時間", "平均視聴時間", "平均視聴率(%)", "視聴維持率曲線"],
        "ctr": ["インプレッション数", "インプレッションCTR(%)"],
        "audience": ["登録者/非登録者比率", "新規視聴者率"],
        "temporal": ["公開後24時間再生数", "公開後7日間再生数", "日次推移"],
        "interaction": ["高評価率", "コメント数", "共有数"],
        "reach": ["ユニーク視聴者数", "リピート率"],
        "advanced": ["End Screen CTR", "カード CTR"]
      }
    },
    "scripts": {
      "description": "台本から抽出できるデータ",
      "groups": {
        "structure": ["三幕構造比率", "セクション数", "総文字数"],
        "hook": ["フック種別", "フック回答位置(%)", "冒頭30秒の構成"],
        "emotion": ["感情曲線パターン", "感情の底の回数", "エスカレーション有無"],
        "media": ["MV挿入数", "非MV映像数", "総メディア数"],
        "topic": ["メインテーマ", "サブテーマ数", "統一テーマの有無"],
        "storytelling": ["ナラティブ技法", "伏線回収の有無", "視聴者への問いかけ回数"],
        "pacing": ["セクション平均長", "最長セクション比率"],
        "cta": ["CTA位置", "CTA種別"]
      }
    },
    "meta": {
      "description": "動画のメタデータ・人間評価",
      "groups": {
        "basic": ["タイトル文字数", "サムネイルタイプ", "公開曜日・時間"],
        "human_scores": ["GI(ゴシップ露出度)", "CA(好奇心アピール度)", "G1-G6サブスコア"],
        "artist": ["アーティスト知名度", "直近ゴシップ有無", "楽曲知名度"]
      }
    }
  },

  "data_ranges": {
    "primary": {
      "window": "24hours",
      "label": "公開後24時間",
      "priority": "最重要",
      "reason": "ブラウジング推薦の初動を決定する"
    },
    "secondary": {
      "window": "7days",
      "label": "公開後7日間",
      "priority": "重要",
      "reason": "ほとんどの動画はここまでで伸びるかどうかが決まる"
    },
    "late_bloomer": {
      "label": "7日後に伸び始めた動画",
      "priority": "特別対応",
      "reason": "突然視聴回数が増えたポイントまで分析範囲を拡張する必要がある",
      "rule": "7日間を過ぎてから伸び始めた動画に関しては、突然視聴回数が増えたところまで見る"
    }
  },

  "methodology": {
    "pillars": [
      {
        "name": "水平思考（Lateral Thinking）",
        "description": "あらゆる前提を疑い、見えていない変数を探す",
        "steps": [
          "前提列挙: 「なぜそれが共通点なのか」「なぜそれが伸びる原因なのか」の前提を明示的に書き出す",
          "前提反転: 各前提を「もし逆だったら？」で検証する",
          "代替説生成: 前提反転の結果から、従来の説明では捕捉できない新しい仮説を生成する"
        ],
        "integration": "Agent Cの分析フローのステップ②③に組み込む"
      },
      {
        "name": "第一原理主義（First Principles Thinking）",
        "description": "YouTubeアルゴリズムの仕組み・視聴者心理・チャンネル固有特性から演繹的に考える",
        "reference": "agents/youtube_fundamentals.md",
        "integration": "Agent C/E両方が分析・検証時に必ず参照する前提知識"
      },
      {
        "name": "仮説駆動アプローチ（Hypothesis-Driven）",
        "description": "McKinsey方式の「答えから始める」手法。まず結論の仮説を立て、それを検証するためにデータを集め、仮説を修正・確定する",
        "process": {
          "step1_issue_definition": {
            "name": "問題の定義（Issue Statement）",
            "description": "解くべき問いを一文で明確にする。具体的で検証可能な問いにする",
            "constraint": "問いは常にcentral_questionsから派生させること。無関係な問いは立てない",
            "agent": "Agent C"
          },
          "step2_issue_decomposition": {
            "name": "イシューの分解",
            "description": "問いをサブイシューへMECEに分解する",
            "example": "「なぜHIT群は伸びるのか」→「アルゴリズム推薦の差か、コンテンツの質の差か」→「推薦なら初動CTRか維持率か」",
            "agent": "Agent C"
          },
          "step3_initial_hypothesis": {
            "name": "初期仮説の設定（Day 1 Answer）",
            "description": "分解した各枝に対して「おそらくこうだろう」という仮説を立てる。限られた情報（過去サイクルの知見、前提知識、データ概要）をもとに設定",
            "rules": [
              "仮説は必ず複数（2〜3パターン）立てること（アンカリング防止）",
              "各仮説が棄却された場合の代替シナリオをあらかじめ用意しておく"
            ],
            "agent": "Agent C"
          },
          "step4_work_plan": {
            "name": "検証計画の設計（Work Plan）",
            "description": "各仮説に対して「何が証明されれば仮説が正しいと言えるか」「どのデータでそれを確認するか」を設計する",
            "constraint": "仮説の検証に関係ないデータは集めない。これが分析のスピードを担保する",
            "agent": "Agent C が計画、Agent E が検証実行"
          },
          "step5_verification_and_evolution": {
            "name": "検証と仮説の進化",
            "description": "データ検証により仮説は3状態のいずれかに移行する",
            "states": {
              "supported": "データが仮説と整合する",
              "modified": "方向性は合っているが詳細が異なる → 修正案を提示",
              "rejected": "データが仮説と矛盾する → 新たな仮説を立て直す。棄却は失敗ではなく学習"
            },
            "agent": "Agent E（レッドチーム）"
          }
        },
        "hypothesis_pyramid": {
          "description": "最終的な仮説は階層構造を取る。この構造がそのまま黄金理論の骨格になる",
          "structure": "最上位仮説（黄金理論の上位原則）→ 支持仮説（根拠となるサブ仮説）→ 根拠（データ分析結果）"
        },
        "bias_prevention": {
          "confirmation_bias": {
            "description": "仮説を支持するデータばかりを集め、矛盾するデータを無視してしまう傾向",
            "countermeasure": "Agent Eをレッドチームとして配置。意図的に反証データを探す"
          },
          "anchoring_effect": {
            "description": "最初の仮説に引きずられて柔軟な修正ができなくなる現象",
            "countermeasure": "初期仮説を必ず2〜3パターン立て、各仮説を独立に評価する"
          }
        }
      }
    ],
    "agent_c_flow": {
      "description": "Agent Cの分析フロー。水平思考と仮説駆動を統合した5ステップ。この順序で必ず実行すること",
      "steps": [
        {
          "id": 1,
          "name": "HIT/MISS共通点抽出（必須・最優先）",
          "maps_to": "仮説駆動Step1（問題の定義）",
          "required_output": "hit_miss_commonalities"
        },
        {
          "id": 2,
          "name": "前提列挙（水平思考ステップ1）",
          "maps_to": "仮説駆動Step2（イシューの分解）",
          "required_output": "premises_listed"
        },
        {
          "id": 3,
          "name": "前提反転・水平思考（水平思考ステップ2-3）",
          "maps_to": "仮説駆動Step2（イシューの分解） + 代替説生成",
          "required_output": "premises_inverted"
        },
        {
          "id": 4,
          "name": "因果仮説生成（Day 1 Answer）",
          "maps_to": "仮説駆動Step3（初期仮説の設定）+ Step4（検証計画の設計）",
          "required_output": "hypotheses（2〜3パターン + 各検証条件）"
        },
        {
          "id": 5,
          "name": "新仮説提示（仮説ピラミッド形式）",
          "maps_to": "仮説ピラミッド構造で出力 → Agent Eへ渡す",
          "required_output": "hypothesis_pyramid"
        }
      ]
    },
    "agent_e_role": {
      "description": "レッドチーム。仮説駆動Step5（検証と仮説の進化）を担当",
      "responsibilities": [
        "Agent Cの仮説を支持するデータだけでなく、矛盾するデータを意図的に探す（確証バイアス防止）",
        "Agent Cが複数仮説を提示した場合、各仮説を独立に評価する（アンカリング防止）",
        "検証結果を supported / modified / rejected の3状態で報告する",
        "Agent Cが方法論ステップを飛ばしていないかをレビューする（W-21方法論レビュー）"
      ]
    },
    "hypothesis_quality": {
      "description": "良い仮説の3条件。すべての仮説はこの基準を満たすこと",
      "conditions": [
        {"name": "具体的", "check": "検証可能な粒度まで落とし込まれているか。「どのデータで確認するか」が明確か"},
        {"name": "反証可能", "check": "データで覆せる可能性があるか。「何が起きたら棄却か」が定義されているか"},
        {"name": "行動接続", "check": "正しければ黄金理論のどこに入るかが明確か。「チェックリストのどの条件になるか」が言えるか"}
      ]
    },
    "enforcement": {
      "description": "方法論の実施を強制する仕組み",
      "agent_c_output_validation": {
        "description": "step2_analyze.pyがAgent C出力のJSONを検証し、方法論ステップの実施証跡を確認する",
        "required_fields": {
          "methodology_steps_completed": "実施した方法論ステップのIDリスト（[1,2,3,4,5]が必須）",
          "hit_miss_commonalities": "ステップ1の出力（HIT/MISS共通点）",
          "premises": "ステップ2-3の出力（列挙した前提と反転結果）",
          "hypotheses": "ステップ4の出力（2〜3パターンの仮説 + 各検証条件）",
          "hypothesis_pyramid": "ステップ5の出力（階層構造の仮説提示）"
        },
        "validation_rules": [
          "methodology_steps_completed に [1,2,3,4,5] が全て含まれていなければ WARNING を出力",
          "hypotheses が2件未満の場合 WARNING（アンカリングリスク）",
          "各 hypothesis に verification_criteria が未定義の場合 WARNING"
        ]
      },
      "agent_e_methodology_review": {
        "description": "W-21の方法論レビューで、Agent Eが「Agent Cは方法論ステップを踏んだか」を評価",
        "check_items": [
          "共通点抽出を全動画で実施したか（サンプリングしていないか）",
          "前提を明示的に列挙したか（暗黙の前提で進めていないか）",
          "前提反転を実施したか（確証バイアスに陥っていないか）",
          "仮説を複数立てたか（アンカリングしていないか）",
          "検証条件を各仮説に付記したか（反証可能性があるか）"
        ]
      }
    }
  }
}
```

#### 23-c. 整合性チェック機構

**1. Pythonスクリプト側: `validate_fundamentals()` を `scripts/common/data_loader.py` に追加**

```python
def load_fundamentals():
    """analysis_fundamentals.json を読み込み、返す。存在しない場合はエラー終了。"""
    path = os.path.join(DATA_DIR, "analysis_fundamentals.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "FATAL: data/analysis_fundamentals.json が見つかりません。"
            "分析の不変基盤ファイルが必要です。"
        )
    with open(path) as f:
        return json.load(f)

def validate_fundamentals():
    """
    analysis_fundamentals.json と config.py の整合性を検証する。
    不一致があれば即座にエラー終了（サイレントな不整合を防止）。

    チェック項目:
    1. hit_threshold が config.HIT_THRESHOLD と一致するか
    2. data_ranges.primary.window が config.PRIMARY_ANALYSIS_WINDOW と一致するか
    3. data_ranges.secondary.window が config.SECONDARY_ANALYSIS_WINDOW と一致するか
    4. metrics.analytics/scripts/meta のキーが config.DATA_CATEGORIES と一致するか
    """
    fundamentals = load_fundamentals()
    errors = []

    # HIT閾値チェック
    if fundamentals["hit_miss_definition"]["hit_threshold"] != config.HIT_THRESHOLD:
        errors.append(
            f"HIT_THRESHOLD不一致: "
            f"fundamentals={fundamentals['hit_miss_definition']['hit_threshold']}, "
            f"config={config.HIT_THRESHOLD}"
        )

    # データ範囲チェック
    if fundamentals["data_ranges"]["primary"]["window"] == "24hours":
        if config.PRIMARY_ANALYSIS_WINDOW != 1:
            errors.append("PRIMARY_ANALYSIS_WINDOW不一致")
    if fundamentals["data_ranges"]["secondary"]["window"] == "7days":
        if config.SECONDARY_ANALYSIS_WINDOW != 7:
            errors.append("SECONDARY_ANALYSIS_WINDOW不一致")

    # カテゴリチェック
    fund_categories = set(fundamentals["metrics"].keys())
    config_categories = set(config.DATA_CATEGORIES.keys())
    if fund_categories != config_categories:
        errors.append(f"DATA_CATEGORIES不一致: {fund_categories} vs {config_categories}")

    if errors:
        raise ValueError(
            "FATAL: analysis_fundamentals.json と config.py の整合性エラー:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    return fundamentals
```

**2. Agent C出力の方法論バリデーション: `validate_methodology_compliance()` を `step2_analyze.py` に追加**

```python
def validate_methodology_compliance(agent_c_output: dict) -> list[str]:
    """
    Agent C出力のJSONを検証し、方法論ステップの実施証跡を確認する。
    analysis_fundamentals.json の methodology.enforcement.agent_c_output_validation に基づく。

    Returns: WARNINGメッセージのリスト（空なら全ステップ実施済み）
    """
    warnings = []

    # ステップ完了チェック
    steps = agent_c_output.get("methodology_steps_completed", [])
    missing = [s for s in [1, 2, 3, 4, 5] if s not in steps]
    if missing:
        warnings.append(
            f"方法論ステップ未実施: {missing} "
            f"（1=共通点抽出, 2=前提列挙, 3=前提反転, 4=仮説生成, 5=仮説提示）"
        )

    # HIT/MISS共通点チェック
    if not agent_c_output.get("hit_miss_commonalities"):
        warnings.append("hit_miss_commonalities が未出力（ステップ1: 共通点抽出が未実施）")

    # 前提列挙チェック
    if not agent_c_output.get("premises"):
        warnings.append("premises が未出力（ステップ2: 前提列挙が未実施）")

    # 仮説数チェック（アンカリング防止）
    hypotheses = agent_c_output.get("hypotheses", [])
    if len(hypotheses) < 2:
        warnings.append(
            f"仮説が{len(hypotheses)}件のみ（アンカリングリスク: 2〜3パターン必須）"
        )

    # 検証条件チェック
    for i, h in enumerate(hypotheses):
        if not h.get("verification_criteria"):
            warnings.append(
                f"仮説{i+1}に verification_criteria が未定義（反証可能性が不明）"
            )

    # 仮説ピラミッドチェック
    if not agent_c_output.get("hypothesis_pyramid"):
        warnings.append("hypothesis_pyramid が未出力（ステップ5: 階層構造の仮説提示が未実施）")

    if warnings:
        print("=" * 60)
        print("⚠ 方法論コンプライアンス WARNING:")
        for w in warnings:
            print(f"  - {w}")
        print("=" * 60)

    return warnings
```

この関数は `integrate()` の Agent C 出力パース直後に呼び出す。WARNING があっても処理は続行するが、insights.md の当該サイクルに WARNING を記録する。Agent E の W-21 方法論レビューでもこの WARNING 一覧を参照できる。

**3. 各スクリプトの起動時に呼び出し**

```python
# step2_analyze.py, step3_build_model.py, data_summarizer.py, step4_pdca.py の冒頭
from common.data_loader import validate_fundamentals
fundamentals = validate_fundamentals()  # 不整合なら即座に停止
```

**4. エージェント側: coordinator.md に参照指示を追加**

coordinator.md の Phase 1（データ読み込み）に以下を追記:

```markdown
## 必読ファイル（分析開始前に必ず読むこと）

1. **`data/analysis_fundamentals.json`** — 分析の不変基盤。目的・定義・指標・方法論の全てがここに定義されている。
   この内容に反する分析は無効とする。

2. `data/golden_theory.json` — 現在の黄金理論（変動する知見の蓄積）
3. `data/analysis_history/insights.md` — 過去の仮説・検証結果の履歴
```

agent_c_meta_analysis.md と agent_e_verification.md の入力ファイルリストにも `data/analysis_fundamentals.json` を追加し、以下の注記を付ける:

```markdown
**注意**: analysis_fundamentals.json に定義された中心的な問い・分析方法論・指標体系に従うこと。
このファイルの内容を変更・無視・省略することは禁止。
```

#### 23-d. 変更管理ルール

**不変ファイル群（Immutable Files）**:

以下のファイルは分析パイプラインの「憲法」であり、通常の分析サイクルでは**一切変更しない**:

| ファイル | 役割 | 変更リスク |
|---------|------|-----------|
| `data/analysis_fundamentals.json` | 分析の方法と基準（目的・定義・指標・方法論） | Pythonスクリプトが書き込み可能→書き込みを禁止 |
| `agents/agent_c_meta_analysis.md` | Agent Cの分析フロー・出力フォーマット定義 | W-21の方法論レビューで「プロンプト改善提案」が生成される→自動編集を禁止 |
| `agents/agent_e_verification.md` | Agent Eの検証方法・レッドチーム役割定義 | 同上 |
| `agents/coordinator.md` | ワークフロー全体の制御フロー | Agent出力を受けて自動変更される可能性→禁止 |
| `agents/youtube_fundamentals.md` | 第一原理の前提知識（アルゴリズム・心理・チャンネル固有） | データ更新で自動書き換えリスク→禁止 |

**保護の仕組み**:

1. **Pythonスクリプトからの保護**: step2, step3, step4 のいずれもこれらのファイルへの書き込みを行わない。コード上でopen(path, "w")を呼ぶ対象から除外する
2. **Agent出力からの保護**: Agent C/E もこれらのファイルの変更を提案しない。W-21の方法論レビューで生成される改善提案は `workspace/prompt_modifications.md` に出力し、人間がレビューして手動適用する
3. **変更が必要な場合のプロセス**:
   - fundamentals.json: `schema_version` をインクリメント + `last_reviewed` を更新
   - Agent定義ファイル: 変更理由と変更内容を ANALYSIS_FRAMEWORK_CHANGES.md に記録
   - 全変更は人間が明示的に判断して実施する
   - 変更後、`validate_fundamentals()` が通ることを確認する

**不変ファイル vs 可変ファイルの対比**:

| 分類 | ファイル | 変更者 |
|------|---------|--------|
| 不変（ルールブック） | analysis_fundamentals.json, agent_c/e/coordinator.md, youtube_fundamentals.md | 人間のみ（明示的判断） |
| 可変（スコアボード） | golden_theory.json, insights.md, model.json, analysis_conclusion.md | Pythonスクリプト（自動） |
| 可変（提案書） | workspace/prompt_modifications.md, workspace/production_feedback.md | Pythonスクリプト（自動生成、人間がレビュー） |

#### 23-e. 既存ファイルとの関係

| 既存ファイル | 現在の役割 | W-23後の変更 |
|---|---|---|
| `config.py` | HIT閾値・パス・パラメータ | HIT閾値の「正」は fundamentals.json に移動。config.py の値は fundamentals から読み込むか、validate_fundamentals() で一致を強制 |
| `coordinator.md` | 分析目的・指標・方法論を記述 | **不変ファイルに指定**。fundamentals.json を「必読ファイル」として参照。自動編集禁止 |
| `agent_c_meta_analysis.md` | 分析フロー・方法論を記述 | **不変ファイルに指定**。方法論の定義元を fundamentals.json に変更。フローの具体的手順はここに残す。自動編集禁止 |
| `agent_e_verification.md` | 検証方法を記述 | **不変ファイルに指定**。入力ファイルに fundamentals.json を追加。自動編集禁止 |
| `youtube_fundamentals.md` | 第一原理の前提知識 | **不変ファイルに指定**。チャンネル固有データの更新も人間が手動で実施 |
| `ANALYSIS_FRAMEWORK_CHANGES.md` | 0.1-0.3 で目的・定義・方法論を記述 | fundamentals.json がマスター。本文書は「変更履歴」としての役割を維持 |

---

## 3. 実行順序

```
--- ANALYSIS_FRAMEWORK_CHANGES.md の変更が完了した後 ---

1. scripts/common/__init__.py       ← 新規作成（空ファイル）
2. scripts/common/data_loader.py    ← 新規作成（共通データ読み込み）
3. scripts/common/metrics.py        ← 新規作成（共通指標計算）
4. data/golden_theory.json          ← 新規作成（初期スキーマで空データ）
5. data/analysis_history/insights.md ← フォーマット変更（YAML frontmatter化）
6. scripts/step3_filters.py         ← step3から分割
7. scripts/step3_patterns.py        ← step3から分割
8. scripts/step3_report.py          ← step3から分割
9. scripts/step3_history.py         ← step3から分割
10. scripts/step3_build_model.py    ← 薄いエントリーポイントに改修 + golden_theory読み込み追加
11. scripts/data_summarizer.py      ← common/data_loader, common/metrics を使うように改修
12. scripts/step2_analyze.py        ← 半自動オーケストレーターに改修
13. agents/agent_c_meta_analysis.md ← 出力フォーマットにJSONブロック規約を追加 + 2フェーズ読み込みに変更
14. agents/agent_e_verification.md  ← 出力フォーマットにJSONブロック規約を追加
15. agents/coordinator.md           ← パス修正 + ループ制御の明確化

--- ファイル整理（W-10: 他の変更の前でも後でも可） ---
16. IMPLEMENTATION_PLAN.md を削除
17. workflow_diagram_v2.html を削除
18. data/manual_exports/ を削除
19. data/pdca_reports/ を削除
20. scripts/__pycache__/ を削除
21. .gitignore を更新（__pycache__/, *.pyc, .DS_Store を追加）
22. data/video_index.json を整理（実データのない11本を削除、total_count→24）

--- W-12: 結論レポート機能追加 ---
23. scripts/step2_analyze.py に generate_conclusion_report() を追加
24. agents/coordinator.md の Phase 3 に結論レポート手順を追加

--- W-13〜W-20: 監査対応 ---
25. data/analysis_history/index.md から棄却仮説テーブルを削除（W-13）
26. agents/agent_e_verification.md の入力ファイルに golden_theory.json を追加（W-14）
27. scripts/data_summarizer.py から §6b セクションを削除（W-15）
28. scripts/config.py から PDCA_DIR, MANUAL_DIR を削除（W-16）
29. scripts/step4_pdca.py の出力先を workspace/ に変更（W-16）
30. agents/coordinator.md から手動ステップ残存・IMPLEMENTATION_PLAN参照を削除（W-17）
31. scripts/step3_report.py にフィルター精度の注意喚起を追加（W-18）
32. agents/agent_c_meta_analysis.md にフィルター精度の注記を追加（W-18）
33. scripts/step3_history.py にスナップショット保持ポリシーを追加（W-19）
34. scripts/step3_report.py に analysis_report.md の読み手ヘッダーを追加（W-20）

--- W-21: 方法論レビュー自動化 ---
35. agents/agent_e_verification.md の構造化データに methodology_review を追加（W-21）
36. scripts/step2_analyze.py に apply_methodology_review() を追加（W-21）

--- W-22: youtube-long パイプライン接続 ---
37. scripts/config.py に YOUTUBE_LONG_DIR, SELECTION_REPORT_TEMPLATE を追加（W-22）
38. scripts/step2_analyze.py に generate_production_feedback() を追加（W-22）

--- W-23: 不変基盤ファイル（他の全変更より先に実施することを推奨） ---
39. data/analysis_fundamentals.json           ← 新規作成（6要素を集約）
40. scripts/common/data_loader.py             ← load_fundamentals() + validate_fundamentals() を追加
41. scripts/step2_analyze.py                  ← 冒頭に validate_fundamentals() 呼び出しを追加
42. scripts/step3_build_model.py              ← 冒頭に validate_fundamentals() 呼び出しを追加
43. scripts/data_summarizer.py                ← 冒頭に validate_fundamentals() 呼び出しを追加
44. scripts/step4_pdca.py                     ← 冒頭に validate_fundamentals() 呼び出しを追加
45. agents/coordinator.md                     ← 必読ファイルに analysis_fundamentals.json を追加
46. agents/agent_c_meta_analysis.md           ← 入力ファイルに analysis_fundamentals.json を追加 + 参照義務注記
47. agents/agent_e_verification.md            ← 入力ファイルに analysis_fundamentals.json を追加 + 参照義務注記

--- 統合テスト ---
48. python scripts/step3_build_model.py        ← 分割後の動作確認（fundamentals整合性チェック含む）
49. python scripts/step2_analyze.py             ← データ準備の動作確認（fundamentals整合性チェック含む）
50. Agent C/E を1サイクル手動実行               ← 出力フォーマット + fundamentals参照の確認
51. python scripts/step2_analyze.py --integrate ← 統合処理 + 方法論レビュー + 結論レポート + production_feedback生成の確認
52. python scripts/step4_pdca.py TEST_ID --skip-fetch ← PDCA出力先の確認
```

---

## 4. 問題対応マッピング

| # | 元の問題 | 対応する変更 | 解決方法 |
|---|---------|------------|---------|
| 1 | Agent出力→モデルの断絶 | W-1, W-2, W-6 | golden_theory.jsonを介してAgent知見をモデルに反映 |
| 2 | 黄金理論のデータ構造不在 | W-1 | golden_theory.jsonの新設（二層構造スキーマ） |
| 3 | step2→step3の断絶 | W-2 | step2の`--integrate`でAgent出力パース→step3実行を自動化 |
| 4 | フィードバックループ手動依存 | W-3, W-9 | insights.mdの構造化 + coordinator.mdでループ制御を明確化 |
| 5 | チェックリスト提案が消える | W-1, W-2, W-5 | Agent E出力のJSONブロック→step2がパース→golden_theory.jsonに書き込み |
| 6 | coordinator.mdのパス不一致 | W-9 | 実ファイルパスに修正 |
| 7 | データ読み込みの重複 | W-7 | common/data_loader.pyに集約 |
| 8 | step3が巨大すぎる | W-6, W-8 | 6モジュールに機能分割 |
| 9 | insights.mdスキーマ未定義 | W-3 | YAML frontmatter + 構造化セクション規約を定義 |
| 10 | 不要ファイル・データ不整合 | W-10 | 完了済みドキュメント削除、空ディレクトリ削除、video_index.json整理、.gitignore整備 |
| 11 | Agent Cの非効率な全件読み込み | W-11 | 2フェーズ読み込み（概要で地図把握→注目動画のみ深掘り）+ 読み込み計画の明示化 |
| 12 | 分析結論の統合ドキュメント不在 | W-12 | サイクル完了時にanalysis_conclusion.mdを自動生成（ゴースト・デック形式） |
| 13 | index.mdとinsights.mdで棄却仮説が重複 | W-13 | index.mdをバージョン履歴専用に縮小。棄却仮説はinsights.mdに一本化 |
| 14 | Agent Eがgolden_theory.jsonを参照していない | W-14 | 入力ファイルにgolden_theory.jsonを追加。既存理論との整合性チェックを実施 |
| 15 | §6b AI評価セクションが誤誘導リスク | W-15 | 判別力のないAI評価テーブル（§6b）をdata_summaryから削除 |
| 16 | step4_pdca.pyがW-10削除対象のPDCA_DIRを参照 | W-16 | 出力先をworkspace/に変更。config.pyからPDCA_DIR/MANUAL_DIRを削除 |
| 17 | coordinator.mdに手動ステップ残存・削除予定ファイル参照 | W-17 | Phase 3の手動ステップ削除 + IMPLEMENTATION_PLAN参照を削除 |
| 18 | 3段階フィルター精度66.7%（ほぼランダム） | W-18 | レポートとAgent C入力に注意喚起を追加。golden_theory.jsonを優先する旨を明記 |
| 19 | analysis_historyスナップショットの無制限蓄積 | W-19 | 保持ポリシー導入（直近5件+マイルストーン保持、自動クリーンアップ） |
| 20 | analysis_report.mdの読み手が不明確 | W-20 | 読み手をAgent C/E/開発者に限定するヘッダーを追加。結論レポートとの棲み分けを明記 |
| 21 | Agent Eの方法論レビュー提案が放置される | W-21 | 「分析方法の評価」をパースし品質メトリクスを自動記録。プロンプト改善提案をworkspace/に出力 |
| 22 | 分析結果が制作パイプライン（youtube-long）にフィードバックされない | W-22 | --integrate完了時にproduction_feedback.mdを自動生成。選定基準・台本ガイドライン・レビュー基準の更新提案 |
| 23 | 分析の不変基盤（目的・定義・指標・方法論）が散在し、無検証で変更可能 | W-23 | analysis_fundamentals.jsonに集約。全スクリプト起動時にvalidate_fundamentals()で整合性チェック。エージェントは必読ファイルとして参照義務 |

---

## 5. 実装バグ・ギャップ一覧（2エージェント完全性検証で発見）

> Agent C + Agent E の2エージェントでワークフローが完全に機能するかを検証した結果、以下のバグ・ギャップが発見された。
> **結論: アーキテクチャとしては2エージェントで完結する。追加エージェント不要。ただし以下のPythonコード修正が必要。**

### BUG-1: 「条件付き採択」ステータスのサイレント消失（重大度: 高）

**問題**: Agent Eの判定基準は3段階（採択 / 条件付き採択 / 棄却）だが、`step2_analyze.py` の `update_insights()` は `status == "supported"` と `status == "rejected"` のみを処理する。

```python
# step2_analyze.py line 157-158（現状）
adopted = [r for r in results if r.get("status") == "supported"]
rejected = [r for r in results if r.get("status") == "rejected"]
```

Agent Eが `"status": "conditional"` または `"status": "modified"` を返した場合、insights.mdにもgolden_theory.jsonにも反映されず、データが消失する。

**修正方針**:
- `"conditional"` を `adopted` と同様に処理し、信頼度「中」でinsights.mdに追記
- 修正提案（`modification` フィールド）も合わせて記録する
- Agent Eの出力JSON仕様に `"conditional"` を正式に定義する

### BUG-2: principle_updatesの「modify」「remove」アクション未対応（重大度: 中）

**問題**: `update_golden_theory()` は `action == "add"` のみ処理する。

```python
# step2_analyze.py line 258-259（現状）
for pu in verification.get("principle_updates", []):
    if pu.get("action") == "add":
```

Agent Eが「この原則は反証された」（remove）や「この原則の条件を修正すべき」（modify）と判断しても、golden_theory.jsonに反映されない。

**修正方針**:
- `"modify"`: 既存principleのstatement/mechanism/statusを更新
- `"remove"`: statusを `"rejected"` に変更（物理削除はしない）
- `"demote"`: statusを `"hypothesis"` に格下げ

### BUG-3: validate_golden_theory()がスタブのまま（重大度: 中）

**問題**: `step3_build_model.py` の `validate_golden_theory()` は `pass` のみで、チェックリスト条件を実データで一切検証していない。

```python
# step3_build_model.py line 225-233（現状）
def validate_golden_theory(golden, records):
    hits = [r for r in records if r["is_hit"]]
    misses = [r for r in records if not r["is_hit"]]
    for item in golden.get("checklist", []):
        pass  # ← 何もしていない
    return golden
```

新データが追加されても、チェックリストの充足率（hit_fulfillment / miss_fulfillment）が更新されない。

**修正方針**:
- 各checklist条件をrecordsに適用し、HIT群/MISS群の充足率を再計算
- 充足率が大幅に変化した場合はWARNINGを出力
- 結果をgolden_theory.jsonに書き戻す

### GAP-4: W-21 方法論レビューが未実装（重大度: 中）

**問題**: coordinator.md Step 8で定義、W-21で設計済みだが、step2_analyze.pyにコード未反映。

**対応**: W-21の実装時に解消。

### GAP-5: サイクル番号の自動管理がない（重大度: 低）

**問題**: Agent C/E出力JSONの `cycle` フィールドはAgent自身が手動設定する。step2_analyze.pyは現在のサイクル番号を管理・インクリメントする仕組みがなく、Agentが誤ったcycle番号を出力した場合、insights.mdのID（INS-001-H1等）が重複する可能性がある。

**修正方針**:
- insights.mdのfrontmatterの `total_cycles` を正として、integrate()時に `cycle = frontmatter["total_cycles"] + 1` で自動付番
- Agent出力のcycle値は参考値として扱い、実際の採番はstep2が行う

### GAP-6: hit_miss_commonalities（Agent C出力）がstep2で未使用（重大度: 低）

**問題**: Agent Cの構造化JSONに `hit_miss_commonalities` フィールド（HIT群/MISS群共通点の分析結果）が定義されているが、step2の `update_insights()` はこれを処理しない。Agent Cの共通点分析結果がinsights.mdに自動反映されない。

**修正方針**:
- insights.mdに「## HIT/MISS共通点分析」セクションを追加
- hit_common / miss_common / hit_only の各発見をサイクルごとに記録
- 共通点分析はAgent Eの検証を経て仮説→チェックリストになるため**致命的ではない**が、分析の透明性のために記録が望ましい

---

### 修正の実行順序（ステップ44〜49）

```
--- BUG修正（優先度高→低）---
44. step2_analyze.py: update_insights()に "conditional" ステータス処理を追加（BUG-1）
45. step2_analyze.py: update_golden_theory()に "modify"/"remove" アクション処理を追加（BUG-2）
46. step3_build_model.py: validate_golden_theory()を実装（BUG-3）
47. step2_analyze.py: integrate()でサイクル番号を自動付番（GAP-5）
48. step2_analyze.py: hit_miss_commonalitiesをinsights.mdに記録（GAP-6）

--- テスト ---
49. Agent C/Eの出力例JSONで統合処理をドライラン（全ステータスの処理確認）
```

### 問題対応マッピング（追加分）

| # | 元の問題 | 対応する変更 | 解決方法 |
|---|---------|------------|---------|
| 22 | 条件付き採択仮説がinsights.mdに記録されない | BUG-1 | "conditional"ステータスを処理し、信頼度「中」で記録 |
| 23 | 確立済み原則の修正・棄却がgolden_theoryに反映されない | BUG-2 | principle_updatesの"modify"/"remove"アクションを処理 |
| 24 | チェックリスト充足率が新データで更新されない | BUG-3 | validate_golden_theory()で実データ再検証を実装 |
| 25 | サイクル番号がAgent依存でID重複リスク | GAP-5 | insights.mdのfrontmatterで一元管理 |
| 26 | HIT/MISS共通点分析結果が記録されない | GAP-6 | insights.mdに共通点分析セクションを追加 |
