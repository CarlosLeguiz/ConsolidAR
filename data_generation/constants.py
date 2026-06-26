"""Domain constants for ConsolidAR synthetic data generation.

This module centralizes the immutable parameters of the fictional Andina
Holdings group: the entities, their currencies, the time horizon, and the
group structure. Every other module in the package imports from here so
that changes to the group composition propagate consistently.

The values defined here are deliberately frozen as module-level constants
rather than function arguments because they define the dataset's identity.
A different group would be a different project.
"""

from datetime import date
from typing import Final

# ---------------------------------------------------------------------------
# Group identity
# ---------------------------------------------------------------------------

GROUP_NAME: Final[str] = "Andina Holdings"
PRESENTATION_CURRENCY: Final[str] = "USD"

# ---------------------------------------------------------------------------
# Time horizon
# ---------------------------------------------------------------------------
# Two full fiscal years of monthly closes. The choice of 24 months ensures
# year-over-year comparisons are meaningful in the analytical marts.

PERIOD_START: Final[date] = date(2024, 1, 1)
PERIOD_END: Final[date] = date(2025, 12, 31)

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
# Each dict captures the immutable identity of a legal entity in the group.
#
# Ownership convention: 1.00 = 100% (full consolidation, no minority interest).
# Andina Holdings SA is the apex parent (parent_entity_id = None) and reports
# in USD even though its local books are in ARS.

ENTITIES: Final[list[dict]] = [
    {
        "entity_id": "AR_HOLD",
        "entity_name": "Andina Holdings SA",
        "country_iso2": "AR",
        "local_currency": "ARS",
        "functional_currency": "ARS",
        "ownership_pct": 1.00,
        "parent_entity_id": None,
        "industry": "Holding",
        "consolidation_method": "FULL",
    },
    {
        "entity_id": "BR_RET",
        "entity_name": "Andina Brasil Ltda",
        "country_iso2": "BR",
        "local_currency": "BRL",
        "functional_currency": "BRL",
        "ownership_pct": 1.00,
        "parent_entity_id": "AR_HOLD",
        "industry": "Retail",
        "consolidation_method": "FULL",
    },
    {
        "entity_id": "CL_RET",
        "entity_name": "Andina Chile SpA",
        "country_iso2": "CL",
        "local_currency": "CLP",
        "functional_currency": "CLP",
        "ownership_pct": 1.00,
        "parent_entity_id": "AR_HOLD",
        "industry": "Retail",
        "consolidation_method": "FULL",
    },
    {
        "entity_id": "PE_MFG",
        "entity_name": "Andina Peru SAC",
        "country_iso2": "PE",
        "local_currency": "PEN",
        "functional_currency": "PEN",
        "ownership_pct": 0.80,
        "parent_entity_id": "AR_HOLD",
        "industry": "Manufacturing",
        "consolidation_method": "FULL",
    },
    {
        "entity_id": "US_DIST",
        "entity_name": "Andina USA Inc",
        "country_iso2": "US",
        "local_currency": "USD",
        "functional_currency": "USD",
        "ownership_pct": 1.00,
        "parent_entity_id": "AR_HOLD",
        "industry": "Distribution",
        "consolidation_method": "FULL",
    },
]

# Derived constants for convenience and validation
ENTITY_IDS: Final[list[str]] = [e["entity_id"] for e in ENTITIES]
LOCAL_CURRENCIES: Final[set[str]] = {e["local_currency"] for e in ENTITIES}

# ---------------------------------------------------------------------------
# Source systems
# ---------------------------------------------------------------------------
# Used as the source_system column on journal_entries. Mimics how a real
# multinational has heterogeneous ERPs across subsidiaries.

SOURCE_SYSTEM_BY_ENTITY: Final[dict[str, str]] = {
    "AR_HOLD": "ERP_SAP_R3",
    "BR_RET": "ERP_ORACLE_EBS",
    "CL_RET": "ERP_ORACLE_EBS",
    "PE_MFG": "ERP_SAP_S4",
    "US_DIST": "ERP_NETSUITE",
}

# ---------------------------------------------------------------------------
# Random seed
# ---------------------------------------------------------------------------
# Fixed for reproducibility. Two runs of the generator must produce
# byte-identical output for the same seed.

RANDOM_SEED: Final[int] = 202606