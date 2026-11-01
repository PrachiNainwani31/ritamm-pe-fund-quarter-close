
import json

from services.pdf_service import (
    extract_transactions,
    validate_balances
)
from services.nav_service import calculate_nav
from services.a2a_service import run_agents

from services.llm_service import categorize_transactions


def main():
    pdf_path = "./pack/GPF_Bank_Statement_Q4_2022.pdf"

    print("STEP 1: Extracting transactions...")

    transactions = extract_transactions(pdf_path)

    print("Extracted:", len(transactions))

    print("\nSTEP 2: Validating bank balances...")

    result = validate_balances(
        transactions,
        12450000.00
    )

    print(result)

    print("\nSTEP 3: Categorizing transactions using LLM...")

    transactions = categorize_transactions(transactions)

    print("\nCategorization completed!")

    # Save transactions
    with open("output/transactions.json", "w") as f:
        json.dump(transactions, f, indent=4)

    print("\nSaved output/transactions.json")

    print("\nCATEGORY SUMMARY:")

    summary = {}

    for tx in transactions:
        category = tx["category"]
        summary[category] = summary.get(category, 0) + 1

    for category, count in sorted(summary.items()):
        print(category, ":", count)

    print("\nSAMPLE TRANSACTIONS:")

    for tx in transactions[:5]:
        print(
            tx["date"],
            tx["description"],
            tx["category"],
            tx["lp_code"],
            tx["company"]
        )

    
    print("\nVERIFYING PURCHASES AND SALES:")

    purchase_found = False
    sale_found = False

    for tx in transactions:

        if tx["category"] == "investment_purchase":

            purchase_found = True

            assert tx["company"] == "Ionmere Materials Ltd", (
                f"Wrong purchase company: {tx['company']}"
            )

            assert tx["debit"] == 14000000.0

        elif tx["category"] == "sale_proceeds":

            sale_found = True

            assert tx["company"] == "Fjord Payments AS", (
                f"Wrong sale company: {tx['company']}"
            )

            assert tx["credit"] == 29000000.0

    assert purchase_found, "Purchase transaction missing!"
    assert sale_found, "Sale transaction missing!"

    print("Purchase and sale validation passed!")

    for tx in transactions:
        if tx["category"] in [
            "investment_purchase",
            "sale_proceeds"
        ]:
            print(tx)

    print("\nSTEP 4: Starting A2A communication...")

    marks = run_agents()

    print("\nSTEP 5: Received Q4 valuation marks!")

    print("Fund:", marks["fund"])
    print("Valuation date:", marks["valuation_date"])
    print("Number of marks:", len(marks["marks"]))

    print("\nSTEP 6: Calculating Q4 NAV...")

    nav, review = calculate_nav(
        "./pack",
        transactions,
        marks
    )
    # Save transactions after accrual settlement reclassification
    with open("output/transactions.json", "w") as f:
        json.dump(transactions, f, indent=4)
        
    with open("output/nav.json", "w") as f:
        json.dump(nav, f, indent=4)

    with open("output/review.json", "w") as f:
        json.dump({
            "threshold_pct": 15,
            "eurusd_rate": 1.0666,
            "companies": review
        }, f, indent=4)

    print("\nNAV CALCULATION COMPLETED!")
    print(json.dumps(nav, indent=4))

if __name__ == "__main__":
    main()
