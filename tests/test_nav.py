import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_nav_file_exists():
    assert (ROOT / "output" / "nav.json").exists()


def test_nav_calculation():
    path = ROOT / "output" / "nav.json"

    with open(path) as f:
        nav = json.load(f)

    assert nav["nav_q4"] == 169764039.25
    assert nav["closing_cash"] == 23896579.25
    assert nav["investments_usd"] == 146062460.0
    assert nav["liabilities"] == 195000.0


def test_nav_bridge_balances():
    path = ROOT / "output" / "nav.json"

    with open(path) as f:
        nav = json.load(f)

    bridge = nav["bridge"]

    assert bridge["difference"] == 0.0
    assert bridge["nav_q3"] == 160224800.0
    assert bridge["nav_q4"] == nav["nav_q4"]


def test_review_flags():
    path = ROOT / "output" / "review.json"

    with open(path) as f:
        review = json.load(f)

    flags = {
        company["company"]: company["flags"]
        for company in review["companies"]
    }

    assert flags["Bluetarn Software Inc"] == ["R1"]
    assert flags["Cedar Health Holdings"] == ["R1"]
    assert flags["Harbor Analytics Inc"] == ["R1"]
    assert flags["Delta Agritech Ltd"] == ["R2"]
    assert flags["Ionmere Materials Ltd"] == ["R3"]
    assert flags["Fjord Payments AS"] == []