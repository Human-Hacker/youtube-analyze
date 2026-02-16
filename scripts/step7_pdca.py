"""
Step 7: 新動画のPDCA評価 → モデル更新

実行方法:
  python scripts/step7_pdca.py VIDEO_ID
  python scripts/step7_pdca.py VIDEO_ID --skip-fetch
  python scripts/step7_pdca.py VIDEO_ID --skip-fetch --update-model

動作:
  1. 新動画のアナリティクスデータを取得（--skip-fetch で省略可）
  2. 現在のモデルと比較 → 予測 vs 実績を評価
  3. PDCAレポートを data/output/ に出力
  4. --update-model を付けるとモデルを再構築（step2_build_model経由）

運用サイクル:
  新動画公開 → Day7で実行 → レポート確認
  → 手動CSV更新 + 台本分析 → --update-model でモデル更新
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VIDEOS_DIR, DATA_DIR, MODEL_FILE, HIT_THRESHOLD, OUTPUT_DIR
from common.data_loader import validate_fundamentals
from step1_fetch import fetch_single_video
from step2_build_model import build_and_save


def load_model():
    if not os.path.exists(MODEL_FILE):
        print("❌ model.json がありません。step2_build_model.py を先に実行してください。")
        return None
    with open(MODEL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(video_data, model):
    """予測 vs 実績を評価"""
    views = video_data["metadata"]["current_stats"]["view_count"]
    title = video_data["metadata"]["title"]
    artist = (video_data.get("manual_data") or {}).get("artist_name", title[:20])

    # ティア判定
    if views >= 500000:
        tier = "S_500k+"
    elif views >= 200000:
        tier = "A_200k-500k"
    elif views >= 100000:
        tier = "B_100k-200k"
    else:
        tier = "C_under_100k"

    # トラフィック分析
    traffic = video_data.get("traffic_sources", {})
    browse_pct = traffic.get("BROWSE", {}).get("percentage", 0)
    related_pct = traffic.get("RELATED_VIDEO", {}).get("percentage", 0)

    # Day変化
    daily = video_data.get("daily_data", {})
    day_change = daily.get("day1_to_day2_change_percent")

    return {
        "video_id": video_data["metadata"]["video_id"],
        "artist_name": artist,
        "title": title,
        "actual_views": views,
        "actual_tier": tier,
        "is_hit": views >= HIT_THRESHOLD,
        "browsing_percent": browse_pct,
        "related_percent": related_pct,
        "day2_change": day_change,
        "hook_fraud_detected": day_change is not None and day_change <= -50,
        "evaluation_date": datetime.now().isoformat(),
    }


def generate_pdca_report(ev, video_data, model):
    """PDCAレポート生成"""
    o = video_data.get("analytics_overview", {})
    corrs = model.get("correlations", {})

    lines = [
        f"# PDCA評価: {ev['artist_name']}",
        f"\n評価日: {ev['evaluation_date'][:10]}",
        f"\n## 実績",
        f"\n| 項目 | 値 |", "|------|-----|",
        f"| 再生数 | {ev['actual_views']:,} |",
        f"| ティア | {ev['actual_tier']} |",
        f"| 判定 | {'🔥 ヒット' if ev['is_hit'] else '📉 不振'} |",
        f"| ブラウジング | {ev['browsing_percent']}% |",
        f"| 関連動画 | {ev['related_percent']}% |",
    ]

    if ev.get("day2_change") is not None:
        flag = " ⚠️フック詐欺疑い" if ev["hook_fraud_detected"] else ""
        lines.append(f"| Day1→Day2 | {ev['day2_change']:+.1f}%{flag} |")

    # モデル指標との比較
    if o:
        lines.extend([
            f"\n## モデル指標との比較",
            f"\n| 指標 | この動画 | モデル相関 |", "|------|---------|----------|",
        ])
        checks = [
            ("全体CTR", f"{o.get('impression_ctr', 0):.2f}%"),
            ("平均視聴時間(秒)", f"{o.get('average_view_duration_seconds', 0):.0f}"),
            ("インプレッション数", f"{o.get('impressions', 0):,}"),
        ]
        for name, display in checks:
            r = corrs.get(name, "N/A")
            lines.append(f"| {name} | {display} | r={r} |")

    # グループ比較
    comp = model.get("group_comparisons", {})
    if ev["is_hit"] and "伸びた動画" in comp:
        avg = comp["伸びた動画"].get("平均再生数", 0)
        lines.append(f"\n伸びた動画の平均({avg:,})に対して {ev['actual_views']/avg*100:.0f}%" if avg else "")
    elif not ev["is_hit"] and "伸びてない動画" in comp:
        avg = comp["伸びてない動画"].get("平均再生数", 0)
        lines.append(f"\n伸びてない動画の平均({avg:,})に対して {ev['actual_views']/avg*100:.0f}%" if avg else "")

    lines.extend([
        f"\n## 学びとアクション",
        f"\n以下をClaude Codeで分析してください:",
        f"- モデルの予測は正しかったか？",
        f"- 予測と乖離した原因は何か？",
        f"- モデルに追加すべき新パターンはあるか？",
        f"- 閾値や係数を修正すべきか？",
        f"\n### 更新チェックリスト",
        f"- [ ] model.json の更新が必要",
        f"- [ ] selection.md の基準値を修正",
        f"- [ ] レビュープロンプトのチェックリストを修正",
    ])

    return "\n".join(lines)


def update_model():
    """新データを含めてモデルを再構築（step2_build_model経由）"""
    print("\nモデル再構築中...")
    model, _ = build_and_save()
    return model


def main():
    parser = argparse.ArgumentParser(description="Step 4: PDCA評価・モデル更新")
    parser.add_argument("video_id", help="評価する動画ID")
    parser.add_argument("--skip-fetch", action="store_true", help="データ取得をスキップ")
    parser.add_argument("--update-model", action="store_true", help="モデルも再構築")
    args = parser.parse_args()

    print("=" * 50)
    print(f"Step 4: PDCA評価 - {args.video_id}")
    print("=" * 50)

    # 不変基盤の整合性チェック (W-23)
    validate_fundamentals()

    model = load_model()
    if not model:
        return

    # データ取得
    if not args.skip_fetch:
        print("\n[1/3] データ取得中...")
        fetch_single_video(args.video_id)
    else:
        print("\n[1/3] データ取得スキップ")

    # データ読み込み
    json_path = os.path.join(VIDEOS_DIR, f"{args.video_id}.json")
    if not os.path.exists(json_path):
        print(f"❌ {json_path} がありません")
        return
    with open(json_path, "r", encoding="utf-8") as f:
        video_data = json.load(f)

    # 評価
    print("[2/3] PDCA評価中...")
    ev = evaluate(video_data, model)

    # レポート
    report = generate_pdca_report(ev, video_data, model)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rpath = os.path.join(OUTPUT_DIR, f"pdca_{args.video_id}_{datetime.now().strftime('%Y%m%d')}.md")
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  ✅ PDCAレポート: {rpath}")

    # ログ
    log_path = os.path.join(DATA_DIR, "pdca_log.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # モデル更新
    if args.update_model:
        print("\n[3/3] モデル更新中...")
        update_model()
    else:
        print(f"\n[3/3] モデル更新スキップ")
        print(f"  → 更新する場合: python scripts/step7_pdca.py {args.video_id} --skip-fetch --update-model")

    # サマリー
    print(f"\n{'='*50}")
    print(f"完了: {ev['artist_name']}")
    print(f"  {ev['actual_views']:,}回 → {ev['actual_tier']} {'🔥' if ev['is_hit'] else '📉'}")
    if ev.get("hook_fraud_detected"):
        print(f"  ⚠️ フック詐欺疑い（Day2: {ev['day2_change']:+.1f}%）")
    print("=" * 50)


if __name__ == "__main__":
    main()
