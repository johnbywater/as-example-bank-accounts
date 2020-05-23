import json
from typing import Any
import uvicorn
from collections import OrderedDict
from uuid import UUID
from bankaccounts.system.accounts import Accounts
from fastapi import FastAPI, WebSocket, Request
from fastapi import status, FastAPI
from bankaccounts.system.interface import InterfaceApplication
from bankaccounts.system.commands import Commands
from bankaccounts.system.definition import BankAccountSystem
from eventsourcing.system.runner import SingleThreadedRunner
from starlette.types import Message
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from decimal import Decimal


templates = Jinja2Templates(directory="bankaccounts/templates")
runner: SingleThreadedRunner = SingleThreadedRunner(BankAccountSystem(None))
app: FastAPI = FastAPI()


@app.on_event("startup")
def on_app_start():
    runner.start()
    commands: Commands = runner.get(Commands)
    interface: InterfaceApplication = runner.get(InterfaceApplication)
    accounts: Accounts = runner.get(Accounts)
    app.state.commands = commands
    app.state.interface = interface
    app.state.accounts = accounts


@app.on_event("shutdown")
def on_app_shutdown():
    runner.close()


async def handle_message(commands: Commands, message: Message):
    data: dict = json.loads(message['text'])
    command_type = data['type']
    if command_type == "deposit":
        credit_account_id = UUID(data["credit_account_id"])
        amount = Decimal(data["amount"])
        commands.deposit_funds(credit_account_id, amount)
    elif command_type == "transfer":
        debit_account_id = UUID(data["debit_account_id"])
        credit_account_id = UUID(data["credit_account_id"])
        amount = Decimal(data["amount"])
        commands.transfer_funds(debit_account_id, credit_account_id, amount)
    elif command_type == "withdraw":
        debit_account_id = UUID(data["debit_account_id"])
        amount = Decimal(data["amount"])
        commands.withdraw_funds(debit_account_id, amount)

@app.get("/accounts")
async def get_all_accounts(request: Request):
    return JSONResponse(request.app.state.interface.dummy_datastore)

@app.websocket("/ws/{state}")
async def ws(websocket: WebSocket, state: Any=None):
    app: FastAPI = websocket.app
    commands: Commands = app.state.commands
    accounts: Accounts = app.state.accounts
    interface: InterfaceApplication = app.state.interface
    connections: OrderedDict[str, WebSocket] = interface.connections
    assert isinstance(connections, OrderedDict)
    await websocket.accept()
    account_id: UUID = accounts.create_account()
    websocket.state.account_id = account_id
    connections[str(account_id)] = websocket
    await websocket.send_json({"event_type": "connected", "account_id": str(account_id), "state": state})
    try:
        while True:
            message: Message = await websocket.receive()
            if message["type"] == "websocket.receive":
                await handle_message(commands, message)
            elif message["type"] == "websocket.disconnect":
                close_code = int(message.get("code", status.WS_1000_NORMAL_CLOSURE))
                del connections[str(websocket.state.account_id)]
                await websocket.close(close_code=close_code)
    except Exception as exc:
        raise exc
    finally:
        await websocket.close(close_code = status.WS_1011_INTERNAL_ERROR)

@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("bankaccounts.main:app", reload=True)
