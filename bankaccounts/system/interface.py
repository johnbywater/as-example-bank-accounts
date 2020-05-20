import asyncio
import typing
from uuid import UUID
from bankaccounts.domainmodel import BankAccount
from collections import OrderedDict
from eventsourcing.application.decorators import applicationpolicy
from eventsourcing.application.process import ProcessApplication
from eventsourcing.domain.model.aggregate import BaseAggregateRoot
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from starlette.types import Message
from fastapi import status


class User(BaseAggregateRoot):
    __subclassevents__ = True





class InterfaceApplication(ProcessApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._web_app: FastAPI = FastAPI()
        self._web_app.state.connections = OrderedDict() #holds all websocket connections

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

    @policy.register(BankAccount.TransactionAppended)
    def _(self, repository, event):
        for uid, connection in self.connections.items():
            asyncio.get_event_loop().run_until_complete(connection.send_json(event.__dict__))

    @policy.register(BankAccount.Created)
    def _(self, repository, event):
        data = {
            "account_id": str(event.originator_id),
            "timestamp": str(event.timestamp)
        }
        for uid, connection in self.connections.items():
            asyncio.create_task(connection.send_json(data))
