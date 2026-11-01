import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_a2a_log_exists():
    path = ROOT / "output" / "a2a_log.jsonl"
    assert path.exists()


def test_a2a_log_entries():
    path = ROOT / "output" / "a2a_log.jsonl"

    with open(path) as f:
        entries = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    assert len(entries) == 6


def test_a2a_two_turn_communication():
    path = ROOT / "output" / "a2a_log.jsonl"

    with open(path) as f:
        entries = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    agents = [entry["agent"] for entry in entries]

    assert "Agent A -> Agent B" in agents
    assert "Agent B -> Agent A" in agents