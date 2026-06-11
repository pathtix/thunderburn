"""Cost estimation.

We treat the prompt as input tokens and assume an output of `output_tokens`
(default modest) so the per-call cost reflects a realistic round-trip, not just
the prompt. All prices are per 1,000,000 tokens.
"""

from models import Model


def cost_per_call(
    input_tokens: int,
    output_tokens: int,
    model: Model,
) -> float:
    """USD cost for a single call (input + assumed output)."""
    return (
        input_tokens / 1_000_000 * model.price_in
        + output_tokens / 1_000_000 * model.price_out
    )


def project_costs(per_call: float) -> dict[str, float]:
    """Scale a single-call cost to common volumes."""
    return {
        "per_call": per_call,
        "per_1k_calls": per_call * 1_000,
        "per_month_100k": per_call * 100_000,  # ~100k calls/month
    }
