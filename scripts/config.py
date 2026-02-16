"""
共通設定ファイル（全スクリプトから参照される）
"""

import os

# ファイルパス
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
SCRIPTS_DIR = os.path.join(DATA_DIR, "scripts")
MODEL_FILE = os.path.join(DATA_DIR, "model.json")
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
WORKSPACE_DIR = os.path.join(DATA_DIR, "workspace")
ANALYSIS_HISTORY_DIR = os.path.join(DATA_DIR, "analysis_history")
HISTORY_INDEX = os.path.join(ANALYSIS_HISTORY_DIR, "index.md")
INSIGHTS_FILE = os.path.join(ANALYSIS_HISTORY_DIR, "insights.md")
HUMAN_SCORES_FILE = os.path.join(DATA_DIR, "human_scores.json")

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
