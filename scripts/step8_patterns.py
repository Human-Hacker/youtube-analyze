"""
Step 3 サブモジュール: 相関分析 / パターン分析 / グループ比較 / ベンチマーク
"""

import math
from common.metrics import avg, median, pearson


# ===========================================================================
#  相関分析（原因と結果を分離）
# ===========================================================================

def compute_correlations(records):
    """原因指標・結果指標それぞれと log(再生数) の相関を計算"""
    log_views = [r["log_views"] for r in records]
    raw_views = [r["views"] for r in records]

    # 原因指標: 制作者がコントロール可能な変数
    cause_defs = [
        ("ブラウジングCTR(%)", "browsing_ctr"),
        ("関連動画CTR(%)", "related_ctr"),
        ("MV挿入数", "mv_count"),
        ("感情の底の数", "emotional_bottoms"),
        ("文字数", "word_count"),
        ("動画の長さ(秒)", "duration_seconds"),
        ("感情曲線の転換数", "emotional_transitions"),
        ("導入30秒の引きの強さ", "hook_strength"),
        ("非MVリンク数", "non_mv_links"),
        ("総メディア数(MV+非MV)", "total_media_count"),
    ]

    # 結果指標: 動画が伸びた「結果」として発生する数値
    effect_defs = [
        ("総インプレッション", "total_impressions"),
        ("ブラウジングIMP", "browsing_impressions"),
        ("関連動画IMP", "related_impressions"),
        ("ブラウジング視聴数", "browsing_views"),
        ("SUBSCRIBER視聴数", "subscriber_views"),
        ("いいね数", "likes_total"),
        ("コメント数", "comments_total"),
        ("シェア数", "shares_total"),
        ("登録者獲得数", "subs_gained"),
        ("エンゲージメント率(%)", "engagement_rate"),
        ("いいね率(%)", "like_rate"),
        ("コメント率(%)", "comment_rate"),
        ("平均視聴時間(秒)", "avg_view_duration"),
        ("平均視聴率(%)", "avg_view_percentage"),
        ("Day1→Day2変化率(%)", "day1_day2_change"),
        ("新規視聴者率(%)", "new_viewer_pct"),
        ("コア視聴者率(%)", "core_viewer_pct"),
        ("コアターゲット比率(%)", "core_target_pct"),
        ("Day1ブラウジング視聴数", "day1_browse_views"),
        ("Day1関連動画視聴数", "day1_related_views"),
        ("流入元関連動画数", "related_source_count"),
        ("最大流入元の視聴数", "top_related_source_views"),
    ]

    def _calc(metric_defs, category):
        out = {}
        for name, key in metric_defs:
            paired = [
                (r.get(key), lv, rv)
                for r, lv, rv in zip(records, log_views, raw_views)
                if r.get(key) is not None
            ]
            if len(paired) >= 3:
                xs, lvs, rvs = zip(*paired)
                out[name] = {
                    "r_log_views": round(pearson(list(xs), list(lvs)), 3),
                    "r_raw_views": round(pearson(list(xs), list(rvs)), 3),
                    "n": len(paired),
                    "type": category,
                }
        return dict(
            sorted(out.items(), key=lambda x: abs(x[1]["r_log_views"]),
                   reverse=True)
        )

    # VPD (Views Per Day) ベースの相関 — 経過時間の交絡を除去
    log_vpd = [r.get("log_vpd") for r in records]
    has_vpd = all(v is not None for v in log_vpd)

    vpd_correlations = {}
    if has_vpd:
        for name, key in cause_defs:
            paired = [
                (r.get(key), r["log_vpd"])
                for r in records
                if r.get(key) is not None and r.get("log_vpd") is not None
            ]
            if len(paired) >= 3:
                xs, vs = zip(*paired)
                vpd_correlations[name] = {
                    "r_log_vpd": round(pearson(list(xs), list(vs)), 3),
                    "n": len(paired),
                }

        # 経過日数 vs log_views / log_vpd
        age_paired = [
            (r["age_days"], r["log_views"], r["log_vpd"])
            for r in records
            if r.get("age_days") is not None and r.get("log_vpd") is not None
        ]
        if len(age_paired) >= 3:
            ages, lvs, vps = zip(*age_paired)
            vpd_correlations["経過日数"] = {
                "r_log_views": round(pearson(list(ages), list(lvs)), 3),
                "r_log_vpd": round(pearson(list(ages), list(vps)), 3),
                "n": len(age_paired),
            }

    return {
        "cause_metrics": _calc(cause_defs, "cause"),
        "effect_metrics": _calc(effect_defs, "effect"),
        "vpd_correlations": vpd_correlations,
    }


