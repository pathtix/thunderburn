"""Environmental impact estimate.

This is a deliberately simple, transparent model — good enough to give users an
intuition for "more tokens = more energy = more CO2", not a lab-grade figure.

Method
------
1. Energy per 1k tokens (Wh) is a baseline constant, scaled by a per-model
   `energy` factor (a bigger model burns more per token).
2. Energy (kWh) * grid carbon intensity (g CO2 / kWh) = grams CO2.

Defaults
--------
- BASELINE_WH_PER_1K   ~ energy to process 1,000 tokens on a mid-size model.
- GRID_INTENSITY        world-average grid carbon intensity (g CO2 / kWh).

Published estimates for LLM inference energy vary widely; these constants are
exposed in the UI so users can dial them to whichever study they trust.
"""

from models import Model

BASELINE_WH_PER_1K = 0.4    # Wh to process 1k tokens at energy factor 1.0
GRID_INTENSITY = 430.0      # g CO2 per kWh (world average-ish)


def grams_co2(
    tokens: int,
    model: Model,
    wh_per_1k: float = BASELINE_WH_PER_1K,
    grid_intensity: float = GRID_INTENSITY,
) -> float:
    """Estimated grams of CO2 for processing `tokens` on `model`."""
    energy_wh = (tokens / 1_000) * wh_per_1k * model.energy
    energy_kwh = energy_wh / 1_000
    return energy_kwh * grid_intensity


def green_score(grams: float) -> tuple[str, str]:
    """Map a CO2 figure to a simple letter grade + emoji for the dashboard."""
    if grams < 0.05:
        return "A", "🟢"
    if grams < 0.15:
        return "B", "🟢"
    if grams < 0.4:
        return "C", "🟡"
    if grams < 1.0:
        return "D", "🟠"
    return "E", "🔴"


def equivalent(grams: float) -> str:
    """A relatable comparison for a gram-scale CO2 figure."""
    # A smartphone charge is ~8g CO2; a Google search ~0.2g.
    if grams < 0.2:
        return f"≈ {grams / 0.2:.1f} web searches"
    phone = grams / 8.0
    return f"≈ {phone:.2f} smartphone charges"
