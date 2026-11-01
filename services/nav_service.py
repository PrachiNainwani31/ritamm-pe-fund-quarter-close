import openpyxl

from decimal import Decimal


D = Decimal

EURUSD_RATE = D("1.0666")
THRESHOLD = D("0.15")


def load_q3_data(pack_dir):

    path = f"{pack_dir}/CVP_Valuation_Report_Q3_2022.xlsx"

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    companies = {}

    for row in ws.iter_rows(min_row=6, max_row=13, values_only=True):

        name, currency, cost, fair_value, fx, fair_usd, method, date = row

        cost_usd = D(str(cost)) if currency == "USD" else D(str(cost)) * D(str(fx))

        # Ember's cost is translated at its 2021 purchase-date FX rate.
        if name == "Ember Retail GmbH":
            cost_usd = D("14184000")

        companies[name] = {
            "currency": currency,
            "cost_usd": cost_usd,
            "fair_value": D(str(fair_value)),
            "fair_value_usd": D(str(fair_usd)),
            "method": method
        }

    return companies


def load_q3_nav(pack_dir):

    path = f"{pack_dir}/GPF_NAV_Summary_Q3_2022.xlsx"

    wb = openpyxl.load_workbook(path, data_only=True)

    ws = wb["Net assets 30 Sep 2022"]

    nav_q3 = D(str(ws["B13"].value))

    # Q3 liabilities
    old_liabilities = {
        "Audit fee accrual (Coral & Finch LLP)": D("120000"),
        "Administration fee payable Q3 (Harbourside Fund Services)": D("65000")
    }

    # Q4 liabilities
    ws2 = wb["Q4 accruals 31 Dec 2022"]

    liabilities = D(str(ws2["B6"].value))

    return nav_q3, old_liabilities, liabilities


def calculate_review(q3, marks, notes):

    q4_map = {
        m["company"]: m for m in marks
    }

    sold = {
        "Fjord Payments AS"
    }

    purchased = {
        "Ionmere Materials Ltd"
    }

    held = set(q3.keys()) - sold | purchased

    # R4: A Q4 mark exists for a company no longer held.
    for company in sorted(set(q4_map) - held):
        review.append({
            "company": company,
            "currency": q4_map[company]["currency"],
            "q3_fair_value": (
                float(q3[company]["fair_value"]) if company in q3 else None
            ),
            "q4_fair_value": float(q4_map[company]["fair_value"]),
            "change_pct": None,
            "q3_method": q3[company]["method"] if company in q3 else None,
            "q4_method": q4_map[company]["valuation_method"],
            "flags": ["R4"],
            "reason": "Q4 mark provided for a company no longer held"
        })
        
    review = []
    investments = D("0")
    unrealized_q4 = D("0")

    for company in sorted(set(q3) | set(q4_map) | purchased):

        old = q3.get(company)
        new = q4_map.get(company)

        flags = []
        reasons = []

        if company in sold:
            review.append({
                "company": company,
                "currency": old["currency"] if old else "USD",
                "q3_fair_value": float(old["fair_value"]) if old else None,
                "q4_fair_value": None,
                "change_pct": None,
                "q3_method": old["method"] if old else None,
                "q4_method": None,
                "flags": [],
                "reason": "Sold during Q4; excluded from Q4 holdings"
            })
            continue

        if company in purchased:
            fair_usd = D("14000000")
            cost_usd = D("14000000")
            currency = "USD"
            method = None
            reasons.append("No Q4 mark; carried at recent purchase cost")
                        
            investments += fair_usd
            unrealized_q4 += fair_usd - cost_usd

            review.append({
                "company": company,
                "currency": currency,
                "q3_fair_value": None,
                "q4_fair_value": float(fair_usd),
                "change_pct": None,
                "q3_method": None,
                "q4_method": None,
                "flags": ["R3"],
                "reason": "; ".join(reasons)
            })

            continue

        if not new:
            if company in held:
                flags.append("R3")
                reasons.append("Held company has no Q4 mark")

                review.append({
                    "company": company,
                    "currency": old["currency"] if old else "USD",
                    "q3_fair_value": float(old["fair_value"]) if old else None,
                    "q4_fair_value": None,
                    "change_pct": None,
                    "q3_method": old["method"] if old else None,
                    "q4_method": None,
                    "flags": flags,
                    "reason": "; ".join(reasons)
                })

            continue

        fair_local = D(str(new["fair_value"]))

        if new["currency"] == "EUR":
            fair_usd = fair_local * EURUSD_RATE
        else:
            fair_usd = fair_local

        old_value = old["fair_value"]

        change_pct = (
            (fair_local - old_value) / old_value
        )
        
        if abs(change_pct) > THRESHOLD:
            flags.append("R1")
            reasons.append(
                "Fair value changed materially by "
                f"{change_pct * 100:.2f}%"
            )

        if new["valuation_method"] != old["method"]:
            flags.append("R2")
            reasons.append("Valuation method changed")

        cost_usd = old["cost_usd"]

        investments += fair_usd
        unrealized_q4 += fair_usd - cost_usd

        review.append({
            "company": company,
            "currency": new["currency"],
            "q3_fair_value": float(old_value),
            "q4_fair_value": float(fair_local),
            "change_pct": float(change_pct * 100),
            "q3_method": old["method"],
            "q4_method": new["valuation_method"],
            "flags": flags,
            "reason": "; ".join(reasons) if reasons else "No anomaly detected"
        })

    return review, investments, unrealized_q4


