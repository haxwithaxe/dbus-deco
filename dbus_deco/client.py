
import logging

import dbus

from dbus_deco import extrapolate_service_path, fix_class_name


def client_factory(service_name, service_path=None, class_name=None, class_doc=None):
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

        def __init__(slf):
            slf.logger = logging.getLogger(slf.__class__.__name__)
            bus = dbus.SessionBus()
            slf.interface = bus.get_object(slf._service_name, slf._service_path)

        def get_method(slf, method_name, interface):
            return slf.interface.get_dbus_method(
                    method_name,
                    '.'.join([x for x in (slf._service_name, interface) if x])
                    )

        @classmethod
        def method(cls, method_name, interface=''):
            def method_decorator(func):
                def method_wrapper(obj, *args, **kwargs):
                    method = obj.get_method(method_name, interface)
                    value = method(*args, **kwargs)
                    return func(obj, value)
                return method_wrapper
            return method_decorator

    if class_name:
        fix_class_name(ClientBaseClass, class_name)
    if class_doc:
        ClientBaseClass.__doc__ = class_doc
    return ClientBaseClass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    client = client_factory('com.example.service', '/com/example/service')

    class ExampleClient(client):

        @client.method('quit', 'Quit')
        def quit(self, value=None):
            return value

        @client.method('get_message', 'Message')
        def get_message(self, value=None):
            return value

        def run(self):
            self.logger.debug("Message from service: %s", self.get_message())
            self.quit()


    ExampleClient().run()
