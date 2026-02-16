"""
Step 1: 動画データ取得 & 手動CSVマージ

実行方法:
  python scripts/step1_fetch.py                  # 全動画API取得のみ
  python scripts/step1_fetch.py VIDEO_ID         # 単体取得
  python scripts/step1_fetch.py --merge          # API取得後にCSVマージも実行
  python scripts/step1_fetch.py --merge-only     # マージのみ（API取得スキップ）

動作:
  [API取得]
  1. チャンネル内の全長編動画（60秒超）を自動検出
  2. 各動画のアナリティクスデータを取得
  3. data/videos/{video_id}.json として保存
  4. data/video_index.json に全動画一覧を保存

  [CSVマージ] (--merge / --merge-only)
  1. data/video_index.json の各動画の manual_data_path を読み取り
  2. traffic_source.csv と viewer_segments.csv を列名ベースでパース
  3. data/videos/{video_id}.json の manual_data フィールドにマージ
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from googleapiclient.discovery import build
from auth import get_credentials
from config import VIDEOS_DIR, DATA_DIR, INPUT_DIR, DAYS_AFTER_PUBLISH, CHANNEL_ID


# ============================================================
#  1動画のデータ取得（step7_pdca.py からも呼ばれる）
# ============================================================

def fetch_single_video(video_id, creds=None):
    """1動画の全アナリティクスデータを取得してJSONで保存"""
    if creds is None:
        creds = get_credentials()
    if not creds:
        return None

    youtube = build("youtube", "v3", credentials=creds)
    analytics = build("youtubeAnalytics", "v2", credentials=creds)

    print(f"\n  動画データ取得中: {video_id}")

    # メタデータ
    metadata = _get_metadata(youtube, video_id)
    if not metadata:
        return None
    print(f"    タイトル: {metadata['title']}")

    publish_date = metadata["published_at"][:10]

    # 各種データ取得
    overview = _get_overview(analytics, video_id, publish_date)
    traffic = _get_traffic(analytics, video_id, publish_date)
    demographics = _get_demographics(analytics, video_id, publish_date)
    daily = _get_daily(analytics, video_id, publish_date)

    result = {
        "fetch_timestamp": datetime.now().isoformat(),
        "metadata": metadata,
        "analytics_overview": overview,
        "traffic_sources": traffic,
        "demographics": demographics,
        "daily_data": daily,
        "manual_data": None,
        "script_analysis": None,
    }

    # 保存
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    filepath = os.path.join(VIDEOS_DIR, f"{video_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    views = metadata["current_stats"]["view_count"]
    print(f"    再生数: {views:,} / 平均視聴率: {overview.get('average_view_percentage', 0):.1f}%" if overview else f"    再生数: {views:,}")
    print(f"    保存: {filepath}")
    return result


# ============================================================
#  全動画一括取得
# ============================================================

def fetch_all(force_refetch=False):
    """全長編動画のデータを一括取得"""
    creds = get_credentials()
    if not creds:
        return

    youtube = build("youtube", "v3", credentials=creds)

    # チャンネル情報
    resp = youtube.channels().list(part="snippet,statistics", id=CHANNEL_ID).execute()
    channel_id = resp["items"][0]["id"]
    channel_name = resp["items"][0]["snippet"]["title"]

    print(f"\nチャンネル: {channel_name} ({channel_id})")

    # 全動画ID取得
    print("全動画を取得中...")
    all_ids = _get_all_ids(youtube, channel_id)
    print(f"  全動画数: {len(all_ids)}")

    # ショート除外
    long_videos = _filter_long(youtube, all_ids)
    print(f"  長編動画数: {len(long_videos)}")

    # 一覧表示
    print(f"\n{'#':>3} {'公開日':<12} {'時間':>6} タイトル")
    print("-" * 70)
    for i, v in enumerate(long_videos, 1):
        dur = v["duration_seconds"] // 60
        print(f"{i:>3} {v['published_at'][:10]:<12} {dur:>4}分  {v['title'][:45]}")

    # 取得済みスキップ（force_refetchの場合は既存もすべて再取得）
    existing = set()
    if os.path.exists(VIDEOS_DIR):
        for f in os.listdir(VIDEOS_DIR):
            if f.endswith(".json"):
                existing.add(f.replace(".json", ""))

    if force_refetch:
        # 既存データがある動画のみ再取得（新規は通常モードで取得）
        to_fetch = [v for v in long_videos if v["video_id"] in existing]
        if not to_fetch:
            to_fetch = list(long_videos)
        print(f"\n  強制再取得モード: {len(to_fetch)}本を再取得します")
    else:
        to_fetch = [v for v in long_videos if v["video_id"] not in existing]
        skipped = len(long_videos) - len(to_fetch)

        if skipped > 0:
            print(f"\n  {skipped}本は取得済み → スキップ")
        if not to_fetch:
            print("\n全動画のデータは取得済みです。")
            _save_index(long_videos)
            return

    print(f"\n{len(to_fetch)}本のデータを取得します。")
    print("（API制限対策で各動画間に2秒の待機あり）\n")
    if not force_refetch:
        input("Enterキーで開始 > ")

    success = 0
    errors = []
    for i, v in enumerate(to_fetch, 1):
        print(f"\n[{i}/{len(to_fetch)}] {v['title'][:40]}...")
        try:
            result = fetch_single_video(v["video_id"], creds)
            if result:
                success += 1
            else:
                errors.append(v["video_id"])
        except Exception as e:
            print(f"    エラー: {e}")
            errors.append(v["video_id"])

        if i < len(to_fetch):
            time.sleep(2)

    print(f"\n{'='*50}")
    print(f"取得完了: {success}/{len(to_fetch)}")
    if errors:
        print(f"失敗({len(errors)}): {errors}")

    _save_index(long_videos)


# ============================================================
#  API取得 内部関数
# ============================================================

def _get_metadata(youtube, video_id):
    resp = youtube.videos().list(part="snippet,statistics,contentDetails", id=video_id).execute()
    if not resp["items"]:
        print(f"    動画 {video_id} が見つかりません")
        return None
    item = resp["items"][0]
    s, st, c = item["snippet"], item["statistics"], item["contentDetails"]
    dur = _parse_duration(c["duration"])
    return {
        "video_id": video_id,
        "title": s["title"],
        "published_at": s["publishedAt"],
        "description": s.get("description", "")[:500],
        "tags": s.get("tags", []),
        "duration_seconds": dur,
        "duration_display": f"{dur//3600}:{(dur%3600)//60:02d}:{dur%60:02d}" if dur >= 3600 else f"{dur//60}:{dur%60:02d}",
        "current_stats": {
            "view_count": int(st.get("viewCount", 0)),
            "like_count": int(st.get("likeCount", 0)),
            "comment_count": int(st.get("commentCount", 0)),
        },
        "thumbnail_url": s["thumbnails"].get("maxres", s["thumbnails"].get("high", {})).get("url", ""),
    }


def _get_overview(analytics, video_id, publish_date):
    try:
        resp = analytics.reports().query(
            ids="channel==MINE", startDate=publish_date,
            endDate=datetime.now().strftime("%Y-%m-%d"),
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost",
            filters=f"video=={video_id}",
        ).execute()
        if not resp.get("rows"):
            return None
        r = resp["rows"][0]
        return {
            "views": r[0], "estimated_minutes_watched": r[1],
            "average_view_duration_seconds": r[2], "average_view_percentage": r[3],
            "likes": r[4], "comments": r[5], "shares": r[6],
            "subscribers_gained": r[7], "subscribers_lost": r[8],
        }
    except Exception as e:
        print(f"    overview取得エラー: {e}")
        return None


def _get_traffic(analytics, video_id, publish_date):
    try:
        resp = analytics.reports().query(
            ids="channel==MINE", startDate=publish_date,
            endDate=datetime.now().strftime("%Y-%m-%d"),
            metrics="views,estimatedMinutesWatched",
            dimensions="insightTrafficSourceType",
            filters=f"video=={video_id}", sort="-views",
        ).execute()
        sources = {}
        total = 0
        for row in (resp.get("rows") or []):
            sources[row[0]] = {"views": row[1], "estimated_minutes_watched": row[2]}
            total += row[1]
        for s in sources.values():
            s["percentage"] = round(s["views"] / total * 100, 1) if total > 0 else 0
        return sources
    except Exception as e:
        print(f"    traffic取得エラー: {e}")
        return {}


def _get_demographics(analytics, video_id, publish_date):
    try:
        resp = analytics.reports().query(
            ids="channel==MINE", startDate=publish_date,
            endDate=datetime.now().strftime("%Y-%m-%d"),
            metrics="viewerPercentage", dimensions="ageGroup,gender",
            filters=f"video=={video_id}", sort="ageGroup",
        ).execute()
        demo = {}
        for row in (resp.get("rows") or []):
            demo.setdefault(row[0], {})[row[1]] = row[2]
        core = sum(
            pct for age in ["age45-54", "age55-64"]
            for pct in demo.get(age, {}).values()
        )
        return {"breakdown": demo, "core_target_45_64_percent": round(core, 1)}
    except Exception as e:
        print(f"    demographics取得エラー: {e}")
        return {"breakdown": {}, "core_target_45_64_percent": 0}


def _get_daily(analytics, video_id, publish_date, days=DAYS_AFTER_PUBLISH):
    try:
        pub = datetime.strptime(publish_date, "%Y-%m-%d")
        end = min(pub + timedelta(days=days - 1), datetime.now())
        end_str = end.strftime("%Y-%m-%d")

        # 基本の日別データ
        resp = analytics.reports().query(
            ids="channel==MINE", startDate=publish_date, endDate=end_str,
            metrics="views,averageViewDuration,subscribersGained",
            dimensions="day", filters=f"video=={video_id}", sort="day",
        ).execute()
        daily = []
        for i, row in enumerate(resp.get("rows") or [], 1):
            daily.append({
                "day_number": i, "date": row[0], "views": row[1],
                "avg_view_duration": row[2], "subs_gained": row[3],
                "traffic_breakdown": {},
            })

        # Day別×トラフィックソース別クロス集計
        try:
            traffic_resp = analytics.reports().query(
                ids="channel==MINE", startDate=publish_date, endDate=end_str,
                metrics="views,estimatedMinutesWatched",
                dimensions="day,insightTrafficSourceType",
                filters=f"video=={video_id}", sort="day",
            ).execute()
            # トラフィックソース名の正規化マッピング
            source_map = {
                "ADVERTISING": "OTHER", "ANNOTATION": "OTHER", "CAMPAIGN_CARD": "OTHER",
                "END_SCREEN": "OTHER", "EXT_URL": "OTHER", "NOTIFICATION": "OTHER",
                "NO_LINK_EMBEDDED": "OTHER", "NO_LINK_OTHER": "OTHER",
                "PLAYLIST": "OTHER", "PROMOTED": "OTHER", "SHORTS": "OTHER",
                "SUBSCRIBER": "SUBSCRIBER", "RELATED_VIDEO": "RELATED",
                "YT_SEARCH": "SEARCH", "YT_CHANNEL": "OTHER", "YT_OTHER_PAGE": "OTHER",
            }
            for row in (traffic_resp.get("rows") or []):
                date_str, source_raw = row[0], row[1]
                views, minutes = row[2], row[3]
                source = source_map.get(source_raw, "OTHER")
                # "BROWSE" はAPIでは "NO_LINK_OTHER" に含まれることがあるが、
                # 明確な "BROWSE" ソースがある場合はそれを使う
                if "BROWSE" in source_raw.upper():
                    source = "BROWSE"
                # 対応する日を探す
                for d in daily:
                    if d["date"] == date_str:
                        tb = d["traffic_breakdown"]
                        if source not in tb:
                            tb[source] = {"views": 0, "minutes_watched": 0.0}
                        tb[source]["views"] += views
                        tb[source]["minutes_watched"] += round(minutes, 1)
                        break
        except Exception as e:
            print(f"    traffic×day クロス集計エラー（スキップ）: {e}")

        # 関連動画ソース詳細（どの動画から流入したか）
        related_video_sources = []
        try:
            related_resp = analytics.reports().query(
                ids="channel==MINE", startDate=publish_date, endDate=end_str,
                metrics="views,estimatedMinutesWatched",
                dimensions="insightTrafficSourceDetail",
                filters=f"video=={video_id};insightTrafficSourceType==RELATED_VIDEO",
                sort="-views",
                maxResults=25,
            ).execute()
            for row in (related_resp.get("rows") or []):
                related_video_sources.append({
                    "source_video_id": row[0],
                    "source_video_title": "",  # APIはIDのみ返す。タイトルは別途取得が必要
                    "views": row[1],
                    "estimated_minutes_watched": round(row[2], 1),
                })
        except Exception as e:
            print(f"    関連動画ソース詳細取得エラー（スキップ）: {e}")

        change = None
        if len(daily) >= 2 and daily[0]["views"] > 0:
            change = round((daily[1]["views"] - daily[0]["views"]) / daily[0]["views"] * 100, 1)
        return {
            "daily": daily,
            "day1_to_day2_change_percent": change,
            "related_video_sources": related_video_sources,
        }
    except Exception as e:
        print(f"    daily取得エラー: {e}")
        return {"daily": [], "day1_to_day2_change_percent": None}


def _get_all_ids(youtube, channel_id):
    ids = []
    token = None
    while True:
        resp = youtube.search().list(
            part="id", channelId=channel_id, type="video",
            order="date", maxResults=50, pageToken=token,
        ).execute()
        ids.extend(item["id"]["videoId"] for item in resp["items"])
        token = resp.get("nextPageToken")
        if not token:
            break
    return ids


def _filter_long(youtube, video_ids, min_sec=60):
    longs = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        resp = youtube.videos().list(part="contentDetails,snippet", id=",".join(batch)).execute()
        for item in resp["items"]:
            dur = _parse_duration(item["contentDetails"]["duration"])
            if dur > min_sec:
                longs.append({
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "published_at": item["snippet"]["publishedAt"],
                    "duration_seconds": dur,
                })
    longs.sort(key=lambda x: x["published_at"])
    return longs


def _save_index(long_videos):
    path = os.path.join(INPUT_DIR, "video_index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now().isoformat(), "total_count": len(long_videos), "videos": long_videos}, f, ensure_ascii=False, indent=2)
    print(f"動画インデックス保存: {path}")


def _parse_duration(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0)


# ============================================================
#  手動CSVマージ
# ============================================================

def parse_time_to_seconds(time_str):
    """'H:MM:SS' or 'M:SS' 形式を秒数に変換"""
    if not time_str or time_str.strip() == "":
        return None
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return None


def safe_int(val):
    if not val or str(val).strip() == "":
        return None
    return int(str(val).replace(",", "").strip())


def safe_float(val):
    if not val or str(val).strip() == "":
        return None
    return float(str(val).replace("%", "").replace(",", "").strip())


def parse_traffic_source(csv_path):
    """traffic_source.csv をパースし、ソース別のデータを返す"""
    if not os.path.exists(csv_path):
        return None

    result = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row.get("トラフィック ソース", "").strip()
            if not source:
                continue
            result[source] = {
                "impressions": safe_int(row.get("インプレッション数")),
                "ctr": safe_float(row.get("インプレッションのクリック率 (%)")),
                "views": safe_int(row.get("視聴回数")),
                "avg_view_time": row.get("平均視聴時間", "").strip() or None,
                "avg_view_time_seconds": parse_time_to_seconds(row.get("平均視聴時間")),
                "watch_hours": safe_float(row.get("総再生時間（単位: 時間）")),
            }
    return result


def parse_viewer_segments(csv_path):
    """viewer_segments.csv をパースし、セグメント別のデータを返す"""
    if not os.path.exists(csv_path):
        return None

    result = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            segment = row.get("視聴行動別の視聴者区分", "").strip()
            if not segment:
                continue
            result[segment] = {
                "impressions": safe_int(row.get("インプレッション数")),
                "ctr": safe_float(row.get("インプレッションのクリック率 (%)")),
                "views": safe_int(row.get("視聴回数")),
                "avg_view_time": row.get("平均視聴時間", "").strip() or None,
                "avg_view_time_seconds": parse_time_to_seconds(row.get("平均視聴時間")),
                "watch_hours": safe_float(row.get("総再生時間（単位: 時間）")),
            }
    return result


def build_manual_data(traffic, segments):
    """traffic_source と viewer_segments から manual_data を構築"""
    total_traffic = traffic.get("合計", {}) if traffic else {}
    browsing = traffic.get("ブラウジング機能", {}) if traffic else {}
    related = traffic.get("関連動画", {}) if traffic else {}

    total_segments = segments.get("合計", {}) if segments else {}
    core = segments.get("コアな視聴者", {}) if segments else {}
    light = segments.get("ライトな視聴者", {}) if segments else {}
    new = segments.get("新しい視聴者数", {}) if segments else {}

    total_views = total_traffic.get("views") or total_segments.get("views")

    # ブラウジング比率
    browsing_views = browsing.get("views")
    browsing_pct = round(browsing_views / total_views * 100, 1) if browsing_views and total_views else None

    # 関連動画比率
    related_views = related.get("views")
    related_pct = round(related_views / total_views * 100, 1) if related_views and total_views else None

    # 視聴者セグメント比率
    core_views = core.get("views")
    light_views = light.get("views")
    new_views = new.get("views")

    core_pct = round(core_views / total_views * 100, 1) if core_views and total_views else None
    light_pct = round(light_views / total_views * 100, 1) if light_views and total_views else None
    new_pct = round(new_views / total_views * 100, 1) if new_views and total_views else None

    return {
        "total_impressions": total_traffic.get("impressions"),
        "total_ctr": total_traffic.get("ctr"),
        "total_views": total_views,
        "total_watch_hours": total_traffic.get("watch_hours"),
        "total_avg_view_time": total_traffic.get("avg_view_time"),
        "total_avg_view_time_seconds": total_traffic.get("avg_view_time_seconds"),
        "browsing": {
            "impressions": browsing.get("impressions"),
            "ctr": browsing.get("ctr"),
            "views": browsing_views,
            "watch_hours": browsing.get("watch_hours"),
            "avg_view_time": browsing.get("avg_view_time"),
            "avg_view_time_seconds": browsing.get("avg_view_time_seconds"),
            "views_percent": browsing_pct,
        },
        "related": {
            "impressions": related.get("impressions"),
            "ctr": related.get("ctr"),
            "views": related_views,
            "watch_hours": related.get("watch_hours"),
            "avg_view_time": related.get("avg_view_time"),
            "avg_view_time_seconds": related.get("avg_view_time_seconds"),
            "views_percent": related_pct,
        },
        "traffic_sources_all": traffic,
        "viewer_segments": {
            "core": {
                "views": core_views,
                "impressions": core.get("impressions"),
                "ctr": core.get("ctr"),
                "watch_hours": core.get("watch_hours"),
                "avg_view_time": core.get("avg_view_time"),
                "avg_view_time_seconds": core.get("avg_view_time_seconds"),
                "views_percent": core_pct,
            },
            "light": {
                "views": light_views,
                "impressions": light.get("impressions"),
                "ctr": light.get("ctr"),
                "watch_hours": light.get("watch_hours"),
                "avg_view_time": light.get("avg_view_time"),
                "avg_view_time_seconds": light.get("avg_view_time_seconds"),
                "views_percent": light_pct,
            },
            "new": {
                "views": new_views,
                "impressions": new.get("impressions"),
                "ctr": new.get("ctr"),
                "watch_hours": new.get("watch_hours"),
                "avg_view_time": new.get("avg_view_time"),
                "avg_view_time_seconds": new.get("avg_view_time_seconds"),
                "views_percent": new_pct,
            },
        },
    }


def merge():
    """video_index.json の manual_data_path から CSV を読み取り、各動画JSONにマージ"""
    index_path = os.path.join(INPUT_DIR, "video_index.json")
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    merged = 0
    errors = []

    for video in index["videos"]:
        vid = video["video_id"]
        artist = video.get("artist_name", vid)
        manual_path = video.get("manual_data_path")

        if not manual_path:
            errors.append(f"  manual_data_pathなし: {artist} ({vid})")
            continue

        traffic_csv = os.path.join(manual_path, "traffic_source.csv")
        segments_csv = os.path.join(manual_path, "viewer_segments.csv")

        if not os.path.exists(traffic_csv) and not os.path.exists(segments_csv):
            errors.append(f"  CSVなし: {artist} ({manual_path})")
            continue

        json_path = os.path.join(VIDEOS_DIR, f"{vid}.json")
        if not os.path.exists(json_path):
            errors.append(f"  JSONなし: {artist} ({vid})")
            continue

        with open(json_path, "r", encoding="utf-8") as jf:
            data = json.load(jf)

        traffic = parse_traffic_source(traffic_csv)
        segments = parse_viewer_segments(segments_csv)
        data["manual_data"] = build_manual_data(traffic, segments)

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(data, jf, ensure_ascii=False, indent=2)

        merged += 1
        print(f"  {artist}")

    print(f"\n{'='*50}")
    print(f"マージ完了: {merged}件")
    if errors:
        print(f"エラー: {len(errors)}件")
        for e in errors:
            print(e)


# ============================================================
#  メイン
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 1: 動画データ取得 & 手動CSVマージ")
    parser.add_argument("video_id", nargs="?", help="単体取得する動画ID")
    parser.add_argument("--merge", action="store_true", help="API取得後にCSVマージも実行")
    parser.add_argument("--merge-only", action="store_true", help="マージのみ（API取得スキップ）")
    parser.add_argument("--force-refetch", action="store_true",
                        help="全動画を強制再取得（Day別×トラフィックソース クロス集計を含む）")
    args = parser.parse_args()

    print("=" * 50)
    print("Step 1: 動画データ取得")
    print("=" * 50)

    if args.merge_only:
        # マージのみ
        print("\n手動データのマージを実行します。")
        merge()
    elif args.force_refetch:
        # 全動画を強制再取得
        if args.video_id:
            print(f"\n1動画を強制再取得: {args.video_id}")
            fetch_single_video(args.video_id)
        else:
            print("\n全動画を強制再取得（クロス集計含む）")
            fetch_all(force_refetch=True)
        if args.merge:
            print(f"\n{'='*50}")
            print("手動データのマージを実行します。")
            print("=" * 50)
            merge()
    elif args.video_id:
        # 単体取得
        print(f"\n1動画のみ取得: {args.video_id}")
        fetch_single_video(args.video_id)
    else:
        # 全動画一括取得
        fetch_all()
        if args.merge:
            print(f"\n{'='*50}")
            print("手動データのマージを実行します。")
            print("=" * 50)
            merge()
