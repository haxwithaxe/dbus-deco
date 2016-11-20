
"""
.. |type_signature| replace:: `type signature <https://dbus.freedesktop.org/doc/dbus-specification.html#type-system>`


"""
import logging

import pydbus
from gi.repository import GObject
from lxml import etree
from lxml.objectify import E


READ = 'read'
READWRITE = 'readwrite'
WRITE = 'write'
OUT = 'out'
IN = 'in'
INVALIDATES = 'invalidates'
CONST = 'const'

def _passthrough_decorator(func):
    def _passthrough_decorator_wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return _passthrough_decorator_wrapper


def _to_xml(item):
    if hasattr(item, '__xml__'):
        return item.__xml__
    return item

def _untail(key):
    if key in ('type_', 'class_', 'id_'):
        return key[:-1]
    return key


def _pack_response(args, response):
    if response:
        args = list(args) + [Response(response)]
    return args

def dot_notation(name):
    return name.replace('/', '.')


def slash_notation(name):
    return name.replace('.', '/')


def join_path(*paths):
    return '.'.join(dot_notation(path) for path in paths)


class DIElement:
    """

    Reference:
        https://dbus.freedesktop.org/doc/dbus-specification.html#introspection-format

<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
         "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">

    """

    def __init__(self, element_factory, *children, **attributes):
        self.__element_factory = element_factory
        self._namespace = None
        self.children = list(children)
        self.attributes = {_untail(key): value for key, value in attributes.items()}

    def __call__(self, func):
        """ Decorator. """
        self.attributes['name'] = self.get_name(func)
        return _passthrough_decorator(func)

    def get_name(self, func):
        return func.__name__

    def append(self, child):
        self.children.append(child)

    def __getitem__(self, attribute):
        return self.attributes[attribute]

    def __setitem__(self, attribute, value):
        self.attributes[attribute] = value

    def get(self, attribute, default=None):
        return self.attributes.get(attribute, default)

    @property
    def __xml__(self):
        """ Returns the DBus introspection XML for this node type. """
        for key, value in self.attributes.items():
            if value in (True, False):
                self.attributes[key] = str(value).lower()
        return self.__element_factory(*[x.__xml__ for x in self.children], **self.attributes)

    def __str__(self):
        return etree.tostring(self.__xml__, prettr_print=True).decode()

class Annotation(DIElement):
    """D-Bus introspection annotation.

    Method, interface, property, signal, and argument elements may have 
    "annotations", which are generic key/value pairs of metadata. They are 
    similar conceptually to Java's annotations and C# attributes.

    """

    name = None
    default_value = None

    def __init__(self, name=None, value=None):
        name = name or self.name
        if value is None:
            if self.default_value is None:
                raise TypeError('There is no default value. Either pass a valid `value`, or specify a `default_value`.')
            value = self.default_value
        super().__init__(E.annotation, name=name or self.name, value=self.validate(value) or self.default_value)

    def validate(self, value):
        """Validate the value supplied by the developer.

        The purpose of this is to break early in this case where we know exactly the valid values.

        Where the D-Bus Introspection documentation specifies "true, false" bool objects are assumed to be used as
        values here.

        This default implementation looks in the `valid_values` attribute of this class for valid values and
        automatically returns as if the value is valid if `valid_values` is falsy.

        Arguments:
            value: The desired value of the `value` element of this annotation element.

        Raises:
            TypeError: When values are invalid.

        """
        if self.valid_values and value not in self.valid_values:
            raise TypeError


class Depricated(Annotation):
    """Whether or not the entity is deprecated.

    Arguments:
        value (bool, optional): !!!. Defaults to True.

    Note:
        This defaults to True rather than False as a convenience. The intent is to mark things as deprecated with this
        rather than to mimic the behavior of the introspection system.

    From the D-Bus Introspection specification:
        org.freedesktop.DBus.Deprecated     true,false  Whether or not the entity is deprecated; defaults to false

    """

    name = 'org.freedesktop.DBus.Deprecated'
    defaault_value = True
    valid_values = (True, False)


