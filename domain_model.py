from eventsourcing.domain.model.aggregate import AggregateRoot


class World(AggregateRoot):

    def __init__(self, **kwargs):
        super(World, self).__init__(**kwargs)
        self.history = []

    def make_it_so(self, something):
        self.__trigger_event__(World.SomethingHappened, what=something)
    
    class SomethingHappened(AggregateRoot.Event):
        def mutate(self, obj):
            obj.history.append(self)
