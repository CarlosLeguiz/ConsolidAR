# ADR 0002 — CTA calculation: current-rate method vs temporal method

- **Status:** Accepted
- **Date:** 2026-06-22
- **Deciders:** Carlos Leguizamon Guillaumet
- **Related ADRs:** [0001 — Snowflake-only architecture](0001-snowflake-only-architecture.md)

## Context

When a parent entity consolidates a subsidiary that keeps its books in a
foreign functional currency, every line item must be translated into the
parent's presentation currency. The translation produces a residual amount
that does not balance to zero — the **Cumulative Translation Adjustment
(CTA)**. Where this residual lives in the consolidated balance sheet, and
which exchange rates are applied to which accounts, are governed by the
**translation method**.

There are two methods recognized by IFRS (IAS 21) and US GAAP (ASC 830):

1. **Current-rate method** — used when the subsidiary's functional currency
   is its local currency (the most common case). All assets and liabilities
   are translated at the **closing rate** on the balance sheet date. Income
   statement items are translated at the **average rate** for the period.
   Equity is translated at **historical rates** (the rate in effect when each
   equity transaction occurred). The residual goes to **Other Comprehensive
   Income (OCI)** as CTA, accumulating in equity, and is recycled to P&L
   only on disposal of the subsidiary.

2. **Temporal method** — used when the subsidiary's functional currency is
   the parent's currency (the subsidiary is essentially an extension of the
   parent, e.g., a sales office that books in local currency but operates
   in USD). Monetary items (cash, receivables, payables, debt) are
   translated at the closing rate; non-monetary items measured at historical
   cost (inventory, PP&E, equity) are translated at historical rates;
   income statement items at the rate when the underlying transaction
   occurred (often approximated by the average rate, except for COGS and
   D&A which are tied to historical rates of the underlying assets). The
   residual goes directly to **P&L** as an FX gain/loss.

The choice of method is **not optional**. It is determined by the functional
currency assessment of the subsidiary, which is itself driven by where the
subsidiary's cash flows, sales prices, costs, and financing are denominated
(IAS 21 paragraphs 9-14, ASC 830-10-45-2 onwards). For Andina Holdings'
subsidiaries:

| Entity              | Local CCY | Functional CCY | Implied method     |
| ------------------- | --------- | -------------- | ------------------ |
| Andina Brasil Ltda  | BRL       | BRL            | Current-rate       |
| Andina Chile SpA    | CLP       | CLP            | Current-rate       |
| Andina Perú SAC     | PEN       | PEN            | Current-rate       |
| Andina USA Inc      | USD       | USD            | None (same as pres.)|
| Andina Holdings SA  | ARS       | ARS            | Current-rate (presentation = USD) |

All foreign subsidiaries have their functional currency equal to their local
currency. This is the standard, expected assumption for entities that
operate, sell, source, and finance in their home market.

## Decision

**ConsolidAR will implement the current-rate method exclusively.** No
temporal-method translation logic will be built.

The implementation will:

1. Maintain three rate tables (closing rate, average rate, historical rate)
   per (currency_pair, period).
2. Classify each chart-of-accounts entry by `account_type` (asset, liability,
   equity, revenue, expense) and apply the appropriate rate based on the
   classification.
3. Calculate the period CTA per entity as the difference between (a) the sum
   of translated trial-balance debits and credits at line-level rates and
   (b) the entity's translated net assets at the closing rate.
4. Post the CTA as a journal line into a dedicated `CTA` account within
   equity, in a dedicated `eliminations_and_adjustments` ledger.
5. Maintain a `cta_walk` mart showing opening CTA, period movement, and
   closing CTA per entity and per consolidation period.

## Alternatives considered

### Implement both methods with a flag per entity

Rejected. Adds substantial complexity (different rate selection rules per
account category, different residual placement, recycling logic on disposal)
for zero realized benefit in this dataset. None of the Andina entities have
a functional currency different from their local currency.

A production consolidation system at a real multinational would need both
methods because functional currency assessment varies by entity and can
change over time. That is out of scope for this implementation.

### Use a single average rate for all P&L items (simplified)

Rejected as the **default** behavior, accepted as an **approximation
documented in the code**. Strictly, IAS 21 requires the rate at the
transaction date for income statement items, with the average period rate
allowed only when rates do not fluctuate significantly. In a real Andean
context (ARS especially), this assumption is questionable. The
implementation will:

- Default to monthly-average rate for P&L translation (the practical norm
  even at large multinationals).
- Flag this assumption explicitly in the `int_translated_balances` model
  documentation.
- Provide a hook for future replacement with transaction-date rates if the
  dataset is enriched to include posting dates with daily rates.

### Recycling of CTA to P&L on disposal

Out of scope. The synthetic dataset does not model disposal events.

## Consequences

### Positive

- The accounting logic is tractable and can be tested rigorously. CTA is
  deterministic given a set of rates and balances, and the trial-balance
  consolidation test ("debits equal credits after translation, in USD") is
  a hard pass/fail check that catches any rate-application bug.
- The current-rate method is what 80%+ of real consolidations use, so
  building it correctly is a stronger technical signal than building both
  superficially.
- The CTA mechanic showcases the difference between debit/credit balancing
  in local currency (always balanced) and in presentation currency (not
  balanced without the plug), which is the conceptual heart of FX
  translation. Worth surfacing in the project narrative.

### Negative

- The implementation does not exercise temporal-method logic. A reviewer
  who asks "how would you handle a subsidiary whose functional currency is
  USD but local books are in EUR?" will get a verbal answer, not a code
  walkthrough. Mitigation: this ADR itself can be cited as evidence of
  understanding the alternative.
- The average-rate-for-P&L simplification may produce minor CTA discrepancies
  versus a transaction-date-rate ground truth. Acceptable given the dataset
  is synthetic and the simplification is documented inline.

### Neutral

- The CTA account lives in equity under "Accumulated Other Comprehensive
  Income". On the synthetic chart of accounts this will be account
  `3900 - Accumulated CTA`.
- The CTA journal is generated as part of the consolidation process and
  posted into a `CONSOLIDATION` source system, distinct from the entity
  source systems, so it is traceable and auditable.

## Implementation pointers

- Rate selection: a macro `{{ select_fx_rate(account_type, period) }}` in
  dbt that returns the appropriate rate type.
- CTA calculation: an intermediate model `int_cta_movements` that joins the
  trial balance to the rate table three times (one per rate type) and
  computes the period CTA per entity as a single SQL expression.
- CTA posting: a final model `int_cta_journal` that emits journal lines in
  the same shape as the source journal_lines, enabling downstream marts to
  treat CTA like any other entry.

## References

- IAS 21 — The Effects of Changes in Foreign Exchange Rates
- ASC 830 — Foreign Currency Matters
- KPMG, "Foreign currency: Translation of financial statements" (handbook,
  general industry reference)