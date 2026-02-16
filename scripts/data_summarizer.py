"""
data_summarizer.py - 全動画データの要約をマークダウン形式で出力する

Usage:
    python scripts/data_summarizer.py              # 全動画の要約
    python scripts/data_summarizer.py --diff VID   # 指定動画の詳細 + 全体比較
"""

import json, os, sys, argparse, math
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import VIDEOS_DIR, DATA_DIR, WORKSPACE_DIR, HUMAN_SCORES_FILE, HIT_THRESHOLD
from common.data_loader import load_all_videos, load_human_scores, validate_fundamentals
from common.metrics import avg_or_none as _avg, median_or_none as _median, deep as _deep, fmt as _fmt, fmt_int as _fmt_int


# ---------------------------------------------------------------------------
# 各動画から指標を抽出
# ---------------------------------------------------------------------------

def extract_metrics(video, human_scores):
    """1本の動画データから表示用の指標辞書を作成する。"""
    vid = video["_video_id"]
    meta = video.get("metadata", {})
    ao = video.get("analytics_overview", {})
    dd = video.get("daily_data", {})
    md = video.get("manual_data", {})

    views = _deep(meta, "current_stats", "view_count") or ao.get("views", 0)
    likes = ao.get("likes", 0) or 0
    comments = ao.get("comments", 0) or 0
    shares = ao.get("shares", 0) or 0

    eng_rate = None
    if views and views > 0:
        eng_rate = (likes + comments + shares) / views * 100

    b_ctr = _deep(md, "browsing", "ctr")
    d1_d2 = dd.get("day1_to_day2_change_percent")
    avg_view = ao.get("average_view_duration_seconds")
    hit = views >= HIT_THRESHOLD if views else False

    # human scores
    hs = human_scores.get(vid, {})
    gi_x_ca = hs.get("GI_x_CA")
    artist_hs = hs.get("artist", "")

    # アーティスト名: human_scores > script_analysis > title から推測
    artist = artist_hs
    if not artist:
        artist = _deep(video, "script_analysis", "artist_name") or ""
    if not artist:
        artist = meta.get("title", vid)[:20]

    return {
        "video_id": vid,
        "artist": artist,
        "title": meta.get("title", ""),
        "views": views,
        "gi_x_ca": gi_x_ca,
        "eng_rate": eng_rate,
        "b_ctr": b_ctr,
        "d1_d2": d1_d2,
        "avg_view": avg_view,
        "hit": hit,
        "published_at": meta.get("published_at", ""),
        "duration_seconds": meta.get("duration_seconds"),
    }


# ---------------------------------------------------------------------------
# フル要約モード
# ---------------------------------------------------------------------------

