
from lxml.objectify import E

from . import DIElement



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
        self._signal = pydbus.generic.signal()

    def __call__(self, func):
        """ Decorator. """
        self._handler = func
        self.emit.__doc__ = func.__doc__
        self.attributes['name'] = self.get_name(func)
        return Emitter(self._namespace, func)
