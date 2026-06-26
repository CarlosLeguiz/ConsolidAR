"""Corporate chart of accounts builder for ConsolidAR.

Defines the canonical chart of accounts that every Andina Holdings entity
maps into for consolidation. The corporate CoA is independent of any local
chart and uses a four-digit numeric coding scheme grouped by account type:

  1xxx: Assets
  2xxx: Liabilities
  3xxx: Equity
  4xxx: Revenue
  5xxx-8xxx: Expenses

The is_intercompany_eliminable flag identifies accounts whose intercompany
balances must be removed during consolidation. These are the accounts the
elimination algorithm targets (see int_ic_elimination_journal in the data
model).

Account 3900 (Accumulated CTA) is reserved for the cumulative translation
adjustment posted by the consolidation engine; see ADR 0002.
"""

from typing import Final

import pandas as pd

# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

_COLUMN_ORDER: Final[list[str]] = [
    "account_code",
    "account_name",
    "account_type",
    "account_subtype",
    "statement_line",
    "presentation_order",
    "is_intercompany_eliminable",
]

# ---------------------------------------------------------------------------
# Corporate chart of accounts (canonical definition)
# ---------------------------------------------------------------------------
# Each tuple: (code, name, type, subtype, statement_line, order, ic_eliminable)
# Order is enforced via the presentation_order column for downstream sorting.

_CORPORATE_COA: Final[list[tuple]] = [
    # ----- ASSETS -----
    ("1000", "Cash and Cash Equivalents",      "ASSET", "CURRENT_ASSET",        "Cash",                  100, False),
    ("1100", "Accounts Receivable Trade",      "ASSET", "CURRENT_ASSET",        "Trade AR",              110, False),
    ("1200", "Accounts Receivable IC",         "ASSET", "CURRENT_ASSET",        "IC Receivables",        120, True),
    ("1300", "Inventory",                      "ASSET", "CURRENT_ASSET",        "Inventory",             130, False),
    ("1400", "Prepaid Expenses",               "ASSET", "CURRENT_ASSET",        "Other Current Assets",  140, False),
    ("1500", "Property Plant Equipment",       "ASSET", "NON_CURRENT_ASSET",    "PP&E",                  150, False),
    ("1600", "Accumulated Depreciation",       "ASSET", "NON_CURRENT_ASSET",    "PP&E",                  160, False),
    ("1700", "Intangible Assets",              "ASSET", "NON_CURRENT_ASSET",    "Intangibles",           170, False),
    ("1800", "Investments in Subsidiaries",    "ASSET", "NON_CURRENT_ASSET",    "Investments",           180, True),

    # ----- LIABILITIES -----
    ("2000", "Accounts Payable Trade",         "LIABILITY", "CURRENT_LIABILITY",     "Trade AP",          200, False),
    ("2100", "Accounts Payable IC",            "LIABILITY", "CURRENT_LIABILITY",     "IC Payables",       210, True),
    ("2200", "Accrued Liabilities",            "LIABILITY", "CURRENT_LIABILITY",     "Accrued Liabilities", 220, False),
    ("2300", "Short-term Debt",                "LIABILITY", "CURRENT_LIABILITY",     "Short-term Debt",   230, False),
    ("2350", "Short-term Debt IC",             "LIABILITY", "CURRENT_LIABILITY",     "IC Debt ST",        235, True),
    ("2400", "Long-term Debt",                 "LIABILITY", "NON_CURRENT_LIABILITY", "Long-term Debt",    240, False),
    ("2450", "Long-term Debt IC",              "LIABILITY", "NON_CURRENT_LIABILITY", "IC Debt LT",        245, True),
    ("2500", "Deferred Tax Liability",         "LIABILITY", "NON_CURRENT_LIABILITY", "Deferred Tax",      250, False),

    # ----- EQUITY -----
    ("3000", "Common Stock",                   "EQUITY", "SHARE_CAPITAL",     "Common Stock",        300, False),
    ("3100", "Additional Paid-in Capital",     "EQUITY", "SHARE_CAPITAL",     "APIC",                310, False),
    ("3200", "Retained Earnings",              "EQUITY", "RETAINED_EARNINGS", "Retained Earnings",   320, False),
    ("3900", "Accumulated CTA",                "EQUITY", "OCI",               "AOCI - Translation",  390, False),
    ("3950", "Non-Controlling Interest",       "EQUITY", "NCI",               "NCI Equity",          395, False),

    # ----- REVENUE -----
    ("4000", "Revenue - Products",             "REVENUE", "OPERATING_REVENUE", "Revenue",       400, False),
    ("4100", "Revenue - Services",             "REVENUE", "OPERATING_REVENUE", "Revenue",       410, False),
    ("4500", "Revenue - Intercompany",         "REVENUE", "OPERATING_REVENUE", "IC Revenue",    450, True),
    ("4900", "Other Operating Income",         "REVENUE", "OTHER_INCOME",      "Other Income",  490, False),

    # ----- EXPENSES: COGS -----
    ("5000", "Cost of Goods Sold",             "EXPENSE", "OPERATING_EXPENSE", "COGS",          500, False),
    ("5500", "COGS - Intercompany",            "EXPENSE", "OPERATING_EXPENSE", "IC COGS",       550, True),

    # ----- EXPENSES: OPEX -----
    ("6000", "Selling Expense",                "EXPENSE", "OPERATING_EXPENSE", "S&M",                   600, False),
    ("6100", "General and Administrative",     "EXPENSE", "OPERATING_EXPENSE", "G&A",                   610, False),
    ("6200", "Payroll Expense",                "EXPENSE", "OPERATING_EXPENSE", "Payroll",               620, False),
    ("6300", "Rent Expense",                   "EXPENSE", "OPERATING_EXPENSE", "Rent",                  630, False),
    ("6400", "Depreciation Expense",           "EXPENSE", "OPERATING_EXPENSE", "Depreciation",          640, False),
    ("6500", "Amortization Expense",           "EXPENSE", "OPERATING_EXPENSE", "Amortization",          650, False),
    ("6900", "Management Fees IC",             "EXPENSE", "OPERATING_EXPENSE", "IC Management Fees",    690, True),

    # ----- EXPENSES: NON-OPERATING -----
    ("7000", "Interest Expense",               "EXPENSE", "NON_OPERATING_EXPENSE", "Interest Expense",         700, False),
    ("7100", "Interest Expense IC",            "EXPENSE", "NON_OPERATING_EXPENSE", "IC Interest Expense",      710, True),
    ("7200", "Foreign Exchange Gain/Loss",     "EXPENSE", "NON_OPERATING_EXPENSE", "FX Gain/Loss",             720, False),

    # ----- EXPENSES: TAXES -----
    ("8000", "Income Tax Expense",             "EXPENSE", "INCOME_TAX", "Income Tax", 800, False),
]


