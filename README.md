# Bank accounts

[![Build Status](https://travis-ci.org/johnbywater/es-example-bank-accounts.svg?branch=master)](https://travis-ci.org/johnbywater/es-example-bank-accounts)
[![Coverage Status](https://coveralls.io/repos/github/johnbywater/es-example-bank-accounts/badge.svg?branch=master#)](https://coveralls.io/github/johnbywater/es-example-bank-accounts)

Example "bank accounts" application using the Python eventsourcing library

## Overview

### Domain model

There is an event sourced ``BankAccount`` aggregate which has a balance. Transactions can be appended, which affects the balance. Transactions are not allowed if the balance would go below the overdraft limit, or if the account has been closed. The overdraft limit can be adjusted.

### Simple application

There is a ``SimpleBankAccountApplication`` which allows accounts to be created and closed, deposits and withdraws on accounts, and transfers between accounts. All actions are atomic, including transfers between accounts.

### System of process applications

There is also a ``BankAccountSystem`` which has similar functionality, but records client requests with ``Command`` aggregates, for maximum availability. These system commands are processed by the ``Sagas`` process application, which is followed by the ``Accounts`` process application.

Deposits and withdraws are processed by creating a command, which creates a saga, and then the account is adjusted. If an error occurs, the saga will not succeed and the account error will be recorded on the saga.

Transfers are processed by firstly debiting one account and then crediting the other account, in a multi-step process controlled by the ``TransferFundsSaga`` saga. 


### Update UI from Interface Layer with Event Handlers
Created a new ``ProcessApplication`` called ``InterfaceApplication`` that follows the ``Accounts`` application. The interface application holds a list of websocket connections. It listens for ``Account.Created`` and ``Account.TransactionAppended`` events and  updates the UI with these events accordingly.

To test this out run ``pip install -e .`` to install dependencies in editable mode and run ``python bankaccounts/main.py`` in the root folder of this example to start the webserver built on ``FastAPI``. 
Then visit ``localhost:8000`` on multiple tabs. The UI is pretty basic and inituitive.