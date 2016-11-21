
from dbus_deco import introspector as intsp


introspector = intsp.Introspector('com.example.service')


@introspector
class ExampleService:

    @introspector.method(response='s')
    def HelloWorld(self):
        return 'Hello!'
    
    @introspector.method(Arg('message', 's'), response='s')
    def Echo(self, message):
        return message

    @introspector.property(type_='b', access=intsp.READ)
    def Status(self):
        return True

    @introspector.property(type_='i', signal_on=[intsp.Events.ON_PROPERTY_CHANGE])
    def Count(self):
        return 100

    @Count.setter
    def Count(self, value):
        print(value)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    example_service = ExampleService()
    print('Generated D-Bus Introspection XML', example_service.dbus)

    loop = GObject.MainLoop()
    bus = pydbus.SessionBus()
    bus.publish('com.example.service', example_service)
    loop.run()
