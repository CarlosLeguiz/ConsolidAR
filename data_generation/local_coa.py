"""Local chart of accounts builder for ConsolidAR.

Defines the per-entity local charts of accounts that mirror the formats
used by real ERPs in each subsidiary's country:

  AR_HOLD: dotted hierarchical, e.g., 1.1.1.01  (Argentine RT/NIIF style)
  BR_RET:  dotted extended hierarchical, e.g., 1.1.01.001  (Brazilian CFC)
  CL_RET:  flat eight-digit numeric, e.g., 11010001  (Chilean SII style)
  PE_MFG:  flat four-digit numeric, e.g., 1011  (Peruvian PCGE)
  US_DIST: flat five-digit numeric, e.g., 10100  (US GAAP common)

Each row represents one local account in one entity's books. The mapping
to the corporate chart of accounts lives in a separate module (coa_mapping)
so that re-coding a local account does not force the mapping to change.

Account names are deliberately in the local language to reflect how an ERP
extract would look in practice. The account_name_english column provides a
normalized label for analyst readability without disturbing the local
ground truth.
"""

from typing import Final

import pandas as pd

# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

_COLUMN_ORDER: Final[list[str]] = [
    "entity_id",
    "account_code_local",
    "account_name_local",
    "account_name_english",
    "account_type",
    "account_subtype",
    "is_intercompany_natural",
]


# ---------------------------------------------------------------------------
# Andina Holdings SA (AR) — Argentine RT/NIIF style, dotted hierarchical
# ---------------------------------------------------------------------------
# Format: <bucket>.<group>.<subgroup>.<sequence>
# Bucket: 1=Asset, 2=Liability, 3=Equity, 4=Revenue, 5=Expense

