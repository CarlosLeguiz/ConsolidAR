"""FX rates builder for ConsolidAR.

Produces the historical FX rate table used to translate local-currency
balances into the presentation currency (USD) during consolidation.

All four foreign currencies (ARS, BRL, CLP, PEN) are synthesized as
deterministic daily trajectories seeded from RANDOM_SEED. This is a
deliberate design choice arrived at after evaluating live-API options:

  - frankfurter.app (backed by the European Central Bank) is the natural
    free option, no API key required. However, of the four currencies
    this project needs, frankfurter only carries BRL. CLP, PEN and ARS
    are all absent from the ECB reference feed. Using frankfurter for
    BRL alone would produce a mixed pipeline (one real currency, three
    synthetic) with no consistency benefit and extra fragility.
  - Paid APIs (exchangerate.host, OpenExchangeRates) cover the missing
    currencies but require per-user API keys, breaking the clone-and-run
    portability that the project relies on for reproducibility.
  - Historical FX data occasionally revises retroactively; a synthetic
    trajectory is immune to this and guarantees byte-identical output on
    every run.

Given the above, generating all four trajectories synthetically is the
consistent choice: one code path, no external dependencies, no per-user
setup, and full reproducibility.

Trajectories are anchored to published 2024-2025 macroeconomic paths for
each currency and interpolated daily with small seeded noise. They are
plausible, not real. The `source` column labels every row as
'synthesized' so no downstream consumer can mistake this for market data.

Two rate types per (currency, period):

  - CLOSING: rate on the last day of the period (ASSET/LIABILITY balances)
  - AVERAGE: arithmetic mean of daily rates in the period (REVENUE/EXPENSE)
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Final

import numpy as np
import pandas as pd

from data_generation.constants import PERIOD_END, PERIOD_START, RANDOM_SEED

# ---------------------------------------------------------------------------
# Anchor points per currency
# ---------------------------------------------------------------------------
# Each list holds (date, rate_vs_usd) tuples anchoring the trajectory.
# Values reflect published official rates for 2024-2025 to lend realism.

_ANCHORS: Final[dict[str, list[tuple[date, float]]]] = {
    "ARS": [
        (date(2024, 1, 1),   810.0),
        (date(2024, 6, 30),  920.0),
        (date(2024, 12, 31), 1030.0),
        (date(2025, 6, 30),  1100.0),
        (date(2025, 12, 31), 1200.0),
    ],
    "BRL": [
        (date(2024, 1, 1),   4.90),
        (date(2024, 6, 30),  5.30),
        (date(2024, 12, 31), 5.65),
        (date(2025, 6, 30),  5.75),
        (date(2025, 12, 31), 5.85),
    ],
    "CLP": [
        (date(2024, 1, 1),   920.0),
        (date(2024, 6, 30),  950.0),
        (date(2024, 12, 31), 965.0),
        (date(2025, 6, 30),  975.0),
        (date(2025, 12, 31), 985.0),
    ],
    "PEN": [
        (date(2024, 1, 1),   3.70),
        (date(2024, 6, 30),  3.74),
        (date(2024, 12, 31), 3.78),
        (date(2025, 6, 30),  3.82),
        (date(2025, 12, 31), 3.85),
    ],
}

# Noise magnitude per currency (standard deviation of daily multiplicative noise)
_NOISE_SIGMA: Final[dict[str, float]] = {
    "ARS": 0.003,   # 0.3% daily typical
    "BRL": 0.006,   # 0.6% daily typical
    "CLP": 0.004,   # 0.4% daily typical
    "PEN": 0.002,   # 0.2% daily typical (most stable)
}


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

_COLUMN_ORDER: Final[list[str]] = [
    "currency",
    "period",
    "rate_type",
    "rate",
    "source",
]


# ---------------------------------------------------------------------------
# Daily trajectory generator
# ---------------------------------------------------------------------------

def _generate_daily_trajectory(
    currency: str,
    start: date,
    end: date,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate a deterministic daily rate trajectory for one currency.

    The trajectory linearly interpolates between anchor points and applies
    small multiplicative noise drawn from a normal distribution. The rng
    is passed in from the caller so all currencies share a single seeded
    stream, keeping the overall output stable under RANDOM_SEED.
    """
    anchors = _ANCHORS[currency]
    sigma = _NOISE_SIGMA[currency]

    anchor_ordinals = [d.toordinal() for d, _ in anchors]
    anchor_rates = [r for _, r in anchors]

    records: list[dict] = []
    day = start
    while day <= end:
        base_rate = float(
            np.interp(day.toordinal(), anchor_ordinals, anchor_rates)
        )
        noise = 1.0 + rng.normal(loc=0.0, scale=sigma)
        rate = base_rate * noise
        records.append({"date": day, "currency": currency, "rate": rate})
        day += timedelta(days=1)
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Period aggregation
# ---------------------------------------------------------------------------

