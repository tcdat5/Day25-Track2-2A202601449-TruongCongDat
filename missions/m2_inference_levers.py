"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing
from finops import sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}
CACHE_AVG_READS = 2.0
CACHE_WRITE_COST_PER_M = 0.50


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    reasoning_base_cost = reasoning_opt_cost = 0.0
    normal_opt_cost = 0.0
    reasoning_tokens = normal_tokens = 0
    reasoning_requests = total_requests = 0
    reasoning_wh = normal_wh = 0.0
    total_tokens = 0
    cache_enabled = pricing.cache_is_worth_it(
        CACHE_AVG_READS, CACHE_WRITE_COST_PER_M
    )
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        request_tokens = inp + out
        total_tokens += request_tokens
        total_requests += 1
        is_reasoning = bool(int(num(r["is_reasoning"])))
        if is_reasoning:
            reasoning_requests += 1
            reasoning_tokens += request_tokens
            reasoning_wh += sustainability.wh_per_query(request_tokens, is_reasoning=True)
        else:
            normal_tokens += request_tokens
            normal_wh += sustainability.wh_per_query(request_tokens)
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        opt_cached = cached if cache_enabled else 0
        optimized_request_cost = pricing.request_cost(
            inp, out, pin, pout, cached_in=opt_cached, batch=is_batch
        )
        opt_cost += optimized_request_cost
        if is_reasoning:
            reasoning_base_cost += pricing.request_cost(inp, out, lin, lout)
            reasoning_opt_cost += optimized_request_cost
        else:
            normal_opt_cost += optimized_request_cost

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0
    reasoning_cost_share_pct = (reasoning_opt_cost / opt_cost * 100) if opt_cost else 0.0
    reasoning_traffic_share_pct = (reasoning_tokens / total_tokens * 100) if total_tokens else 0.0
    reasoning_request_share_pct = (reasoning_requests / total_requests * 100) if total_requests else 0.0
    reasoning_cap_savings = 0.0
    reasoning_cap_wh_savings = 0.0
    if reasoning_requests:
        # A practical policy simulation: cap reasoning at 10% of requests.
        # Excess reasoning requests are routed through the normal path. This
        # measures the direct cost/energy avoided by the policy.
        target_requests = total_requests * 0.10
        excess_requests = max(0, reasoning_requests - target_requests)
        excess_fraction = excess_requests / reasoning_requests
        reasoning_cap_savings = reasoning_opt_cost * excess_fraction
        reasoning_cap_wh_savings = reasoning_wh * excess_fraction * 0.9875

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print(f"cache economics: avg reads={CACHE_AVG_READS:.1f}, write={CACHE_WRITE_COST_PER_M:.2f}/1M -> enabled={cache_enabled}")
        print(f"reasoning: {reasoning_request_share_pct:.1f}% of requests / {reasoning_traffic_share_pct:.1f}% of tokens, {reasoning_cost_share_pct:.1f}% of optimized cost")
        print(f"reasoning cap (10% traffic): save ${reasoning_cap_savings:.2f}/day, {reasoning_cap_wh_savings:,.0f} Wh/day")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "cache_enabled": cache_enabled,
        "cache_avg_reads": CACHE_AVG_READS,
        "reasoning_base_daily": round(reasoning_base_cost, 2),
        "reasoning_optimized_daily": round(reasoning_opt_cost, 2),
        "reasoning_cost_share_pct": round(reasoning_cost_share_pct, 1),
        "reasoning_request_share_pct": round(reasoning_request_share_pct, 1),
        "reasoning_traffic_share_pct": round(reasoning_traffic_share_pct, 1),
        "reasoning_wh_daily": round(reasoning_wh, 2),
        "normal_wh_daily": round(normal_wh, 2),
        "reasoning_cap_savings_daily": round(reasoning_cap_savings, 2),
        "reasoning_cap_wh_savings_daily": round(reasoning_cap_wh_savings, 2),
    }


if __name__ == "__main__":
    run()
