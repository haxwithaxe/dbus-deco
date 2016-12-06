#!/usr/bin/env python3

from dbus_deco import introspector as intsp


introspector = intsp.Introspector('com.example.service')


@introspector
class ExampleService:
    
    _count = 100

    @introspector.method(response='s')
    def HelloWorld(self):
        return 'Hello!'
    
    @introspector.method(intsp.Arg('message', 's'), response='s')
    def Echo(self, message):
        return message

    @introspector.property(type_='b', access=intsp.READ)
    def Status(self):
        return True

    @introspector.property(type_='i', signal_on_change=True)
    def Count(self):
        return self._count

    @Count.setter
    def Count(self, value):
        if value != self._count:
            self._count = value
        self.onCount()
        self.PropertiesChanged(changed=['Count'])

    @Count.signal('i')
    def onCount(self):
        return self.Count


if __name__ == '__main__':

    from gi.repository import GObject
    import pydbus

    example_service = ExampleService()
    #print('Generated D-Bus Introspection XML', example_service.dbus)

    loop = GObject.MainLoop()
    bus = pydbus.SessionBus()
    bus.publish('com.example.service', example_service)
    loop.run()