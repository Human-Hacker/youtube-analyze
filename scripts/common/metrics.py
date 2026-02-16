"""全スクリプト共通の指標計算モジュール"""

import math
from config import HIT_THRESHOLD


def deep(d, *keys):
    """ネストされた辞書を安全に辿る"""
    for k in keys:
        if not d or not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def avg(vals):
    """平均値。空なら0"""
    return sum(vals) / len(vals) if vals else 0


def avg_or_none(vals):
    """平均値。空ならNone"""
    return sum(vals) / len(vals) if vals else None


def median(vals):
    """中央値。空なら0"""
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def median_or_none(vals):
    """中央値。空ならNone"""
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def pearson(x, y):
    """ピアソン相関係数"""
    n = len(x)
    if n < 3:
        return 0
    mx, my = sum(x) / n, sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return cov / (sx * sy) if sx * sy > 0 else 0


def classify_hit_miss(view_count):
    """HIT/MISS判定"""
    return view_count >= HIT_THRESHOLD


def fmt(val, decimals=1):
    """数値フォーマット。Noneなら'-'"""
    if val is None:
        return "-"
    if isinstance(val, float):
        return f"{val:.{decimals}f}"
    return str(val)


def fmt_int(val):
    """整数をカンマ区切り"""
    if val is None:
        return "-"
    return f"{val:,}"
