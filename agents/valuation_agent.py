
import json
import uuid

from decimal import Decimal
from fastapi import FastAPI
from fastapi.responses import JSONResponse


app = FastAPI(title="Valuation & NAV Agent")

tasks = {}


def load_data():
    with open("./pack/agent_b_data.json", "r") as f:
        return json.load(f)


def normalize(name):
    return name.strip().lower()


def records_match(received, expected, amount_key):
    if len(received) != len(expected):
        return False

    expected_map = {
        (
            normalize(x["company"]),
            x["date"],
            Decimal(str(x[amount_key]))
        )
        for x in expected
    }

    received_map = {
        (
            normalize(x["company"]),
            x["date"],
            Decimal(str(x[amount_key]))
        )
        for x in received
    }

    return received_map == expected_map


@app.get("/.well-known/agent-card.json")
def agent_card():
    return {
        "name": "Valuation & NAV Agent",
        "description": "Reviews valuations and calculates fund NAV",
        "url": "http://localhost:8002/a2a",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False
        },
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {
                "id": "valuation",
                "name": "Q4 Valuation Marks",
                "description": "Verifies transactions and releases valuation marks"
            }
        ]
    }


@app.post("/a2a")
async def handle_message(request: dict):

    if request.get("jsonrpc") != "2.0":
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON-RPC version"}
        )

    if request.get("method") != "message/send":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }

    params = request.get("params", {})
    message = params.get("message", {})

    task_id = message.get("taskId")
    context_id = message.get("contextId")

    # TURN 1: Agent A requests marks
    if not task_id:

        task_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())

        tasks[task_id] = {
            "contextId": context_id,
            "status": "input-required"
        }

        response = {
            "kind": "task",
            "id": task_id,
            "contextId": context_id,
            "status": {
                "state": "input-required",
                "message": {
                    "kind": "message",
                    "role": "agent",
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Please provide the fund's Q4 purchases and sales of companies."
                        }
                    ]
                }
            }
        }

    # TURN 2: Agent A sends purchases and sales
    else:

        if task_id not in tasks:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32001,
                    "message": "Unknown task"
                }
            }

        task = tasks[task_id]

        if task["contextId"] != context_id:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32002,
                    "message": "Context ID mismatch"
                }
            }

        data = load_data()

        received = {}

        for part in message.get("parts", []):
            if part.get("kind") == "data":
                received = part.get("data", {})

        purchases = received.get("purchases", [])
        sales = received.get("sales", [])

        purchase_ok = records_match(
            purchases,
            data["purchases"],
            "amount_usd"
        )

        sale_ok = records_match(
            sales,
            data["sales"],
            "proceeds_usd"
        )

        if purchase_ok and sale_ok:

            tasks[task_id]["status"] = "completed"

            artifact_data = {
                "fund": data["fund"]["name"],
                "valuation_date": data["valuation_date"],
                "marks": data["marks"],
                "notes": data["notes"]
            }

            response = {
                "kind": "task",
                "id": task_id,
                "contextId": context_id,
                "status": {
                    "state": "completed"
                },
                "artifacts": [
                    {
                        "artifactId": "marks-GPF-2022-12-31",
                        "parts": [
                            {
                                "kind": "data",
                                "data": artifact_data
                            }
                        ]
                    }
                ]
            }

        else:

            response = {
                "kind": "task",
                "id": task_id,
                "contextId": context_id,
                "status": {
                    "state": "input-required",
                    "message": {
                        "kind": "message",
                        "role": "agent",
                        "parts": [
                            {
                                "kind": "text",
                                "text": (
                                    f"Purchase match: {purchase_ok}. "
                                    f"Sale match: {sale_ok}. "
                                    "Please correct the records."
                                )
                            }
                        ]
                    }
                }
            }

    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": response
    }
