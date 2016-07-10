

def extrapolate_service_path(service_name):
    return '/'+service_name.replace('.', '/')


class DBusProperty:
    """Emulate PyProperty_Type() in Objects/descrobject.c"""

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
        def getter_decorator(fget):
            def getter_wrapper(obj):
                __getter = obj.get_method(getter_name, getter_interface)
                return fget(obj, __getter())
            return type(self)(getter_wrapper, self.fset, self.fdel, self.__doc__, self.name, self.interface)
        return getter_decorator

    def setter(self, setter_name, setter_interface):
        def setter_decorator(fset):
            def setter_wrapper(obj, value):
                __setter = obj.get_method(setter_name or self.name, setter_interface or self.interface)
                return fset(obj, __setter(value))
            return type(self)(self.fget, setter_wrapper, self.fdel, self.__doc__, self.name, self.interface)
        return setter_decorator

    def deleter(self, deleter_name, deleter_interface):
        def deleter_decorator(fdel):
            def deleter_wrapper(obj):
                __deleter = obj.get_method(deleter_name or self.name, deleter_interface or self.interface)
                return fdel(obj, __deleter())
            return type(self)(self.fget, self.fset, deleter_wrapper, self.__doc__, self.name, self.interface)
        return deleter_decorator
