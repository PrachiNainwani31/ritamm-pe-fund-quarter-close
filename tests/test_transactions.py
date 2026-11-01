import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_transactions_file_exists():
    path = ROOT / "output" / "transactions.json"
    assert path.exists()


def test_purchase_and_sale():
    path = ROOT / "output" / "transactions.json"

    with open(path) as f:
        transactions = json.load(f)

    purchases = [
        tx for tx in transactions
        if tx["category"] == "investment_purchase"
    ]

    sales = [
        tx for tx in transactions
        if tx["category"] == "sale_proceeds"
    ]

    assert len(purchases) == 1
    assert purchases[0]["company"] == "Ionmere Materials Ltd"
    assert purchases[0]["debit"] == 14000000.0

    assert len(sales) == 1
    assert sales[0]["company"] == "Fjord Payments AS"
    assert sales[0]["credit"] == 29000000.0


def test_accrual_settlements():
    path = ROOT / "output" / "transactions.json"

    with open(path) as f:
        transactions = json.load(f)

    settlements = [
        tx for tx in transactions
        if tx["category"] == "accrual_settlement"
    ]

    assert len(settlements) == 2