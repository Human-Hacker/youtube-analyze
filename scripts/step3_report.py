"""
Step 3 サブモジュール: レポート生成
"""

from config import HIT_THRESHOLD


# ===========================================================================
#  レポート生成
# ===========================================================================

def generate_report(model, records):
    L = []
    _a = L.append

    _a("> **このファイルの読み手**: Agent C / Agent E / 開発者（デバッグ用）")
    _a("> **一般向けの分析結論**: `data/analysis_conclusion.md` を参照してください\n")
    _a("# ウタヨミ 動画分析レポート v2.0")
    _a(f"\n生成日: {model['built_at'][:10]} / データ: {model['dataset_size']}本")
    _a(
        f"成功（{HIT_THRESHOLD:,}回以上）: {model['classification']['hits']}本 / "
        f"不振: {model['classification']['misses']}本"
    )

    # --- 0. 分析方針 ---
    _a("\n## 0. 分析方針")
    _a(
        "本レポートは「第一原理アプローチ」に基づく。\n"
        "1. **原因と結果を分離**: 総再生数・IMP数は「結果」。CTR・視聴深度・エンゲージメント率が「原因」\n"
        "2. **人間評価GI×CAスコア使用**: AI自己評価(17-24の狭い範囲)は不採用。人間評価(5-23)を使用\n"
        "3. **対数スケール相関**: 再生数はべき乗分布 → log₁₀(再生数)で相関を取る\n"
        "4. **3段階フィルター**: アルゴリズムの評価プロセスを再現"
    )

    # --- 1. GI×CA モデル ---
    gi_ca = model.get("gi_ca_model", {})
    _a("\n## 1. GI×CAモデル（人間評価スコア）")
    _a(f"\n評価済み: {gi_ca.get('scored_count', 0)}/{gi_ca.get('total_count', 0)}本")

    corr = gi_ca.get("correlations", {})
    if corr:
        _a("\n| 指標 | 値 |")
        _a("|------|-----|")
        for k, v in corr.items():
            _a(f"| {k} | {v if v is not None else 'N/A'} |")
        _a(f"\n閾値16判定精度: {gi_ca.get('threshold_16_accuracy', 'N/A')}%")

    details = gi_ca.get("details", [])
    if details:
        _a("\n| アーティスト | 再生数 | GI_v3 | CA | GI×CA | 予測 | 実際 | 正誤 |")
        _a("|------------|--------|-------|-----|-------|------|------|------|")
        for d in details:
            pred = "HIT" if d["predicted_hit"] else "-"
            actual = "HIT" if d["is_hit"] else "-"
            ok = "OK" if d["correct"] else "NG"
            _a(
                f"| {d['artist']} | {d['views']:,} | {d['gi_v3']} | "
                f"{d['ca']} | {d['gi_x_ca']} | {pred} | {actual} | {ok} |"
            )

    unscored = [r for r in records if r.get("score_source") == "none"]
    if unscored:
        _a(f"\n### 未評価動画（{len(unscored)}本 → 人間評価が必要）")
        _a("| アーティスト | 再生数 | AI_GI | AI_CA |")
        _a("|------------|--------|-------|-------|")
        for r in sorted(unscored, key=lambda x: x["views"], reverse=True):
            _a(
                f"| {r['artist']} | {r['views']:,} | "
                f"{r.get('ai_gi_total', '-')} | {r.get('ai_ca', '-')} |"
            )

    # --- 2. 3段階フィルター ---
    fdata = model.get("three_stage_filter", [])
    _a("\n## 2. 3段階フィルター分析")
    _a(
        "- **F1 (初動CTR)**: ブラウジングCTR >= 4.0%\n"
        "- **F2 (Day1→Day2)**: 変化率 > -20%\n"
        "- **F3 (深度×反応)**: 平均視聴 >= 300秒 AND エンゲージメント率 >= 0.8%"
    )

    if fdata:
        _a("\n| アーティスト | 再生数 | F1(CTR) | F2(D1→D2) | F3(深度×反応) | 判定 | 脱落 |")
        _a("|------------|--------|---------|-----------|-------------|------|------|")
        for f in sorted(fdata, key=lambda x: x["views"], reverse=True):
            f1_s = (
                f"{'OK' if f['f1_pass'] else 'NG'} {f['f1_ctr']:.1f}%"
                if f["f1_ctr"] is not None else "\u2014"
            )
            f2_s = (
                f"{'OK' if f['f2_pass'] else 'NG'} {f['f2_change']:+.1f}%"
                if f["f2_change"] is not None else "\u2014"
            )
            dur = f.get("f3_duration")
            eng = f.get("f3_engagement")
            f3_s = (
                f"{'OK' if f['f3_pass'] else 'NG'} {dur:.0f}s/{eng:.2f}%"
                if dur is not None and eng is not None else "\u2014"
            )
            hit = "HIT" if f["is_hit"] else "-"
            fail = f.get("first_fail") or ""
            _a(
                f"| {f['artist']} | {f['views']:,} | {f1_s} | "
                f"{f2_s} | {f3_s} | {hit} | {fail} |"
            )

        # 精度マトリクス
        with_data = [f for f in fdata if f["f1_pass"] is not None]
        if with_data:
            ph = sum(1 for f in with_data if f["passed_all"] and f["is_hit"])
            pm = sum(1 for f in with_data if f["passed_all"] and not f["is_hit"])
            fh = sum(1 for f in with_data if not f["passed_all"] and f["is_hit"])
            fm = sum(1 for f in with_data if not f["passed_all"] and not f["is_hit"])
            _a("\n### フィルター精度")
            _a("| | 実際HIT | 実際MISS |")
            _a("|---|---------|----------|")
            _a(f"| 全通過 | {ph} | {pm} |")
            _a(f"| 脱落あり | {fh} | {fm} |")
            total = ph + pm + fh + fm
            if total > 0:
                acc = (ph + fm) / total * 100
                _a(f"\n精度: {acc:.1f}% ({ph+fm}/{total})")
                if acc < 70:
                    _a(
                        "\n> ⚠️ 3段階フィルターの精度は統計的に有意な判別力とは言えない。\n"
                        "> 黄金理論のチェックリスト（golden_theory.json）の方が信頼性が高い。"
                    )

    # --- 3. 原因指標の相関 ---
    correlations = model.get("correlations", {})
    _a("\n## 3. 原因指標と log(再生数) の相関")
    _a("\n> 原因指標 = コントロール可能な変数。結果指標は別セクションに分離")

    cause = correlations.get("cause_metrics", {})
    if cause:
        _a("\n| 指標 | r(log) | r(raw) | n | 強さ |")
        _a("|------|--------|--------|---|------|")
        for name, data in cause.items():
            rl = data["r_log_views"]
            rr = data["r_raw_views"]
            s = "強" if abs(rl) >= 0.6 else "中" if abs(rl) >= 0.3 else "弱"
            _a(f"| {name} | {rl:+.3f} | {rr:+.3f} | {data['n']} | {s} |")

    _a("\n### 結果指標（参考: これらは「伸びた結果」であり予測因子ではない）")
    effect = correlations.get("effect_metrics", {})
    if effect:
        _a("\n| 指標 | r(log) | r(raw) | n |")
        _a("|------|--------|--------|---|")
        for name, data in effect.items():
            _a(
                f"| {name} | {data['r_log_views']:+.3f} | "
                f"{data['r_raw_views']:+.3f} | {data['n']} |"
            )

    # --- 4. パターン分析 ---
    patterns = model.get("patterns", {})
    _a("\n## 4. 台本構造パターン分析")

    for p in patterns.get("comparisons", []):
        _a(f"\n### {p['name']}")
        _a(
            f"- あり: {p['with_count']}本, "
            f"平均{p['with_avg']:,}回 (中央値{p['with_median']:,})"
        )
        _a(
            f"- なし: {p['without_count']}本, "
            f"平均{p['without_avg']:,}回 (中央値{p['without_median']:,})"
        )
        _a(f"- 倍率: {p['ratio']}倍 / log差: {p['log_diff']}")

    fraud = patterns.get("hook_fraud_cases", [])
    if fraud:
        _a(f"\n### フック詐欺（{len(fraud)}本）")
        for f in fraud:
            d2 = (
                f"{f['day1_day2']:+.1f}%"
                if f["day1_day2"] is not None else "N/A"
            )
            _a(f"- {f['artist']}: {f['views']:,}回 (Day1→Day2: {d2})")

    # --- 5. グループ比較 ---
    _a("\n## 5. 伸びた vs 伸びてない 比較")
    for label, stats in model.get("group_comparisons", {}).items():
        _a(f"\n### {label}")
        _a("| 指標 | 値 |")
        _a("|------|-----|")
        for k, v in stats.items():
            if isinstance(v, float):
                _a(f"| {k} | {v:,.2f} |")
            else:
                _a(f"| {k} | {v:,} |")

    # --- 6. ベンチマーク ---
    _a("\n## 6. ベンチマーク")
    for tier, data in model.get("benchmarks", {}).items():
        _a(f"\n### {tier} ({data['count']}本, 平均{data['avg_views']:,}回)")
        for v in data["videos"]:
            gi = (
                f"GI×CA={v['gi_x_ca']}"
                if v.get("gi_x_ca") is not None else "未評価"
            )
            _a(
                f"- {v['artist']} {v['views']:,}回 "
                f"({gi}, eng={v['engagement_rate']:.2f}%)"
            )

    # --- 7. 全動画一覧 ---
    _a("\n## 7. 全動画一覧")
    _a("| # | アーティスト | 再生数 | GI×CA | eng率 | D1→D2 | B-CTR | 判定 |")
    _a("|---|------------|--------|-------|-------|-------|-------|------|")
    for i, r in enumerate(
        sorted(records, key=lambda x: x["views"], reverse=True), 1
    ):
        gi_ca_s = f"{r['gi_x_ca']}" if r.get("gi_x_ca") is not None else "-"
        eng = f"{r['engagement_rate']:.2f}"
        d12 = (
            f"{r['day1_day2_change']:+.1f}"
            if r.get("day1_day2_change") is not None else "-"
        )
        bctr = (
            f"{r['browsing_ctr']:.1f}"
            if r.get("browsing_ctr") is not None else "-"
        )
        hit = "HIT" if r["is_hit"] else "-"
        _a(
            f"| {i} | {r['artist']} | {r['views']:,} | "
            f"{gi_ca_s} | {eng} | {d12} | {bctr} | {hit} |"
        )

    # --- 8. VPD正規化分析（経過時間の交絡除去） ---
    _a("\n## 8. VPD正規化分析（経過時間の交絡除去）")
    _a(
        "\n> **VPD (Views Per Day)**: 総再生数 ÷ 経過日数。\n"
        "> チャンネル成長に伴い、古い動画ほど再生数が蓄積されるバイアスを除去する。"
    )

    vpd_corr = correlations.get("vpd_correlations", {})
    if vpd_corr:
        _a("\n### 原因指標: log(再生数) vs log(VPD) 相関比較")
        _a("\n| 指標 | r vs log(再生数) | r vs log(VPD) | 交絡判定 |")
        _a("|------|-----------------|---------------|---------|")

        for name, data in cause.items():
            vpd_data = vpd_corr.get(name, {})
            r_lv = data["r_log_views"]
            r_vpd = vpd_data.get("r_log_vpd", None)
            if r_vpd is not None:
                # 交絡判定: log(再生数)で中以上だがVPDで弱い場合は交絡
                if abs(r_lv) >= 0.3 and abs(r_vpd) < 0.15:
                    judge = "交絡（見せかけ）"
                elif abs(r_vpd) >= 0.3:
                    judge = "真の相関"
                elif abs(r_lv) < 0.2 and abs(r_vpd) < 0.2:
                    judge = "無関係"
                else:
                    judge = "弱い"
                _a(f"| {name} | {r_lv:+.3f} | {r_vpd:+.3f} | {judge} |")
            else:
                _a(f"| {name} | {r_lv:+.3f} | N/A | — |")

        # 経過日数の交絡
        age_data = vpd_corr.get("経過日数", {})
        if age_data:
            _a(f"\n- 経過日数 vs log(再生数): r={age_data.get('r_log_views', 'N/A')}")
            _a(f"- 経過日数 vs log(VPD): r={age_data.get('r_log_vpd', 'N/A')}")
            _a("- → 経過日数は再生数と正の相関。VPD正規化により交絡を除去")

    # VPDランキング
    vpd_records = [r for r in records if r.get("views_per_day") is not None]
    if vpd_records:
        vpd_sorted = sorted(vpd_records, key=lambda r: r["views_per_day"], reverse=True)
        _a("\n### VPDランキング（日あたり再生数）")
        _a("\n| # | アーティスト | 再生数 | 経過日数 | VPD | GI×CA | 判定 |")
        _a("|---|------------|--------|---------|-----|-------|------|")
        for i, r in enumerate(vpd_sorted, 1):
            gi_ca_s = f"{r['gi_x_ca']}" if r.get("gi_x_ca") is not None else "-"
            hit = "HIT" if r["is_hit"] else "-"
            _a(
                f"| {i} | {r['artist']} | {r['views']:,} | "
                f"{r['age_days']} | {r['views_per_day']:,.0f} | "
                f"{gi_ca_s} | {hit} |"
            )

    # --- 9. 核心的インサイト ---
    _a("\n## 9. 核心的インサイト")
    _a(
        "\n### 第一原理から導かれる因果関係\n"
        "```\n"
        "アーティスト選定(GI) × 切り口(CA) → 初動CTR(F1) → Day2成長(F2)\n"
        "    → 視聴深度×エンゲージメント(F3) → アルゴリズム増幅 → 総再生数\n"
        "```\n"
        "\n### 重要な発見\n"
        "1. **経過時間が最大の交絡変数**: 古い動画ほど再生数蓄積 → VPD正規化が必須\n"
        "2. **GI×CAは足切りとして機能**: 全動画がGI×CA≧15で素材品質は十分。差は他の要因\n"
        "3. **VPD正規化後、文字数のみが真の正の相関**: 台本の情報密度が日あたり再生数に寄与\n"
        "4. **MV挿入数・メディア数はVPD正規化後に消失**: 経過時間との交絡（見せかけの相関）\n"
        "5. **GI_v3（素材の質）はVPD正規化後も弱い相関**: アーティスト選定は一定の影響あり\n"
        "\n### アクション\n"
        "- **制作前**: GI×CA >= 40 のアーティスト×切り口を推奨（全体の底上げ済み）\n"
        "- **台本**: 文字数（情報密度）を重視。4要素完備 + フック詐欺回避\n"
        "- **制作**: MV2箇所以上挿入（直接的効果は不明だが視聴体験に寄与）\n"
        "- **分析**: 総再生数ではなくVPD（日あたり再生数）で動画パフォーマンスを評価"
    )

    # --- 10. データ品質 ---
    _a("\n## 10. データ品質")
    human_n = sum(1 for r in records if r.get("score_source") == "human")
    ai_cal_n = sum(1 for r in records if r.get("score_source") == "ai_calibrated")
    quant_n = sum(1 for r in records if r.get("score_source") == "quantitative")
    kb_n = sum(1 for r in records if r.get("score_source") == "knowledge_based")
    none_n = sum(1 for r in records if r.get("score_source") == "none")
    manual_n = sum(1 for r in records if r.get("total_impressions") is not None)
    _a(f"- 定量評価GI×CA（Web検索ベース）: {quant_n}/{len(records)}本")
    _a(f"- 人間評価GI×CA: {human_n}/{len(records)}本")
    _a(f"- AI較正評価GI×CA: {ai_cal_n}/{len(records)}本")
    _a(f"- 知識ベース評価: {kb_n}/{len(records)}本")
    _a(f"- 未評価: {none_n}本")
    _a(f"- 手動データ（IMP/CTR）: {manual_n}/{len(records)}本")

    return "\n".join(L)
