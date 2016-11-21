
import pydbus

from . import DIElement, annotations


class EmitSignal(Exception):
    """Tell a parent scope that there is a signal to emit.
    
    Arguments:
        args (tuple): pydbus.generic.signal callback arguments.
        return_value (optional): The return value that would have been given had this exception not been thrown.

    """

    def __init__(self, *args, return_value=None):
        super().__init__('Emit a signal')


class Events:
    ON_PROPERTY_CHANGE = annotations.PropertyEmitsChangedSignal.name


class BuiltInEmitter(pydbus.generic.signal):
    """Preloaded pydbus.generic.signal with the namespace and method to call. """

    def __init__(self, namespace):
        super().__init__()
        self._namespace = namespace

    def emit(self, obj, name, *args):
        super().emit(obj, self._namespace, {name: lambda *x: x}, *args)

class Emitter(pydbus.generic.signal):
    """Preloaded pydbus.generic.signal with the namespace and method to call. """

    def __init__(self, namespace, func):
        super().__init__()
        self._namespace = namespace
        self._func = func

    def emit(self, obj, *args):
        super().emit(obj, self._namespace, {self._func.__name__: self._func}, *args)


class Signal(DIElement):
    """Signal element.

    Arguments:
        namespace (str): The D-Bus namespace path for the D-Bus interface.
        *children (tuple): A tuple of DIElement instances.
        **attributes (dict): dict of `method` element attributes.

    """

    def __init__(self, namespace, *children, **attributes):
        super().__init__(E.signal, *children, **attributes)
        self._namespace = namespace


    def get_emitter(self, name):
        self.attributes['name'] = name
        return Emitter(self._namespace, func)

    def __call__(self, func):
        """ Decorator. """
        super().__call__(func)
        return self.get_emitter(self.get_name(func))
