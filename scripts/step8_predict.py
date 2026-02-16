"""
Step 8: 事前予測の一括記録

実行方法:
  python scripts/step8_predict.py                    # next_*_artists.md から全件一括インポート
  python scripts/step8_predict.py --dry-run           # 実行せず結果だけ表示
  python scripts/step8_predict.py --artist "名前" --G1 5 --G6 5 --G_ST 3 --G_YT 5  # 1件追加

動作:
  1. data/output/next_*_artists.md のMarkdown表をパース
  2. 各アーティストに golden_theory ルール（P1/P3/C13/C14）を適用
  3. data/predictions.jsonl に全件一括追記（既存アーティストはスキップ）
  4. data/output/predictions/ に予測カード(Markdown)を出力

前提条件（重要）:
  全スコア（G1/G6/G_ST/G_YT）は prompts/scoring_criteria.md v1.0 の
  定量基準に基づきWeb検索で算出済みであること。概算・推定は禁止。
  詳細: commands/analyze-pipeline.md モードC参照。

運用:
  next_*_artists.md 作成後に1回実行 → 全予測がロックされる
  → 動画公開 → Day7でstep7実行 → 自動照合
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PREDICTIONS_FILE, PREDICTIONS_DIR, MODEL_FILE, OUTPUT_DIR
from common.data_loader import validate_fundamentals


NEXT_ARTISTS_FILE = os.path.join(OUTPUT_DIR, "next_26_artists.md")


def parse_next_artists_md(filepath):
    """next_26_artists.md のMarkdown表をパースし、アーティスト一覧を返す。

    Returns:
        list of dict: [{"artist": "Whitney Houston", "G1": 5, "G6": 5, "G_ST": 3, "G_YT": 5}, ...]
    """
    if not os.path.exists(filepath):
        print(f"エラー: {filepath} が見つかりません")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    artists = []
    # 表の行をパース: | # | **名前** | G1 | G6 | G1+G6 | G_ST | G_YT | 理由 |
    pattern = re.compile(
        r"\|\s*\d+\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
    )
    for m in pattern.finditer(content):
        artists.append({
            "artist": m.group(1).strip(),
            "G1": int(m.group(2)),
            "G6": int(m.group(3)),
            "G_ST": int(m.group(4)),
            "G_YT": int(m.group(5)),
        })

    return artists


def load_existing_predictions():
    """predictions.jsonl から既存の予測アーティスト名セットを返す。"""
    names = set()
    if not os.path.exists(PREDICTIONS_FILE):
        return names
    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("type") == "verification":
                continue
            names.add(rec.get("artist_name", ""))
    return names


def apply_golden_rules(G1, G6, G_ST, G_YT):
    """golden_theory のルール(P1/P3)を適用し、予測結果を返す。

    ランク判定:
      S: G1+G6>=8 AND G_ST>=3 (実績100% HIT, 6/6)
      A: G1+G6>=8 AND G_ST<=2 AND G_YT>=5 (実績67%)
      B: G_ST>=5 (G1+G6不問)
      C: 上記いずれも不該当

    HIT/MISS判定 (C13): G1+G6>=8 OR G_ST>=5 → HIT, else MISS
    """
    g1_g6 = G1 + G6
    meets_c13 = g1_g6 >= 8 or G_ST >= 5
    meets_c14 = g1_g6 >= 8 and G_ST >= 3

    if g1_g6 >= 8 and G_ST >= 3:
        rank = "S"
        confidence = "high"
    elif g1_g6 >= 8 and G_ST <= 2 and G_YT >= 5:
        rank = "A"
        confidence = "medium"
    elif G_ST >= 5:
        rank = "B"
        confidence = "medium"
    else:
        rank = "C"
        confidence = "low"

    hit_or_miss = "HIT" if meets_c13 else "MISS"

    reasoning_parts = []
    if meets_c14:
        reasoning_parts.append(
            f"G1+G6={g1_g6}>=8 AND G_ST={G_ST}>=3 -> Sランク(過去6/6 HIT)"
        )
    elif g1_g6 >= 8:
        reasoning_parts.append(f"G1+G6={g1_g6}>=8 -> C13充足(精度83.3%)")
        if G_ST <= 2:
            reasoning_parts.append(
                f"G_ST={G_ST}<=2 -> 偽陽性リスクあり(マドンナ/オアシス型)"
            )
    elif G_ST >= 5:
        reasoning_parts.append(
            f"G_ST={G_ST}>=5 -> C13充足(EdSheeran型: ストリーミング駆動)"
        )
    else:
        reasoning_parts.append(
            f"G1+G6={g1_g6}<8 AND G_ST={G_ST}<5 -> C13不充足"
        )
        if G1 <= 2 or G6 <= 2:
            reasoning_parts.append("C12レッドフラグ: G1<=2 OR G6<=2")

    confidence_labels = {"high": "高", "medium": "中", "low": "低"}
    reasoning_parts.append(f"信頼度: {confidence_labels[confidence]}")

    return {
        "G1_plus_G6": g1_g6,
        "meets_C13": meets_c13,
        "meets_C14_srank": meets_c14,
        "meets_G_ST_5": G_ST >= 5,
        "hit_or_miss": hit_or_miss,
        "rank": rank,
        "confidence": confidence,
        "reasoning": "。".join(reasoning_parts),
    }


def build_prediction_record(artist, G1, G6, G_ST, G_YT, rules, note=None):
    """予測レコード(JSONL 1行分)を組み立てる。"""
    sanitized = re.sub(r"[^a-zA-Z0-9\u3040-\u9fff]", "_", artist).strip("_")
    sanitized = re.sub(r"_+", "_", sanitized)
    date_str = datetime.now().strftime("%Y%m%d")
    prediction_id = f"pred_{sanitized}_{date_str}"

    model_version = None
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, "r", encoding="utf-8") as f:
            model_version = json.load(f).get("version")

    return {
        "prediction_id": prediction_id,
        "artist_name": artist,
        "prediction_date": datetime.now().isoformat(),
        "scores": {"G1": G1, "G6": G6, "G_ST": G_ST, "G_YT": G_YT},
        "derived": {
            "G1_plus_G6": rules["G1_plus_G6"],
            "meets_C13": rules["meets_C13"],
            "meets_C14_srank": rules["meets_C14_srank"],
            "meets_G_ST_5": rules["meets_G_ST_5"],
        },
        "prediction": {
            "hit_or_miss": rules["hit_or_miss"],
            "rank": rules["rank"],
            "confidence": rules["confidence"],
            "reasoning": rules["reasoning"],
        },
        "note": note,
        "status": "pending",
        "video_id": None,
        "model_version": model_version,
    }


def generate_prediction_card(record):
    """人間可読なMarkdown予測カードを生成。"""
    s = record["scores"]
    d = record["derived"]
    p = record["prediction"]
    date_str = record["prediction_date"][:10]
    mv = record.get("model_version") or "N/A"

    yn = lambda b: "YES" if b else "NO"
    conf_label = {"high": "高", "medium": "中", "low": "低"}[p["confidence"]]

    lines = [
        f"# 事前予測: {record['artist_name']}",
        f"\n予測日: {date_str} | モデル: v{mv}",
        f"\n## スコア",
        f"\n| 指標 | 値 |",
        "|------|-----|",
        f"| G1（ゴシップ露出度） | {s['G1']} |",
        f"| G6（楽曲知名度） | {s['G6']} |",
        f"| G1+G6 | {d['G1_plus_G6']} |",
        f"| G_ST（ストリーミング需要） | {s['G_ST']} |",
        f"| G_YT（YouTube解説需要） | {s['G_YT']} |",
        f"\n## 判定",
        f"\n| 項目 | 結果 |",
        "|------|------|",
        f"| 予測 | {p['hit_or_miss']} |",
        f"| ランク | {p['rank']} |",
        f"| 信頼度 | {conf_label} |",
        f"| C13充足 (G1+G6>=8 OR G_ST>=5) | {yn(d['meets_C13'])} |",
        f"| C14 Sランク (G1+G6>=8 AND G_ST>=3) | {yn(d['meets_C14_srank'])} |",
        f"\n## 根拠",
        f"\n{p['reasoning']}",
    ]

    if record.get("note"):
        lines.extend([f"\n## 備考", f"\n{record['note']}"])

    return "\n".join(lines) + "\n"


def save_prediction(record):
    """predictions.jsonl に1行追記。"""
    os.makedirs(os.path.dirname(PREDICTIONS_FILE), exist_ok=True)
    with open(PREDICTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_prediction_card(record):
    """予測カードMarkdownを保存。"""
    card = generate_prediction_card(record)
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    sanitized = re.sub(r"[^a-zA-Z0-9\u3040-\u9fff]", "_", record["artist_name"]).strip("_")
    sanitized = re.sub(r"_+", "_", sanitized)
    card_path = os.path.join(PREDICTIONS_DIR, f"pred_{sanitized}.md")
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(card)
    return card_path


def main():
    parser = argparse.ArgumentParser(description="Step 8: 事前予測の一括記録")
    parser.add_argument("--dry-run", action="store_true", help="実行せず結果だけ表示")
    # 1件追加用（補充候補など）
    parser.add_argument("--artist", type=str, help="アーティスト名（1件追加時）")
    parser.add_argument("--G1", type=int, help="ゴシップ露出度 (1-5)")
    parser.add_argument("--G6", type=int, help="楽曲知名度 (1-5)")
    parser.add_argument("--G_ST", type=int, help="ストリーミング需要 (1-5)")
    parser.add_argument("--G_YT", type=int, help="YouTube解説需要 (1-5)")
    parser.add_argument("--note", type=str, default=None, help="補足理由")
    args = parser.parse_args()

    print("=" * 60)
    print("Step 8: 事前予測の記録")
    print("=" * 60)

    validate_fundamentals()

    # モード判定: 1件追加 or 一括インポート
    if args.artist:
        # 1件追加モード
        for name, val in [("G1", args.G1), ("G6", args.G6), ("G_ST", args.G_ST), ("G_YT", args.G_YT)]:
            if val is None:
                print(f"エラー: --artist 指定時は --{name} も必須です")
                sys.exit(1)
            if not 1 <= val <= 5:
                print(f"エラー: {name}={val} は範囲外です（1-5）")
                sys.exit(1)
        artists = [{"artist": args.artist, "G1": args.G1, "G6": args.G6, "G_ST": args.G_ST, "G_YT": args.G_YT}]
        print(f"\n1件追加モード: {args.artist}")
    else:
        # 一括インポートモード
        print(f"\n一括インポート: {NEXT_ARTISTS_FILE}")
        artists = parse_next_artists_md(NEXT_ARTISTS_FILE)
        print(f"  パース結果: {len(artists)}件")

    # 既存予測をチェック
    existing = load_existing_predictions()
    if existing:
        print(f"  既存予測: {len(existing)}件")

    # 処理
    added = 0
    skipped = 0
    results = []

    for a in artists:
        if a["artist"] in existing:
            skipped += 1
            continue

        rules = apply_golden_rules(a["G1"], a["G6"], a["G_ST"], a["G_YT"])
        record = build_prediction_record(
            a["artist"], a["G1"], a["G6"], a["G_ST"], a["G_YT"], rules,
            args.note if args.artist else None
        )
        results.append(record)

        conf_label = {"high": "高", "medium": "中", "low": "低"}[rules["confidence"]]
        mark = "HIT" if rules["hit_or_miss"] == "HIT" else "MISS"
        print(f"  {a['artist']:30s} -> {mark} | {rules['rank']}ランク | 信頼度:{conf_label}")

        if not args.dry_run:
            save_prediction(record)
            save_prediction_card(record)
            added += 1

    # サマリー
    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"[DRY RUN] 追加予定: {len(results)}件 | スキップ: {skipped}件")
    else:
        print(f"完了: 追加 {added}件 | スキップ(既存) {skipped}件")
        if added > 0:
            print(f"  予測ログ: {PREDICTIONS_FILE}")
            print(f"  予測カード: {PREDICTIONS_DIR}/")

    # HIT/MISS内訳
    hit_count = sum(1 for r in results if r["prediction"]["hit_or_miss"] == "HIT")
    miss_count = len(results) - hit_count
    if results:
        print(f"  予測内訳: HIT {hit_count}件 / MISS {miss_count}件")
    print("=" * 60)


if __name__ == "__main__":
    main()
