"""
Step 3 サブモジュール: 3段階フィルター分析 / GI×CA モデル分析
"""

from common.metrics import pearson


# ===========================================================================
#  3段階フィルター分析
# ===========================================================================

def analyze_three_stage_filter(records):
    """
    F1: 初動 CTR     -> ブラウジング CTR >= 4.0%
    F2: Day1->Day2    -> 変化率 > -20%
    F3: 深度×エンゲージメント -> 平均視聴>=300s AND eng率>=0.8%
    """
    results = []
    for r in records:
        f1 = f2 = f3 = None

        ctr = r.get("browsing_ctr")
        if ctr is not None:
            f1 = ctr >= 4.0

        change = r.get("day1_day2_change")
        if change is not None:
            f2 = change > -20.0

        avd = r.get("avg_view_duration")
        eng = r.get("engagement_rate")
        if avd is not None and eng is not None:
            f3 = avd >= 300 and eng >= 0.8

        # 総合判定 -- データがある項目のみで判定
        evaluated = [x for x in [f1, f2, f3] if x is not None]
        passed_all = all(evaluated) if evaluated else None

        first_fail = None
        if f1 is False:
            first_fail = "F1_CTR"
        elif f2 is False:
            first_fail = "F2_Day2Drop"
        elif f3 is False:
            first_fail = "F3_Depth"

        results.append({
            "video_id": r["video_id"],
            "artist": r["artist"],
            "views": r["views"],
            "is_hit": r["is_hit"],
            "f1_ctr": ctr,
            "f1_pass": f1,
            "f2_change": change,
            "f2_pass": f2,
            "f3_duration": avd,
            "f3_engagement": round(eng, 2) if eng else None,
            "f3_pass": f3,
            "passed_all": passed_all,
            "first_fail": first_fail,
        })
    return results


# ===========================================================================
#  GI×CA モデル分析
# ===========================================================================

def analyze_gi_ca_model(records):
    """人間評価スコアがある動画のみで GI×CA モデルを検証"""
    scored = [
        r for r in records
        if r.get("gi_v3") is not None and r.get("ca") is not None
    ]

    if len(scored) < 3:
        return {
            "error": "人間評価スコアが不足（3本未満）",
            "scored_count": len(scored),
            "total_count": len(records),
        }

    gi_ca_vals = [r["gi_x_ca"] for r in scored]
    log_views = [r["log_views"] for r in scored]
    raw_views = [r["views"] for r in scored]
    gi_vals = [r["gi_v3"] for r in scored]
    ca_vals = [r["ca"] for r in scored]

    r_gi_ca_log = pearson(gi_ca_vals, log_views)
    r_gi_ca_raw = pearson(gi_ca_vals, raw_views)
    r_gi_only_log = pearson(gi_vals, log_views)
    r_ca_only_log = pearson(ca_vals, log_views)

    # 閾値 16 での判定精度
    correct = sum(
        1 for r in scored if (r["gi_x_ca"] >= 16) == r["is_hit"]
    )
    accuracy_16 = correct / len(scored) * 100

    # 登録者数 vs 再生数
    subs_views = [
        (r["subs_at_publish"], r["views"])
        for r in scored
        if r.get("subs_at_publish")
    ]
    r_subs_views = None
    if len(subs_views) >= 3:
        sx, sy = zip(*subs_views)
        r_subs_views = round(pearson(list(sx), list(sy)), 3)

    details = [
        {
            "artist": r["artist"],
            "views": r["views"],
            "gi_v3": r["gi_v3"],
            "ca": r["ca"],
            "gi_x_ca": r["gi_x_ca"],
            "is_hit": r["is_hit"],
            "predicted_hit": r["gi_x_ca"] >= 16,
            "correct": (r["gi_x_ca"] >= 16) == r["is_hit"],
        }
        for r in sorted(scored, key=lambda x: x["gi_x_ca"], reverse=True)
    ]

    return {
        "scored_count": len(scored),
        "total_count": len(records),
        "correlations": {
            "GI×CA_vs_log_views": round(r_gi_ca_log, 3),
            "GI×CA_vs_raw_views": round(r_gi_ca_raw, 3),
            "GI_only_vs_log_views": round(r_gi_only_log, 3),
            "CA_only_vs_log_views": round(r_ca_only_log, 3),
            "R_squared": round(r_gi_ca_log ** 2, 3),
            "subscribers_at_publish_vs_views": r_subs_views,
        },
        "threshold_16_accuracy": round(accuracy_16, 1),
        "details": details,
    }
