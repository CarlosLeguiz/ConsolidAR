# ADR 0001 — Snowflake-only architecture

- **Status:** Accepted
- **Date:** 2026-06-22
- **Deciders:** Carlos Leguizamon Guillaumet

## Context

ConsolidAR is the second portfolio project in a planned series of three. The
first project, [FinClose AI](https://github.com/CarlosLeguiz/finclose-ai),
deliberately chose a portable, warehouse-agnostic stack (DuckDB + dbt) so
that the consolidation logic could be reproduced cheaply on a laptop.

This project has a different goal. It is meant to demonstrate **depth in a
specific cloud data platform** to support job applications for Senior Data /
Analytics Engineer roles where Snowflake is named as a required skill in the
job description.

There are three plausible architectural stances available:

1. **Warehouse-agnostic** — write dbt models that compile to any adapter,
   keep all logic in standard SQL, use no platform-specific features. The
   project would run on Snowflake during the trial and remain reproducible
   on DuckDB afterwards.

2. **Open table format** — use Apache Iceberg as the storage layer, with
   Snowflake as one of several possible query engines. Compute is portable;
   storage is open.

3. **Snowflake-native** — use Snowflake-specific features (Dynamic Tables,
   Streams, Tasks, Snowpark, Cortex, row access policies, search
   optimization, zero-copy cloning, time travel) as first-class building
   blocks of the architecture. The codebase becomes non-portable by design.

Each stance has merit. The question is which one fits the goal of this
specific project.

## Decision

**ConsolidAR will be Snowflake-native.** The architecture will deliberately
use features that have no direct equivalent in other warehouses, and will
not abstract over the platform.

Concretely, the following Snowflake-specific features will be load-bearing
in the design:

- **Dynamic Tables** for the FX-translation hot path, replacing the
  dbt-incremental-plus-cron pattern that would be required on other engines.
- **Streams + Tasks** for change-data-capture on the journal layer, driving
  recomputation of intercompany eliminations when new IC transactions land.
- **Snowpark Python UDFs** for the intercompany matching algorithm. The
  matching logic is procedural (fuzzy amount matching, counterparty priority,
  age-weighted resolution) and is implemented in Python executing inside the
  warehouse, not as an external service.
- **Cortex Complete** for in-database generation of consolidated variance
  commentary. The LLM call is a SQL function on top of the marts; no data
  leaves Snowflake.
- **Row access policies** for per-entity data segmentation. A subsidiary
  controller and a corporate consolidator query the same physical table and
  see different rows.
- **Zero-copy cloning** for environment management (dev / UAT / prod /
  per-PR CI), what-if scenarios, and time-travel-based audit drills.
- **Search optimization service** for journal-line text search, with query
  profile evidence captured before and after.

dbt remains in the stack, but only as the transformation orchestrator. dbt
models will call Snowflake-specific SQL functions and reference Dynamic
Tables; they will not be portable.

## Alternatives considered

### Option 1 — Warehouse-agnostic on dbt

Rejected. This pattern is already demonstrated in FinClose AI. Repeating it
on Snowflake would add no new capability to the portfolio, and would
explicitly avoid using the features that make Snowflake worth choosing as a
warehouse in the first place. A reader of the repository would correctly
conclude that the author has not actually used Snowflake in depth.

### Option 2 — Apache Iceberg with Snowflake as one engine

Rejected for this project, with a note. Iceberg is an interesting and
relevant architectural choice in production settings where lock-in cost is
real and the workload spans engines. For a portfolio project with a 30-day
trial budget, adding Iceberg increases setup complexity and dilutes the
narrative ("is this a Snowflake project or an Iceberg project?"). It is a
better fit for the third planned project, where the lakehouse paradigm is
the central theme.

### Option 3 — Snowflake-native (chosen)

Accepted. The features listed above are not decorative; they map to real
problems in multi-entity consolidation:

- FX revaluation is continuous (rates land throughout the day) → Dynamic
  Tables.
- Intercompany matching is procedural and benefits from Python libraries →
  Snowpark UDF.
- Different stakeholders need different views of the same data →
  row access policies.
- Variance narrative is a natural LLM task and the data is already in
  Snowflake → Cortex Complete.

## Consequences

### Positive

- The project demonstrates working knowledge of features that are commonly
  named in Snowflake-specific job descriptions but rarely shown end-to-end
  in public portfolios (Dynamic Tables, Cortex, Snowpark, row access
  policies).
- Architecture decisions can lean on Snowflake semantics directly without
  generalization, which produces a simpler design and more honest code.
- The CI strategy (per-PR zero-copy clone of production) is itself a
  Snowflake-only capability and a meaningful talking point in interviews.

### Negative

- The codebase is not portable. Reproducing this project on Postgres,
  BigQuery, Redshift, or DuckDB would require rewriting significant portions
  of the SQL, replacing Dynamic Tables with cron-driven incremental models,
  removing Cortex calls, and reimplementing the IC matching UDF outside the
  warehouse.
- The project will run only as long as a Snowflake account is available.
  Mitigation: a 30-day-trial reproduction runbook will be included
  (`docs/runbook.md`), and DDL plus sample data will be checked into the
  repository so that any reader with a fresh trial can stand up the entire
  environment.
- Knowledge transferred is partially Snowflake-specific. Mitigation: the
  underlying modeling concepts (consolidation, FX translation, CTA,
  intercompany) are platform-agnostic, and a planned third project will
  reuse the same domain model on a different platform.

### Neutral

- Future maintenance is bounded by the lifetime of the trial. Once the trial
  ends, the project is effectively archival. This is acceptable for a
  portfolio piece; it would not be acceptable for a production system, and
  this distinction should be called out explicitly in the README.

## References

- [Snowflake Dynamic Tables documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Snowflake Cortex LLM Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Snowpark for Python](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- FinClose AI ADR 0001 — Warehouse-agnostic architecture (for contrast)
