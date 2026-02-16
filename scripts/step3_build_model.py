"""
Step 3: 「伸びる動画モデル」構築 — 第一原理に基づく分析

第一原理アプローチ:
  - 原因指標と結果指標を明確に分離（因果の混同を排除）
  - 人間評価 GI×CA スコアを使用（AI 自己評価 17-24 の狭い範囲を排除）
  - 3段階フィルターモデルを実装（F1→F2→F3）
  - log₁₀(再生数) での相関分析（べき乗分布への対応）
  - エンゲージメント率など正規化指標を追加
  - 中央値の追加（外れ値に頑健）

実行方法:
  python scripts/step3_build_model.py

出力:
  - data/model.json                          <- モデル定義
  - data/analysis_report.md                  <- 人間向け分析レポート
  - data/analysis_history/v{X.X}_{date}/     <- 履歴スナップショット
  - data/analysis_history/index.md           <- 履歴インデックス更新
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, MODEL_FILE, HIT_THRESHOLD
from common.data_loader import load_all_videos, load_video_index, load_human_scores, load_golden_theory, save_golden_theory, validate_fundamentals
from common.metrics import deep, avg, median, pearson
from step3_filters import analyze_three_stage_filter, analyze_gi_ca_model
from step3_patterns import compute_correlations, analyze_patterns, compute_group_comparisons, compute_benchmarks
from step3_report import generate_report
from step3_history import get_next_version, save_history_snapshot, update_history_index


# ===========================================================================
#  派生指標の計算
# ===========================================================================

def compute_derived_metrics(v, human_scores, index):
    """各動画の全指標を計算して1つのフラットな辞書にまとめる"""
    vid = v["metadata"]["video_id"]
    views = v["metadata"]["current_stats"]["view_count"]
    likes = v["metadata"]["current_stats"]["like_count"]
    comments = v["metadata"]["current_stats"]["comment_count"]
    duration = v["metadata"]["duration_seconds"]

    overview = v.get("analytics_overview") or {}
    daily = v.get("daily_data") or {}
    manual = v.get("manual_data") or {}
    script = v.get("script_analysis") or {}
    human = human_scores.get(vid, {})
    idx = index.get(vid, {})

    shares = overview.get("shares", 0)

    d = {
        "video_id": vid,
        "artist": idx.get("artist_name", ""),
        "views": views,
        "log_views": math.log10(views) if views > 0 else 0,
        "is_hit": views >= HIT_THRESHOLD,
        "published_at": v["metadata"]["published_at"][:10],
        "duration_seconds": duration,
    }

    # 動画年齢（日数）
    try:
        pub = datetime.fromisoformat(
            v["metadata"]["published_at"].replace("Z", "+00:00")
        )
        age_days = (datetime.now(timezone.utc) - pub).days
        d["age_days"] = age_days
        d["views_per_day"] = round(views / age_days, 1) if age_days > 0 else 0
        d["log_vpd"] = round(math.log10(views / age_days), 3) if age_days > 0 and views > 0 else None
    except Exception:
        d["age_days"] = None
        d["views_per_day"] = None
        d["log_vpd"] = None

    # ======= 原因指標（CAUSE: コントロール可能） =======

    # エンゲージメント率
    d["engagement_rate"] = round(
        (likes + comments + shares) / views * 100, 3
    ) if views > 0 else 0
    d["like_rate"] = round(likes / views * 100, 3) if views > 0 else 0
    d["comment_rate"] = round(comments / views * 100, 3) if views > 0 else 0

    # 視聴深度
    d["avg_view_duration"] = overview.get("average_view_duration_seconds")
    d["avg_view_percentage"] = overview.get("average_view_percentage")

    # 初動
    d["day1_day2_change"] = daily.get("day1_to_day2_change_percent")
    daily_list = daily.get("daily", [])
    d["day1_views"] = daily_list[0]["views"] if len(daily_list) >= 1 else None
    d["day2_views"] = daily_list[1]["views"] if len(daily_list) >= 2 else None
    d["day7_total"] = (
        sum(dd["views"] for dd in daily_list[:7]) if daily_list else None
    )

    # CTR（手動データ）
    d["browsing_ctr"] = deep(manual, "browsing", "ctr")
    d["related_ctr"] = deep(manual, "related", "ctr")
    d["total_ctr"] = manual.get("total_ctr")

    # 視聴者セグメント
    d["new_viewer_pct"] = deep(manual, "viewer_segments", "new", "views_percent")
    d["core_viewer_pct"] = deep(
        manual, "viewer_segments", "core", "views_percent"
    )

    # コアターゲット比率
    d["core_target_pct"] = deep(v, "demographics", "core_target_45_64_percent")

    # ======= 結果指標（EFFECT: 伸びた「結果」） =======

    d["total_impressions"] = manual.get("total_impressions")
    d["browsing_impressions"] = deep(manual, "browsing", "impressions")
    d["related_impressions"] = deep(manual, "related", "impressions")
    d["browsing_views"] = deep(manual, "browsing", "views")
    d["browsing_pct"] = deep(manual, "browsing", "views_percent")
    d["subscriber_views"] = deep(
        v, "traffic_sources", "SUBSCRIBER", "views"
    )
    d["subscriber_pct"] = deep(
        v, "traffic_sources", "SUBSCRIBER", "percentage"
    )
    d["likes_total"] = likes
    d["comments_total"] = comments
    d["shares_total"] = shares
    d["subs_gained"] = overview.get("subscribers_gained", 0)

    # ======= 人間評価 GI×CA スコア =======

    if human and human.get("source") in ("human", "ai_calibrated", "quantitative", "knowledge_based"):
        d["gi_v3"] = human.get("GI_v3")
        d["ca"] = human.get("CA")
        d["gi_x_ca"] = human.get("GI_x_CA")
        d["score_source"] = human.get("source")
        d["g1"] = human.get("G1")
        d["g2"] = human.get("G2")
        d["g3"] = human.get("G3")
        d["g4"] = human.get("G4")
        d["g6"] = human.get("G6")
        d["subs_at_publish"] = human.get("subscribers_at_publish")
    else:
        d["gi_v3"] = None
        d["ca"] = None
        d["gi_x_ca"] = None
        d["score_source"] = "none"
        d["subs_at_publish"] = None

    # ======= AI 生成スコア（参考値のみ） =======

    d["ai_gi_total"] = deep(script, "gi_scores", "total")
    d["ai_ca"] = deep(script, "curiosity_alignment", "ca_score")

    # ======= 台本構造 =======

    structure = script.get("structure", {})
    d["has_unified_theme"] = structure.get("has_unified_theme", False)
    d["has_antagonist"] = structure.get("has_antagonist", False)
    d["emotional_bottoms"] = structure.get("emotional_bottoms_count", 0)
    d["bottoms_escalate"] = structure.get("bottoms_escalate", False)
    d["has_savior"] = structure.get("has_savior", False)
    d["has_4elements"] = (
        d["has_unified_theme"]
        and d["has_antagonist"]
        and d["emotional_bottoms"] >= 3
        and d["has_savior"]
    )

    hook = script.get("hook_analysis", {})
    d["hook_answered"] = hook.get("hook_answered_in_script", True)

    mv = script.get("mv_insertions", {})
    d["mv_count"] = mv.get("count", 0)

    d["word_count"] = script.get("word_count", 0)

    # ======= 新規台本指標 =======

    ec = script.get("emotional_curve", {})
    d["emotional_ups"] = ec.get("total_ups")
    d["emotional_downs"] = ec.get("total_downs")
    d["emotional_transitions"] = ec.get("total_transitions")

    o30 = script.get("opening_30sec", {})
    d["opening_type"] = o30.get("opening_type")
    d["hook_strength"] = o30.get("hook_strength")

    nmv = script.get("non_mv_media", {})
    d["non_mv_links"] = nmv.get("total_links", 0) or 0
    d["total_media_count"] = d["mv_count"] + d["non_mv_links"]

    # ======= Day1トラフィック内訳 =======

    day1_entry = daily_list[0] if daily_list else {}
    day1_tb = day1_entry.get("traffic_breakdown", {})
    d["day1_browse_views"] = deep(day1_tb, "BROWSE", "views")
    d["day1_related_views"] = deep(day1_tb, "RELATED", "views")
    d["day1_search_views"] = deep(day1_tb, "SEARCH", "views")
    d["day1_subscriber_views"] = deep(day1_tb, "SUBSCRIBER", "views")

    # ======= 関連動画ソース =======

    related_sources = daily.get("related_video_sources", [])
    d["related_source_count"] = len(related_sources)
    d["top_related_source_views"] = max(
        [s["views"] for s in related_sources], default=0
    ) if related_sources else 0

    return d


# ===========================================================================
#  golden_theory 検証
# ===========================================================================

def validate_golden_theory(golden, records):
    """golden_theory.json のチェックリスト条件を実データで再検証する (BUG-3)"""
    hits = [r for r in records if r["is_hit"]]
    misses = [r for r in records if not r["is_hit"]]

    # 条件名→評価関数のマッピング
    CONDITION_EVALUATORS = {
        "G1+G6>=8": lambda r: (r.get("g1") or 0) + (r.get("g6") or 0) >= 8,
        "GI×CA >= 16": lambda r: (r.get("gi_x_ca") or 0) >= 16,
        "GI×CA >= 36": lambda r: (r.get("gi_x_ca") or 0) >= 36,
        "CA >= 2.5": lambda r: (r.get("ca") or 0) >= 2.5,
        "CA >= 2": lambda r: (r.get("ca") or 0) >= 2,
        "GI>=18": lambda r: (r.get("gi_v3") or 0) >= 18,
        "メディア挿入2件以上": lambda r: (r.get("total_media_count") or 0) >= 2,
    }

    for item in golden.get("checklist", []):
        condition = item["condition"]
        # 条件名から評価関数を部分一致で検索
        evaluator = None
        for key, func in CONDITION_EVALUATORS.items():
            if key in condition:
                evaluator = func
                break

        if evaluator is None:
            continue  # 評価不能な条件はスキップ

        # 評価対象: GI/CAスコアを使う条件はscored recordsのみ
        scored_hits = [r for r in hits if r.get("gi_v3") is not None]
        scored_misses = [r for r in misses if r.get("gi_v3") is not None]

        if not scored_hits and not scored_misses:
            continue

        hit_pass = sum(1 for r in scored_hits if evaluator(r))
        miss_pass = sum(1 for r in scored_misses if evaluator(r))

        old_hit_rate = item.get("hit_fulfillment", {}).get("rate", 0)
        new_hit_rate = hit_pass / len(scored_hits) if scored_hits else 0
        old_miss_rate = item.get("miss_fulfillment", {}).get("rate", 0)
        new_miss_rate = miss_pass / len(scored_misses) if scored_misses else 0

        item["hit_fulfillment"] = {
            "count": hit_pass, "total": len(scored_hits),
            "rate": round(new_hit_rate, 3),
        }
        item["miss_fulfillment"] = {
            "count": miss_pass, "total": len(scored_misses),
            "rate": round(new_miss_rate, 3),
        }

        # 弁別力を再判定
        diff = new_hit_rate - new_miss_rate
        if diff > 0.5:
            item["discriminative_power"] = "high"
        elif diff > 0.2:
            item["discriminative_power"] = "medium"
        elif diff > 0:
            item["discriminative_power"] = "low"
        else:
            item["discriminative_power"] = "none"

        # 大幅変化時にWARNING
        if abs(new_hit_rate - old_hit_rate) > 0.1 or abs(new_miss_rate - old_miss_rate) > 0.1:
            print(f"  WARNING: {condition} の充足率が変化 "
                  f"(HIT: {old_hit_rate:.3f}→{new_hit_rate:.3f}, "
                  f"MISS: {old_miss_rate:.3f}→{new_miss_rate:.3f})")

    save_golden_theory(golden)
    return golden


# ===========================================================================
#  メイン
# ===========================================================================

def build_and_save():
    """モデル構築→保存→履歴保存。外部から呼び出し可能。"""
    # 不変基盤の整合性チェック (W-23)
    validate_fundamentals()

    print("\n[1/7] データ読み込み...")
    videos = load_all_videos()
    if not videos:
        print("data/videos/ にデータがありません。")
        return None, None
    index = load_video_index()
    human_scores = load_human_scores()
    print(f"  動画: {len(videos)}本 / 人間評価: {len(human_scores)}件")

    print("[2/7] 派生指標計算...")
    records = [compute_derived_metrics(v, human_scores, index) for v in videos]

    hits = [r for r in records if r["is_hit"]]
    misses = [r for r in records if not r["is_hit"]]
    scored = [r for r in records if r.get("gi_v3") is not None]
    print(f"  HIT: {len(hits)}本 / MISS: {len(misses)}本")
    print(f"  人間評価あり: {len(scored)}本 / なし: {len(records) - len(scored)}本")

    # golden_theory 読み込み・検証
    golden = load_golden_theory()
    golden = validate_golden_theory(golden, records)

    print("[3/7] 3段階フィルター分析...")
    filter_results = analyze_three_stage_filter(records)

    print("[4/7] GI×CAモデル分析...")
    gi_ca_result = analyze_gi_ca_model(records)

    print("[5/7] 相関・パターン分析...")
    correlations = compute_correlations(records)
    patterns = analyze_patterns(records)
    group_comp = compute_group_comparisons(records)
    benchmarks = compute_benchmarks(records)

    version = get_next_version()

    model = {
        "version": version,
        "built_at": datetime.now().isoformat(),
        "dataset_size": len(videos),
        "hit_threshold": HIT_THRESHOLD,
        "classification": {"hits": len(hits), "misses": len(misses)},
        "gi_ca_model": gi_ca_result,
        "three_stage_filter": filter_results,
        "correlations": correlations,
        "patterns": patterns,
        "group_comparisons": group_comp,
        "benchmarks": benchmarks,
        "video_list": [
            {
                "video_id": r["video_id"],
                "artist": r["artist"],
                "views": r["views"],
                "is_hit": r["is_hit"],
                "gi_x_ca": r.get("gi_x_ca"),
                "engagement_rate": r["engagement_rate"],
                "day1_day2": r.get("day1_day2_change"),
                "published_at": r["published_at"],
                "age_days": r.get("age_days"),
                "views_per_day": r.get("views_per_day"),
                "log_vpd": r.get("log_vpd"),
            }
            for r in sorted(records, key=lambda x: x["views"], reverse=True)
        ],
    }

    print("[6/7] 出力中...")
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    print(f"  {MODEL_FILE}")

    report = generate_report(model, records)
    rpath = os.path.join(DATA_DIR, "analysis_report.md")
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  {rpath}")

    print("[7/7] 履歴保存...")
    save_history_snapshot(model, report)
    update_history_index(model)

    # サマリー
    print(f"\n{'=' * 60}")
    print(f"モデル構築完了 (v{model['version']})")
    print(
        f"  データ: {model['dataset_size']}本 "
        f"(HIT:{len(hits)} / MISS:{len(misses)})"
    )

    if gi_ca_result.get("correlations"):
        c = gi_ca_result["correlations"]
        print(f"\n  GI×CA モデル ({gi_ca_result['scored_count']}本):")
        print(f"    GI×CA vs log(再生数): r={c.get('GI×CA_vs_log_views', 'N/A')}")
        print(f"    R²: {c.get('R_squared', 'N/A')}")
        print(f"    閾値16判定精度: {gi_ca_result['threshold_16_accuracy']}%")

    cause = correlations.get("cause_metrics", {})
    if cause:
        print(f"\n  原因指標 TOP5 (vs log再生数):")
        for i, (name, data) in enumerate(list(cause.items())[:5], 1):
            print(f"    {i}. {name}: r={data['r_log_views']:+.3f}")

    if filter_results:
        with_data = [f for f in filter_results if f["f1_pass"] is not None]
        if with_data:
            ph = sum(
                1 for f in with_data if f["passed_all"] and f["is_hit"]
            )
            fm = sum(
                1 for f in with_data
                if not f["passed_all"] and not f["is_hit"]
            )
            total = len(with_data)
            print(f"\n  3段階フィルター精度: {(ph+fm)/total*100:.1f}% ({ph+fm}/{total})")

    return model, records


def main():
    print("=" * 60)
    print("Step 3: モデル構築 (第一原理アプローチ)")
    print("=" * 60)
    build_and_save()


if __name__ == "__main__":
    main()
