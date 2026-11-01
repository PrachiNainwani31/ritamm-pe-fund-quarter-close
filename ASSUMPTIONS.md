# Assumptions

This document records the accounting, valuation, and implementation assumptions used in the Q4 2022 NAV closing process.

## 1. Transaction Processing

- The opening bank balance is USD 12,450,000.
- Transactions are extracted from the supplied Q4 bank statement.
- The extracted debit, credit, and running balance values are used for bank reconciliation.
- Each transaction is assigned one category from the supported transaction categories.
- Investment purchases and sale proceeds are validated against Agent B's supplied data.
- Company names are normalized before matching.

## 2. Transaction Categories

The following categories are used:

- capital_call
- distribution
- management_fee
- investment_purchase
- sale_proceeds
- dividend_income
- interest_income
- bank_charges
- expense
- expense_refund
- accrual_settlement

Payments settling liabilities already recorded in the Q3 NAV are classified as `accrual_settlement`, not as new Q4 expenses.

The following payments are treated as settlements of existing liabilities:

- USD 65,000 paid to Harbourside Fund Services.
- USD 120,000 paid to Coral & Finch LLP.

## 3. Valuation Assumptions

- Q3 valuation data is taken from the supplied Q3 valuation workbook.
- Q4 valuation marks are obtained from Agent B.
- Companies sold during Q4 are excluded from Q4 investment holdings.
- Ionmere Materials Ltd was purchased during Q4 for USD 14,000,000.
- Since no Q4 valuation mark is supplied for Ionmere, its value is carried at its recent purchase cost.
- Cost basis is retained using the applicable historical purchase-date conversion basis.

## 4. Foreign Currency Conversion

- Q4 EUR-denominated valuation marks are converted into USD using an EUR/USD rate of 1.0666.
- The rate represents the selected 30 December 2022 conversion rate because 31 December 2022 was a Saturday.
- Ember Retail GmbH's historical USD cost basis is USD 14,184,000, as recorded in the supplied Q3 valuation data.
- Ember's Q3 and Q4 fair values are compared in EUR to avoid treating exchange-rate movement as an underlying valuation movement.

## 5. Valuation Review Rules

The valuation review uses a materiality threshold of 15%.

### R1 – Material valuation movement

A review flag is raised when the absolute percentage change in fair value exceeds 15%.

### R2 – Valuation methodology change

A review flag is raised when the Q4 valuation methodology differs from the Q3 methodology.

### R3 – Missing Q4 valuation

A review flag is raised when a company held at 31 December 2022 has no Q4 valuation mark.

When applicable, a recent purchase is carried at cost.

### R4 – Mark for a company no longer held

A review flag is raised when Agent B supplies a Q4 valuation mark for a company that is no longer held by the fund.

## 6. NAV Calculation

The NAV is calculated as:

```text
NAV = Closing Cash + Investments - Liabilities
```

The NAV bridge is calculated as:

```text
Q4 NAV =
    Q3 NAV
    + Capital Calls
    - Distributions
    + Income
    - Expenses
    + Realized Gain
    + Change in Unrealized Gain
```

Q4 expenses include:
- Management fees.
- Other expenses paid during Q4, net of refunds.
- Bank charges.
- Q4 accrued expenses.

Payments settling previously recorded Q3 liabilities are excluded from Q4 expenses.

Realized gain is calculated as sale proceeds less the sold investment's cost basis.

Change in unrealized gain is calculated as Q4 unrealized gain less Q3 unrealized gain.

## 7. A2A Communication

- Agent A and Agent B communicate through JSON-RPC 2.0 over HTTP.
- The A2A interaction follows a two-turn request and response flow.
- Agent B first requests purchase and sale details.
- Agent A provides the requested information.
- Agent B returns Q4 marks after validation.

## 8. Limitations

- LLM transaction categorization depends on the availability and response quality of the configured API.
- The implementation is designed around the supplied fund data and input document formats.
- The Q4 accrual and historical liability information is based on the supplied workbooks.
- The review threshold is configurable in the NAV service.
