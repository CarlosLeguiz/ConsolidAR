# Architecture Decision Records

This directory contains the architecture decisions taken during the design
and implementation of ConsolidAR. Each ADR follows the format proposed by
Michael Nygard:

1. **Title** — short noun phrase
2. **Status** — Proposed / Accepted / Deprecated / Superseded
3. **Context** — the forces at play, business and technical
4. **Decision** — what we are doing
5. **Consequences** — what becomes easier and harder as a result

ADRs are immutable once accepted. If a decision is later reversed, a new ADR
is written that supersedes the old one, and the old one is marked
`Superseded by ADR-XXXX`.

## Index

| #    | Title                                                              | Status   |
| ---- | ------------------------------------------------------------------ | -------- |
| 0001 | [Snowflake-only architecture](0001-snowflake-only-architecture.md) | Accepted |
| 0002 | [CTA calculation: current-rate vs temporal method](0002-cta-current-rate-method.md) | Accepted |
| 0003 | Intercompany matching: SQL vs Snowpark Python                      | Pending  |
| 0004 | Dynamic Tables vs dbt incremental models                           | Pending  |
| 0005 | Cortex in-database vs external LLM API                             | Pending  |
| 0006 | Row access policies vs separate databases per entity               | Pending  |
| 0007 | Tasks-based orchestration vs Airflow                               | Pending  |
| 0008 | NCI calculation timing: pre or post eliminations                   | Pending  |
| 0009 | Cost governance: warehouse sizing, auto-suspend, monitors          | Pending  |
