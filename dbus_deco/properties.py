
from functools import partialmethod
from . import DIElement, DIElementGroup, E, READ, READWRITE, WRITE, annotations
from .signals import Events, EmitSignal, Signal
from .args import Response


def to_annotation(event):
    if event == Events.ON_PROPERTY_CHANGE:
        return annotations.PropertyEmitsChangedSignal(value=True)
    elif event in Events:
        return Events.get(event)
    elif isinstance(event, annotations.Annotation):
        self.append(event)
    elif isinstance(event, (list, tuple)) and len(event) == 2:
        self.append(annotations.Annotation(name=event[0], value=event[1]))
    else:
        raise TypeError('%s is not a valid event to signal on.' % event)


class SignallingPropertyDescriptor:
    
    _name = None

    def __init__(self, add_signal, fget, fset=None, femit=None, namespace=None, doc=None):
        self._add_signal = add_signal
        self.getter(fget)
        self.setter(fset)
        self.emitter(femit or fget)  # callback
        self._namespace = namespace
        self.__doc__ = doc
        self.__collect_values(self.fget)

    def signal(self, signature=None):
        def _decorated_signal(func):
            return self._add_signal(name=func.__name__, callback=func, signature=signature)
        return _decorated_signal

    def __get__(self, obj, cls=None):
        if cls is None:
            cls = type(obj)
        return self.fget.__get__(obj, cls)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError('Can\'t set attribute')
        return self.fset.__get__(obj, type(obj))(value)

    def __collect_values(self, func):
        if not func:
            return
        if not self.__doc__:
            self.__doc__ = func.__doc__
        if not self._name:
            self._name = func.__name__

    def getter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            self.fget = classmethod(func)
        else:
            self.fget = func
        self.__collect_values(func)
        return self

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            self.fset = classmethod(func)
        else:
            self.fset = func
        self.__collect_values(func)
        return self

    def emitter(self, func):
        self.femit = func
        self.__collect_values(func)
        return self


class _Property(DIElement):
    """Property element.

    Arguments:
        namespace (str): The D-Bus path for the property.
        type_ (str): D-Bus argument |type_signature|.
        *children (tuple): A tuple of DIElement instances.
        access (str): Access type of the property (READ, WRITE, READWRITE). Defaults
            to READWRITE to mimic Python's :class:property object.
        signal_on (list, optional): List of events for the property to signal on. Defaults to an empty list.
        **attributes (dict): dict of `method` element attributes.

    """

    def __init__(self, add_signal, namespace, type_, *children, access=READWRITE, signal_on_change=False, **attributes):
        self.add_signal = add_signal
        for child in children:
            if not isinstance(child, Annotation):
                raise TypeError('%s is not a valid child of a Property.' % type(child))
        super().__init__(
            E.property,
            *children,
            type_=type_,
            access=access,
            **attributes
            )
        self._namespace = namespace
        if signal_on_change:
            self.append(annotations.PropertyEmitsChangedSignal(value=True))
        self.needs_setter = access in (READWRITE, WRITE)
        self.write_only = access == WRITE
        self.read_only = access == READ

    def __call__(self, func):
        """Decorate the method.

        The method being decorated is used as the getter if the Property is readable,
        or if it is write only the method being decorated will be the setter and the
        getter just returns None.

        If the Property instance's access is READWRITE, then a dummy method is set as
        the setter that will throw a NotImplementedError if it is not overwritten.

        """
        super().__call__(func)
        doc = func.__doc__
        if self.write_only:
            # Just use the function we have as the setter.
            prop = SignallingPropertyDescriptor(self.add_signal, fget=lambda *_: None, fset=func, namespace=self._namespace, doc=doc)
        elif self.needs_setter:
            def fake_setter(*_):
                raise NotImplementedError('this property requires a setter according to the introspection signature')
            prop = SignallingPropertyDescriptor(self.add_signal, fget=func, fset=fake_setter, namespace=self._namespace, doc=doc)
        else:
            prop = SignallingPropertyDescriptor(self.add_signal, fget=func, namespace=self._namespace, doc=doc)
        return prop


class Property(DIElementGroup):
    """Property element.

    Arguments:
        namespace (str): The D-Bus path for the property.
        type_ (str): D-Bus argument |type_signature|.
        *children (tuple): A tuple of DIElement instances.
        access (str): Access type of the property (READ, WRITE, READWRITE). Defaults
            to READWRITE to mimic Python's :class:property object.
        signal_on (list, optional): List of events for the property to signal on. Defaults to an empty list.
        **attributes (dict): dict of `method` element attributes.

    """

    def __init__(self, parent, namespace, type_, *children, access=READWRITE, signal_on_change=True, **attributes):
        super().__init__()
        self._parent = parent
        self._namespace = namespace
        self._type = type_
        self._signal_on_change = signal_on_change
        self._property = _Property(
                self.add_signal, self._namespace, self._type,
                *children, access=READWRITE,
                signal_on_change=signal_on_change,
                **attributes
                )
        self.update(self._property)

    def add_signal(self, name=None, callback=None, signature=None):
        signature = signature or self._type
        if not callable(callback):
            raise TypeError('callback `%s` for "%s" must be callable.' % (callback, name))
        new_signal = Signal(self._namespace, Response(signature))
        emitter = new_signal(callback)
        self._parent.decorate_methods(name, emitter)
        self.update(new_signal)
        return emitter

    def __call__(self, func):
        """Method decorator."""
        prop = self._property(func)
        return prop
