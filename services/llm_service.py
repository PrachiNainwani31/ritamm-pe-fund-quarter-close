
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import unicodedata

load_dotenv()

CATEGORIES = {
    "capital_call",
    "distribution",
    "management_fee",
    "investment_purchase",
    "sale_proceeds",
    "dividend_income",
    "interest_income",
    "bank_charges",
    "expense",
    "expense_refund",
    "accrual_settlement"
}


def get_client():
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")

    if not api_key or not base_url or not model:
        raise ValueError("Missing LLM_API_KEY, LLM_BASE_URL or LLM_MODEL in .env")

    return OpenAI(
        api_key=api_key,
        base_url=base_url
    ), model



def normalize_company(name):
    if not name:
        return None

    # Remove accents and convert to lowercase
    normalized = unicodedata.normalize("NFKD", name)
    normalized = "".join(
        ch for ch in normalized
        if not unicodedata.combining(ch)
    ).lower().strip()

    known_names = {
        "fjord payments as": "Fjord Payments AS",
        "ionmere materials ltd": "Ionmere Materials Ltd"
    }

    return known_names.get(normalized, name.strip())

def categorize_batch(transactions):
    client, model = get_client()

    prompt = f"""
You are a financial bank transaction classification assistant.

Classify every transaction into exactly one category from:

{sorted(CATEGORIES)}

Rules:
1. Capital call: money received from fund investors.
2. Distribution: money paid to fund investors.
3. Management fee: fee paid to fund manager.
4. Investment purchase: fund buys a company stake.
5. Sale proceeds: fund receives money from selling a company stake.
6. Dividend income: dividends received from portfolio companies.
7. Interest income: bank interest received.
8. Bank charges: bank maintenance fees and wire charges.
9. Expense: other operational, legal, audit, insurance and administration expenses.
10. Expense refund: refund received against an earlier expense.
11. Accrual settlement: payment settling an expense liability already recorded previously.

Extraction:
- For capital_call and distribution, extract LP code such as LP01, LP02.
- For investment_purchase and sale_proceeds, extract
  the portfolio company whose ownership is being purchased or sold.

IMPORTANT:
- Do NOT extract the bank counterparty as the company.
- For a sale, identify the company being sold, not the buyer.
- For example:
  "INWARD WIRE NORDIC ACQUISITIONS AS SPA
   FJORD PAYMENTS AS COMPLETION"
  means company = "Fjord Payments AS".

- For a purchase, identify the company whose shares
  the fund is purchasing.
- Return company names in proper title case.
- Do not invent information.
- For other categories, company and lp_code must be null.

Transactions:
{json.dumps(transactions, indent=2)}

Return ONLY valid JSON in this exact structure:

{{
  "transactions": [
    {{
      "index": 0,
      "category": "capital_call",
      "lp_code": "LP01",
      "company": null
    }}
  ]
}}

Include exactly one result for every input transaction.
Keep the original transaction order and index.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You classify financial transactions accurately. Return JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return result["transactions"]


def categorize_transactions(transactions, batch_size=8):
    categorized = []

    for start in range(0, len(transactions), batch_size):
        batch = transactions[start:start + batch_size]

        # Send only necessary information to the LLM
        inputs = [
            {
                "index": start + i,
                "date": tx["date"],
                "description": tx["description"],
                "reference": tx["reference"],
                "debit": tx["debit"],
                "credit": tx["credit"]
            }
            for i, tx in enumerate(batch)
        ]

        results = categorize_batch(inputs)

        # Validate returned results
        if len(results) != len(batch):
            raise ValueError("LLM returned an incorrect number of classifications")

        by_index = {}

        for item in results:
            idx = item.get("index")
            if idx not in range(start, start + len(batch)):
                raise ValueError(f"Invalid transaction index: {idx}")

            if idx in by_index:
                raise ValueError(f"Duplicate transaction index: {idx}")

            category = item.get("category")

            if category not in CATEGORIES:
                raise ValueError(f"Invalid category: {category}")

            lp_code = item.get("lp_code")
            company = item.get("company")

            if category in {"capital_call", "distribution"}:
                if lp_code is not None and (
                    not isinstance(lp_code, str)
                    or not lp_code.startswith("LP")
                ):
                    raise ValueError(f"Invalid LP code: {lp_code}")
                company = None

            elif category in {"investment_purchase", "sale_proceeds"}:
                lp_code = None
                company = normalize_company(company)

            else:
                lp_code = None
                company = None

            by_index[idx] = {
                "category": category,
                "lp_code": lp_code,
                "company": company
            }

        if len(by_index) != len(batch):
            raise ValueError("LLM omitted one or more transactions")

        for i, tx in enumerate(batch):
            idx = start + i
            tx.update(by_index[idx])
            categorized.append(tx)

    return categorized
