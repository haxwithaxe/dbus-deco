
import logging

import pydbus
from gi.repository import GObject
from lxml import etree
from lxml.objectify import E

from dbus_deco import fix_class_name


def _decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


class Arg:

    def __init__(self, name, type_='s', direction='in'):
        self._name = name
        self._type = type_
        self._direction = direction

    def __iter__(self):
        return iter((('name', self._name), ('type', self._type), ('direction', self._direction)))

    @property
    def __xml__(self):
        return E.arg(**dict(self))


class Method:

    def __init__(self, name, *args):
        self._name = name
        self._args = args

    def __iter__(self):
        return iter((('name', self._name),))


class Signal:

    def __init__(self, name, *args):
        self._name = name
        self._args = args

    def __iter__(self):
        return iter((('name', self._name),))

    @property
    def __xml__(self):
        return E.signal(*[x.__xml__ for x in self._args], **dict(self))


class Service:

    name = None
    children = []
    
    @classmethod
    def factory(cls, service_name, class_name=None, class_doc=None):
        class ServiceBaseClass(cls):
            pass
        ServiceBaseClass.name = service_name
        if class_name:
            fix_class_name(ServiceBaseClass, class_name)
        if class_doc:
            ServiceBaseClass.__doc__ = class_doc
        return ServiceBaseClass

    @classmethod
    def add_child(cls, child):
        cls.children.append(child.__xml__)

    @classmethod
    def method(cls, name, *args, response=None):
        if response:
            args = list(args) + [Arg('response', response, 'out')]
        cls.add_child(Method(name, *args))
        return _decorator
    
    @classmethod
    def signal(cls, name, *args, response=None):
        return lambda _: signal

    @classmethod
    def tostring(cls):
        return etree.tostring(E.node(E.interface(*cls.children, name=cls.name))).decode()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    service = Service.factory('com.example.service')

    class ExampleService(service):

        @service.method('HelloWorld', response='s')
        def HelloWorld(self):
            return 'Hello!'
        
        @service.method('Echo', Arg('message', 's'), response='s')
        def Echo(self, message):
            return message


    loop = GObject.MainLoop()
    bus = pydbus.SessionBus()
    bus.publish('com.example.service', ExampleService())
    loop.run()
