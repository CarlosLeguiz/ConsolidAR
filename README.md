# ConsolidAR

> Multi-entity financial consolidation platform on Snowflake — FX translation,
> intercompany eliminations, row-level security, and in-database LLM commentary
> for FP&A.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Snowflake](https://img.shields.io/badge/Snowflake-Native-29B5E8)](https://www.snowflake.com/)
[![dbt](https://img.shields.io/badge/dbt-1.8-FF694B)](https://www.getdbt.com/)

---

## What this is

ConsolidAR demonstrates production-grade data engineering applied to a real
FP&A problem: **closing the books for a multi-entity group with multiple
currencies, intercompany activity, and minority interests.**

The dataset is synthetic. The accounting is not every consolidation rule
implemented here (FX translation methods, CTA, intercompany eliminations,
non-controlling interest) follows the same logic that a Big 4 audit team would
apply to a real corporate group.

The platform is **Snowflake-native by design**: the codebase is not portable
to other warehouses without significant rewrite, and that is the point.
Dynamic Tables, Streams, Tasks, Snowpark, Cortex, row access policies, and
zero-copy cloning are all central to the architecture, not decorative.

## The fictional group: Andina Holdings

| Entity                 | Country   | Local CCY | Ownership            | Industry      |
| ---------------------- | --------- | --------- | -------------------- | ------------- |
| Andina Holdings SA     | Argentina | ARS       | Parent (USD reports) | Holding       |
| Andina Brasil Ltda     | Brazil    | BRL       | 100%                 | Retail        |
| Andina Chile SpA       | Chile     | CLP       | 100%                 | Retail        |
| Andina Perú SAC        | Peru      | PEN       | 80% (20% NCI)        | Manufacturing |
| Andina USA Inc         | USA       | USD       | 100%                 | Distribution  |

Presentation currency for the consolidated group: **USD**.

Intercompany flows include management fees from the holding to subsidiaries,
inventory transfers between retail entities, and inter-segment sales between
Manufacturing Peru and Distribution USA.

## Architecture 

```
RAW (one schema per entity, row-access-policy-protected)
    journal_entries, journal_lines, chart_of_accounts_local
        |
        v
STAGING (chart of accounts mapped to corporate)
    stg_journal_lines_mapped, stg_entities, stg_fx_rates
        |
        v
INTERMEDIATE (Snowflake-native compute starts here)
    int_translated_balances        <- Dynamic Table, target lag 1 min
    int_cta_movements              <- per-entity CTA calculation
    int_ic_matched / int_ic_unmatched  <- Snowpark Python UDF
        |
        v
MARTS (consolidated outputs)
    consolidated_trial_balance     <- closes to zero (dbt test)
    consolidated_income_statement
    consolidated_balance_sheet
    consolidated_cash_flow         <- indirect method
    intercompany_elimination_log
    cta_walk, nci_walk
        |
        v
REPORTING
    Snowsight dashboards
    SNOWFLAKE.CORTEX.COMPLETE() 
```

**Orchestration:** Snowflake Tasks (not Airflow — see
[ADR 0007](adrs/0007-tasks-vs-airflow.md) once written).

**CI/CD:** GitHub Actions runs `dbt build` against a per-branch schema
zero-copy-cloned from production. Tests run against a full production replica
with no storage cost.

For the full logical data model — tables, columns, grain, FX rate selection
rules — see [docs/data_model.md](docs/data_model.md).

## ADRs

Architecture decisions are documented in [`adrs/`](adrs/). Index:

- [0001 — Snowflake-only architecture](adrs/0001-snowflake-only-architecture.md)
- [0002 — CTA calculation: current-rate vs temporal method](adrs/0002-cta-current-rate-method.md)
- [0003 — Dependency management: pip + venv vs Poetry](adrs/0003-pip-venv-vs-poetry.md)

## Related work

- [FinClose AI](https://github.com/CarlosLeguiz/finclose-ai) — predecessor
  project covering single-entity accounting close with DuckDB + dbt + Airflow
  + Streamlit + LangChain. ConsolidAR moves to a Snowflake-native architecture
  and adds the multi-entity dimension.

## Author

Carlos Leguizamon Guillaumet — Senior Data BI / Analytics Engineer.
- [LinkedIn](https://www.linkedin.com/in/carlos-leguizamon-guillaumet/)

## License

MIT — see [LICENSE](LICENSE).
