"""全スクリプト共通のデータ読み込みモジュール"""

import json
import os

from config import (
    VIDEOS_DIR, SCRIPTS_DIR, DATA_DIR, HUMAN_SCORES_FILE,
    ANALYSIS_HISTORY_DIR, INSIGHTS_FILE,
    HIT_THRESHOLD, PRIMARY_ANALYSIS_WINDOW, SECONDARY_ANALYSIS_WINDOW, DATA_CATEGORIES,
)


def load_all_videos():
    """data/videos/*.json を全件読み込み、リストで返す。
    各動画に _video_id を付加し、data/scripts/*.json の台本分析データを結合する。
    """
    videos = []
    if not os.path.exists(VIDEOS_DIR):
        return videos

    # 台本データを先に読み込み (video_id -> script_analysis)
    scripts = {}
    if os.path.exists(SCRIPTS_DIR):
        for f in os.listdir(SCRIPTS_DIR):
            if f.endswith(".json"):
                vid = f.replace(".json", "")
                with open(os.path.join(SCRIPTS_DIR, f), "r", encoding="utf-8") as fh:
                    scripts[vid] = json.load(fh)

    for f in sorted(os.listdir(VIDEOS_DIR)):
        if f.endswith(".json"):
            with open(os.path.join(VIDEOS_DIR, f), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            vid = f.replace(".json", "")
            data["_video_id"] = vid
            # script_analysis が None または未設定の場合、scripts/*.json から結合
            if not data.get("script_analysis") and vid in scripts:
                data["script_analysis"] = scripts[vid]
            videos.append(data)
    return videos


def load_video_index():
    """data/video_index.json を読み込み、video_id -> エントリの辞書を返す"""
    path = os.path.join(DATA_DIR, "video_index.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        idx = json.load(f)
    return {v["video_id"]: v for v in idx.get("videos", [])}


def load_human_scores():
    """data/human_scores.json を読み込み、scores 辞書を返す"""
    if not os.path.exists(HUMAN_SCORES_FILE):
        return {}
    with open(HUMAN_SCORES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("scores", {})


def load_golden_theory():
    """data/golden_theory.json を読み込む。存在しなければ空の初期構造を返す"""
    path = os.path.join(DATA_DIR, "golden_theory.json")
    if not os.path.exists(path):
        return {
            "version": "1.0",
            "last_updated": None,
            "last_cycle": 0,
            "principles": [],
            "checklist": [],
            "rejected_conditions": []
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_golden_theory(data):
    """data/golden_theory.json を書き込む"""
    path = os.path.join(DATA_DIR, "golden_theory.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_insights():
    """insights.md のYAML frontmatterと本文を分離して返す"""
    if not os.path.exists(INSIGHTS_FILE):
        return {}, ""
    with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    # YAML frontmatter パース (--- で囲まれた部分)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = {}
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    v = v.strip().strip('"')
                    try:
                        v = int(v)
                    except ValueError:
                        pass
                    frontmatter[k.strip()] = v
            return frontmatter, parts[2].strip()
    return {}, content


def save_insights(frontmatter, body):
    """insights.md を書き込む"""
    os.makedirs(os.path.dirname(INSIGHTS_FILE), exist_ok=True)
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, str):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def load_fundamentals():
    """analysis_fundamentals.json を読み込み、返す。存在しない場合はエラー終了。"""
    path = os.path.join(DATA_DIR, "analysis_fundamentals.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "FATAL: data/analysis_fundamentals.json が見つかりません。"
            "分析の不変基盤ファイルが必要です。"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_fundamentals():
    """
    analysis_fundamentals.json と config.py の整合性を検証する。
    不一致があれば即座にエラー終了（サイレントな不整合を防止）。
    """
    fundamentals = load_fundamentals()
    errors = []

    # HIT閾値チェック
    fund_threshold = fundamentals["hit_miss_definition"]["hit_threshold"]
    if fund_threshold != HIT_THRESHOLD:
        errors.append(
            f"HIT_THRESHOLD不一致: "
            f"fundamentals={fund_threshold}, config={HIT_THRESHOLD}"
        )

    # データ範囲チェック
    if fundamentals["data_ranges"]["primary"]["window"] == "24hours":
        if PRIMARY_ANALYSIS_WINDOW != 1:
            errors.append(
                f"PRIMARY_ANALYSIS_WINDOW不一致: "
                f"fundamentals=24hours(1日), config={PRIMARY_ANALYSIS_WINDOW}"
            )
    if fundamentals["data_ranges"]["secondary"]["window"] == "7days":
        if SECONDARY_ANALYSIS_WINDOW != 7:
            errors.append(
                f"SECONDARY_ANALYSIS_WINDOW不一致: "
                f"fundamentals=7days, config={SECONDARY_ANALYSIS_WINDOW}"
            )

    # カテゴリチェック
    fund_categories = set(fundamentals["metrics"].keys())
    # fundamentals uses "scripts", config uses "script" - normalize
    config_categories = set()
    for k in DATA_CATEGORIES.keys():
        config_categories.add("scripts" if k == "script" else k)
    if fund_categories != config_categories:
        errors.append(f"DATA_CATEGORIES不一致: fundamentals={fund_categories} vs config={config_categories}")

    if errors:
        raise ValueError(
            "FATAL: analysis_fundamentals.json と config.py の整合性エラー:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    return fundamentals