def calculate_nav(pack_dir, transactions, marks):

    q3 = load_q3_data(pack_dir)

    nav_q3, old_liabilities, liabilities = load_q3_nav(pack_dir)

    notes = marks.get("notes", [])

    review, investments, unrealized_q4 = calculate_review(
        q3,
        marks["marks"],
        notes
    )

    # Reclassify previously recorded liabilities paid in Q4
    for tx in transactions:
        description = tx["description"].lower()

        if (
            tx["debit"] > 0
            and "harbourside" in description
            and D(str(tx["debit"])) == D("65000")
        ):
            tx["category"] = "accrual_settlement"

        elif (
            tx["debit"] > 0
            and "coral and finch" in description
            and D(str(tx["debit"])) == D("120000")
        ):
            tx["category"] = "accrual_settlement"

    def total(category, field):
        return sum(
            (D(str(tx[field])) for tx in transactions
             if tx["category"] == category),
            D("0")
        )

    closing_cash = D(str(transactions[-1]["balance"]))

    capital_called = total("capital_call", "credit")
    distributions = total("distribution", "debit")

    income = (
        total("dividend_income", "credit")
        + total("interest_income", "credit")
    )

    management_fee = total("management_fee", "debit")

    other_expenses = (
        total("expense", "debit")
        + total("bank_charges", "debit")
        - total("expense_refund", "credit")
    )

    q4_accruals = liabilities

    expenses = management_fee + other_expenses + q4_accruals

    sale_proceeds = total("sale_proceeds", "credit")

    # Fjord's Q3 cost was $20 million
    realized_gain = sale_proceeds - D("20000000")

    unrealized_q3 = D("23775800")

    change_in_unrealized = unrealized_q4 - unrealized_q3

    nav_q4 = closing_cash + investments - liabilities

    bridge_nav = (
        nav_q3
        + capital_called
        - distributions
        + income
        - expenses
        + realized_gain
        + change_in_unrealized
    )

    difference = nav_q4 - bridge_nav
    
    if difference != D("0"):
        raise ValueError(
            f"NAV bridge does not balance: {difference}"
        )

    nav = {
        "closing_cash": float(closing_cash),
        "investments_usd": float(investments),
        "liabilities": float(liabilities),
        "nav_q4": float(nav_q4),
        "bridge": {
            "nav_q3": float(nav_q3),
            "capital_called": float(capital_called),
            "distributions": float(distributions),
            "income": float(income),
            "management_fee": float(management_fee),
            "expenses": float(expenses),
            "realized_gain": float(realized_gain),
            "change_in_unrealized": float(change_in_unrealized),
            "nav_q4": float(bridge_nav),
            "difference": float(difference)
        }
    }

    return nav, review