class GLibCSymbol(Annotation):
    """

    Arguments:
        value (str): !!!

    From the D-Bus Introspection specification:
        org.freedesktop.DBus.GLib.CSymbol   (string)    The C symbol; may be used for methods and interfaces

    """

    name = 'org.freedesktop.DBus.GLib.CSymbol'


class MethodNoReply(Annotation):
    """ Don't expect a reply to the method call if True.

    Arguments:
        value (bool, optional): !!!. Defaults to True.

    From the D-Bus Introspection specification:
        org.freedesktop.DBus.Method.NoReply     true,false  If set, don't expect a reply to the method call; defaults to false.

    """

    name = 'org.freedesktop.DBus.Method.NoReply'
    default_value = True
    valid_values = (True, False)


class PropertyEmitsChangedSignal(Annotation):
    """Implementation of an 'org.freedesktop.DBus.Property.EmitsChangedSignal' annotation element.

    This has some minor sanity check built in to limit the acceptable inputs the
    constructor to (True, INVALIDATES, CONST, False).

    Arguments:
        value (str or bool): !!!. One of (True, INVALIDATES, CONST, False).

    Note:
        From the D-Bus Introspection specification:
            If set to false, the org.freedesktop.DBus.Properties.PropertiesChanged signal, see the section called
            “org.freedesktop.DBus.Properties” is not guaranteed to be emitted if the property changes.

            If set to const the property never changes value during the lifetime of the object it belongs to, and hence the signal is never emitted for it.
            If set to invalidates the signal is emitted but the value is not included in the signal.

            If set to true the signal is emitted with the value included.

            The value for the annotation defaults to true if the enclosing interface element does not specify the annotation.
            Otherwise it defaults to the value specified in the enclosing interface element.

            This annotation is intended to be used by code generators to implement client-side caching of property values. For all properties for which the annotation is set to const, invalidates or true the client may unconditionally cache the values as the properties don't change or notifications are generated for them if they do.

    """

    name = 'org.freedesktop.DBus.Property.EmitsChangedSignal'
    default_value = None  # there is no reasonable default
    valid_values = (True, INVALIDATES, CONST, False)


class Arg(DIElement):
    """Arg element.
    
    Arguments:
        name (str): The argument name. This should correspond to the name of the
            variable in the method declaration for the sake of sanity. This is
            technically optional according to the D-Bus introspection
            specifications but it is a very goo idea to use.
        type_ (str): D-Bus argument |type_signature|.
        direction (str, optional): The "direction" (input or output) of the argument
            (for output use :class:Response). Defaults to IN.

    """
    
    def __init__(self, name, type_, direction=IN):
        if not type_:
            raise TypeError('need type_ argument as a string.') 
        super().__init__(E.arg, name=name, type_=type_, direction=direction)


class Response(Arg):
    """Arg element tailored for specifying return types.
    
    Arguments:
        type_ (str): D-Bus argument |type_signature| with shortcuts to make declaring the return type brainless.

    """

    def __init__(self, type_):
        super().__init__('response', type_=type_, direction=OUT)


class Method(DIElement):
    """Method element.

    Arguments:
        namespace (str): The D-Bus namespace path for the method.
        *children (tuple): A tuple of DIElement instances.
        **attributes (dict): dict of 'method' element attributes.

    """

    def __init__(self, namespace, *children, **attributes):
        super().__init__(E.method, *children, **attributes)
        self._namespace = namespace


class Signal(DIElement):
    """Signal element.

    Arguments:
        namespace (str): The D-Bus namespace path for the signal.
        *children (tuple): A tuple of DIElement instances.
        **attributes (dict): dict of `method` element attributes.

    """

    def __init__(self, namespace, *children, **attributes):
        super().__init__(E.signal, *children, **attributes)
        self._namespace = namespace


