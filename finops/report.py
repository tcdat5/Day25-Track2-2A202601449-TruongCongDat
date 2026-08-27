"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly",
                 extensions: dict | None = None,
                 analysis: dict | None = None) -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — GPU Cost Optimization Report",
        "",
        f"**Period:** {period}  ",
        f"**Baseline spend:** ${baseline_usd:,.0f}  ",
        f"**Optimized spend:** ${optimized_usd:,.0f}  ",
        f"**Projected savings:** ${savings:,.0f}  (**{pct:.0f}%**)",
        "",
        "## Savings by lever",
        "",
        "| Lever | Savings (USD) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if analysis:
        lines += [
            "",
            "## 1. Baseline vs. Optimized",
            "",
            f"Baseline là **${baseline_usd:,.0f}/tháng**, optimized còn **${optimized_usd:,.0f}/tháng**. "
            f"NimbusAI tiết kiệm **${savings:,.0f}/tháng**, tương đương **{pct:.1f}%**.",
            f"Riêng inference giảm từ **${analysis.get('baseline_per_m', 0):.3f}** xuống "
            f"**${analysis.get('optimized_per_m', 0):.3f}/1M-token**, giảm "
            f"**{analysis.get('inference_savings_pct', 0):.1f}%**.",
            "",
            "## 2. Phân tích từng đòn bẩy",
            "",
            f"Đòn bẩy đóng góp lớn nhất là **{analysis.get('largest_lever', 'n/a')}**, "
            f"tiết kiệm **${analysis.get('largest_savings', 0):,.0f}/tháng**. "
            "Reserved phù hợp với workload chạy ổn định ở duty cycle cao, còn spot phù hợp "
            "với workload interruptible có checkpoint; cả hai đều giảm trực tiếp chi phí GPU-giờ.",
            f"Inference (cascade/cache/batch) tiết kiệm **${levers.get('Inference (cascade/cache/batch)', 0):,.0f}** "
            "nhờ route phần lớn request sang model nhỏ, giảm giá input bằng cache và giảm thêm 50% cho batch.",
            f"Right-sizing tiết kiệm **${analysis.get('rightsize_savings', 0):,.0f}** bằng cách hạ tier GPU có MFU thấp; "
            f"tắt GPU idle tiết kiệm thêm **${analysis.get('idle_savings', 0):,.0f}** mà không ảnh hưởng throughput.",
            "",
            "## 3. GPU-Util Lie",
            "",
            f"M1 phát hiện **{', '.join(analysis.get('lie_ids', []))}**. Các GPU này có GPU-Util ≥90% "
            "nhưng MFU <30%: clock vẫn hoạt động nhưng phần lớn thời gian có thể bị memory stall, "
            "kernel launch overhead hoặc chờ I/O, nên FLOPs hữu ích thấp.",
            f"Hậu quả là vẫn trả đủ GPU-hour cho hiệu suất thấp. Hạ tier các GPU bị lie ước tính tiết kiệm "
            f"**${analysis.get('rightsize_savings', 0):,.0f}/tháng**; idle waste hiện tại là "
            f"**${analysis.get('idle_savings', 0):,.0f}/tháng**. Vì vậy cần theo dõi MFU/MBU cùng GPU-Util.",
        ]
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            f"- Energy per query: {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Carbon per query: {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Cheapest+cleanest region: {sustainability.get('best_region', 'n/a')}",
        ]
    if extensions:
        lines += ["", "## Extensions", ""]
        if "reasoning" in extensions:
            e = extensions["reasoning"]
            lines += [
                "### Reasoning budget",
                "",
                f"- Reasoning traffic: {e.get('request_share_pct', 0):.1f}% of requests / "
                f"{e.get('traffic_share_pct', 0):.1f}% of tokens; "
                f"optimized cost: {e.get('cost_share_pct', 0):.1f}%.",
                f"- A 10% traffic cap is estimated to save ${e.get('cap_savings_daily', 0):.2f}/day "
                f"and {e.get('cap_wh_savings_daily', 0):,.0f} Wh/day. "
                f"Current traffic is below the cap: {e.get('request_share_pct', 0):.1f}% requests.",
                "- Insight: reasoning uses disproportionately long outputs, so it consumes more tokens "
                "and energy; apply reasoning only when task complexity justifies it.",
            ]
        if "cache" in extensions:
            e = extensions["cache"]
            lines += [
                "### Prompt cache economics",
                "",
                f"- Average reads: {e.get('avg_reads', 0):.1f}; write cost: ${e.get('write_cost_per_m', 0):.2f}/1M tokens.",
                f"- Cache enabled: **{e.get('enabled', False)}** (break-even rule: repeated-read savings exceed write cost).",
                f"- Break-even: each read saves {(1 - e.get('read_discount', 0.10)):.0%}; "
                f"{e.get('avg_reads', 0):.1f} reads save ${e.get('read_savings', 0):.2f}, "
                f"greater than the ${e.get('write_cost_per_m', 0):.2f} write cost.",
            ]
        if "inference" in extensions:
            e = extensions["inference"]
            lines += [
                "### Inference unit economics",
                "",
                f"- Baseline: ${e.get('baseline_per_m', 0):.3f}/1M tokens; optimized: "
                f"${e.get('optimized_per_m', 0):.3f}/1M tokens ({e.get('savings_pct', 0):.1f}% lower).",
            ]
    if analysis:
        lines += [
            "",
            "## 5. Khuyến nghị cho NimbusAI",
            "",
            "1. **Chuẩn hóa purchasing ngay:** dùng reserved cho job ổn định, spot + checkpoint cho job interruptible; rà soát lại theo duty cycle hàng tháng.",
            "2. **Thiết lập guardrail hiệu quả GPU:** dashboard MFU, MBU, idle hours và $/1M-token; tự động cảnh báo GPU-Util cao nhưng MFU thấp và tắt GPU idle.",
            "3. **Tối ưu traffic có kiểm soát chất lượng:** cascade mặc định, prompt cache cho prefix lặp lại, batch cho request không yêu cầu realtime; chỉ bật reasoning khi cần và giữ tag coverage ≥80%.",
        ]
    lines += ["", "_Figures are June-2026 as-of snapshots; re-baseline before acting._"]
    return "\n".join(lines)


def savings_waterfall(levers: dict, path: str) -> str:
    """Write a simple savings bar chart PNG. Returns the path. No-op if matplotlib absent."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [levers[n] for n in names]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, vals, color="#2e548a")
    ax.set_ylabel("Savings (USD / month)")
    ax.set_title("GPU cost savings by FinOps lever")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
