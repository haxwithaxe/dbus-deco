
__author__ = 'haxwithaxe <spam@haxwithaxe.net>'
__copyright__ = 'Copyright haxwithaxe 2016'
__license__ = 'GPLv3'


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

def _extrapolate_service_path(service_name):
    """Take a guess at the service path by replacing all '.' with '/' and prepending a '/'."""
    return '/'+service_name.replace('.', '/')


def _fix_class_name(cls, name):
    """Adjust cls.__name__ and cls.__qualname__ to use name"""
    cls.__name__ = name
    qualname = cls.__qualname__.split('.')
    qualname.pop()
    qualname.append(name)
    cls.__qualname__ = '.'.join(qualname)


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


def _dot_notation(name):
    return name.replace('/', '.')


def _slash_notation(name):
    return name.replace('.', '/')


def _join_path(*paths):
    return '.'.join(_dot_notation(path) for path in paths)


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