class Property(DIElement):
    """Property element.

    Arguments:
        namespace (str): The D-Bus namespace path for the property.
        type_ (str): D-Bus argument |type_signature|.
        *children (tuple): A tuple of DIElement instances.
        access (str): Access type of the property (READ, WRITE, READWRITE).
        **attributes (dict): dict of `method` element attributes.

    """

    def __init__(self, namespace, type_, *children, access=READWRITE, **attributes):
        for child in children:
            if not isinstance(child, (Property, Annotation)):
                raise TypeError('%s is not a valid child of a Property.' % type(child) )
        super().__init__(
            E.property,
            *children,
            type_=type_,
            access=access,
            **attributes
            )
        self._namespace = namespace
        self.needs_setter = access in (READWRITE, WRITE)
        self.only_setter = access == WRITE

    def __call__(self, func):
        super().__call__(func)
        doc = func.__doc__
        if self.only_setter:
            return property(fget=lambda *_, **__: None, fset=func, doc=doc)
        if self.needs_setter:
            def fake_setter(*_, **__):
                raise NotImplementedError('this property requires a setter according to the introspection signature')
            return property(fget=func, fset=fake_setter)
        else:
            return property(fget=func)


class Interface(DIElement):
    """Interface element.

    Arguments:
        namespace (str): The D-Bus namespace path for the D-Bus interface.
        *children (tuple): A tuple of DIElement instances.
        **attributes (dict): dict of `interface` element attributes.

    """

    required_attributes = ('name',)
    valid_child_types = None

    def __init__(self, namespace, *children, **attributes):
        super().__init__(E.interface, *children, **attributes)
        self._namespace = namespace

    def __call__(self, cls):
        """ Class decorator. 
        
        Set the 'name' attribute of the element `cls`.
        
        """
        self._namespace = join_path(self._namespace, cls.__name__)
        self.attributes['name'] = self._namespace
        return cls

    def property(self, *annotations, type_=None, access=READWRITE):
        prop = Property(self._namespace, type_, *annotations, access=access)
        self.append(prop)
        return prop

    def method(self, *args, response=None):
        children = _pack_response(args, response)
        method = Method(self._namespace, *children)
        self.append(method)
        return method

    def signal(self, *args, response=None):
        args = _pack_response(args, Response(response))
        signal = Signal(self._namespace, *args)
        self.append(signal)
        return signal



class Introspector(Interface):


    def __init__(self, namespace, *interfaces, **attributes):
        super().__init__(dot_notation(namespace), *interfaces, **attributes)

    def __call__(self, cls):
        """ Class decorator. 
        
        Set the 'name' attribute of the element `cls`, and wrap the `__init__` method in a function that will set the
        `dbus` property of `cls` to the generated introspection XML.
        
        """
        interface_class = super().__call__(cls)
        if hasattr(interface_class, '__init__'):
            # If __init__ exists copy it off to prevent recursively calling it
            undecorated__init__ = interface_class.__init__
        else:
            # Otherwise create a noop to simplify things later
            undecorated__init__ = lambda *_, **__: None
        def decorating__init__(slf, *args, **kwargs):
            if 'namespace' in kwargs:
                raise TypeError(
                    '`namespace` is set in the Introspector '
                    'it must not be set again in this service'
                    )
            self._set_introspection_xml(interface_class)
            undecorated__init__(slf, *args, **kwargs)
        interface_class.__init__ = decorating__init__
        return interface_class

    def _set_introspection_xml(self, service):
        xml_doc = E.node(super().__xml__, name=self._namespace)
        service.dbus = etree.tostring(xml_doc, pretty_print=True).decode()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    introspector = Introspector('com.example.service')

    @introspector
    class ExampleService:

        @introspector.method(response='s')
        def HelloWorld(self):
            return 'Hello!'
        
        @introspector.method(Arg('message', 's'), response='s')
        def Echo(self, message):
            return message

        @introspector.property(type_='b', access='read')
        def Status(self):
            return True

        @introspector.property(type_='i', access='readwrite')
        def Count(self):
            return 100

        @Count.setter
        def Count(self, value):
            print(value)

    example_service = ExampleService()
    print(example_service.dbus)


    loop = GObject.MainLoop()
    bus = pydbus.SessionBus()
    bus.publish('com.example.service', example_service)
    loop.run()
