
from lxml.etree import tostring
from lxml.objectify import E
from gi.repository import GObject
import pydbus

from dbus_deco import DBusServiceProperty


def toxml(node):
    print('node', node)
    if hasattr(node, '__xml__'):
        if callable(node.__xml__):
            return node.__xml__()
        else:
            return node.__xml__
    return node


class XMLNode:

    element = None
    name = None

    def __init__(self, *children, **attribs):
        self._attribs = attribs
        self._children = list(children)

    def append(self, value):
        self._children.append(value)

    def extend(self, children):
        self._children.extend(children)

    def set(self, key, value):
        self._attribs[key] = value

    def update(self, attribs):
        self._attribs.update(attribs)

    def finalize(self):
        pass

    def _finalize(self):
        self.finalize()
        if self.name:
            self.set('name', self.name)
        self.__process_children()
        self.__process_attribs()

    def __process_children(self):
        for index, child in enumerate(self._children):
            if child is None:
                print('popped child',self._children.pop(index))
            else:
                self._children[index] = toxml(child)
                print('index, child', index, child)

    def __process_attribs(self):
        for key, value in self._attribs.items():
            if not key or value is None:
                print(self._attribs.pop(key))
            elif key.endswith('_'):
                self.set(key[:-1], self._attribs.pop(key))
            elif key.startswith('_'):
                self._attribs.pop(key)


    def __xml__(self):
        print(self.__class__.__name__, 'element, children, attribs', self.element, self._children, self._attribs)
        self._finalize()
        xml = E(self.element, *self._children, **self._attribs)
        return xml

    def __str__(self):
        xml = self.__xml__()
        string = tostring(xml).decode()
        return string


class DIInterface(XMLNode):

    element = 'interface'

    def __init__(self, name=None, properties=tuple(), methods=tuple(), **attributes):
        super().__init__(**attributes)
        if name:
            self.set('name', name)
        for prop in properties:
            self.append(DIProperty(**prop))
        for method in methods:
            self.append(DIMethod(**method))

    def method(self, name, *args):
        self.append(DIMethod(name=name, args=args))
        def method_decorator(func):
            def method_wrapper(obj, *_args, **kwargs):
                return func(obj, *_args, **kwargs)
            return method_wrapper
        return method_decorator

    def property(self, name, *args, **kwargs):
        prop = DIProperty(name, **kwargs)
        self.append(prop)
        return DBusServiceProperty(name, prop)


class DIAnnotation(XMLNode):

    element = 'annotation'


class DIArg(XMLNode):

    element = 'arg'

    def __init__(self, name=None, type_=None, direction=None):
        super().__init__(name=name, type_=type_, direction=direction)


class DIMethod(XMLNode):

    element = 'method'

    def __init__(self, name=None, args=[], **attributes):
        attributes['name'] = name
        super().__init__(**attributes)
        for arg in args:
            self.append(DIArg(**arg))
        print('method', str(self))


class DIProperty(XMLNode):

    element = 'property'

    def __init__(self, name=None, access=4, type_=None, annotations=tuple()):
        self._mode = access
        super().__init__(name=name, access=self.access, type_=type_, _annotations=annotations)

    @property
    def access(self):
        return {2:'write', 4:'read', 6:'readwrite'}[self._mode]

    @property
    def readable(self):
        return self._mode in (4, 6)

    @readable.setter
    def readable(self, value):
        if value and self._mode in (0, 2):
            self._mode += 4
        elif not value and self._mode in (4, 6):
            self._mode -= 4

    @property
    def writeable(self):
        return self._mode in (2, 6)

    @writeable.setter
    def writeable(self, value):
        if value and self._mode in (0, 4):
            self._mode += 2
        elif not value and self._mode in (2, 6):
            self._mode -= 2

    def finalize(self):
        self._attribs['access'] = self.access


class DIService(DIInterface):

    name = None

    def __init__(self):
        super().__init__(self.name)

    @classmethod
    def new(cls, interface_name):
        class ServiceDecorator(cls):
            name = interface_name

        class ServiceBaseClass:
            di = ServiceDecorator()
            name = interface_name
            dbus = ''

            def __init__(slf):
                slf.dbus = str(slf.di)
                print('di children', tostring(slf.di._children[0]))

        return ServiceBaseClass

    def __xml__(self):
        return E('node', super().__xml__())


if __name__ == '__main__':
    Service = DIService.new('com.example.service')
    service = Service.di

    class Example(Service):

        def run(self):
            bus = pydbus.SessionBus()
            bus.publish(self.name, self)
            self.loop = GObject.MainLoop()
            self.loop.run()

        @service.method('foo', {'name':'bar', 'type_':'s', 'direction':'out'})
        def foo(self):
            return 'bar value'

    e = Example()
    print(e.dbus)
    e.run()
