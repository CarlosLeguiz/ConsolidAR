"""Entity reference table builder for ConsolidAR.

Transforms the immutable ENTITIES list from constants.py into a typed
pandas DataFrame ready to be written as Parquet. The output corresponds
to the corp_ref.entities table in the target Snowflake data model
(see docs/data_model.md, section 3.5).

The table is slowly-changing (SCD type 2) in the data model, but the
synthetic dataset has only one validity window per entity: all entities
are effective from PERIOD_START with no end date (still active).
"""

from datetime import date
from typing import Final

import pandas as pd

from data_generation.constants import ENTITIES, PERIOD_START

# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
# Column order is fixed because downstream consumers (Parquet readers,
# Snowflake COPY INTO, dbt source definitions) rely on it.

_COLUMN_ORDER: Final[list[str]] = [
    "entity_id",
    "entity_name",
    "country_iso2",
    "local_currency",
    "functional_currency",
    "ownership_pct",
    "parent_entity_id",
    "industry",
    "consolidation_method",
    "effective_from",
    "effective_to",
]


def build_entities_df() -> pd.DataFrame:
    """Build the entities reference DataFrame.

    Returns a DataFrame with one row per legal entity in the Andina
    Holdings group, including SCD2 validity columns. All entities are
    effective from PERIOD_START with no end date.

    The DataFrame schema is deterministic and stable: column names,
    column order, and dtypes are fixed across runs.
    """
    # Start from the canonical ENTITIES list
    df = pd.DataFrame(ENTITIES)

    # Add SCD2 validity columns
    df["effective_from"] = PERIOD_START
    df["effective_to"] = pd.NaT  # null timestamp: still active

    # Enforce column order
    df = df[_COLUMN_ORDER]

    # Cast types explicitly so Parquet output has a predictable schema
    df = df.astype({
        "entity_id": "string",
        "entity_name": "string",
        "country_iso2": "string",
        "local_currency": "string",
        "functional_currency": "string",
        "ownership_pct": "float64",
        "parent_entity_id": "string",  # nullable string
        "industry": "string",
        "consolidation_method": "string",
    })

    # Date columns: convert via pandas datetime
    df["effective_from"] = pd.to_datetime(df["effective_from"])
    df["effective_to"] = pd.to_datetime(df["effective_to"])

    return df


def validate_entities_df(df: pd.DataFrame) -> None:
    """Run business-rule validations on the entities DataFrame.

    Raises AssertionError if any rule is violated. These rules encode
    invariants of the group structure that must hold by construction.
    """
    # Cardinality: exactly five entities
    assert len(df) == 5, f"Expected 5 entities, got {len(df)}"

    # Uniqueness of entity_id
    assert df["entity_id"].is_unique, "entity_id values must be unique"

    # Exactly one parent (entity with parent_entity_id = NaN)
    parents = df[df["parent_entity_id"].isna()]
    assert len(parents) == 1, f"Expected exactly 1 apex parent, got {len(parents)}"

    # Every non-parent points to a valid parent_entity_id
    non_parent_parents = df[df["parent_entity_id"].notna()]["parent_entity_id"]
    valid_ids = set(df["entity_id"])
    invalid = set(non_parent_parents) - valid_ids
    assert not invalid, f"Invalid parent_entity_id references: {invalid}"

    # Ownership percentages within [0, 1]
    assert df["ownership_pct"].between(0, 1).all(), (
        "ownership_pct must be in [0, 1]"
    )