import settings
from eventsourcing.application.simple import SimpleApplication
from eventsourcing.exceptions import ConcurrencyError
from domain_model import World

# Construct simple application (used here as a context manager).
with SimpleApplication() as app:

    # Create new aggregate.
    world = World.__create__()

    # Aggregate not yet in repository.
    assert world.id not in app.repository

    # Execute commands.
    world.make_it_so('dinosaurs')
    world.make_it_so('trucks')

    # View current state of aggregate object.
    assert world.history[0].what == 'dinosaurs'
    assert world.history[1].what == 'trucks'

    # Note version of object at this stage.
    version = world.__version__

    # Execute another command.
    world.make_it_so('internet')

    # Store pending domain events.
    world.__save__()

    # Aggregate now exists in repository.
    assert world.id in app.repository

    # Replay stored events for aggregate.
    copy = app.repository[world.id]

    # View retrieved aggregate.
    assert isinstance(copy, World)
    assert copy.history[0].what == 'dinosaurs'
    assert copy.history[1].what == 'trucks'
    assert copy.history[2].what == 'internet'

    # Verify retrieved state (cryptographically).
    assert copy.__head__ == world.__head__

    # Delete aggregate.
    world.__discard__()

    # Discarded aggregate not found.
    assert world.id not in app.repository
    try:
        # Repository raises key error.
        app.repository[world.id]
    except KeyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Get historical state (at version from above).
    old = app.repository.get_entity(world.id, at=version)
    assert old.history[-1].what == 'trucks' # internet not happened
    assert len(old.history) == 2

    # Optimistic concurrency control (no branches).
    old.make_it_so('future')
    try:
        old.__save__()
    except ConcurrencyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Check domain event data integrity (happens also during replay).
    events = app.event_store.get_domain_events(world.id)
    last_hash = ''
    for event in events:
        event.__check_hash__()
        assert event.__previous_hash__ == last_hash
        last_hash = event.__event_hash__

    # Verify stored sequence of events against known value.
    assert last_hash == world.__head__

    # Check records are encrypted (values not visible in database).
    record_manager = app.event_store.record_manager
    items = record_manager.get_items(world.id)
    for item in items:
        for what in ['dinosaurs', 'trucks', 'internet']:
            assert what not in item.state
        assert world.id == item.originator_id

    # Project application event notifications.
    from eventsourcing.interface.notificationlog import NotificationLogReader
    reader = NotificationLogReader(app.notification_log)
    notification_ids = [n['id'] for n in reader.read()]
    assert notification_ids == [1, 2, 3, 4, 5]

    # - create two more aggregates
    world = World.__create__()
    world.__save__()

    world = World.__create__()
    world.__save__()

    # - get the new event notifications from the reader
    notification_ids = [n['id'] for n in reader.read()]
    assert notification_ids == [6, 7]
