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
        self.connections = OrderedDict()
        self.dummy_datastore: dict = {}

    @applicationpolicy
    def policy(self, repository, event):
        pass

    @policy.register(BankAccount.ErrorRecorded)
    def _(self, repository, event):
        data = {
            "account_id": str(event.originator_id),
            "timestamp": str(event.timestamp),
            "transaction_id": str(event.transaction_id),
            "error": event.error.__class__.__name__,
            "event_type": "account_error"
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
            "amount": float(event.amount),
            "event_type": "account_transaction"
        }
        print(f"\n\n\ntransaction appended {data}\n\n\n")
        self.dummy_datastore[data["account_id"]]["balance"] += data["amount"]
        for uid, connection in self.connections.items():
            asyncio.create_task(connection.send_json(data))

    @policy.register(BankAccount.Created)
    def _(self, repository, event):
        data = {
            "account_id": str(event.originator_id),
            "timestamp": str(event.timestamp),
            "event_type": "new_account"
        }
        #similar to saving an orm object in the applications database
        self.dummy_datastore[data["account_id"]] = {"balance":0, "errors":[]}
        for uid, connection in self.connections.items():
            asyncio.create_task(connection.send_json(data))
