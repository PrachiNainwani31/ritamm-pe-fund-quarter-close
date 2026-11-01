
import uuid
import httpx

from fastapi import FastAPI
from services.a2a_logger import log_a2a

app = FastAPI(title="Bank & Ingestion Agent")

AGENT_B_URL = "http://localhost:8002/a2a"


@app.get("/.well-known/agent-card.json")
def agent_card():
    return {
        "name": "Bank & Ingestion Agent",
        "description": "Extracts and categorizes bank transactions",
        "url": "http://localhost:8001/a2a",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False
        },
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {
                "id": "bank-ingestion",
                "name": "Bank Transaction Ingestion",
                "description": "Extracts and categorizes fund transactions"
            }
        ]
    }


async def send_message(message):

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": message
        }
    }

    log_a2a("outgoing", "Agent A -> Agent B", payload)

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(AGENT_B_URL, json=payload)

        response.raise_for_status()

        result = response.json()

        log_a2a("incoming", "Agent B -> Agent A", result)

        return result


@app.post("/a2a")
async def handle_message(request: dict):

    message = request.get("params", {}).get("message", {})

    # Agent A starts the conversation
    first_message = {
        "kind": "message",
        "role": "user",
        "messageId": str(uuid.uuid4()),
        "parts": [
            {
                "kind": "data",
                "data": {
                    "fund": "GPF",
                    "valuation_date": "2022-12-31"
                }
            }
        ]
    }

    first_response = await send_message(first_message)

    task = first_response["result"]

    if task["status"]["state"] != "input-required":
        raise ValueError("Agent B did not request purchase/sale details")

    # Read Agent A's categorized transactions
    with open("output/transactions.json", "r") as f:
        transactions = __import__("json").load(f)

    purchases = []
    sales = []

    for tx in transactions:

        if tx["category"] == "investment_purchase":
            purchases.append({
                "company": tx["company"],
                "date": tx["date"],
                "amount_usd": tx["debit"]
            })

        elif tx["category"] == "sale_proceeds":
            sales.append({
                "company": tx["company"],
                "date": tx["date"],
                "proceeds_usd": tx["credit"]
            })

    # Agent A answers Agent B's question
    second_message = {
        "kind": "message",
        "role": "user",
        "messageId": str(uuid.uuid4()),
        "taskId": task["id"],
        "contextId": task["contextId"],
        "parts": [
            {
                "kind": "data",
                "data": {
                    "purchases": purchases,
                    "sales": sales
                }
            }
        ]
    }

    second_response = await send_message(second_message)

    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": second_response["result"]
    }
