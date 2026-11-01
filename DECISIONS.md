# Technical Decisions

This document describes the main implementation decisions and their rationale.

## 1. Python

Python was selected because of its libraries for PDF extraction, spreadsheet processing, API development, and financial calculations.

## 2. PDF Extraction

`pdfplumber` is used to extract transaction information from the supplied bank statement.

This keeps the extraction process local and avoids requiring a separate document-processing service.

## 3. LLM-Based Categorization

The OpenAI-compatible Groq API is used for transaction categorization.

The LLM identifies transaction categories and extracts relevant information such as LP codes and company names.

Batch processing is used to categorize transactions efficiently.

Deterministic validation is performed after categorization to check important purchase and sale information.

## 4. Two-Agent Architecture

The application separates bank ingestion and valuation responsibilities into two agents.

**Agent A – Bank & Ingestion Agent**
- Owns the bank transaction data.
- Identifies investment purchases and sales.
- Responds to Agent B's information requests.

**Agent B – Valuation Agent**
- Owns valuation data.
- Verifies purchase and sale details.
- Provides Q4 valuation marks after validation.

This separation keeps the transaction-processing and valuation responsibilities independent.

## 5. A2A Protocol

JSON-RPC 2.0 over HTTP is used for communication between the agents, following the required A2A v0.3 interaction pattern.

The two-turn flow is used because Agent B needs purchase and sale details before releasing valuation marks.

## 6. Data Storage

JSON is used for structured output files because it is simple to inspect and integrate with other applications.

JSONL is used for A2A logging because each communication event can be stored as an independent JSON record.

## 7. Financial Precision

Python's `Decimal` type is used for NAV calculations to reduce floating-point precision errors in financial arithmetic.

## 8. Valuation Review

The review logic is implemented using deterministic rules rather than relying on the LLM.

This makes valuation flags reproducible and easier to audit.

The four review rules are implemented independently:
- R1: Material fair value movement.
- R2: Valuation methodology change.
- R3: Missing Q4 valuation for a held company.
- R4: Valuation provided for a company no longer held.

## 9. NAV Reconciliation

The final NAV is calculated independently using closing cash, investments, and liabilities.

A separate NAV bridge is calculated from Q3 NAV and Q4 movements.

The application raises an error if the two NAV values do not reconcile.

This prevents an inconsistent NAV from being silently accepted.

## 10. Testing Strategy

Pytest is used for automated validation.

The tests focus on:
- Transaction identification.
- Accrual settlement classification.
- NAV calculation.
- NAV bridge reconciliation.
- Valuation review flags.
- A2A log generation.

Tests use previously generated output files and do not require an external LLM API call.
