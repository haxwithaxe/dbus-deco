
import logging

import dbus
import dbus.mainloop.glib
from gi.repository import GObject

from dbus_deco import extrapolate_service_path, fix_class_name


class _SignalHandler:

    def __init__(self, handler, interface_name, signal_name):
        self.name = signal_name
        self.interface = interface_name
        self.handler = handler

    def __call__(self, obj, bus):
        """bus.add_signal_receiver(catchall_hello_signals_handler, dbus_interface = "com.example.TestService", signal_name = "HelloSignal")"""
        func = lambda *a, **k: self.handler(obj, *a, **k)
        bus.add_signal_receiver(func, dbus_interface=self.interface, signal_name=self.name)

    def __iter__(self):
        return iter(       
                ('signal_name', self.name), 
                ('interface', self.interface),
                ('handler', self.handler)
                )


def client_factory(service_name, service_path=None, class_name=None, class_doc=None, bus_class=None):
    """A factory for producing a DBus client class with helper decorators builtin.
    
    Arguments:
        service_name (str): The DBus service name (eg "com.example.service").
        service_path (str, optional): The DBus service name
            (eg "/com/example/service"). Defaults to the extrapolation of the
            service_name (eg "/com/example/service" from "com.example.service").
        class_name (str, optional): The name to set the `__name__` and 
            `__qualname__` attributes with. Defaults to "ClientBaseClass".
        class_doc (str, optional): Used as the class docstring of the new class. Defaults to None.

    Returns:
        class: A class with helpers for creating a DBus client interface subclass with little coding overhead.

    """
    service_path = service_path or extrapolate_service_path(service_name)

    class ClientBaseClass:

        _service_name = service_name
        _service_path = service_path
        _signal_handlers = []
        _bus_class = bus_class or dbus.SessionBus

        def __init__(slf):
            slf.logger = logging.getLogger(slf.__class__.__name__)
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = slf._bus_class()
            slf.interface = bus.get_object(slf._service_name, slf._service_path)
            for handler in slf._signal_handlers:
                handler(slf, bus)

        def get_method(slf, method_name, interface):
            return slf.interface.get_dbus_method(
                    method_name,
                    slf._interface_string(interface)
                    )

        @classmethod
        def method(cls, method_name):
            def method_decorator(func):
                def method_wrapper(obj, *args, **kwargs):
                    method = obj.get_method(method_name, '')
                    value = method(*args, **kwargs)
                    return func(obj, value)
                return method_wrapper
            return method_decorator

        @classmethod
        def listener(cls, signal_name, interface=''):
            def signal_decorator(func):
                cls.add_signal_handler(func, interface_name=cls._interface_string(interface), signal_name=signal_name)
            return signal_decorator

        @classmethod
        def add_signal_handler(cls, handler, interface_name, signal_name):
            cls._signal_handlers.append(_SignalHandler(handler, interface_name, signal_name))

        @classmethod
        def _interface_string(cls, interface):
            return '.'.join([x for x in (cls._service_name, interface) if x])

    if class_name:
        fix_class_name(ClientBaseClass, class_name)
    if class_doc:
        ClientBaseClass.__doc__ = class_doc
    return ClientBaseClass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    client = client_factory('com.example.service', '/com/example/service')

    class ExampleClient(client):

        @client.method('quit')
        def quit(self, value=None):
            return value

        @client.method('get_message')
        def get_message(self, value=None):
            return value

        @client.listener('message_ready')
        def message_ready_handler(self, message):
            self.logger.debug("Message from service: %s", message)
            self.quit()

        def run(self):
            self.logger.debug("Waiting for service to send a message")
            self.get_message()



    GObject.timeout_add(1000, ExampleClient().run)
    loop = GObject.MainLoop()
    loop.run()
