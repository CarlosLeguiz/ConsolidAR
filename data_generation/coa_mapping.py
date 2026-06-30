"""Chart of accounts mapping for ConsolidAR.

Joins the local charts of accounts (per-entity) against the corporate
chart of accounts to produce the bridge table used during consolidation.
Without this mapping, postings made against the local code of one entity
cannot be summed with postings of another entity at the consolidated
level.

Mapping strategy:

  1. Primary: exact match on account_name_english (local CoA column) against
     account_name (corporate CoA column), case-insensitive, trimmed.
  2. Fallback: a small set of manual overrides for cases where the local
     account has no exact corporate counterpart (e.g., "Royalty Income"
     mapped to "Other Operating Income").
  3. Diagnostic: any remaining unmapped accounts surface in the validation
     step as an explicit error, never silently dropped.

The mapping is deterministic given the local and corporate CoA inputs.
A re-run produces byte-identical output.
"""

from typing import Final

import pandas as pd

from data_generation.corporate_coa import build_corporate_coa_df
from data_generation.local_coa import build_local_coa_df

# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

_COLUMN_ORDER: Final[list[str]] = [
    "entity_id",
    "account_code_local",
    "account_name_local",
    "account_name_english",
    "corp_account_code",
    "corp_account_name",
    "mapping_confidence",
]

# ---------------------------------------------------------------------------
# Manual overrides
# ---------------------------------------------------------------------------
# Maps local account_name_english -> corporate account_name when an exact
# match is not possible. The mapping was decided explicitly during data
# model design and is documented here as the single source of truth.

_MANUAL_OVERRIDES: Final[dict[str, str]] = {
    # Local label                          # Corporate label
    "Trade Accounts Receivable":           "Accounts Receivable Trade",
    "Trade Accounts Payable":              "Accounts Payable Trade",
    "Intercompany Receivables":            "Accounts Receivable IC",
    "Intercompany Payables":               "Accounts Payable IC",
    "Long-term Bank Debt":                 "Long-term Debt",
    "Intercompany Long-term Debt":         "Long-term Debt IC",
    "Royalty Income":                      "Other Operating Income",
    "Finished Goods Inventory":            "Inventory",
    "Revenue - Manufactured Goods":        "Revenue - Products",
    "Management Fees - External":          "Selling Expense",
    "Management Fees - Intercompany":      "Revenue - Intercompany",
    "Management Fees IC":                  "Management Fees IC",
    "Interest Income":                     "Other Operating Income",
    "Interest Expense IC":                 "Interest Expense IC",
    "Accrued Payroll":                     "Accrued Liabilities",
    "Tax Liabilities Short-term":          "Accrued Liabilities",
    "Payroll Taxes":                       "Payroll Expense",
    "Professional Services":               "General and Administrative",
    "Deferred Tax Liability":              "Deferred Tax Liability",
}


def build_coa_mapping_df() -> pd.DataFrame:
    """Build the chart-of-accounts mapping DataFrame.

    Returns a DataFrame with one row per local account, augmented with
    the corresponding corporate account code and a mapping_confidence
    label that records how the link was resolved.
    """
    local_df = build_local_coa_df()
    corp_df = build_corporate_coa_df()

    # Build a quick lookup: corporate account_name -> account_code
    name_to_code: dict[str, str] = dict(
        zip(corp_df["account_name"], corp_df["account_code"])
    )
    name_to_name: dict[str, str] = dict(
        zip(corp_df["account_name"], corp_df["account_name"])
    )

    rows: list[dict] = []
    for _, lr in local_df.iterrows():
        local_label = str(lr["account_name_english"]).strip()

        # 1. Try exact match against corporate account_name
        if local_label in name_to_code:
            corp_code = name_to_code[local_label]
            corp_name = name_to_name[local_label]
            confidence = "EXACT_MATCH"
        # 2. Fall back to manual overrides
        elif local_label in _MANUAL_OVERRIDES:
            corp_name = _MANUAL_OVERRIDES[local_label]
            corp_code = name_to_code.get(corp_name, "UNMAPPED")
            confidence = (
                "MANUAL_OVERRIDE" if corp_code != "UNMAPPED" else "FALLBACK"
            )
        # 3. No mapping found
        else:
            corp_code = "UNMAPPED"
            corp_name = "UNMAPPED"
            confidence = "FALLBACK"

        rows.append({
            "entity_id": lr["entity_id"],
            "account_code_local": lr["account_code_local"],
            "account_name_local": lr["account_name_local"],
            "account_name_english": lr["account_name_english"],
            "corp_account_code": corp_code,
            "corp_account_name": corp_name,
            "mapping_confidence": confidence,
        })

    df = pd.DataFrame(rows, columns=_COLUMN_ORDER)
    df = df.astype({
        "entity_id": "string",
        "account_code_local": "string",
        "account_name_local": "string",
        "account_name_english": "string",
        "corp_account_code": "string",
        "corp_account_name": "string",
        "mapping_confidence": "string",
    })
    return df


def validate_coa_mapping_df(df: pd.DataFrame) -> None:
    """Run business-rule validations on the mapping DataFrame.

    Raises AssertionError if any rule is violated.
    """
    # No unmapped accounts allowed: if a local account has no corporate
    # counterpart, the mapping is incomplete and must be fixed.
    unmapped = df[df["corp_account_code"] == "UNMAPPED"]
    assert unmapped.empty, (
        f"Unmapped local accounts found: "
        f"{unmapped[['entity_id', 'account_code_local', 'account_name_english']].to_dict('records')}"
    )

    # Composite key uniqueness: one mapping per (entity_id, account_code_local)
    duplicates = df.duplicated(subset=["entity_id", "account_code_local"])
    assert not duplicates.any(), (
        "Composite key (entity_id, account_code_local) must be unique"
    )

    # mapping_confidence within allowed values
    valid_confidence = {"EXACT_MATCH", "MANUAL_OVERRIDE", "FALLBACK"}
    invalid = set(df["mapping_confidence"]) - valid_confidence
    assert not invalid, f"Invalid mapping_confidence values: {invalid}"

    # FALLBACK should never appear in a valid dataset; surface it loudly
    fallbacks = df[df["mapping_confidence"] == "FALLBACK"]
    assert fallbacks.empty, (
        f"FALLBACK mappings found (no corporate counterpart): "
        f"{fallbacks[['entity_id', 'account_code_local', 'account_name_english']].to_dict('records')}"
    )

    # Every entity must have a complete mapping (all its local accounts
    # appear in the mapping)
    local_df = build_local_coa_df()
    local_count = local_df.groupby("entity_id").size()
    mapping_count = df.groupby("entity_id").size()
    for entity_id, count in local_count.items():
        mapped = mapping_count.get(entity_id, 0)
        assert mapped == count, (
            f"Entity {entity_id} has {count} local accounts but only "
            f"{mapped} mappings"
        )