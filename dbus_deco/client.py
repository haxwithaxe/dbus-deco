
import logging

import dbus

from dbus_deco import extrapolate_service_path


def client_factory(service_name, service_path, class_name=None):
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
        ClientBaseClass.__name__ = class_name
        ClientBaseClass.__qualname__ = '.'.join(ClientBaseClass.__qualname__.split('.')[:-2]+[class_name])
    return ClientBaseClass


if __name__ == '__main__':
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