# ===========================================================================
#  パターン分析
# ===========================================================================

def analyze_patterns(records):
    patterns = []

    def _compare(name, cond):
        yes = [r["views"] for r in records if cond(r)]
        no = [r["views"] for r in records if not cond(r)]
        if yes and no:
            patterns.append({
                "name": name,
                "with_count": len(yes),
                "with_avg": int(avg(yes)),
                "with_median": int(median(yes)),
                "without_count": len(no),
                "without_avg": int(avg(no)),
                "without_median": int(median(no)),
                "ratio": round(avg(yes) / avg(no), 2) if avg(no) > 0 else None,
                "log_diff": round(
                    avg([math.log10(v) for v in yes if v > 0])
                    - avg([math.log10(v) for v in no if v > 0]),
                    3,
                ),
            })

    _compare("4要素完備", lambda r: r["has_4elements"])
    _compare("MV挿入2箇所以上", lambda r: r["mv_count"] >= 2)
    _compare("フック回答あり", lambda r: r["hook_answered"])
    _compare("感情エスカレーション", lambda r: r["bottoms_escalate"])
    _compare("感情の底3回以上", lambda r: r["emotional_bottoms"] >= 3)

    fraud = [
        {"artist": r["artist"], "views": r["views"],
         "day1_day2": r["day1_day2_change"]}
        for r in records if not r["hook_answered"]
    ]

    return {"comparisons": patterns, "hook_fraud_cases": fraud}


# ===========================================================================
#  グループ比較
# ===========================================================================

def compute_group_comparisons(records):
    hits = [r for r in records if r["is_hit"]]
    misses = [r for r in records if not r["is_hit"]]
    result = {}

    for label, group in [("伸びた動画", hits), ("伸びてない動画", misses)]:
        if not group:
            continue
        stats = {
            "動画数": len(group),
            "平均再生数": int(avg([r["views"] for r in group])),
            "中央値再生数": int(median([r["views"] for r in group])),
        }
        for key, jp in [
            ("engagement_rate", "エンゲージメント率(%)"),
            ("avg_view_duration", "平均視聴時間(秒)"),
            ("avg_view_percentage", "平均視聴率(%)"),
            ("day1_day2_change", "Day1→Day2(%)"),
            ("browsing_ctr", "ブラウジングCTR(%)"),
            ("new_viewer_pct", "新規視聴者率(%)"),
            ("mv_count", "MV挿入数"),
            ("emotional_bottoms", "感情の底の数"),
        ]:
            vals = [r[key] for r in group if r.get(key) is not None]
            if vals:
                stats[jp] = round(avg(vals), 2)

        for key, jp in [
            ("total_impressions", "総IMP"),
            ("browsing_impressions", "ブラウジングIMP"),
        ]:
            vals = [r[key] for r in group if r.get(key) is not None]
            if vals:
                stats[jp] = int(avg(vals))

        result[label] = stats
    return result


# ===========================================================================
#  ベンチマーク
# ===========================================================================

def compute_benchmarks(records):
    tiers = {
        "S_500k+": [r for r in records if r["views"] >= 500000],
        "A_200k-500k": [
            r for r in records if 200000 <= r["views"] < 500000
        ],
        "B_100k-200k": [
            r for r in records if 100000 <= r["views"] < 200000
        ],
        "C_under_100k": [r for r in records if r["views"] < 100000],
    }
    out = {}
    for tier, group in tiers.items():
        if group:
            out[tier] = {
                "count": len(group),
                "avg_views": int(avg([r["views"] for r in group])),
                "videos": [
                    {
                        "artist": r["artist"],
                        "views": r["views"],
                        "gi_x_ca": r.get("gi_x_ca"),
                        "engagement_rate": r["engagement_rate"],
                        "day1_day2": r.get("day1_day2_change"),
                    }
                    for r in sorted(
                        group, key=lambda x: x["views"], reverse=True
                    )
                ],
            }
    return out
