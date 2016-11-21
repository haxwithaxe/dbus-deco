
from lxml.objectify import E
    
from . import DIElement
from .annotations import PropertyEmitsChangedSignal
from .signals import Emitter


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
        self.signal_on = signal_on
        self._emitter = None
        if self.signal_on:
            self._emitter = Emitter(self._namespace, lambda *_: None)
        for event in self.signal_on:
            if event == PropertyEmitsChangedSignal.name:
                self.append(PropertyEmitsChangedSignal(value=True))
        self.needs_setter = access in (READWRITE, WRITE)
        self.write_only = access == WRITE
        self.read_only = access == READ
        self._property = None

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
            self._property = property(fget=lambda *_, **__: None, fset=func, doc=doc)
        elif self.needs_setter:
            def fake_setter(*_, **__):
                raise NotImplementedError('this property requires a setter according to the introspection signature')
            self._property = property(fget=func, fset=fake_setter)
        else:
            self.property = property(fget=func)
        return self

    @property
    def emitter(self):
        return self._emitter

    @emitter.setter
    def emitter(self, func):
        if self._emitter:
            self._emitter.func = func

    def getter(self, func):
        if self.write_only:
            raise AttributeError('This property is *read only*. It cannot have a setter.')
        self._property = self._property.getter(func)

    def setter(self, func):
        if self.read_only:
            raise AttributeError('This property is *read only*. It cannot have a setter.')
        self._property = self._property.setter(func)
