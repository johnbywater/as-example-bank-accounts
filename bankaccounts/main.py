from collections import OrderedDict
from uuid import UUID
from bankaccounts.system.accounts import Accounts
import uvicorn
from fastapi import FastAPI, WebSocket, Request
from fastapi import status
from bankaccounts.system.interface import InterfaceApplication
from bankaccounts.system.commands import Commands
from bankaccounts.system.definition import BankAccountSystem
from eventsourcing.system.runner import SingleThreadedRunner
from starlette.types import Message
from fastapi.responses import JSONResponse

async def get_all_accounts(request: Request):
    return JSONResponse({"accounts":  list(request.app.state.connections.keys()) })


async def handle_message(commands: Commands, message: Message):
    data: dict = message['text']
    command_type = data['type']
    if command_type == "deposit":
        pass

async def ws(websocket: WebSocket):
    app: FastAPI = websocket.app
    commands: Commands = app.state.commands
    accounts: Accounts = app.state.accounts
    connections: OrderedDict[str, WebSocket] = app.state.connections
    assert isinstance(connections, OrderedDict)
    await websocket.accept()
    account_id: UUID = accounts.create_account()
    connections[str(account_id)] = websocket 
    try:
        while True:
            message: Message = await websocket.receive()
            if message["type"] == "websocket.receive":
                print("\n\n\n\nmessage received")
                print(message)
                print("\n\n\n")
            elif message["type"] == "websocket.disconnect":
                close_code = int(message.get("code", status.WS_1000_NORMAL_CLOSURE))
                break
    except Exception as exc:
        pass
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