
import logging

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GObject

from dbus_deco import DBusProperty, extrapolate_service_path, fix_class_name


def service_factory(name, path=None, class_name=None, class_doc=None):
        service_name = name
        service_path = path or extrapolate_service_path(name)

        class ServiceBaseClass(dbus.service.Object):

            name = service_name
            path = service_path

            def __init__(slf):
                slf.logger = logging.getLogger(
                        name=slf.__class__.__name__+'.'+slf.name
                        )

            def run(slf):
                dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
                bus_name = dbus.service.BusName(slf.name, dbus.SessionBus())
                dbus.service.Object.__init__(slf, bus_name, slf.path)
                slf._loop = GObject.MainLoop()
                slf.logger.debug("Service running...")
                slf._loop.run()
                slf.logger.debug("Service stopped")

            @classmethod
            def method(cls, method_name, *args, **kwargs):
                return dbus.service.method(cls.name+'.'+method_name.title(), *args, **kwargs)

            @classmethod
            def attribute(cls, getter_name, *args, doc=None, **kwargs):
                def attribute_decorator(func):
                    return DBusProperty(fget=func, name=getter_name, interface=cls.name+'.'+getter_name.title(), doc=doc)
                return attribute_decorator

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

        @service.method('message', in_signature='', out_signature='s')
        def get_message(self):
            self.logger.debug("  sending message")
            return self._message

        @service.method('quit', in_signature='', out_signature='')
        def quit(self):
            self.logger.debug("  shutting down")
            self._loop.quit()

    
    ExampleService("This is the service").run()
