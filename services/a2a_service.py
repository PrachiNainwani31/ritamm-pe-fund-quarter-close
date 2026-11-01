
import os
import time
import threading
import httpx
import uvicorn

from dotenv import load_dotenv

from agents.bank_agent import app as bank_app
from agents.valuation_agent import app as valuation_app
from services.a2a_logger import log_a2a

load_dotenv()

PORT_A = int(os.getenv("AGENT_A_PORT", 8001))
PORT_B = int(os.getenv("AGENT_B_PORT", 8002))

import json
from datetime import datetime, timezone

def start_server(app, port):
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning"
    )

    server = uvicorn.Server(config)

    thread = threading.Thread(
        target=server.run,
        daemon=True
    )

    thread.start()

    return server, thread


def wait_for_server(port):
    url = f"http://127.0.0.1:{port}/.well-known/agent-card.json"

    for _ in range(50):
        try:
            response = httpx.get(url, timeout=2)

            if response.status_code == 200:
                return

        except httpx.RequestError:
            time.sleep(0.2)

    raise RuntimeError(f"Agent on port {port} did not start")


def run_agents():
    os.makedirs("output", exist_ok=True)

    with open("output/a2a_log.jsonl", "w", encoding="utf-8"):
        pass

    server_a, thread_a = start_server(bank_app, PORT_A)
    server_b, thread_b = start_server(valuation_app, PORT_B)

    try:
        wait_for_server(PORT_A)
        wait_for_server(PORT_B)

        print("Both agents started successfully!")

        payload = {
            "jsonrpc": "2.0",
            "id": "run-001",
            "method": "message/send",
            "params": {
                "message": {
                    "kind": "message",
                    "role": "user",
                    "messageId": "trigger-001",
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Start Q4 NAV valuation for GPF."
                        }
                    ]
                }
            }
        }
        log_a2a("outgoing", "Agent A", payload)
        response = httpx.post(
            f"http://127.0.0.1:{PORT_A}/a2a",
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        log_a2a("incoming", "Agent A", response.json())
        result = response.json()["result"]

        if result["status"]["state"] != "completed":
            raise RuntimeError(f"A2A conversation failed: {result}")

        # Extract marks artifact
        marks = result["artifacts"][0]["parts"][0]["data"]

        os.makedirs("output", exist_ok=True)

        import json

        with open("output/marks.json", "w") as f:
            json.dump(marks, f, indent=4)

        print("A2A conversation completed!")
        print("Marks saved to output/marks.json")

        return marks

    finally:
        server_a.should_exit = True
        server_b.should_exit = True

        thread_a.join(timeout=5)
        thread_b.join(timeout=5)
