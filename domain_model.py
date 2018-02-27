from typing import Any
from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.decorators import attribute
from eventsourcing.domain.model.events import subscribe


class WalletType:
    real = 'Real' 
    bonus = 'Bonus'


class TransactionType:
    deposit = 'Deposit'
    bet = 'Bet'
    cashin = 'Cashin'


class Wallet(AggregateRoot):

    def __init__(self, player_id:int, wallet_type:WalletType, **kwargs):
        super(Wallet, self).__init__(**kwargs)
        self.player_id = player_id
        self.wallet_type = wallet_type
        self.transactions = []
        #subscribe(handler=self.calc_balance, predicate=self.TransactionCreatedEvent)

    @attribute
    def balance(self):
        """sdfdsfs"""
    #
    # Domain events.
    #

    class WalletCreated(AggregateRoot.Created):
        """Published when the wallet is created."""
        def mutate(self, entity):
            entity.balance = 0

    class TransactionCreated(AggregateRoot.Event):
        """Published when a new transaction is added."""

        @property
        def origin(self):
            return self.__dict__['origin']

        @property
        def transaction_type(self):
            return self.__dict__['transaction_type']

        @property
        def ammount(self):
            return self.__dict__['ammount']

        def mutate(self, entity):
            entity.transactions.append(self)
            return entity

    
    class WalletDiscarded(AggregateRoot.Discarded):
        """Published when the wallet is discarded."""
        pass

    #
    # Commands.
    #

    def add_transaction(self, origin:Any, transaction_type:TransactionType, ammount:int) -> None:
        self.__trigger_event__(Wallet.TransactionCreatedEvent, origin=origin, transaction_type=transaction_type, ammount=ammount)

    def is_transaction_event(event):
        return isinstance(event, Wallet.TransactionCreatedEvent)

    def calc_balance(self) ->None:
        import pudb; pu.db
        print('puto')
    
    subscribe(handler=calc_balance, predicate=is_transaction_event)
