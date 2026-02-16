"""
Step 2: LLM分析コーディネーター（半自動オーケストレーター）

Phase 1: データ準備（自動） -> Agent実行指示を表示
Phase 2: Agent C/E 実行（手動 -- Claude Codeで実行）
Phase 3: Agent出力の統合（自動 -- --integrate で実行）
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import WORKSPACE_DIR, ANALYSIS_HISTORY_DIR, INSIGHTS_FILE, HISTORY_INDEX, DATA_DIR, MODEL_FILE
from common.data_loader import (
    load_golden_theory, save_golden_theory,
    load_insights, save_insights,
    validate_fundamentals,
)


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
    "engagement_rate": "エンゲージメント率",
    "avg_view_duration": "平均視聴時間（秒）",
    "browsing_ctr": "ブラウジングCTR（クリック率）",
    "related_ctr": "関連動画CTR",
    "day1_browse_views": "Day1のブラウジング視聴数",
    "day1_related_views": "Day1の関連動画視聴数",
}


def run_data_summarizer(diff_video_id=None):
    """data_summarizer.py を実行"""
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "data_summarizer.py")]
    if diff_video_id:
        cmd.extend(["--diff", diff_video_id])
    print("\n[Phase 1] データ要約を生成中...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"エラー: {result.stderr}")
        return False
    return True


def print_agent_instructions(mode="full", diff_video_id=None):
    """Agent C/E の実行手順を表示"""
    print(f"\n{'='*60}")
    print("Phase 2: Agent C/E を Claude Code で実行してください")
    print(f"{'='*60}")

    if mode == "diff":
        print(f"\nモード: 差分分析（動画: {diff_video_id}）")
    else:
        print(f"\nモード: フル分析")

    print(f"""
【1】Agent C（メタ分析）を実行:
  → agents/agent_c_meta_analysis.md の仕様に従い実行
  → 出力: data/workspace/new_hypotheses.md

【2】Agent E（検証）を実行:
  → agents/agent_e_verification.md の仕様に従い実行
  → 出力: data/workspace/verification_report.md

【3】統合処理を実行:
  python scripts/step2_analyze.py --integrate
""")


def check_agent_outputs():
    """Agent出力ファイルの存在チェック"""
    hyp_path = os.path.join(WORKSPACE_DIR, "new_hypotheses.md")
    ver_path = os.path.join(WORKSPACE_DIR, "verification_report.md")

    missing = []
    if not os.path.exists(hyp_path):
        missing.append("new_hypotheses.md")
    if not os.path.exists(ver_path):
        missing.append("verification_report.md")

    if missing:
        print(f"WARNING: Agent出力が見つかりません: {', '.join(missing)}")
        print("Agent C/E を先に実行してください。")
        return False
    return True


def extract_json_block(filepath):
    """Markdownファイルから「## 構造化データ」セクション内のJSONブロックを抽出"""
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 「## 構造化データ」セクションを探す
    pattern = r'## 構造化データ.*?```json\s*\n(.*?)```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"WARNING: JSONパースエラー ({filepath}): {e}")
            return None

    # フォールバック: 任意の```jsonブロックを探す（最後のもの）
    json_blocks = re.findall(r'```json\s*\n(.*?)```', content, re.DOTALL)
    if json_blocks:
        try:
            return json.loads(json_blocks[-1])
        except json.JSONDecodeError:
            pass

    return None


def parse_agent_c_output(filepath):
    """new_hypotheses.md からJSONブロックを抽出"""
    data = extract_json_block(filepath)
    if data is None:
        print(f"WARNING: Agent C出力のJSONブロックが見つかりません: {filepath}")
        return {}
    return data


def parse_agent_e_output(filepath):
    """verification_report.md からJSONブロックを抽出"""
    data = extract_json_block(filepath)
    if data is None:
        print(f"WARNING: Agent E出力のJSONブロックが見つかりません: {filepath}")
        return {}
    return data


