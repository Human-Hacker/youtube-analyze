"""
共通設定ファイル（全スクリプトから参照される）
"""

import os

# ファイルパス
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_DIR = os.path.join(DATA_DIR, "input")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
VIDEOS_DIR = os.path.join(INPUT_DIR, "videos")
SCRIPTS_DIR = os.path.join(INPUT_DIR, "scripts")
HUMAN_SCORES_FILE = os.path.join(INPUT_DIR, "human_scores.json")
MODEL_FILE = os.path.join(OUTPUT_DIR, "model.json")
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
HISTORY_INDEX = os.path.join(HISTORY_DIR, "index.md")
INSIGHTS_FILE = os.path.join(OUTPUT_DIR, "insights.md")
PREDICTIONS_FILE = os.path.join(DATA_DIR, "predictions.jsonl")
PREDICTIONS_DIR = os.path.join(OUTPUT_DIR, "predictions")

# youtube-long パイプライン接続 (W-22)
YOUTUBE_LONG_DIR = os.path.join(os.path.dirname(BASE_DIR), "youtube-long")

# selection_report.mdはテンプレートではなく、各アーティストのプロジェクトフォルダに生成される
# 後方互換: SELECTION_REPORT_TEMPLATE は非推奨。get_selection_report_path() を使用すること
SELECTION_REPORT_TEMPLATE = None  # 旧パスは無効（M57）


def get_selection_report_path(artist_name):
    """アーティスト名からselection_report.mdのパスを構築する"""
    return os.path.join(YOUTUBE_LONG_DIR, "projects", artist_name, "selection_report.md")


def find_all_selection_reports():
    """youtube-long/projects/配下の全selection_report.mdを走査して返す"""
    projects_dir = os.path.join(YOUTUBE_LONG_DIR, "projects")
    results = []
    if not os.path.exists(projects_dir):
        return results
    for entry in os.listdir(projects_dir):
        report_path = os.path.join(projects_dir, entry, "selection_report.md")
        if os.path.isfile(report_path):
            results.append((entry, report_path))
    return results

# OAuth スコープ
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube",
]

# チャンネルID（ブランドアカウント対応：mine=True の代わりに直接指定）
CHANNEL_ID = "UClSjp1IEwVrFcf0AXhquxyw"

# 分析パラメータ
DAYS_AFTER_PUBLISH = 7   # 公開後何日分の日別データを取得するか
HIT_THRESHOLD = 150000   # 「伸びた」と判定する再生数の閾値（旧: 100000）

# データ分析範囲
PRIMARY_ANALYSIS_WINDOW = 1    # 最重要: 最初の24時間（Day1）
SECONDARY_ANALYSIS_WINDOW = 7  # 重要: 最初の7日間
# 7日後に伸び始めた動画は、視聴回数が急増したポイントまで分析範囲を拡張する

# 指標分類
DATA_CATEGORIES = {
    "analytics": "アナリティクスデータ（YouTube API + Studio）",
    "script": "台本データ（台本構造分析JSON）",
    "meta": "メタデータ（人間評価・コンテキスト情報）"
}
