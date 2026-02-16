"""
台本分析JSON → human_scores.json 自動同期

実行方法:
  python scripts/step_sync_scores.py              # 全件同期
  python scripts/step_sync_scores.py --video-id VIDEO_ID  # 1件のみ
  python scripts/step_sync_scores.py --dry-run     # 実行せず差分表示

動作:
  1. data/input/scripts/*.json の gi_scores と ca_score を読み込む
  2. human_scores.json の対応エントリを更新（新規追加 or 上書き）
  3. GI_v3 = G1+G2+G3+G4+G6, GI_x_CA = GI_v3 × CA を自動計算

用途:
  台本分析JSONを作成した後に実行 → human_scores.json が自動更新される
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SCRIPTS_DIR, HUMAN_SCORES_FILE


def load_script_analysis(video_id):
    """1件の台本分析JSONを読み込む。"""
    path = os.path.join(SCRIPTS_DIR, f"{video_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_script_analyses():
    """data/input/scripts/*.json を全件読み込む。"""
    results = {}
    if not os.path.exists(SCRIPTS_DIR):
        return results
    for f in os.listdir(SCRIPTS_DIR):
        if f.endswith(".json"):
            vid = f.replace(".json", "")
            with open(os.path.join(SCRIPTS_DIR, f), "r", encoding="utf-8") as fh:
                results[vid] = json.load(fh)
    return results


def load_human_scores():
    """human_scores.json を読み込む。"""
    if not os.path.exists(HUMAN_SCORES_FILE):
        return {"description": "GI_v3スコアとCAスコア", "scoring_version": "v4.1", "scores": {}}
    with open(HUMAN_SCORES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_scores_from_analysis(analysis):
    """台本分析JSONからGI/CAスコアを抽出する。

    Returns:
        dict: {G1, G2, G3, G4, G6, GI_v3, CA, GI_x_CA, artist, source} or None
    """
    gi = analysis.get("gi_scores", {})
    ca_obj = analysis.get("curiosity_alignment", {})

    G1 = gi.get("G1_gossip", 0)
    G2 = gi.get("G2_curiosity", 0)
    G3 = gi.get("G3_emotional", 0)
    G4 = gi.get("G4_movie", 0)
    G6 = gi.get("G6_songs", 0)
    CA = ca_obj.get("ca_score", 0)

    # 全部0なら未記入と判断
    if G1 == 0 and G2 == 0 and G3 == 0 and G4 == 0 and G6 == 0:
        return None

    GI_v3 = G1 + G2 + G3 + G4 + G6
    GI_x_CA = GI_v3 * CA

    return {
        "artist": analysis.get("artist_name", ""),
        "source": "script_analysis",
        "G1": G1,
        "G2": G2,
        "G3": G3,
        "G4": G4,
        "G6": G6,
        "GI_v3": GI_v3,
        "CA": CA,
        "GI_x_CA": GI_x_CA,
        "sync_date": datetime.now().strftime("%Y-%m-%d"),
    }


def sync_scores(script_analyses, dry_run=False):
    """台本分析 → human_scores.json を同期する。

    Returns:
        (added, updated, skipped): 各件数
    """
    hs_data = load_human_scores()
    scores = hs_data.get("scores", {})

    added = 0
    updated = 0
    skipped = 0

    for vid, analysis in sorted(script_analyses.items()):
        extracted = extract_scores_from_analysis(analysis)
        if not extracted:
            print(f"  {vid}: スコア未記入 → スキップ")
            skipped += 1
            continue

        existing = scores.get(vid)
        if existing:
            # 既存エントリがquantitativeソースなら上書きしない
            if existing.get("source") == "quantitative":
                print(f"  {vid}: quantitativeソース(手動採点済み) → スキップ")
                skipped += 1
                continue
            # script_analysisソースなら更新
            action = "更新"
            updated += 1
        else:
            action = "追加"
            added += 1

        artist = extracted["artist"]
        gi = extracted["GI_v3"]
        ca = extracted["CA"]
        gi_x_ca = extracted["GI_x_CA"]
        print(f"  {vid} ({artist}): GI={gi} CA={ca} GIxCA={gi_x_ca} → {action}")

        if not dry_run:
            if existing:
                # 既存のエビデンスフィールドは保持
                for key in extracted:
                    existing[key] = extracted[key]
            else:
                scores[vid] = extracted

    if not dry_run and (added > 0 or updated > 0):
        hs_data["scores"] = scores
        with open(HUMAN_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(hs_data, f, ensure_ascii=False, indent=2)

    return added, updated, skipped


def main():
    parser = argparse.ArgumentParser(description="台本分析JSON → human_scores.json 同期")
    parser.add_argument("--video-id", type=str, help="1件のみ同期")
    parser.add_argument("--dry-run", action="store_true", help="実行せず差分表示")
    args = parser.parse_args()

    print("=" * 60)
    print("台本分析 → human_scores.json 同期")
    print("=" * 60)

    if args.video_id:
        analysis = load_script_analysis(args.video_id)
        if not analysis:
            print(f"エラー: {SCRIPTS_DIR}/{args.video_id}.json が見つかりません")
            sys.exit(1)
        analyses = {args.video_id: analysis}
    else:
        analyses = load_all_script_analyses()
        print(f"  台本分析JSON: {len(analyses)}件")

    if not analyses:
        print("  同期対象なし")
        return

    added, updated, skipped = sync_scores(analyses, args.dry_run)

    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"[DRY RUN] 追加予定: {added}件 | 更新予定: {updated}件 | スキップ: {skipped}件")
    else:
        print(f"完了: 追加 {added}件 | 更新 {updated}件 | スキップ {skipped}件")
    print("=" * 60)


if __name__ == "__main__":
    main()
