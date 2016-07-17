
import logging

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GObject

from dbus_deco import DBusServiceProperty, extrapolate_service_path, fix_class_name


def factory(name, path=None, class_name=None, class_doc=None, bus_class=None):
        service_name = name
        service_path = path or extrapolate_service_path(name)

        class ServiceBaseClass(dbus.service.Object):

            name = service_name
            path = service_path
            bus = bus_class or dbus.SessionBus

            def __init__(slf):
                slf.logger = logging.getLogger(
                        name=slf.__class__.__name__+'.'+slf.name
                        )

            def run(slf):
                dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
                bus_name = dbus.service.BusName(slf.name, slf.bus())
                dbus.service.Object.__init__(slf, bus_name, slf.path)
                slf._loop = GObject.MainLoop()
                slf.logger.debug("Service running...")
                slf._loop.run()
                slf.logger.debug("Service stopped")

            @classmethod
            def _get_dbus_method_name(cls, name):
                return '.'.join((cls.name, name))

            @classmethod
            def method(cls, **kwargs):
                return dbus.service.method(cls.name, **kwargs)

            @classmethod
            def attribute(cls, getter_name, *args, doc=None, **kwargs):
                def attribute_decorator(func):
                   return DBusServiceProperty(
                            fget=func,
                            name=getter_name,
                            interface=cls._get_dbus_method_name(getter_name),
                            doc=doc
                            )
                return attribute_decorator

            @classmethod
            def signal(cls, **kwargs):
                return dbus.service.signal(cls.name, **kwargs)

        if class_name:
            fix_class_name(ServiceBaseClass, class_name)
        if class_doc:
            ServiceBaseClass.__doc__ = class_doc
        return ServiceBaseClass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    service = service_factory('com.example.service')

    class ExampleService(service):

        def __init__(self, message):
            super().__init__()
            self._message = message

        @service.method()
        def get_message(self):
            self.message_ready(self._message)

        @service.signal(signature='s')
        def message_ready(self, message):
            self.logger.debug("  sending message")
            return message

        @service.method()
        def quit(self):
            self.logger.debug("  shutting down")
            self._loop.quit()

    
    ExampleService("This is the service").run()