def build_full_summary(videos, human_scores):
    """全動画の要約マークダウンを生成する。"""
    lines = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"# 動画データ要約\n")
    lines.append(f"生成日時: {now_str}\n")

    # 指標抽出
    all_metrics = [extract_metrics(v, human_scores) for v in videos]
    # 再生数降順
    all_metrics.sort(key=lambda m: m["views"] or 0, reverse=True)

    # ----- 1. 概要テーブル -----
    lines.append("## 1. 概要テーブル\n")
    lines.append("| # | アーティスト | 再生数 | GI×CA | eng率(%) | B-CTR(%) | D1→D2(%) | 平均視聴(秒) | HIT |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        hit_label = "HIT" if m["hit"] else "MISS"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {_fmt_int(m['views'])} "
            f"| {_fmt(m['gi_x_ca'])} "
            f"| {_fmt(m['eng_rate'])} "
            f"| {_fmt(m['b_ctr'])} "
            f"| {_fmt(m['d1_d2'])} "
            f"| {_fmt(m['avg_view'], 0)} "
            f"| {hit_label} |"
        )

    lines.append("")

    # ----- 2. 分布サマリ -----
    lines.append("## 2. 分布サマリ\n")

    hit_list = [m for m in all_metrics if m["hit"]]
    miss_list = [m for m in all_metrics if not m["hit"]]
    n_total = len(all_metrics)
    n_hit = len(hit_list)
    n_miss = len(miss_list)

    lines.append(f"- 全体: {n_total}本、HIT {n_hit}本、MISS {n_miss}本\n")

    # 再生数
    views_all = [m["views"] for m in all_metrics if m["views"] is not None]
    lines.append("### 再生数")
    lines.append(f"- 平均: {_fmt_int(round(_avg(views_all))) if _avg(views_all) is not None else '-'}")
    lines.append(f"- 中央値: {_fmt_int(round(_median(views_all))) if _median(views_all) is not None else '-'}")
    lines.append(f"- 最大: {_fmt_int(max(views_all)) if views_all else '-'}")
    lines.append(f"- 最小: {_fmt_int(min(views_all)) if views_all else '-'}")
    lines.append("")

    # eng率
    eng_hit = [m["eng_rate"] for m in hit_list if m["eng_rate"] is not None]
    eng_miss = [m["eng_rate"] for m in miss_list if m["eng_rate"] is not None]
    eng_all = [m["eng_rate"] for m in all_metrics if m["eng_rate"] is not None]
    lines.append("### eng率(%)")
    lines.append(f"- 全体: 平均 {_fmt(_avg(eng_all))} / 中央値 {_fmt(_median(eng_all))}")
    lines.append(f"- HIT: 平均 {_fmt(_avg(eng_hit))} / 中央値 {_fmt(_median(eng_hit))}")
    lines.append(f"- MISS: 平均 {_fmt(_avg(eng_miss))} / 中央値 {_fmt(_median(eng_miss))}")
    lines.append("")

    # 視聴時間
    avd_hit = [m["avg_view"] for m in hit_list if m["avg_view"] is not None]
    avd_miss = [m["avg_view"] for m in miss_list if m["avg_view"] is not None]
    avd_all = [m["avg_view"] for m in all_metrics if m["avg_view"] is not None]
    lines.append("### 平均視聴時間(秒)")
    lines.append(f"- 全体: 平均 {_fmt(_avg(avd_all), 0)} / 中央値 {_fmt(_median(avd_all), 0)}")
    lines.append(f"- HIT: 平均 {_fmt(_avg(avd_hit), 0)} / 中央値 {_fmt(_median(avd_hit), 0)}")
    lines.append(f"- MISS: 平均 {_fmt(_avg(avd_miss), 0)} / 中央値 {_fmt(_median(avd_miss), 0)}")
    lines.append("")

    # ----- 3. 人間評価スコア概要 -----
    lines.append("## 3. 人間評価スコア概要\n")

    scored = {vid: s for vid, s in human_scores.items() if s.get("GI_x_CA") is not None}
    unscored = {vid: s for vid, s in human_scores.items() if s.get("GI_x_CA") is None}

    lines.append(f"- 評価済み {len(scored)}本、未評価 {len(unscored)}本")

    if scored:
        gi_x_ca_vals = [s["GI_x_CA"] for s in scored.values()]
        lines.append(f"- GI×CA範囲: {min(gi_x_ca_vals)} - {max(gi_x_ca_vals)}")
    lines.append("")

    lines.append("| アーティスト | VID | GI_v3 | CA | GI×CA |")
    lines.append("|---|---|---|---|---|")

    # 評価済みをGI×CA降順で表示
    for vid, s in sorted(scored.items(), key=lambda x: x[1].get("GI_x_CA", 0), reverse=True):
        lines.append(
            f"| {s.get('artist', '-')} | {vid} "
            f"| {_fmt(s.get('GI_v3'))} | {_fmt(s.get('CA'))} | {_fmt(s.get('GI_x_CA'))} |"
        )
    # 未評価
    for vid, s in sorted(unscored.items(), key=lambda x: x[1].get("artist", "")):
        lines.append(
            f"| {s.get('artist', '-')} | {vid} "
            f"| - | - | - |"
        )

    lines.append("")

    # ----- 4. 台本構造・フック・好奇心テーブル -----
    lines.append("## 4. 台本構造テーブル\n")
    lines.append(
        "| # | アーティスト | テーマ | 敵役 | 底の数 | エスカレート | 救世主 "
        "| MV数 | フック回答 | 回答位置(%) | CA_top1回答 | CA_top2回答 | HIT |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        sa = (v.get("script_analysis") or {}) if v else {}
        st = sa.get("structure", {})
        hook = sa.get("hook_analysis", {})
        mv = sa.get("mv_insertions", {})
        ca = sa.get("curiosity_alignment", {})

        hit_label = "HIT" if m["hit"] else "MISS"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {st.get('theme_word', '-')} "
            f"| {'Y' if st.get('has_antagonist') else 'N'} "
            f"| {st.get('emotional_bottoms_count', '-')} "
            f"| {'Y' if st.get('bottoms_escalate') else 'N'} "
            f"| {'Y' if st.get('has_savior') else 'N'} "
            f"| {mv.get('count', '-')} "
            f"| {'Y' if hook.get('hook_answered_in_script') else 'N'} "
            f"| {_fmt(hook.get('hook_answer_position_percent'), 0)} "
            f"| {'Y' if ca.get('top1_addressed') else 'N'} "
            f"| {'Y' if ca.get('top2_addressed') else 'N'} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 5. タイトル・切り口一覧 -----
    lines.append("## 5. タイトル・好奇心TOP1-2\n")
    lines.append("| # | アーティスト | タイトル | 好奇心TOP1 | 好奇心TOP2 | 公開日 | HIT |")
    lines.append("|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        sa = (v.get("script_analysis") or {}) if v else {}
        ca = sa.get("curiosity_alignment", {})
        pub = m.get("published_at", "")
        if pub and len(pub) >= 10:
            pub = pub[:10]
        hit_label = "HIT" if m["hit"] else "MISS"
        title = m.get("title", "-")
        if len(title) > 40:
            title = title[:40] + "…"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {title} "
            f"| {ca.get('top1_topic', '-')[:30] if ca.get('top1_topic') else '-'} "
            f"| {ca.get('top2_topic', '-')[:30] if ca.get('top2_topic') else '-'} "
            f"| {pub} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 6. GIサブスコア -----
    # 人間評価を優先表示。AI評価は参考値として併記（系統的過大評価あり）
    lines.append("## 6. GIサブスコア\n")
    lines.append("> **注意**: 人間評価とAI評価は異なる。AI評価は系統的に過大評価する（insights参照）。")
    lines.append("> 予測にはGI×CA（人間/定量評価）のみを使用すること。\n")

    # 評価済み（quantitative or human）を集計
    scored_vids = {vid: s for vid, s in human_scores.items()
                   if s.get("GI_x_CA") is not None}
    q_count = sum(1 for s in scored_vids.values() if s.get("source") == "quantitative")
    h_count = sum(1 for s in scored_vids.values() if s.get("source") == "human")
    lines.append(f"### 6a. 評価済み（{len(scored_vids)}本: 定量{q_count}本 + 人間{h_count}本）\n")
    lines.append("| アーティスト | G1 | G2 | G3 | G4 | G6 | GI_v3 | CA | GI×CA | src | TOP1 | HIT |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")

    for m in all_metrics:
        hs = human_scores.get(m["video_id"], {})
        if hs.get("GI_x_CA") is None:
            continue
        hit_label = "HIT" if m["hit"] else "MISS"
        src = (hs.get("source", "-") or "-")[:1]  # q/h/a の頭文字
        top1 = hs.get("curiosity_top1", "-")
        if top1 and len(top1) > 20:
            top1 = top1[:20] + "…"
        lines.append(
            f"| {m['artist']} "
            f"| {hs.get('G1', '-')} "
            f"| {hs.get('G2', '-')} "
            f"| {hs.get('G3', '-')} "
            f"| {hs.get('G4', '-')} "
            f"| {hs.get('G6', '-')} "
            f"| {hs.get('GI_v3', '-')} "
            f"| {hs.get('CA', '-')} "
            f"| {hs.get('GI_x_CA', '-')} "
            f"| {src} "
            f"| {top1 if top1 else '-'} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 7. トラフィック構成 -----
    lines.append("## 7. トラフィック構成\n")
    lines.append("| # | アーティスト | BROWSING(%) | SUBSCRIBER(%) | RELATED(%) | 検索(%) | 再生数 | HIT |")
    lines.append("|---|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        md_data = v.get("manual_data", {}) if v else {}
        ts = v.get("traffic_sources", {}) if v else {}
        # browsing % from manual_data or traffic_sources
        brow_pct = _deep(md_data, "browsing", "views_percent")
        sub_pct = _deep(ts, "SUBSCRIBER", "percentage")
        rel_pct = _deep(ts, "RELATED_VIDEO", "percentage")
        search_pct = _deep(ts, "YT_SEARCH", "percentage")

        hit_label = "HIT" if m["hit"] else "MISS"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {_fmt(brow_pct)} "
            f"| {_fmt(sub_pct)} "
            f"| {_fmt(rel_pct)} "
            f"| {_fmt(search_pct)} "
            f"| {_fmt_int(m['views'])} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 8. 日別成長パターン (Day1-7) -----
    lines.append("## 8. 日別再生数推移 (Day1-7)\n")
    lines.append("| # | アーティスト | Day1 | Day2 | Day3 | Day4 | Day5 | Day6 | Day7 | パターン | HIT |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        dd = v.get("daily_data", {}).get("daily", []) if v else []
        day_views = []
        for d in range(1, 8):
            dv = None
            for entry in dd:
                if entry.get("day_number") == d:
                    dv = entry.get("views")
                    break
            day_views.append(dv)

        # パターン分類
        pattern = _classify_growth_pattern(day_views)
        hit_label = "HIT" if m["hit"] else "MISS"
        day_strs = [_fmt_int(dv) if dv is not None else "-" for dv in day_views]
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {day_strs[0]} | {day_strs[1]} | {day_strs[2]} | {day_strs[3]} "
            f"| {day_strs[4]} | {day_strs[5]} | {day_strs[6]} "
            f"| {pattern} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 9. 感情曲線テーブル -----
    lines.append("## 9. 感情曲線テーブル\n")
    lines.append("| # | アーティスト | UP数 | DOWN数 | 転換合計 | Intro | 1幕 | 2幕 | 3幕 | HIT |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        sa = (v.get("script_analysis") or {}) if v else {}
        ec = sa.get("emotional_curve", {})
        hit_label = "HIT" if m["hit"] else "MISS"
        pba = ec.get("pattern_by_act", {})
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {ec.get('total_ups', '-')} "
            f"| {ec.get('total_downs', '-')} "
            f"| {ec.get('total_transitions', '-')} "
            f"| {pba.get('intro', '-')} "
            f"| {pba.get('first_act', '-')} "
            f"| {pba.get('second_act', '-')} "
            f"| {pba.get('third_act', '-')} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 10. 導入30秒テーブル -----
    lines.append("## 10. 導入30秒テーブル\n")
    lines.append("| # | アーティスト | 開始タイプ | 引きの強さ(1-5) | HIT |")
    lines.append("|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        sa = (v.get("script_analysis") or {}) if v else {}
        o30 = sa.get("opening_30sec", {})
        hit_label = "HIT" if m["hit"] else "MISS"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {o30.get('opening_type', '-')} "
            f"| {o30.get('hook_strength', '-')} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 11. 本人映像テーブル -----
    lines.append("## 11. 本人映像テーブル\n")
    lines.append("| # | アーティスト | MV数 | 非MVリンク数 | 合計メディア数 | HIT |")
    lines.append("|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        sa = (v.get("script_analysis") or {}) if v else {}
        mv_count = sa.get("mv_insertions", {}).get("count", 0) or 0
        non_mv = sa.get("non_mv_media", {}).get("total_links", 0) or 0
        total_media = mv_count + non_mv
        hit_label = "HIT" if m["hit"] else "MISS"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {mv_count} "
            f"| {non_mv} "
            f"| {total_media} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 12. Day1トラフィック内訳テーブル -----
    lines.append("## 12. Day1トラフィック内訳テーブル\n")
    lines.append("| # | アーティスト | D1合計 | D1_BROWSE | D1_RELATED | D1_SEARCH | D1_SUB | HIT |")
    lines.append("|---|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        dd = v.get("daily_data", {}).get("daily", []) if v else []
        day1 = dd[0] if dd else {}
        tb = day1.get("traffic_breakdown", {})
        d1_total = day1.get("views", "-")
        d1_browse = tb.get("BROWSE", {}).get("views", "-") if tb else "-"
        d1_related = tb.get("RELATED", {}).get("views", "-") if tb else "-"
        d1_search = tb.get("SEARCH", {}).get("views", "-") if tb else "-"
        d1_sub = tb.get("SUBSCRIBER", {}).get("views", "-") if tb else "-"
        hit_label = "HIT" if m["hit"] else "MISS"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {_fmt_int(d1_total) if isinstance(d1_total, (int, float)) else d1_total} "
            f"| {_fmt_int(d1_browse) if isinstance(d1_browse, (int, float)) else d1_browse} "
            f"| {_fmt_int(d1_related) if isinstance(d1_related, (int, float)) else d1_related} "
            f"| {_fmt_int(d1_search) if isinstance(d1_search, (int, float)) else d1_search} "
            f"| {_fmt_int(d1_sub) if isinstance(d1_sub, (int, float)) else d1_sub} "
            f"| {hit_label} |"
        )
    lines.append("")

    # ----- 13. 関連動画ソーステーブル -----
    lines.append("## 13. 関連動画ソーステーブル\n")
    lines.append("| # | アーティスト | ソース上位1 | ソース上位2 | ソース上位3 | 関連合計視聴数 | HIT |")
    lines.append("|---|---|---|---|---|---|---|")

    for i, m in enumerate(all_metrics, 1):
        v = _find_video(videos, m["video_id"])
        dd = v.get("daily_data", {}) if v else {}
        sources = dd.get("related_video_sources", [])
        # 視聴数降順で上位3件
        top3 = sorted(sources, key=lambda s: s.get("views", 0), reverse=True)[:3]
        total_related = sum(s.get("views", 0) for s in sources)

        def _fmt_source(s):
            title = s.get("source_video_title") or s.get("source_video_id", "?")
            v_count = s.get("views", 0)
            return f"{title}({_fmt_int(v_count)})"

        s1 = _fmt_source(top3[0]) if len(top3) > 0 else "-"
        s2 = _fmt_source(top3[1]) if len(top3) > 1 else "-"
        s3 = _fmt_source(top3[2]) if len(top3) > 2 else "-"
        hit_label = "HIT" if m["hit"] else "MISS"
        lines.append(
            f"| {i} "
            f"| {m['artist']} "
            f"| {s1} "
            f"| {s2} "
            f"| {s3} "
            f"| {_fmt_int(total_related)} "
            f"| {hit_label} |"
        )
    lines.append("")

    return "\n".join(lines)


def _find_video(videos, video_id):
    """video_idに一致する動画データを返す。"""
    for v in videos:
        if v.get("_video_id") == video_id:
            return v
    return None


def _classify_growth_pattern(day_views):
    """Day1-7の再生数リストから成長パターンを分類する。"""
    valid = [v for v in day_views if v is not None]
    if len(valid) < 3:
        return "データ不足"

    # ピーク日を特定
    peak_day = valid.index(max(valid)) + 1
    # Day7がDay1の何倍か
    if valid[0] and valid[0] > 0:
        growth_ratio = valid[-1] / valid[0] if len(valid) >= 7 else valid[-1] / valid[0]
    else:
        growth_ratio = 0

    if peak_day <= 2 and growth_ratio < 0.5:
        return "初日ピーク→急落"
    elif peak_day >= 5:
        return "遅延爆発"
    elif growth_ratio >= 3:
        return "加速成長"
    elif growth_ratio >= 1:
        return "安定成長"
    elif growth_ratio >= 0.3:
        return "緩やかな減衰"
    else:
        return "初日ピーク→急落"


# ---------------------------------------------------------------------------
# 差分モード
# ---------------------------------------------------------------------------

def _percentile(val, all_vals):
    """val が all_vals の中で何パーセンタイルに位置するかを返す。"""
    if not all_vals or val is None:
        return None
    below = sum(1 for v in all_vals if v < val)
    return round(below / len(all_vals) * 100, 1)


def build_diff_summary(target_vid, videos, human_scores):
    """指定動画の詳細 + 全体比較マークダウンを生成する。"""
    lines = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # 対象動画を探す
    target = None
    for v in videos:
        if v["_video_id"] == target_vid:
            target = v
            break

    if target is None:
        return f"# エラー\n\n動画 `{target_vid}` が見つかりません。\n"

    all_metrics = [extract_metrics(v, human_scores) for v in videos]
    target_metrics = extract_metrics(target, human_scores)

    lines.append(f"# 動画詳細: {target_metrics['artist']} ({target_vid})\n")
    lines.append(f"生成日時: {now_str}\n")

    # 基本情報
    lines.append("## 基本情報\n")
    meta = target.get("metadata", {})
    lines.append(f"- タイトル: {meta.get('title', '-')}")
    lines.append(f"- 公開日: {meta.get('published_at', '-')}")
    lines.append(f"- 動画長: {meta.get('duration_display', '-')} ({meta.get('duration_seconds', '-')}秒)")
    lines.append(f"- 再生数: {_fmt_int(target_metrics['views'])}")
    lines.append(f"- HIT判定: {'HIT' if target_metrics['hit'] else 'MISS'}")
    lines.append("")

    # パーセンタイル比較
    lines.append("## 全体での位置づけ (パーセンタイル)\n")

    views_all = [m["views"] for m in all_metrics if m["views"] is not None]
    eng_all = [m["eng_rate"] for m in all_metrics if m["eng_rate"] is not None]
    avd_all = [m["avg_view"] for m in all_metrics if m["avg_view"] is not None]
    bctr_all = [m["b_ctr"] for m in all_metrics if m["b_ctr"] is not None]

    lines.append(f"| 指標 | 値 | パーセンタイル |")
    lines.append(f"|---|---|---|")
    lines.append(f"| 再生数 | {_fmt_int(target_metrics['views'])} | {_fmt(_percentile(target_metrics['views'], views_all))}% |")
    lines.append(f"| eng率 | {_fmt(target_metrics['eng_rate'])}% | {_fmt(_percentile(target_metrics['eng_rate'], eng_all))}% |")
    lines.append(f"| B-CTR | {_fmt(target_metrics['b_ctr'])}% | {_fmt(_percentile(target_metrics['b_ctr'], bctr_all))}% |")
    lines.append(f"| 平均視聴 | {_fmt(target_metrics['avg_view'], 0)}秒 | {_fmt(_percentile(target_metrics['avg_view'], avd_all))}% |")
    lines.append("")

    # analytics_overview 全フィールド
    lines.append("## Analytics Overview\n")
    ao = target.get("analytics_overview", {})
    for k, v in ao.items():
        lines.append(f"- {k}: {_fmt(v) if isinstance(v, float) else v}")
    lines.append("")

    # traffic_sources
    lines.append("## Traffic Sources\n")
    ts = target.get("traffic_sources", {})
    if ts:
        lines.append("| ソース | 再生数 | 割合(%) |")
        lines.append("|---|---|---|")
        for src, info in sorted(ts.items(), key=lambda x: x[1].get("views", 0), reverse=True):
            lines.append(f"| {src} | {_fmt_int(info.get('views'))} | {_fmt(info.get('percentage'))} |")
    lines.append("")

    # demographics
    lines.append("## Demographics\n")
    demo = target.get("demographics", {})
    breakdown = demo.get("breakdown", {})
    if breakdown:
        lines.append("| 年代 | 男性(%) | 女性(%) |")
        lines.append("|---|---|---|")
        for age, genders in sorted(breakdown.items()):
            lines.append(f"| {age} | {_fmt(genders.get('male'))} | {_fmt(genders.get('female'))} |")
    core = demo.get("core_target_45_64_percent")
    if core is not None:
        lines.append(f"\nコアターゲット(45-64): {_fmt(core)}%")
    lines.append("")

    # daily_data
    lines.append("## Daily Data\n")
    dd = target.get("daily_data", {})
    daily = dd.get("daily", [])
    if daily:
        lines.append("| Day | 日付 | 再生数 | 平均視聴(秒) | 登録者増 |")
        lines.append("|---|---|---|---|---|")
        for d in daily:
            lines.append(
                f"| {d.get('day_number')} | {d.get('date')} "
                f"| {_fmt_int(d.get('views'))} | {d.get('avg_view_duration', '-')} "
                f"| {d.get('subs_gained', '-')} |"
            )
    d1_d2 = dd.get("day1_to_day2_change_percent")
    if d1_d2 is not None:
        lines.append(f"\nD1→D2変化率: {_fmt(d1_d2)}%")
    lines.append("")

    # manual_data (browsing / related)
    lines.append("## Manual Data (主要トラフィック)\n")
    md = target.get("manual_data", {})
    for section_name in ["browsing", "related"]:
        sec = md.get(section_name, {})
        if sec:
            lines.append(f"### {section_name}")
            for k, v in sec.items():
                lines.append(f"- {k}: {v}")
            lines.append("")

    # human_scores
    hs = human_scores.get(target_vid, {})
    if hs:
        lines.append("## Human Scores\n")
        for k, v in hs.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    # script_analysis
    sa = target.get("script_analysis")
    if sa:
        lines.append("## Script Analysis\n")
        lines.append(f"- word_count: {sa.get('word_count')}")
        structure = sa.get("structure", {})
        for k, v in structure.items():
            lines.append(f"- {k}: {v}")
        hook = sa.get("hook_analysis", {})
        for k, v in hook.items():
            lines.append(f"- {k}: {v}")
        ca = sa.get("curiosity_alignment", {})
        for k, v in ca.items():
            lines.append(f"- {k}: {v}")
        gi = sa.get("gi_scores", {})
        for k, v in gi.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="動画データ要約ツール")
    parser.add_argument("--diff", metavar="VIDEO_ID", help="指定動画の詳細 + 全体比較")
    args = parser.parse_args()

    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    # 不変基盤の整合性チェック (W-23)
    validate_fundamentals()

    output_path = os.path.join(WORKSPACE_DIR, "data_summary.md")

    videos = load_all_videos()
    human_scores = load_human_scores()

    if args.diff:
        md_content = build_diff_summary(args.diff, videos, human_scores)
        print(f"[diff] 動画 {args.diff} の詳細を生成しました")
    else:
        md_content = build_full_summary(videos, human_scores)
        n_videos = len(videos)
        n_hit = sum(1 for v in videos
                    if (_deep(v, "metadata", "current_stats", "view_count") or 0) >= HIT_THRESHOLD)
        print(f"[summary] {n_videos}本の動画を要約しました (HIT: {n_hit}本, MISS: {n_videos - n_hit}本)")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[output] {output_path}")


if __name__ == "__main__":
    main()
