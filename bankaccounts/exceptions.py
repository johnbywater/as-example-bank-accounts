class TransactionError(Exception):
    pass


class AccountClosedError(TransactionError):
    pass


class InsufficientFundsError(TransactionError):
    pass