def validate_methodology_compliance(agent_c_output):
    """
    Agent C出力のJSONを検証し、方法論ステップの実施証跡を確認する (W-23)。
    analysis_fundamentals.json の methodology.enforcement に基づく。

    Returns: WARNINGメッセージのリスト（空なら全ステップ実施済み）
    """
    warnings = []

    # HIT/MISS共通点チェック
    if not agent_c_output.get("hit_miss_commonalities"):
        warnings.append("hit_miss_commonalities が未出力（ステップ1: 共通点抽出が未実施）")

    # 前提列挙チェック（lateral_thinking_log内）
    ltl = agent_c_output.get("lateral_thinking_log", {})
    if not ltl.get("premises_listed"):
        warnings.append("lateral_thinking_log.premises_listed が未出力（ステップ2: 前提列挙が未実施）")

    # 仮説数チェック（アンカリング防止）
    hypotheses = agent_c_output.get("hypotheses", [])
    if len(hypotheses) < 2:
        warnings.append(
            f"仮説が{len(hypotheses)}件のみ（アンカリングリスク: 2〜3パターン必須）"
        )

    # 検証条件チェック
    for i, h in enumerate(hypotheses):
        if not h.get("verification_condition"):
            warnings.append(
                f"仮説{i+1}({h.get('id', '?')})に verification_condition が未定義（反証可能性が不明）"
            )

    if warnings:
        print("=" * 60)
        print("WARNING: 方法論コンプライアンス")
        for w in warnings:
            print(f"  - {w}")
        print("=" * 60)

    return warnings


