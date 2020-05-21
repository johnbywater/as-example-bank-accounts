import asyncio
import typing
from uuid import UUID
from bankaccounts.domainmodel import BankAccount
from collections import OrderedDict
from eventsourcing.application.decorators import applicationpolicy
from eventsourcing.application.process import ProcessApplication
from eventsourcing.domain.model.aggregate import BaseAggregateRoot
from fastapi import FastAPI, WebSocket

class User(BaseAggregateRoot):
    __subclassevents__ = True





class InterfaceApplication(ProcessApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._web_app: FastAPI = FastAPI()
        self._web_app.state.connections = OrderedDict() #holds all websocket connections
        self._web_app.state.interface = self
        self.dummy_datastore: dict = {}

    @property
    def web_app(self) -> FastAPI:
        return self._web_app

    @property
    def connections(self) -> typing.OrderedDict[UUID, WebSocket]:
        assert self._web_app.state.connections is not None
        return self._web_app.state.connections

    def new_user(self, socket: WebSocket):
        user = User.__create__()
        self.accounts[user.id] = socket
        self.save(user)

    @applicationpolicy
    def policy(self, repository, event):
        pass

    @policy.register(BankAccount.ErrorRecorded)
    def _(self, repository, event):
        data = {
            "account_id": str(event.originator_id),
            "timestamp": str(event.timestamp),
            "transaction_id": str(event.transaction_id),
            "error": event.error.__class__.__name__
        }
        self.dummy_datastore[data["account_id"]]["errors"].append(data["error"])
        for uid, connection in self.connections.items():
            asyncio.create_task(connection.send_json(data))

    @policy.register(BankAccount.TransactionAppended)
    def _(self, repository, event):
        data = {
            "account_id": str(event.originator_id),
            "timestamp": str(event.timestamp),
            "transaction_id": str(event.transaction_id),
            "amount": float(event.amount)
        }
        self.dummy_datastore[data["account_id"]]["balance"] += data["amount"]
        for uid, connection in self.connections.items():
            asyncio.create_task(connection.send_json(data))

    @policy.register(BankAccount.Created)
    def _(self, repository, event):
        data = {
            "account_id": str(event.originator_id),
            "timestamp": str(event.timestamp)
        }
        #similar to saving an orm object in the applications database
        self.dummy_datastore[data["account_id"]] = {"balance":0, "errors":[]}
        for uid, connection in self.connections.items():
            asyncio.create_task(connection.send_json(data))
