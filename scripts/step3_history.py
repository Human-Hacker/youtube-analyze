"""
Step 3 サブモジュール: 履歴保存
"""

import json
import os
import re
from datetime import datetime

from config import MODEL_FILE, ANALYSIS_HISTORY_DIR, HISTORY_INDEX


# スナップショット保持ポリシー
SNAPSHOT_POLICY = {
    "keep_latest": 5,           # 直近5バージョンは常に保持
    "keep_milestones": True,    # R²が0.05以上変化したバージョンはマイルストーンとして永久保持
    "auto_cleanup": True,       # save_history()実行時に自動でポリシーを適用
}


def get_next_version():
    """既存model.jsonからバージョンを読み、0.1インクリメント"""
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        try:
            return f"{float(old.get('version', '2.0')) + 0.1:.1f}"
        except (ValueError, TypeError):
            return "2.1"
    return "2.0"


def save_history_snapshot(model, report_text):
    """model.json と analysis_report.md を履歴フォルダに保存"""
    version = model["version"]
    date = datetime.now().strftime("%Y%m%d")
    snapshot_dir = os.path.join(ANALYSIS_HISTORY_DIR, f"v{version}_{date}")
    os.makedirs(snapshot_dir, exist_ok=True)

    with open(os.path.join(snapshot_dir, "model.json"), "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    with open(os.path.join(snapshot_dir, "analysis_report.md"), "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"  履歴保存: {snapshot_dir}")

    # 自動クリーンアップ
    if SNAPSHOT_POLICY["auto_cleanup"]:
        cleanup_old_snapshots()

    return snapshot_dir


def cleanup_old_snapshots():
    """保持ポリシーに基づき古いスナップショットを削除する。
    - 直近N件は常に保持
    - R²が0.05以上変化したバージョンはマイルストーンとして永久保持
    - 削除対象はディレクトリのみ削除（index.mdの履歴テーブルには残る）
    """
    if not os.path.exists(ANALYSIS_HISTORY_DIR):
        return

    # スナップショットディレクトリを列挙（v{X.X}_{date} 形式）
    snapshot_dirs = []
    for name in os.listdir(ANALYSIS_HISTORY_DIR):
        full_path = os.path.join(ANALYSIS_HISTORY_DIR, name)
        if os.path.isdir(full_path) and name.startswith("v"):
            snapshot_dirs.append((name, full_path))

    if len(snapshot_dirs) <= SNAPSHOT_POLICY["keep_latest"]:
        return  # 保持上限以下なら何もしない

    # バージョン番号でソート（新しい順）
    def _version_key(item):
        name = item[0]
        match = re.match(r'v(\d+\.?\d*)_', name)
        return float(match.group(1)) if match else 0

    snapshot_dirs.sort(key=_version_key, reverse=True)

    # 直近N件を保護
    keep_latest = set()
    for i, (name, path) in enumerate(snapshot_dirs):
        if i < SNAPSHOT_POLICY["keep_latest"]:
            keep_latest.add(name)

    # マイルストーン検出（R²が0.05以上変化したバージョン）
    milestones = set()
    if SNAPSHOT_POLICY["keep_milestones"]:
        prev_r2 = None
        for name, path in reversed(snapshot_dirs):  # 古い順に処理
            model_path = os.path.join(path, "model.json")
            if not os.path.exists(model_path):
                continue
            try:
                with open(model_path, "r", encoding="utf-8") as f:
                    m = json.load(f)
                r2 = m.get("gi_ca_model", {}).get("correlations", {}).get("R_squared")
                if r2 is not None:
                    if prev_r2 is not None and abs(r2 - prev_r2) >= 0.05:
                        milestones.add(name)
                    prev_r2 = r2
            except (json.JSONDecodeError, KeyError):
                continue

    # 削除実行
    import shutil
    deleted = 0
    for name, path in snapshot_dirs:
        if name not in keep_latest and name not in milestones:
            shutil.rmtree(path)
            deleted += 1

    if deleted > 0:
        print(f"  スナップショットクリーンアップ: {deleted}件削除（保持: 直近{SNAPSHOT_POLICY['keep_latest']}件 + マイルストーン{len(milestones)}件）")


def update_history_index(model):
    """index.md に1行サマリを追記"""
    os.makedirs(ANALYSIS_HISTORY_DIR, exist_ok=True)

    version = model["version"]
    date = datetime.now().strftime("%Y-%m-%d")
    gi_ca = model.get("gi_ca_model", {})
    corr = gi_ca.get("correlations", {})
    r2 = corr.get("R_squared", "?")
    acc = gi_ca.get("threshold_16_accuracy", "?")
    n = model.get("dataset_size", 0)
    hits = model["classification"]["hits"]

    summary = (
        f"| v{version} | {date} | {n}本(HIT:{hits}) | "
        f"R2={r2}, 閾値16精度={acc}% |"
    )

    # index.md が無ければヘッダ付きで作成
    if not os.path.exists(HISTORY_INDEX):
        header = (
            "# 分析履歴インデックス\n\n"
            "## バージョン履歴\n\n"
            "| バージョン | 日付 | データ | サマリ |\n"
            "|-----------|------|--------|--------|\n"
        )
        with open(HISTORY_INDEX, "w", encoding="utf-8") as f:
            f.write(header + summary + "\n")
    else:
        # 「## 未解決問題」の直前に挿入（なければ末尾に追記）
        with open(HISTORY_INDEX, "r", encoding="utf-8") as f:
            content = f.read()
        marker = "\n## 未解決問題"
        if marker in content:
            content = content.replace(marker, summary + "\n" + marker)
        else:
            content = content.rstrip() + "\n" + summary + "\n"
        with open(HISTORY_INDEX, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"  履歴インデックス更新: {HISTORY_INDEX}")