def update_insights(hypotheses, verification):
    """insights.md を更新"""
    frontmatter, body = load_insights()

    # サイクル番号: frontmatterのtotal_cyclesを正として自動インクリメント (GAP-5)
    cycle = frontmatter.get("total_cycles", 0) + 1

    # 重複チェック: 同じ仮説内容が既にinsights.mdに存在する場合はスキップ
    # Agent出力の仮説statementの先頭40文字で照合（同一Agent出力の再実行を検出）
    results = verification.get("verification_results", [])
    hyp_map_pre = {}
    for h in hypotheses.get("hypotheses", []):
        hyp_map_pre[h["id"]] = h
    duplicate_found = False
    for r in results:
        hid = r.get("hypothesis_id", "?")
        h = hyp_map_pre.get(hid, {})
        stmt = h.get("statement", "")[:40]
        if stmt and stmt in body:
            duplicate_found = True
            break
    if duplicate_found:
        print(f"  WARNING: Agent出力の仮説が既にinsights.mdに存在します。重複追加をスキップします。")
        return

    # 採択された仮説を追加 (BUG-1: conditionally_supported も処理)
    results = verification.get("verification_results", [])
    adopted = [r for r in results if r.get("status") in ("supported", "conditionally_supported", "conditional")]
    rejected = [r for r in results if r.get("status") == "rejected"]

    # 仮説IDと内容のマッピング
    hyp_map = {}
    for h in hypotheses.get("hypotheses", []):
        hyp_map[h["id"]] = h

    # 採択セクションに追加
    adopted_section = ""
    for r in adopted:
        hid = r.get("hypothesis_id", "?")
        h = hyp_map.get(hid, {})
        ins_id = f"INS-{cycle:03d}-{hid}"
        adopted_section += f"\n### {ins_id}: {h.get('statement', r.get('detail', ''))}\n"
        adopted_section += f"- **サイクル**: {cycle}\n"
        status_label = "conditionally_adopted" if r.get("status") in ("conditionally_supported", "conditional") else "adopted"
        adopted_section += f"- **ステータス**: {status_label}\n"
        adopted_section += f"- **精度**: {r.get('accuracy', 'N/A')}\n"
        adopted_section += f"- **根拠**: {r.get('detail', '')}\n"
        if r.get("modification"):
            adopted_section += f"- **修正提案**: {r['modification']}\n"

    # 棄却セクションに追加
    rejected_section = ""
    for r in rejected:
        hid = r.get("hypothesis_id", "?")
        h = hyp_map.get(hid, {})
        rej_id = f"REJ-{cycle:03d}-{hid}"
        rejected_section += f"\n### {rej_id}: {h.get('statement', '')}\n"
        rejected_section += f"- **サイクル**: {cycle}\n"
        rejected_section += f"- **棄却理由**: {r.get('detail', '')}\n"
        rejected_section += f"- **学び**: {r.get('learning', '')}\n"

    # 未解決の問い
    unresolved_section = ""
    for u in verification.get("unresolved_contradictions", []):
        unresolved_section += f"\n### Q-{cycle:03d}: {u.get('description', '')}\n"
        unresolved_section += f"- **発見サイクル**: {cycle}\n"
        unresolved_section += f"- **関連仮説**: {', '.join(u.get('related_hypotheses', []))}\n"
        unresolved_section += f"- **調査方向**: {u.get('suggested_investigation', '')}\n"

    # 探索的発見
    exploratory_section = ""
    for e in verification.get("exploratory_findings", []):
        exploratory_section += f"\n### EXP-{cycle:03d}: {e.get('description', '')}\n"
        exploratory_section += f"- **サイクル**: {cycle}\n"
        exploratory_section += f"- **次のアクション**: {e.get('next_action', '')}\n"

    # bodyの各セクションに追記
    if "## 採択済みインサイト" in body:
        body = body.replace(
            "## 棄却仮説と学び",
            adopted_section + "\n## 棄却仮説と学び"
        )
    if "## 棄却仮説と学び" in body:
        body = body.replace(
            "## 未解決の問い",
            rejected_section + "\n## 未解決の問い"
        )
    if "## 未解決の問い" in body:
        body = body.replace(
            "## 探索的発見",
            unresolved_section + "\n## 探索的発見"
        )
    if "## 探索的発見" in body:
        body += exploratory_section

    # HIT/MISS共通点分析の記録 (GAP-6)
    commonalities = hypotheses.get("hit_miss_commonalities", {})
    if commonalities:
        comm_section = ""
        for cat in ["hit_common", "miss_common", "hit_only"]:
            items = commonalities.get(cat, [])
            if items:
                label = {"hit_common": "HIT群共通", "miss_common": "MISS群共通", "hit_only": "HIT群のみ"}[cat]
                for item in items:
                    comm_section += f"\n- **{label}**: {item.get('feature', '')} ({item.get('detail', '')})"
        if comm_section:
            marker = "## 探索的発見"
            if marker in body:
                body = body.replace(
                    marker,
                    f"## HIT/MISS共通点分析（サイクル{cycle}）\n{comm_section}\n\n{marker}"
                )

    # frontmatter更新
    frontmatter["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    frontmatter["total_cycles"] = cycle
    frontmatter["adopted_count"] = frontmatter.get("adopted_count", 0) + len(adopted)
    frontmatter["rejected_count"] = frontmatter.get("rejected_count", 0) + len(rejected)
    frontmatter["open_questions"] = len(verification.get("unresolved_contradictions", []))

    save_insights(frontmatter, body)
    print(f"  insights.md 更新: 採択 {len(adopted)}件, 棄却 {len(rejected)}件")


def update_golden_theory(verification):
    """golden_theory.json を更新"""
    golden = load_golden_theory()
    cycle = verification.get("cycle", 0)

    # チェックリスト提案を追加
    # 最大IDを算出（checklist + rejected_conditions の両方を考慮）
    all_ids = [c.get("id", "C0") for c in golden.get("checklist", [])]
    all_ids += [c.get("id", "C0") for c in golden.get("rejected_conditions", [])]
    max_id = max((int(cid[1:]) for cid in all_ids if cid.startswith("C") and cid[1:].isdigit()), default=0)

    for proposal in verification.get("checklist_proposal", []):
        # 既存の条件と重複チェック
        raw_cond = proposal.get("condition", "")
        # IDプレフィックス除去 + 括弧内の説明を除去して核心部分で比較
        normalized_cond = re.sub(r'^C\d+:\s*', '', raw_cond)
        core_cond = re.sub(r'[（(].+?[）)]', '', normalized_cond).strip()
        existing_cores = []
        for c in golden.get("checklist", []):
            ec = re.sub(r'^C\d+:\s*', '', c["condition"])
            existing_cores.append(re.sub(r'[（(].+?[）)]', '', ec).strip())
        for c in golden.get("rejected_conditions", []):
            ec = re.sub(r'^C\d+:\s*', '', c.get("condition", ""))
            existing_cores.append(re.sub(r'[（(].+?[）)]', '', ec).strip())
        if core_cond not in existing_cores:
            max_id += 1
            item = {
                "id": f"C{max_id}",
                "condition": proposal["condition"],
                "hit_fulfillment": proposal.get("hit_fulfillment", {}),
                "miss_fulfillment": proposal.get("miss_fulfillment", {}),
                "discriminative_power": proposal.get("discriminative_power", "unknown"),
                "status": proposal.get("status", "proposed"),
                "established_cycle": cycle,
                "linked_principle": proposal.get("linked_principle"),
                "data_category": proposal.get("data_category"),
                "notes": proposal.get("notes", ""),
            }
            golden["checklist"].append(item)

    # 原則の更新 (BUG-2: modify/remove も処理)
    for pu in verification.get("principle_updates", []):
        action = pu.get("action")
        if action == "add":
            p = pu.get("principle", {})
            item = {
                "id": f"P{len(golden['principles']) + 1}",
                "statement": p.get("statement", ""),
                "mechanism": p.get("mechanism", ""),
                "status": "hypothesis",
                "established_cycle": cycle,
                "supporting_evidence": [],
                "contradicting_evidence": [],
            }
            golden["principles"].append(item)
        elif action == "modify":
            pid = pu.get("principle", {}).get("id")
            for p in golden["principles"]:
                if p["id"] == pid:
                    new_p = pu.get("principle", {})
                    if "statement" in new_p:
                        p["statement"] = new_p["statement"]
                    if "mechanism" in new_p:
                        p["mechanism"] = new_p["mechanism"]
                    if "status" in new_p:
                        p["status"] = new_p["status"]
                    break
        elif action == "remove":
            pid = pu.get("principle", {}).get("id")
            for p in golden["principles"]:
                if p["id"] == pid:
                    p["status"] = "rejected"
                    break

    golden["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    golden["last_cycle"] = cycle

    save_golden_theory(golden)
    print(f"  golden_theory.json 更新: チェックリスト {len(golden['checklist'])}件, 原則 {len(golden['principles'])}件")


def run_step3():
    """step3_build_model.py を実行"""
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "step3_build_model.py")]
    print("\n[統合] モデル再構築中...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"エラー: {result.stderr}")
        return False
    return True


def integrate(auto=False):
    """Phase 3: Agent出力の統合処理"""
    print(f"\n{'='*60}")
    print("Phase 3: Agent出力の統合処理")
    print(f"{'='*60}")

    # 0. 不変基盤の整合性チェック (W-23)
    print("\n[統合] 不変基盤の整合性チェック...")
    validate_fundamentals()
    print("  OK: analysis_fundamentals.json と config.py は整合しています")

    # 1. Agent出力チェック
    if not check_agent_outputs():
        return False

    # 2. Agent C出力をパース
    hyp_path = os.path.join(WORKSPACE_DIR, "new_hypotheses.md")
    hypotheses = parse_agent_c_output(hyp_path)

    # 2.5 方法論コンプライアンスチェック (W-23)
    if hypotheses:
        methodology_warnings = validate_methodology_compliance(hypotheses)
        if methodology_warnings:
            print(f"  方法論WARNING: {len(methodology_warnings)}件")

    # 3. Agent E出力をパース
    ver_path = os.path.join(WORKSPACE_DIR, "verification_report.md")
    verification = parse_agent_e_output(ver_path)

    if not hypotheses and not verification:
        print("WARNING: Agent出力にJSONブロックがありません。手動で統合してください。")
        return False

    # 4. insights.md 更新
    print("\n[統合] insights.md 更新中...")
    update_insights(hypotheses, verification)

    # 5. golden_theory.json 更新
    print("[統合] golden_theory.json 更新中...")
    update_golden_theory(verification)

    # 6. step3 実行
    run_step3()

    # 7. 残存矛盾チェック
    unresolved = verification.get("unresolved_contradictions", [])
    if unresolved:
        print(f"\nWARNING: 未解決の矛盾が {len(unresolved)}件 あります:")
        for u in unresolved:
            print(f"  - {u.get('description', '不明')}")
        print("次サイクルを実行してください。")
    else:
        print("\nOK: 未解決の矛盾はありません。分析サイクル完了。")

    # 8. 方法論レビュー (W-21)
    review = verification.get("methodology_review")
    if review:
        print("\n[統合] 方法論レビュー...")
        cycle_num = verification.get("cycle", 0)
        result = apply_methodology_review(review, cycle_num)
        if result["auto_applied"]:
            print(f"  自動適用: {result['auto_applied']}件")
        if result["manual_count"]:
            print(f"  手動確認が必要: {result['manual_count']}件")
            print(f"  → data/workspace/prompt_modifications.md を確認してください")

    # 9. 結論レポート生成
    print("\n[統合] 結論レポート生成中...")
    generate_conclusion_report()
    print("  analysis_conclusion.md 生成完了")

    return True


def apply_methodology_review(review, cycle):
    """
    Agent Eの方法論レビューに基づきプロンプト改善を実行する (W-21)。

    自動適用: insights.md への品質メトリクスの記録
    手動確認用: workspace/prompt_modifications.md に提案内容を出力
    """
    result = {"auto_applied": 0, "manual_count": 0}

    # 1. insights.md に品質メトリクスを自動記録
    frontmatter, body = load_insights()
    quality = review.get("agent_c_quality", {})
    if quality:
        metrics_entry = f"\n### サイクル{cycle}\n"
        rmi = quality.get("result_metric_hypotheses", {})
        if rmi:
            metrics_entry += f"- 結果指標使用率: {rmi.get('count', '?')}/{rmi.get('total', '?')}本（{rmi.get('trend', '')}）\n"
        issues = quality.get("data_accuracy_issues", [])
        metrics_entry += f"- データ正確性: {'、'.join(issues) if issues else '問題なし'}\n"
        metrics_entry += f"- 棄却済み仮説の再提案: {'あり' if quality.get('re_proposed_rejected') else 'なし'}\n"
        metrics_entry += f"- 仮説の多様性: {quality.get('diversity_assessment', '不明')}\n"

        if "## 方法論レビュー履歴" not in body:
            body += "\n\n## 方法論レビュー履歴\n"
        # 同サイクルの重複チェック
        cycle_header = f"### サイクル{cycle}"
        if cycle_header not in body:
            body += metrics_entry
        save_insights(frontmatter, body)
        result["auto_applied"] += 1

    # 2. 改善提案をworkspace/prompt_modifications.mdに出力
    proposed = review.get("proposed_changes", [])
    if proposed:
        date = datetime.now().strftime("%Y-%m-%d")
        lines = [
            f"# プロンプト改善提案 — サイクル {cycle}\n",
            f"> 生成日: {date}",
            "> Agent Eの「分析方法の評価」に基づく自動生成\n",
            "---\n",
        ]

        for i, p in enumerate(proposed, 1):
            lines.append(f"### 提案{i}: {p.get('description', '')}")
            lines.append(f"- **対象ファイル**: `agents/{p.get('target', '?')}.md`")
            lines.append(f"- **変更種別**: {p.get('type', '?')}")
            lines.append(f"- **理由**: {p.get('reason', '')}")
            lines.append(f"- **優先度**: {p.get('priority', '?')}\n")

        mod_path = os.path.join(WORKSPACE_DIR, "prompt_modifications.md")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        result["manual_count"] = len(proposed)

    return result


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

    # model.json 読み込み
    model = {}
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, "r", encoding="utf-8") as f:
            model = json.load(f)

    # index.md 読み込み（バージョン履歴用）
    index_content = ""
    index_path = os.path.join(ANALYSIS_HISTORY_DIR, "index.md")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()

    date = datetime.now().strftime("%Y-%m-%d")
    cycle = frontmatter.get("total_cycles", 0)
    n = model.get("dataset_size", 24)

    lines = []
    lines.append("# 伸びる動画の黄金理論 — 分析結論レポート")
    lines.append(f"\n> 最終更新: {date} | 分析サイクル: {cycle}回完了 | 対象動画: {n}本")
    lines.append("\n---")

    # このレポートの読み方
    lines.append("\n## このレポートの読み方")
    lines.append(f"この文書は、{n}本の動画データを分析した結果をまとめたものです。")
    lines.append("「伸びる動画（15万再生以上）」と「伸びない動画」に分けて共通点を調べ、")
    lines.append("制作前に確認できるチェックリストとして整理しました。")
    lines.append("\n---")

    # 1. 結論: 伸びる動画の条件
    lines.append("\n## 1. 結論: 伸びる動画の条件（黄金理論）")
    lines.append("\n### なぜ伸びるのか（上位原則）")

    principles = golden.get("principles", [])
    active_principles = [p for p in principles if p.get("status") in ("established", "supported", "hypothesis")]
    if active_principles:
        for p in active_principles:
            status_label = {"established": "確立済み", "supported": "データで支持", "hypothesis": "仮説段階"}.get(p.get("status"), "")
            lines.append(f"- {p.get('statement', '')}（{status_label}）")
            if p.get("mechanism"):
                lines.append(f"  - メカニズム: {p['mechanism']}")
    else:
        lines.append("- （まだ確立された原則はありません。分析サイクルを実行してください）")

    lines.append("\n### 制作前チェックリスト")
    checklist = [c for c in golden.get("checklist", []) if c.get("status") in ("adopted", "conditional")]
    if checklist:
        lines.append("| # | チェック項目 | HITの中でクリアした割合 | MISSの中でクリアした割合 | 判別力 |")
        lines.append("|---|------------|---------------------|----------------------|-------|")
        for c in checklist:
            hit_rate = c.get("hit_fulfillment", {}).get("rate", 0)
            miss_rate = c.get("miss_fulfillment", {}).get("rate", 0)
            power_label = {"high": "高", "medium": "中", "low": "低"}.get(c.get("discriminative_power", ""), "?")
            lines.append(f"| {c.get('id', '')} | {c.get('condition', '')} | {hit_rate*100:.0f}% | {miss_rate*100:.0f}% | {power_label} |")
    else:
        lines.append("（まだ採択されたチェックリスト条件はありません）")

    # 理論の信頼度
    lines.append("\n### この理論の信頼度")
    gi_ca = model.get("gi_ca_model", {})
    acc = gi_ca.get("threshold_16_accuracy")
    if acc is not None:
        scored_n = gi_ca.get("scored_count", 0)
        lines.append(f"- GI×CA閾値16の判定精度: {acc}%（{scored_n}本で評価）")
    lines.append(f"- 未解決の問い: {frontmatter.get('open_questions', 0)}件")

    lines.append("\n---")

    # 2. 発見の要約
    lines.append("\n## 2. 発見の要約")
    lines.append("\n### 伸びた動画（HIT）に共通していたこと")

    # insights.mdの採択済みセクションから抽出
    adopted_section = ""
    if "## 採択済みインサイト" in body:
        start = body.index("## 採択済みインサイト")
        end = body.index("## 棄却仮説と学び") if "## 棄却仮説と学び" in body else len(body)
        adopted_section = body[start:end]
    # 主要インサイトを箇条書き化
    if adopted_section:
        insight_headers = re.findall(r'### (?:INS-\d+-\w+: |)(.+)', adopted_section)
        for h in insight_headers[:5]:
            lines.append(f"- {h}")
    if not adopted_section or not insight_headers:
        lines.append("- （採択済みインサイトの詳細は insights.md を参照）")

    lines.append("\n### 伸びなかった動画（MISS）に共通していたこと")
    lines.append("- （insights.md + model.json の分析結果を参照）")

    lines.append("\n### 試したが間違いだった仮説")
    rejected_section = ""
    if "## 棄却仮説と学び" in body:
        start = body.index("## 棄却仮説と学び")
        end = body.index("## 未解決の問い") if "## 未解決の問い" in body else len(body)
        rejected_section = body[start:end]
    if rejected_section:
        rej_headers = re.findall(r'### (?:REJ-\d+-\w+: |)(.+)', rejected_section)
        for h in rej_headers[:5]:
            lines.append(f"- {h}")
    if not rejected_section or not rej_headers:
        lines.append("- （棄却された仮説はまだありません）")

    lines.append("\n---")

    # 3. 統計サマリ
    lines.append("\n## 3. 統計サマリ")
    lines.append("\n### 予測力の高い指標")

    cause = model.get("correlations", {}).get("cause_metrics", {})
    if cause:
        lines.append("| 指標 | 再生数との相関 | 意味 |")
        lines.append("|------|-------------|------|")
        for name, data in list(cause.items())[:5]:
            desc = METRIC_DESCRIPTIONS.get(name, name)
            lines.append(f"| {name} | r={data['r_log_views']:+.3f} | {desc} |")
    else:
        lines.append("（モデルが未構築です）")

    lines.append("\n### モデルの精度推移")
    # index.mdからバージョン履歴テーブルをそのまま抽出
    if "| バージョン |" in index_content or "| v" in index_content:
        in_table = False
        for line in index_content.split("\n"):
            if line.strip().startswith("| バージョン") or line.strip().startswith("|---"):
                lines.append(line)
                in_table = True
            elif in_table and line.strip().startswith("| v"):
                lines.append(line)
            elif in_table and not line.strip().startswith("|"):
                break
    else:
        lines.append("（バージョン履歴はまだありません）")

    lines.append("\n---")

    # 4. 次のアクション
    lines.append("\n## 4. 次のアクション")
    lines.append("\n### 未解決の問い")
    if "## 未解決の問い" in body:
        start = body.index("## 未解決の問い")
        end = body.index("## 探索的発見") if "## 探索的発見" in body else len(body)
        q_section = body[start:end]
        q_headers = re.findall(r'### (?:Q-\d+: |)(.+)', q_section)
        for h in q_headers:
            lines.append(f"- {h}")
    if "## 未解決の問い" not in body:
        lines.append("- （未解決の問いはありません）")

    lines.append("\n### 次に検証すべきこと")
    if "## 探索的発見" in body:
        start = body.index("## 探索的発見")
        exp_section = body[start:]
        exp_headers = re.findall(r'### (?:EXP-\d+: |)(.+)', exp_section)
        for h in exp_headers:
            lines.append(f"- {h}")
    if "## 探索的発見" not in body:
        lines.append("- （探索的発見はまだありません）")

    lines.append("\n### データ品質の課題")
    lines.append("- AI評価のGI/CAは系統的に過大評価（予測に使用禁止）")
    lines.append(f"- 人間評価は{gi_ca.get('scored_count', 0)}/{n}本のみ完了。残りの人間評価が急務")
    lines.append(f"- サンプルサイズ: {n}本（統計的検出力に限界あり）")

    lines.append("\n---")
    lines.append("\n> このレポートは `python scripts/step2_analyze.py --integrate` の実行時に自動生成されます。")
    lines.append("> 詳細データ: model.json / golden_theory.json / insights.md")

    output_path = os.path.join(DATA_DIR, "analysis_conclusion.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Step 2: LLM分析コーディネーター（半自動）")
    parser.add_argument("--diff", metavar="VIDEO_ID", help="差分分析（指定動画のみ）")
    parser.add_argument("--integrate", action="store_true", help="Agent出力の統合処理を実行")
    parser.add_argument("--auto", action="store_true", help="統合処理を自動実行（Agent出力が存在する場合）")
    args = parser.parse_args()

    print("=" * 60)
    print("Step 2: LLM分析コーディネーター")
    print("=" * 60)

    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    # 不変基盤の整合性チェック (W-23)
    try:
        validate_fundamentals()
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        return

    if args.integrate:
        # Phase 3: 統合処理
        integrate(auto=args.auto)
    else:
        # Phase 1: データ準備
        success = run_data_summarizer(diff_video_id=args.diff)
        if not success:
            return

        mode = "diff" if args.diff else "full"
        print_agent_instructions(mode=mode, diff_video_id=args.diff)

        # ファイル状態表示
        print(f"\n{'='*60}")
        print("現在のファイル状態:")
        for name in ["data_summary.md", "new_hypotheses.md", "verification_report.md"]:
            path = os.path.join(WORKSPACE_DIR, name)
            if os.path.exists(path):
                mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
                print(f"  OK: {name} ({mtime})")
            else:
                print(f"  --: {name} (未作成)")
        print("=" * 60)


if __name__ == "__main__":
    main()
