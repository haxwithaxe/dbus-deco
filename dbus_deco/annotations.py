
from lxml.objectify import E

from . import DIElement, INVALIDATES, CONST


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
        super().__init__(E.annotation, name=name or self.name, value=value or self.default_value)

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

    def __init__(self, value=None):
        super().__init__(value=value)


class GLibCSymbol(Annotation):
    """

    Arguments:
        value (str): !!!

    From the D-Bus Introspection specification:
        org.freedesktop.DBus.GLib.CSymbol   (string)    The C symbol; may be used for methods and interfaces

    """

    name = 'org.freedesktop.DBus.GLib.CSymbol'

    def __init__(self, value=None):
        super().__init__(value=value)


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

    def __init__(self, value=None):
        super().__init__(value=value)


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

    def __init__(self, value=None):
        super().__init__(value=value)

class WellKnown:

    depricated = Depricated
    glib_c_symbol = GLibCSymbol
    method_noreply = MethodNoReply
    property_emits_changed_signal = PropertyEmitsChangedSignal
