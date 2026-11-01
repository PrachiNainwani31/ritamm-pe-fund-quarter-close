
import pdfplumber
import re
from decimal import Decimal
from datetime import datetime


DATE_PATTERN = re.compile(r"^(\d{2} [A-Z][a-z]{2} 2022)\s+(.*)$")
MONEY_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}")
REFERENCE_PATTERN = re.compile(r"\b(?:OW|IW)-\d{6}-\d{2}\b")


def to_decimal(value):
    return Decimal(value.replace(",", ""))


def extract_transactions(pdf_path):
    # Step 1: Extract text from every PDF page
    lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.splitlines())

    # Step 2: Join wrapped descriptions to their transaction
    records = []
    current = None

    for line in lines:
        line = line.strip()

        # Ignore totals and footer
        if "TOTAL DEBITS / CREDITS FOR PERIOD" in line:
            if current:
                records.append(current)
                current = None
            continue

        if "This statement is generated" in line:
            continue

        if "Meridian Trust Bank (Cayman) Ltd ·" in line:
            continue

        match = DATE_PATTERN.match(line)

        if match:
            # Ignore statement period heading
            if "–" in match.group(2):
                continue

            if current:
                records.append(current)

            current = {
                "date": match.group(1),
                "text": match.group(2)
            }

        elif current and line:
            if not any(x in line for x in [
                "Statement period",
                "Statement no.",
                "Account holder",
                "Account type",
                "Date Description",
                "Meridian Trust Bank",
                "TOTAL DEBITS",
                "This statement"
            ]):
                current["text"] += " " + line

    if current:
        records.append(current)

    # Step 3: Extract transaction fields
    transactions = []
    previous_balance = Decimal("12450000.00")

    for record in records:
        raw = record["text"]

        # Opening balance is not a transaction
        if "BALANCE BROUGHT FORWARD" in raw:
            continue

        amounts = MONEY_PATTERN.findall(raw)

        if len(amounts) < 2:
            continue

        # Last amount is the running balance
        balance = to_decimal(amounts[-1])

        # Amount immediately before balance
        amount = to_decimal(amounts[-2])

        # Determine debit or credit using balance movement
        movement = balance - previous_balance

        if movement < 0:
            debit = amount
            credit = Decimal("0.00")
        else:
            debit = Decimal("0.00")
            credit = amount

        # Extract bank reference
        ref_match = REFERENCE_PATTERN.search(raw)
        reference = ref_match.group(0) if ref_match else None

        # Clean description
        description = raw

        if reference:
            description = description.replace(reference, "")

        description = MONEY_PATTERN.sub("", description)
        description = re.sub(r"\s+", " ", description).strip()

        # Verify amount against running balance
        if abs(movement) != amount:
            raise ValueError(
                f"Balance mismatch on {record['date']}: "
                f"expected movement {movement}, found {amount}"
            )

        transactions.append({
            "date": datetime.strptime(
                record["date"], "%d %b %Y"
            ).strftime("%Y-%m-%d"),
            "description": description,
            "reference": reference,
            "debit": float(debit),
            "credit": float(credit),
            "balance": float(balance),
            "category": None,
            "lp_code": None,
            "company": None
        })

        previous_balance = balance

    return transactions


def validate_balances(transactions, opening_balance):
    balance = Decimal(str(opening_balance))

    for tx in transactions:
        debit = Decimal(str(tx["debit"]))
        credit = Decimal(str(tx["credit"]))
        actual_balance = Decimal(str(tx["balance"]))

        balance = balance - debit + credit

        if balance != actual_balance:
            raise ValueError(
                f"Incorrect balance on {tx['date']}: "
                f"calculated={balance}, "
                f"statement={actual_balance}"
            )

    return {
        "valid": True,
        "opening_balance": float(opening_balance),
        "closing_balance": float(balance),
        "transaction_count": len(transactions)
    }