def _iter_periods(start: date, end: date):
    """Yield (period_string, first_day, last_day) for each month in range."""
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        last_day_num = monthrange(y, m)[1]
        first = date(y, m, 1)
        last = date(y, m, last_day_num)
        yield f"{y:04d}{m:02d}", first, last
        m += 1
        if m > 12:
            m = 1
            y += 1


def _aggregate_to_periods(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Collapse a daily rate DataFrame into per-period CLOSING and AVERAGE."""
    rows: list[dict] = []
    for period, first, last in _iter_periods(PERIOD_START, PERIOD_END):
        month_slice = daily_df[
            (daily_df["date"] >= first) & (daily_df["date"] <= last)
        ]
        if month_slice.empty:
            continue
        for ccy in month_slice["currency"].unique():
            ccy_slice = month_slice[month_slice["currency"] == ccy]
            closing_rate = float(
                ccy_slice.sort_values("date").iloc[-1]["rate"]
            )
            average_rate = float(ccy_slice["rate"].mean())
            rows.extend([
                {
                    "currency": ccy,
                    "period": period,
                    "rate_type": "CLOSING",
                    "rate": closing_rate,
                    "source": "synthesized",
                },
                {
                    "currency": ccy,
                    "period": period,
                    "rate_type": "AVERAGE",
                    "rate": average_rate,
                    "source": "synthesized",
                },
            ])
    return pd.DataFrame(rows, columns=_COLUMN_ORDER)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_fx_rates_df() -> pd.DataFrame:
    """Build the FX rates DataFrame.

    Generates deterministic daily trajectories for all four foreign
    currencies (ARS, BRL, CLP, PEN), aggregates them to per-period
    CLOSING and AVERAGE rates, and returns the sorted result. The output
    contains 192 rows (4 currencies * 24 periods * 2 rate types).
    """
    rng = np.random.default_rng(RANDOM_SEED)

    dailies: list[pd.DataFrame] = []
    for currency in ["ARS", "BRL", "CLP", "PEN"]:
        dailies.append(
            _generate_daily_trajectory(currency, PERIOD_START, PERIOD_END, rng)
        )
    all_daily = pd.concat(dailies, ignore_index=True)

    df = _aggregate_to_periods(all_daily)

    df = df.astype({
        "currency": "string",
        "period": "string",
        "rate_type": "string",
        "rate": "float64",
        "source": "string",
    })
    df = df.sort_values(
        ["currency", "period", "rate_type"]
    ).reset_index(drop=True)
    return df


def validate_fx_rates_df(df: pd.DataFrame) -> None:
    """Run business-rule validations on the FX rates DataFrame."""
    # Composite key uniqueness
    duplicates = df.duplicated(subset=["currency", "period", "rate_type"])
    assert not duplicates.any(), (
        "Composite key (currency, period, rate_type) must be unique"
    )

    # rate_type within allowed values
    valid_types = {"CLOSING", "AVERAGE"}
    invalid = set(df["rate_type"]) - valid_types
    assert not invalid, f"Invalid rate_type values: {invalid}"

    # All rates strictly positive
    assert (df["rate"] > 0).all(), "All FX rates must be positive"

    # Expected volume: 4 currencies * 24 periods * 2 types = 192
    expected_rows = 4 * 24 * 2
    assert len(df) == expected_rows, (
        f"Expected {expected_rows} rows, got {len(df)}"
    )

    # Each currency has both rate types for every period
    for currency in ["ARS", "BRL", "CLP", "PEN"]:
        sub = df[df["currency"] == currency]
        assert len(sub) == 24 * 2, (
            f"Currency {currency}: expected 48 rows, got {len(sub)}"
        )

    # ARS trajectory must be monotonically non-decreasing (devaluation)
    ars_closing = df[
        (df["currency"] == "ARS") & (df["rate_type"] == "CLOSING")
    ].sort_values("period")
    diffs = ars_closing["rate"].diff().dropna()
    assert (diffs >= 0).all(), (
        "ARS CLOSING rates must be monotonically non-decreasing"
    )