def build_corporate_coa_df() -> pd.DataFrame:
    """Build the corporate chart of accounts DataFrame.

    Returns a DataFrame with one row per corporate account, ordered by
    presentation_order. The schema is deterministic across runs.
    """
    df = pd.DataFrame(_CORPORATE_COA, columns=_COLUMN_ORDER)

    df = df.astype({
        "account_code": "string",
        "account_name": "string",
        "account_type": "string",
        "account_subtype": "string",
        "statement_line": "string",
        "presentation_order": "int32",
        "is_intercompany_eliminable": "boolean",
    })

    df = df.sort_values("presentation_order").reset_index(drop=True)
    return df


def validate_corporate_coa_df(df: pd.DataFrame) -> None:
    """Run business-rule validations on the corporate CoA DataFrame.

    Raises AssertionError if any rule is violated. These rules encode
    invariants of the chart of accounts that must hold by construction.
    """
    # Uniqueness of account_code
    assert df["account_code"].is_unique, "account_code values must be unique"

    # Uniqueness of presentation_order
    assert df["presentation_order"].is_unique, (
        "presentation_order values must be unique to guarantee stable sorting"
    )

    # account_type must be one of the canonical five
    valid_types = {"ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"}
    invalid_types = set(df["account_type"]) - valid_types
    assert not invalid_types, f"Invalid account_type values: {invalid_types}"

    # account_code first digit must match account_type bucket
    type_to_first_digit = {
        "ASSET": "1",
        "LIABILITY": "2",
        "EQUITY": "3",
        "REVENUE": "4",
        # EXPENSE spans 5xxx-8xxx; checked below
    }
    for atype, first_digit in type_to_first_digit.items():
        subset = df[df["account_type"] == atype]
        bad = subset[~subset["account_code"].str.startswith(first_digit)]
        assert bad.empty, (
            f"{atype} accounts must start with {first_digit}: "
            f"violations = {bad['account_code'].tolist()}"
        )
    # EXPENSE: must start with 5, 6, 7 or 8
    expense = df[df["account_type"] == "EXPENSE"]
    bad_expense = expense[~expense["account_code"].str.match(r"^[5678]")]
    assert bad_expense.empty, (
        f"EXPENSE accounts must start with 5/6/7/8: "
        f"violations = {bad_expense['account_code'].tolist()}"
    )

    # CTA account must exist with the agreed code
    assert "3900" in df["account_code"].values, (
        "Account 3900 (Accumulated CTA) is required by ADR 0002"
    )

    # At least one intercompany-eliminable account per relevant bucket
    ic_accounts = df[df["is_intercompany_eliminable"]]
    assert len(ic_accounts) >= 4, (
        "Expected at least 4 intercompany-eliminable accounts "
        "(AR, AP, Revenue, COGS minimum)"
    )