_AR_HOLD_ACCOUNTS: Final[list[tuple]] = [
    # Assets
    ("1.1.1.01", "Caja y Equivalentes",            "Cash and Cash Equivalents",      "ASSET",     "CURRENT_ASSET",     False),
    ("1.1.1.02", "Cuentas por Cobrar Comerciales", "Trade Accounts Receivable",      "ASSET",     "CURRENT_ASSET",     False),
    ("1.1.1.03", "Cuentas por Cobrar Intercompany","Intercompany Receivables",       "ASSET",     "CURRENT_ASSET",     True),
    ("1.1.2.01", "Inversiones en Subsidiarias",    "Investments in Subsidiaries",    "ASSET",     "NON_CURRENT_ASSET", True),
    ("1.1.2.02", "Bienes de Uso",                  "Property Plant Equipment",       "ASSET",     "NON_CURRENT_ASSET", False),
    ("1.1.2.03", "Amortizacion Acumulada",         "Accumulated Depreciation",       "ASSET",     "NON_CURRENT_ASSET", False),
    # Liabilities
    ("2.1.1.01", "Cuentas por Pagar Comerciales",  "Trade Accounts Payable",         "LIABILITY", "CURRENT_LIABILITY", False),
    ("2.1.1.02", "Cuentas por Pagar Intercompany", "Intercompany Payables",          "LIABILITY", "CURRENT_LIABILITY", True),
    ("2.1.1.03", "Cargas Sociales y Sueldos",      "Accrued Payroll",                "LIABILITY", "CURRENT_LIABILITY", False),
    ("2.1.2.01", "Deuda Bancaria de Largo Plazo",  "Long-term Bank Debt",            "LIABILITY", "NON_CURRENT_LIABILITY", False),
    ("2.1.2.02", "Impuesto Diferido Pasivo",       "Deferred Tax Liability",         "LIABILITY", "NON_CURRENT_LIABILITY", False),
    # Equity
    ("3.1.1.01", "Capital Social",                 "Common Stock",                   "EQUITY",    "SHARE_CAPITAL",     False),
    ("3.1.1.02", "Aportes Irrevocables",           "Additional Paid-in Capital",     "EQUITY",    "SHARE_CAPITAL",     False),
    ("3.1.2.01", "Resultados Acumulados",          "Retained Earnings",              "EQUITY",    "RETAINED_EARNINGS", False),
    # Revenue
    ("4.1.1.01", "Honorarios de Direccion",        "Management Fees - External",     "REVENUE",   "OPERATING_REVENUE", False),
    ("4.1.1.02", "Honorarios Intercompany",        "Management Fees - Intercompany", "REVENUE",   "OPERATING_REVENUE", True),
    ("4.1.2.01", "Ingresos Financieros",           "Interest Income",                "REVENUE",   "OTHER_INCOME",      False),
    # Expenses
    ("5.1.1.01", "Sueldos y Jornales",             "Payroll Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.1.1.02", "Cargas Sociales",                "Payroll Taxes",                  "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.1.2.01", "Alquileres",                     "Rent Expense",                   "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.1.2.02", "Servicios Profesionales",        "Professional Services",          "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.1.2.03", "Amortizacion del Ejercicio",     "Depreciation Expense",           "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.1.3.01", "Intereses Pagados",              "Interest Expense",               "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("5.1.3.02", "Diferencia de Cambio",           "Foreign Exchange Gain/Loss",     "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("5.1.4.01", "Impuesto a las Ganancias",       "Income Tax Expense",             "EXPENSE",   "INCOME_TAX",        False),
]


# ---------------------------------------------------------------------------
# Andina Brasil Ltda (BR) — Brazilian CFC style, dotted extended hierarchical
# ---------------------------------------------------------------------------
# Format: <bucket>.<group>.<subgroup>.<sequence>
# Like Argentine but with three-digit sequence terminal block.

_BR_RET_ACCOUNTS: Final[list[tuple]] = [
    # Assets
    ("1.1.01.001", "Caixa e Equivalentes",        "Cash and Cash Equivalents",      "ASSET",     "CURRENT_ASSET",     False),
    ("1.1.01.002", "Clientes a Receber",          "Trade Accounts Receivable",      "ASSET",     "CURRENT_ASSET",     False),
    ("1.1.01.003", "Clientes Intercompany",       "Intercompany Receivables",       "ASSET",     "CURRENT_ASSET",     True),
    ("1.1.02.001", "Estoques",                    "Inventory",                      "ASSET",     "CURRENT_ASSET",     False),
    ("1.1.02.002", "Despesas Antecipadas",        "Prepaid Expenses",               "ASSET",     "CURRENT_ASSET",     False),
    ("1.2.01.001", "Imobilizado",                 "Property Plant Equipment",       "ASSET",     "NON_CURRENT_ASSET", False),
    ("1.2.01.002", "Depreciacao Acumulada",       "Accumulated Depreciation",       "ASSET",     "NON_CURRENT_ASSET", False),
    # Liabilities
    ("2.1.01.001", "Fornecedores",                "Trade Accounts Payable",         "LIABILITY", "CURRENT_LIABILITY", False),
    ("2.1.01.002", "Fornecedores Intercompany",   "Intercompany Payables",          "LIABILITY", "CURRENT_LIABILITY", True),
    ("2.1.01.003", "Obrigacoes Trabalhistas",     "Accrued Payroll",                "LIABILITY", "CURRENT_LIABILITY", False),
    ("2.1.01.004", "Tributos a Recolher",         "Tax Liabilities Short-term",     "LIABILITY", "CURRENT_LIABILITY", False),
    ("2.2.01.001", "Emprestimos Longo Prazo",     "Long-term Bank Debt",            "LIABILITY", "NON_CURRENT_LIABILITY", False),
    ("2.2.01.002", "Emprestimos IC Longo Prazo",  "Intercompany Long-term Debt",    "LIABILITY", "NON_CURRENT_LIABILITY", True),
    # Equity
    ("3.1.01.001", "Capital Social",              "Common Stock",                   "EQUITY",    "SHARE_CAPITAL",     False),
    ("3.1.02.001", "Lucros Acumulados",           "Retained Earnings",              "EQUITY",    "RETAINED_EARNINGS", False),
    # Revenue
    ("4.1.01.001", "Receita de Vendas",           "Revenue - Products",             "REVENUE",   "OPERATING_REVENUE", False),
    ("4.1.01.002", "Receita de Servicos",         "Revenue - Services",             "REVENUE",   "OPERATING_REVENUE", False),
    ("4.1.02.001", "Receita Intercompany",        "Revenue - Intercompany",         "REVENUE",   "OPERATING_REVENUE", True),
    # Expenses
    ("5.1.01.001", "Custo das Mercadorias Vendidas","Cost of Goods Sold",           "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.1.01.002", "CMV Intercompany",            "COGS - Intercompany",            "EXPENSE",   "OPERATING_EXPENSE", True),
    ("5.2.01.001", "Despesas com Vendas",         "Selling Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.2.01.002", "Despesas Administrativas",    "General and Administrative",     "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.2.01.003", "Salarios e Encargos",         "Payroll Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.2.01.004", "Aluguel",                     "Rent Expense",                   "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.2.01.005", "Depreciacao do Exercicio",    "Depreciation Expense",           "EXPENSE",   "OPERATING_EXPENSE", False),
    ("5.2.02.001", "Honorarios IC",               "Management Fees IC",             "EXPENSE",   "OPERATING_EXPENSE", True),
    ("5.3.01.001", "Despesas Financeiras",        "Interest Expense",               "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("5.3.01.002", "Despesas Financeiras IC",     "Interest Expense IC",            "EXPENSE",   "NON_OPERATING_EXPENSE", True),
    ("5.3.02.001", "Variacao Cambial",            "Foreign Exchange Gain/Loss",     "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("5.4.01.001", "IRPJ e CSLL",                 "Income Tax Expense",             "EXPENSE",   "INCOME_TAX",        False),
]


# ---------------------------------------------------------------------------
# Andina Chile SpA (CL) — Chilean SII style, flat eight-digit numeric
# ---------------------------------------------------------------------------
# Format: AABBCCDD where AA=bucket, BB=group, CC=subgroup, DD=sequence
# Bucket: 11=Asset, 21=Liability, 31=Equity, 41=Revenue, 51=Expense

_CL_RET_ACCOUNTS: Final[list[tuple]] = [
    # Assets
    ("11010001", "Caja y Banco",                   "Cash and Cash Equivalents",      "ASSET",     "CURRENT_ASSET",     False),
    ("11010002", "Deudores por Venta",             "Trade Accounts Receivable",      "ASSET",     "CURRENT_ASSET",     False),
    ("11010003", "Deudores Empresas Relacionadas", "Intercompany Receivables",       "ASSET",     "CURRENT_ASSET",     True),
    ("11020001", "Existencias",                    "Inventory",                      "ASSET",     "CURRENT_ASSET",     False),
    ("11020002", "Gastos Pagados por Anticipado",  "Prepaid Expenses",               "ASSET",     "CURRENT_ASSET",     False),
    ("12010001", "Activo Fijo",                    "Property Plant Equipment",       "ASSET",     "NON_CURRENT_ASSET", False),
    ("12010002", "Depreciacion Acumulada",         "Accumulated Depreciation",       "ASSET",     "NON_CURRENT_ASSET", False),
    # Liabilities
    ("21010001", "Proveedores",                    "Trade Accounts Payable",         "LIABILITY", "CURRENT_LIABILITY", False),
    ("21010002", "Cuentas por Pagar Relacionadas", "Intercompany Payables",          "LIABILITY", "CURRENT_LIABILITY", True),
    ("21010003", "Provision Remuneraciones",       "Accrued Payroll",                "LIABILITY", "CURRENT_LIABILITY", False),
    ("21010004", "Impuestos por Pagar",            "Tax Liabilities Short-term",     "LIABILITY", "CURRENT_LIABILITY", False),
    ("22010001", "Obligaciones con Bancos LP",     "Long-term Bank Debt",            "LIABILITY", "NON_CURRENT_LIABILITY", False),
    # Equity
    ("31010001", "Capital",                        "Common Stock",                   "EQUITY",    "SHARE_CAPITAL",     False),
    ("31020001", "Utilidades Acumuladas",          "Retained Earnings",              "EQUITY",    "RETAINED_EARNINGS", False),
    # Revenue
    ("41010001", "Ventas Nacionales",              "Revenue - Products",             "REVENUE",   "OPERATING_REVENUE", False),
    ("41010002", "Ingresos por Servicios",         "Revenue - Services",             "REVENUE",   "OPERATING_REVENUE", False),
    ("41020001", "Ventas Intercompany",            "Revenue - Intercompany",         "REVENUE",   "OPERATING_REVENUE", True),
    # Expenses
    ("51010001", "Costo de Ventas",                "Cost of Goods Sold",             "EXPENSE",   "OPERATING_EXPENSE", False),
    ("51010002", "Costo de Ventas IC",             "COGS - Intercompany",            "EXPENSE",   "OPERATING_EXPENSE", True),
    ("52010001", "Gastos de Comercializacion",     "Selling Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("52010002", "Gastos de Administracion",       "General and Administrative",     "EXPENSE",   "OPERATING_EXPENSE", False),
    ("52010003", "Remuneraciones",                 "Payroll Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("52010004", "Arriendos",                      "Rent Expense",                   "EXPENSE",   "OPERATING_EXPENSE", False),
    ("52010005", "Depreciacion del Ejercicio",     "Depreciation Expense",           "EXPENSE",   "OPERATING_EXPENSE", False),
    ("52020001", "Honorarios IC",                  "Management Fees IC",             "EXPENSE",   "OPERATING_EXPENSE", True),
    ("53010001", "Gastos Financieros",             "Interest Expense",               "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("53020001", "Diferencias de Cambio",          "Foreign Exchange Gain/Loss",     "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("54010001", "Impuesto a la Renta",            "Income Tax Expense",             "EXPENSE",   "INCOME_TAX",        False),
]


# ---------------------------------------------------------------------------
# Andina Peru SAC (PE) — Peruvian PCGE style, flat four-digit numeric
# ---------------------------------------------------------------------------
# Format: ABCD where A=bucket digit, BCD=sequence
# Peruvian Plan Contable General Empresarial uses dense 4-digit codes.

_PE_MFG_ACCOUNTS: Final[list[tuple]] = [
    # Assets
    ("1011", "Caja MN",                            "Cash and Cash Equivalents",      "ASSET",     "CURRENT_ASSET",     False),
    ("1212", "Facturas por Cobrar",                "Trade Accounts Receivable",      "ASSET",     "CURRENT_ASSET",     False),
    ("1213", "Cuentas por Cobrar Vinculadas",      "Intercompany Receivables",       "ASSET",     "CURRENT_ASSET",     True),
    ("2011", "Mercaderias",                        "Inventory",                      "ASSET",     "CURRENT_ASSET",     False),
    ("2021", "Productos Terminados",               "Finished Goods Inventory",       "ASSET",     "CURRENT_ASSET",     False),
    ("3311", "Maquinaria y Equipo",                "Property Plant Equipment",       "ASSET",     "NON_CURRENT_ASSET", False),
    ("3911", "Depreciacion Acumulada",             "Accumulated Depreciation",       "ASSET",     "NON_CURRENT_ASSET", False),
    # Liabilities
    ("4212", "Facturas por Pagar",                 "Trade Accounts Payable",         "LIABILITY", "CURRENT_LIABILITY", False),
    ("4213", "Cuentas por Pagar Vinculadas",       "Intercompany Payables",          "LIABILITY", "CURRENT_LIABILITY", True),
    ("4111", "Sueldos por Pagar",                  "Accrued Payroll",                "LIABILITY", "CURRENT_LIABILITY", False),
    ("4011", "IGV por Pagar",                      "Tax Liabilities Short-term",     "LIABILITY", "CURRENT_LIABILITY", False),
    ("4511", "Obligaciones Financieras",           "Long-term Bank Debt",            "LIABILITY", "NON_CURRENT_LIABILITY", False),
    # Equity
    ("5011", "Capital Social",                     "Common Stock",                   "EQUITY",    "SHARE_CAPITAL",     False),
    ("5911", "Resultados Acumulados",              "Retained Earnings",              "EQUITY",    "RETAINED_EARNINGS", False),
    # Revenue
    ("7011", "Ventas Mercaderias",                 "Revenue - Products",             "REVENUE",   "OPERATING_REVENUE", False),
    ("7012", "Ventas Productos Terminados",        "Revenue - Manufactured Goods",   "REVENUE",   "OPERATING_REVENUE", False),
    ("7013", "Ventas Intercompany",                "Revenue - Intercompany",         "REVENUE",   "OPERATING_REVENUE", True),
    # Expenses
    ("6911", "Costo de Ventas Mercaderias",        "Cost of Goods Sold",             "EXPENSE",   "OPERATING_EXPENSE", False),
    ("6912", "Costo de Ventas IC",                 "COGS - Intercompany",            "EXPENSE",   "OPERATING_EXPENSE", True),
    ("9411", "Gastos de Ventas",                   "Selling Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("9412", "Gastos Administrativos",             "General and Administrative",     "EXPENSE",   "OPERATING_EXPENSE", False),
    ("6211", "Sueldos y Salarios",                 "Payroll Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("6353", "Alquileres",                         "Rent Expense",                   "EXPENSE",   "OPERATING_EXPENSE", False),
    ("6814", "Depreciacion Activo Fijo",           "Depreciation Expense",           "EXPENSE",   "OPERATING_EXPENSE", False),
    ("6391", "Honorarios IC",                      "Management Fees IC",             "EXPENSE",   "OPERATING_EXPENSE", True),
    ("6711", "Intereses por Prestamos",            "Interest Expense",               "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("6761", "Diferencia de Cambio",               "Foreign Exchange Gain/Loss",     "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("8811", "Impuesto a la Renta",                "Income Tax Expense",             "EXPENSE",   "INCOME_TAX",        False),
]


# ---------------------------------------------------------------------------
# Andina USA Inc (US) — US GAAP common, flat five-digit numeric
# ---------------------------------------------------------------------------
# Format: ABCDE where A=bucket digit, BCDE=sequence
# Common US small-mid-cap convention. No leading zero on bucket digit.

_US_DIST_ACCOUNTS: Final[list[tuple]] = [
    # Assets
    ("10100", "Cash - Operating",                  "Cash and Cash Equivalents",      "ASSET",     "CURRENT_ASSET",     False),
    ("12000", "Accounts Receivable",               "Trade Accounts Receivable",      "ASSET",     "CURRENT_ASSET",     False),
    ("12500", "Accounts Receivable - IC",          "Intercompany Receivables",       "ASSET",     "CURRENT_ASSET",     True),
    ("13000", "Inventory - Distribution",          "Inventory",                      "ASSET",     "CURRENT_ASSET",     False),
    ("14000", "Prepaid Expenses",                  "Prepaid Expenses",               "ASSET",     "CURRENT_ASSET",     False),
    ("15000", "Fixed Assets",                      "Property Plant Equipment",       "ASSET",     "NON_CURRENT_ASSET", False),
    ("15500", "Accumulated Depreciation",          "Accumulated Depreciation",       "ASSET",     "NON_CURRENT_ASSET", False),
    # Liabilities
    ("20100", "Accounts Payable",                  "Trade Accounts Payable",         "LIABILITY", "CURRENT_LIABILITY", False),
    ("20500", "Accounts Payable - IC",             "Intercompany Payables",          "LIABILITY", "CURRENT_LIABILITY", True),
    ("21000", "Accrued Payroll",                   "Accrued Payroll",                "LIABILITY", "CURRENT_LIABILITY", False),
    ("21500", "Sales Tax Payable",                 "Tax Liabilities Short-term",     "LIABILITY", "CURRENT_LIABILITY", False),
    ("25000", "Long-term Debt",                    "Long-term Bank Debt",            "LIABILITY", "NON_CURRENT_LIABILITY", False),
    # Equity
    ("30100", "Common Stock",                      "Common Stock",                   "EQUITY",    "SHARE_CAPITAL",     False),
    ("30200", "Additional Paid-in Capital",        "Additional Paid-in Capital",     "EQUITY",    "SHARE_CAPITAL",     False),
    ("31000", "Retained Earnings",                 "Retained Earnings",              "EQUITY",    "RETAINED_EARNINGS", False),
    # Revenue
    ("40100", "Net Sales - Distribution",          "Revenue - Products",             "REVENUE",   "OPERATING_REVENUE", False),
    ("40500", "Net Sales - Intercompany",          "Revenue - Intercompany",         "REVENUE",   "OPERATING_REVENUE", True),
    ("41000", "Royalty Income",                    "Royalty Income",                 "REVENUE",   "OTHER_INCOME",      False),
    # Expenses
    ("50100", "Cost of Goods Sold",                "Cost of Goods Sold",             "EXPENSE",   "OPERATING_EXPENSE", False),
    ("50500", "Cost of Goods Sold - IC",           "COGS - Intercompany",            "EXPENSE",   "OPERATING_EXPENSE", True),
    ("60100", "Selling Expense",                   "Selling Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("60200", "General and Administrative",        "General and Administrative",     "EXPENSE",   "OPERATING_EXPENSE", False),
    ("60300", "Payroll Expense",                   "Payroll Expense",                "EXPENSE",   "OPERATING_EXPENSE", False),
    ("60400", "Rent Expense",                      "Rent Expense",                   "EXPENSE",   "OPERATING_EXPENSE", False),
    ("60500", "Depreciation Expense",              "Depreciation Expense",           "EXPENSE",   "OPERATING_EXPENSE", False),
    ("60900", "Management Fees - IC",              "Management Fees IC",             "EXPENSE",   "OPERATING_EXPENSE", True),
    ("70100", "Interest Expense",                  "Interest Expense",               "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("70900", "Foreign Exchange Gain/Loss",        "Foreign Exchange Gain/Loss",     "EXPENSE",   "NON_OPERATING_EXPENSE", False),
    ("80100", "Income Tax Expense",                "Income Tax Expense",             "EXPENSE",   "INCOME_TAX",        False),
]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

_ACCOUNTS_BY_ENTITY: Final[dict[str, list[tuple]]] = {
    "AR_HOLD": _AR_HOLD_ACCOUNTS,
    "BR_RET":  _BR_RET_ACCOUNTS,
    "CL_RET":  _CL_RET_ACCOUNTS,
    "PE_MFG":  _PE_MFG_ACCOUNTS,
    "US_DIST": _US_DIST_ACCOUNTS,
}


def build_local_coa_df() -> pd.DataFrame:
    """Build the local charts of accounts DataFrame across all entities.

    Returns a DataFrame with one row per (entity_id, account_code_local).
    Each entity contributes its own block; the entity_id column makes the
    combined table queryable by entity downstream.
    """
    rows: list[tuple] = []
    for entity_id, accounts in _ACCOUNTS_BY_ENTITY.items():
        for acc in accounts:
            rows.append((entity_id, *acc))

    df = pd.DataFrame(rows, columns=_COLUMN_ORDER)

    df = df.astype({
        "entity_id": "string",
        "account_code_local": "string",
        "account_name_local": "string",
        "account_name_english": "string",
        "account_type": "string",
        "account_subtype": "string",
        "is_intercompany_natural": "boolean",
    })

    return df


def validate_local_coa_df(df: pd.DataFrame) -> None:
    """Run business-rule validations on the local CoA DataFrame.

    Raises AssertionError if any rule is violated.
    """
    # Composite key uniqueness: (entity_id, account_code_local)
    duplicates = df.duplicated(subset=["entity_id", "account_code_local"])
    assert not duplicates.any(), (
        "Composite key (entity_id, account_code_local) must be unique; "
        f"found {duplicates.sum()} duplicates"
    )

    # account_type within the canonical five
    valid_types = {"ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"}
    invalid_types = set(df["account_type"]) - valid_types
    assert not invalid_types, f"Invalid account_type values: {invalid_types}"

    # Each entity has at least one account of each fundamental type that a
    # going concern must have postings for. Equity is optional for some
    # entities in the synthetic dataset, so we relax that to A/L/R/E only.
    required_types = {"ASSET", "LIABILITY", "REVENUE", "EXPENSE"}
    for entity_id in df["entity_id"].unique():
        entity_types = set(df[df["entity_id"] == entity_id]["account_type"])
        missing = required_types - entity_types
        assert not missing, (
            f"Entity {entity_id} missing account types: {missing}"
        )

    # Every entity has at least one IC-natural account (the dataset is
    # multi-entity and consolidation requires IC volume)
    for entity_id in df["entity_id"].unique():
        ic_count = df[
            (df["entity_id"] == entity_id) & df["is_intercompany_natural"]
        ].shape[0]
        assert ic_count > 0, (
            f"Entity {entity_id} has no intercompany-natural accounts; "
            "at least one is required for the matching engine to do work"
        )