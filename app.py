import settings
from eventsourcing.application.simple import SimpleApplication
from eventsourcing.exceptions import ConcurrencyError
from domain_model import Wallet, WalletType, TransactionType

# Construct simple application (used here as a context manager).
with SimpleApplication() as app:
    import pudb; pu.db

    # Create new aggregate.
    wallet = Wallet.__create__(player_id=1, wallet_type=WalletType.real)

    # Aggregate not yet in repository.
    assert wallet.id not in app.repository

    # Execute commands.
    wallet.add_transaction('origin1', TransactionType.deposit, 10000)
    wallet.add_transaction('origin2', TransactionType.bet, 500)
    wallet.add_transaction('origin3', TransactionType.bet, -5000)

    # View current state of aggregate object.
    assert wallet.transactions[0].transaction_type == TransactionType.deposit
    assert wallet.transactions[1].transaction_type == TransactionType.bet
    assert wallet.transactions[2].transaction_type == TransactionType.bet

    # Note version of object at this stage.
    version = wallet.__version__

    # Execute another command.
    wallet.add_transaction('origin4', TransactionType.bet, 45000)

    # Store pending domain events.
    wallet.__save__()

    # Aggregate now exists in repository.
    assert wallet.id in app.repository

    # Replay stored events for aggregate.
    copy = app.repository[wallet.id]

    # View retrieved aggregate.
    assert isinstance(copy, Wallet)
    assert copy.transactions[0].transaction_type == TransactionType.deposit
    assert copy.transactions[1].transaction_type == TransactionType.bet
    assert copy.transactions[2].transaction_type == TransactionType.bet

    # Verify retrieved state (cryptographically).
    assert copy.__head__ == wallet.__head__

    # Delete aggregate.
    wallet.__discard__()

    # Discarded aggregate not found.
    assert wallet.id not in app.repository
    try:
        # Repository raises key error.
        app.repository[wallet.id]
    except KeyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Get historical state (at version from above).
    old = app.repository.get_entity(wallet.id, at=version)
    assert old.transactions[-1].ammount == -5000
    assert len(old.transactions) == 3

    # Optimistic concurrency control (no branches).
    old.add_transaction(45000, TransactionType.bet)
    try:
        old.__save__()
    except ConcurrencyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Check domain event data integrity (happens also during replay).
    events = app.event_store.get_domain_events(wallet.id)
    last_hash = ''
    for event in events:
        event.__check_hash__()
        assert event.__previous_hash__ == last_hash
        last_hash = event.__event_hash__

    # Verify stored sequence of events against known value.
    assert last_hash == wallet.__head__

    # Check records are encrypted (values not visible in database).
    record_manager = app.event_store.record_manager
    items = record_manager.get_items(wallet.id)
    for item in items:
        for transaction_type in [TransactionType.deposit,
                                 TransactionType.bet,
                                 TransactionType.cashin]:
            assert transaction_type not in item.state
        assert wallet.id == item.originator_id

    # Project application event notifications.
    from eventsourcing.interface.notificationlog import NotificationLogReader
    reader = NotificationLogReader(app.notification_log)
    notification_ids = [n['id'] for n in reader.read()]
    assert notification_ids == [1, 2, 3, 4, 5, 6]

    # - create two more aggregates
    wallet = Wallet.__create__(player_id=2, wallet_type=WalletType.real)
    wallet.__save__()

    wallet = Wallet.__create__(player_id=3, wallet_type=WalletType.real)
    wallet.__save__()

    # - get the new event notifications from the reader
    notification_ids = [n['id'] for n in reader.read()]
    assert notification_ids == [7, 8]
