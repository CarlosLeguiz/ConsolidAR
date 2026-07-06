"""Journal entries generator.

Produces double-entry journal lines for each entity. Every entry
balances (debits == credits within the entry). Currently only sales
for BR_RET, one month; more transaction types and entities coming.
"""

import numpy as np
import pandas as pd

from data_generation.constants import RANDOM_SEED


COLUMNS = [
    "entry_id", "line_id", "entity_id", "period", "posting_date",
    "account_code_local", "debit_amount", "credit_amount",
    "description", "transaction_type",
]

# Sales distribution for retail: 40 sales/month split into three bands
SALES_BANDS = [
    (25, 500, 2000),    # small
    (12, 2000, 5000),   # medium
    (3,  5000, 15000),  # large
]
CASH_PROBABILITY = 0.60
COGS_RATIO = 0.65

BR_RET_ACCOUNTS = {
    "cash":      "1.1.01.001",
    "ar":        "1.1.01.002",
    "inventory": "1.1.02.001",
    "revenue":   "4.1.01.001",
    "cogs":      "5.1.01.001",
}


def _generate_sales(entity_id, period, accounts, rng):
    """One month of sales for a retail entity, 4 lines per sale."""
    amounts = []
    for count, low, high in SALES_BANDS:
        amounts.extend(rng.uniform(low, high, size=count).tolist())

    rows = []
    for i, revenue in enumerate(amounts, start=1):
        revenue = round(float(revenue), 2)
        cogs = round(revenue * COGS_RATIO, 2)
        is_cash = rng.uniform() < CASH_PROBABILITY
        collect_acc = accounts["cash"] if is_cash else accounts["ar"]

        entry_id = f"{entity_id}-{period}-{i:05d}"
        day = min(28, (i % 28) + 1)
        posting_date = f"{period[:4]}-{period[4:]}-{day:02d}"

        rows.append((entry_id, 1, entity_id, period, posting_date,
                     collect_acc, revenue, 0.0,
                     f"Sale #{i} ({'cash' if is_cash else 'credit'})", "SALES"))
        rows.append((entry_id, 2, entity_id, period, posting_date,
                     accounts["revenue"], 0.0, revenue,
                     f"Sale #{i} revenue", "SALES"))
        rows.append((entry_id, 3, entity_id, period, posting_date,
                     accounts["cogs"], cogs, 0.0,
                     f"Sale #{i} COGS", "SALES"))
        rows.append((entry_id, 4, entity_id, period, posting_date,
                     accounts["inventory"], 0.0, cogs,
                     f"Sale #{i} inventory relief", "SALES"))

    return pd.DataFrame(rows, columns=COLUMNS)


def build_journal_entries_df():
    """Generate journal entries. Scope: BR_RET sales for 202401."""
    rng = np.random.default_rng(RANDOM_SEED)
    df = _generate_sales("BR_RET", "202401", BR_RET_ACCOUNTS, rng)

    df = df.astype({
        "line_id": "int32",
        "debit_amount": "float64",
        "credit_amount": "float64",
    })
    return df


def validate_journal_entries_df(df):
    """Check that entries balance and lines are well-formed."""
    totals = df.groupby("entry_id")[["debit_amount", "credit_amount"]].sum()
    diff = (totals["debit_amount"] - totals["credit_amount"]).abs()
    unbalanced = totals[diff > 0.01]
    assert unbalanced.empty, f"Unbalanced entries: {unbalanced.to_dict('index')}"

    both = df[(df["debit_amount"] > 0) & (df["credit_amount"] > 0)]
    assert both.empty, "A line cannot have both debit and credit"

    assert not df.duplicated(subset=["entry_id", "line_id"]).any(), \
        "entry_id + line_id must be unique"