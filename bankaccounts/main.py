import json
import uvicorn
from collections import OrderedDict
from uuid import UUID
from bankaccounts.system.accounts import Accounts
from fastapi import FastAPI, WebSocket, Request
from fastapi import status
from bankaccounts.system.interface import InterfaceApplication
from bankaccounts.system.commands import Commands
from bankaccounts.system.definition import BankAccountSystem
from eventsourcing.system.runner import SingleThreadedRunner
from starlette.types import Message
from fastapi.responses import JSONResponse
from decimal import Decimal


async def get_all_accounts(request: Request):
    return JSONResponse(request.app.state.interface.dummy_datastore)

async def handle_message(commands: Commands, message: Message):
    data: dict = json.loads(message['text'])
    print(f"\n\n\n\nfrom handle message data is \n{data}\n\n\n")
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

async def ws(websocket: WebSocket):
    app: FastAPI = websocket.app
    commands: Commands = app.state.commands
    accounts: Accounts = app.state.accounts
    connections: OrderedDict[str, WebSocket] = app.state.connections
    assert isinstance(connections, OrderedDict)
    await websocket.accept()
    account_id: UUID = accounts.create_account()
    websocket.state.account_id = account_id
    connections[str(account_id)] = websocket 
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

if __name__ == "__main__":
    with SingleThreadedRunner(BankAccountSystem(None)) as runner:
        interface: InterfaceApplication = runner.get(InterfaceApplication)
        commands: Commands = runner.get(Commands)
        accounts: Accounts = runner.get(Accounts)
        app = interface.web_app
        app.state.commands = commands
        app.state.accounts = accounts
        app.add_websocket_route("/ws", ws)
        app.add_route("/accounts", get_all_accounts, methods=["GET"])
        uvicorn.run(app)