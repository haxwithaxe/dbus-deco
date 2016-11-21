
from . import DIElement, E, READ, READWRITE, WRITE, annotations
from .signals import Emitter, Events, EmitSignal


class SignallingPropertyDescriptor:

    def __init__(self, fget, fset=None, femit=None, namespace=None, doc=None):
        self.fget = fget
        self._name = self.fget.__name__
        self.fset = fset
        self.femit = femit or fget  # callback
        self._namespace =  namespace
        self.__doc__ = doc
        self.__collect_values(self.fget)

    def __get__(self, obj, cls=None):
        if cls is None:
            cls = type(obj)
        return self.fget.__get__(obj, cls)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        try:
            return self.fset.__get__(obj, type(obj))(value)
        except signal.EmitSignal as sig:
            self.emit(sig.args)
            return sig.return_value

    def emit(self, *args):
        pydbus.generic.signal().emit(self._namespace, {self._name: self.femit}, args)

    def __collect_values(self, func):
        if not func:
            return
        if not self.__doc__:
            self.__doc__ = func.__doc__
        if not self._name:
            self._name = func.__name__


    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        self.__collect_values(self.fset)
        return self    

    def emitter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.femit = func
        self.__collect_values(self.femit)
        return self





class Property(DIElement):
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

    def __init__(self, namespace, type_, *children, access=READWRITE, signal_on=[], **attributes):
        for child in children:
            if not isinstance(child, Annotation):
                raise TypeError('%s is not a valid child of a Property.' % type(child) )
        super().__init__(
            E.property,
            *children,
            type_=type_,
            access=access,
            **attributes
            )
        self._namespace = namespace
        self._emitter = None
        if signal_on:
            self._emitter = Emitter(self._namespace, lambda *_: None)
        for event in signal_on:
            if event == Events.ON_PROPERTY_CHANGE:
                self.append(annotations.PropertyEmitsChangedSignal(value=True))
            elif isinstance(event, annotations.Annotation):
                self.append(event)
            elif isinstance(event, (list, tuple)) and len(event) == 2:
                self.append(annotations.Annotation(name=event[0], value=event[1]))
            else:
                raise TypeError('%s is not a valid event to signal on.' % event)
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
            prop = SignallingPropertyDescriptor(fget=lambda *_: None, fset=func, namespace=self._namespace, doc=doc)
        elif self.needs_setter:
            def fake_setter(*_):
                raise NotImplementedError('this property requires a setter according to the introspection signature')
            prop = SignallingPropertyDescriptor(fget=func, fset=fake_setter, namespace=self._namespace, doc=doc)
        else:
            prop = SignallingPropertyDescriptor(fget=func, namespace=self._namespace, doc=doc)
        return prop

