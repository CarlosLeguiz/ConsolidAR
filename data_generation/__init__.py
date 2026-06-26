"""Synthetic data generation for ConsolidAR.

Generates a complete, internally consistent dataset for the five entities
of the fictional Andina Holdings group over a 24-month horizon. The output
is a collection of Parquet files ready to be loaded into Snowflake's RAW
schemas via COPY INTO.

The package is organized into focused modules:

- constants:        domain constants (entities, currencies, period range)
- entities:         entity reference table
- corporate_coa:    corporate chart of accounts
- local_coa:        per-entity local charts of accounts
- coa_mapping:      mapping from local accounts to corporate accounts
- fx_rates:         FX rate download from a public source
- journal_entries:  balanced journal entries and lines (double-entry)
- intercompany:     intercompany transaction pairs
- output:           Parquet serialization layout
- cli:              command-line entrypoint

Run end-to-end via: `make generate-data` or `python -m data_generation.cli`.
"""
