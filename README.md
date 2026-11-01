# Q4 Fund NAV Closing System

## Overview

This project automates the Q4 2022 closing process for The Greatness PE Fund, L.P. (GPF).

It extracts transactions from a bank statement PDF, categorizes them using an LLM, coordinates two AI agents through the A2A protocol, retrieves Q4 valuation marks, performs valuation reviews, and calculates the fund's Net Asset Value (NAV).

## Features

- PDF transaction extraction using `pdfplumber`.
- LLM-based transaction categorization using the OpenAI-compatible Groq API.
- Bank balance validation.
- Two-agent communication using A2A protocol v0.3 and JSON-RPC 2.0 over HTTP.
- Q4 valuation mark retrieval with purchase and sale verification.
- Valuation review checks:
  - R1: Material fair value movement.
  - R2: Valuation methodology change.
  - R3: Held company missing Q4 valuation mark.
  - R4: Valuation mark provided for a company no longer held.
- NAV calculation and reconciliation.
- JSON and JSONL output generation.
- Offline automated tests.

## Architecture

The application consists of two agents and supporting services.

### Agent A: Bank & Ingestion Agent

Responsibilities:
- Reads categorized bank transactions.
- Identifies investment purchases and sale proceeds.
- Communicates with Agent B.
- Provides purchase and sale information when requested.

### Agent B: Valuation Agent

Responsibilities:
- Loads Q4 valuation data.
- Initially requests purchase and sale details.
- Verifies the information received from Agent A.
- Returns Q4 valuation marks after successful validation.

### Supporting Services

- `pdf_service.py`: Extracts transactions and validates bank balances.
- `llm_service.py`: Categorizes transactions using the LLM.
- `a2a_service.py`: Starts agents and coordinates communication.
- `a2a_logger.py`: Records A2A communication in JSONL format.
- `nav_service.py`: Calculates NAV and performs valuation reviews.

## Project Structure

```text
ritamm-takehome/
│
├── agents/
│   ├── bank_agent.py
│   └── valuation_agent.py
│
├── services/
│   ├── pdf_service.py
│   ├── llm_service.py
│   ├── a2a_service.py
│   ├── a2a_logger.py
│   └── nav_service.py
│
├── tests/
│   ├── test_transactions.py
│   ├── test_nav.py
│   └── test_a2a.py
│
├── pack/
│   ├── GPF_Bank_Statement_Q4_2022.pdf
│   ├── CVP_Valuation_Report_Q3_2022.xlsx
│   ├── GPF_NAV_Summary_Q3_2022.xlsx
│   └── agent_b_data.json
│
├── output/
├── main.py
├── requirements.txt
├── README.md
├── ASSUMPTIONS.md
├── DECISIONS.md
└── .env.example
```

## Requirements

- Python 3.11 or newer.
- Groq API key.
- Internet connection for LLM categorization.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b

AGENT_A_PORT=8001
AGENT_B_PORT=8002
```

Do not commit the `.env` file.

## Execution

Run the complete application from the project root:

```bash
python main.py ./pack
```

The application performs the following steps:

1. Extracts transactions from the bank statement.
2. Validates transaction balances.
3. Categorizes transactions using the LLM.
4. Validates investment purchases and sales.
5. Starts Agent A and Agent B.
6. Executes the two-turn A2A conversation.
7. Retrieves Q4 valuation marks.
8. Performs valuation review checks.
9. Calculates and reconciles Q4 NAV.
10. Writes the output files.

## Output Files

All generated files are stored in `output/`.

| File | Description |
|---|---|
| `transactions.json` | Extracted and categorized bank transactions |
| `a2a_log.jsonl` | A2A requests and responses |
| `marks.json` | Q4 valuation marks |
| `review.json` | Valuation review results and flags |
| `nav.json` | Final NAV and reconciliation bridge |

## Testing

Run the automated tests:

```bash
python -m pytest tests -v
```

The tests validate:
- Transaction output and purchase/sale identification.
- Accrual settlement classification.
- NAV calculation and bridge reconciliation.
- Valuation review flags.
- A2A communication logs.

The tests operate on generated output files and do not make LLM API calls.

## Final Result

For the supplied Q4 2022 dataset:

**Calculated Q4 NAV: USD 169,764,039.25**

The NAV bridge reconciles with a difference of USD 0.00.

## Security

- API credentials are stored in environment variables.
- The `.env` file must not be committed.
- A2A agents communicate over local HTTP endpoints.
