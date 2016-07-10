
__author__ = 'haxwithaxe <spam@haxwithaxe.net>'
__copyright__ = 'Copyright haxwithaxe 2016'
__license__ = 'GPLv3'


def extrapolate_service_path(service_name):
    """Take a guess at the service path by replacing all '.' with '/' and prepending a '/'."""
    return '/'+service_name.replace('.', '/')


def fix_class_name(klass, name):
    """Adjust klass.__name__ and klass.__qualname__ to use name"""
    klass.__name__ = name
    qualname = klass.__qualname__.split('.')
    qualname.pop()
    qualname.append(name)
    klass.__qualname__ = '.'.join(qualname)


class DBusProperty:
    """A @property work-alike for DBus methods.
    This is based on `PyProperty_Type()` in `Objects/descrobject.c` as interpreted by Raymond Hettinger on
    http://stackoverflow.com/questions/12405087/subclassing-pythons-property

    Attributes:
        fget (callable): The function or method to use to get the value.
        fset (callable): The function or method to use to set the value.
        fdel (callable): The function or method to use to delete the value.
        name (str): The default DBus service method name (eg "get_message" of
            "com.example.service.Message.get_message"). This is used as the
            method name if none is specified in the getter, setter, or deleter
            method calls.
        interface (str): The default DBus service interface name (eg "Message"
            of "com.example.service.Message"). This is used as the method name
            if none is specified in the getter, setter, or deleter method calls.


    Arguments:
        fget (callable): The function or method to use to get the value.
        fset (callable, optional): The function or method to use to set the
            value. Defaults to None.
        fdel (callable, optional): The function or method to use to delete the
            value. Defaults to None.
        doc (str, optional): The docstring for the property. Defaults to
            `fget.__doc__`.
        name (str, optional): The DBus service method name (eg "get_message" of
            "com.example.service.Message.get_message"). Defaults to None.
        interface (str, optional): The DBus service interface name
            (eg "Message" of "com.example.service.Message"). Defaults to None.

    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None, interface=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.name = name
        self.interface = interface
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def getter(self, getter_name, getter_interface):
        """ A decorator to set the getter method.

        Arguments:
            name (str): The DBus service method name (eg "get_message" of "com.example.service.Message.get_message").
            interface (str): The DBus service interface name (eg "Message" of "com.example.service.Message").

        """
        def getter_decorator(fget):
            def getter_wrapper(obj):
                __getter = obj.get_method(getter_name, getter_interface)
                return fget(obj, __getter())
            return type(self)(getter_wrapper, self.fset, self.fdel, self.__doc__, self.name, self.interface)
        return getter_decorator

    def setter(self, setter_name=None, setter_interface=None):
        """ A decorator to set the setter method.

        Arguments:
            setter_name (str): The DBus service method name (eg "set_message" of "com.example.service.Message.get_message"). Defaults to `self.name`.
            setter_interface (str): The DBus service interface name (eg "Message" of "com.example.service.Message"). Defaults to `self.interface`.

        """
        def setter_decorator(fset):
            def setter_wrapper(obj, value):
                __setter = obj.get_method(setter_name or self.name, setter_interface or self.interface)
                return fset(obj, __setter(value))
            return type(self)(self.fget, setter_wrapper, self.fdel, self.__doc__, self.name, self.interface)
        return setter_decorator

    def deleter(self, deleter_name=None, deleter_interface=None):
        """ A decorator to set the getter method.

        Arguments:
            deleter_name (str): The DBus service method name (eg "del_message" of "com.example.service.Message.del_message"). Defaults to `self.name`.
            deleter_interface (str): The DBus service interface name (eg "Message" of "com.example.service.Message"). Defaults to `self.interface`.

        """
        def deleter_decorator(fdel):
            def deleter_wrapper(obj):
                __deleter = obj.get_method(deleter_name or self.name, deleter_interface or self.interface)
                return fdel(obj, __deleter())
            return type(self)(self.fget, self.fset, deleter_wrapper, self.__doc__, self.name, self.interface)
        return deleter_decorator
