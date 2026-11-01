import os
import json
from datetime import datetime, timezone

LOG_FILE = "output/a2a_log.jsonl"


def log_a2a(direction, agent, payload):
    os.makedirs("output", exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "direction": direction,
        "agent": agent,
        "payload": payload
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")