
from . import DIElement, _pack_response, READ, READWRITE, WRITE
from .args import Response
from .properties import Property
from .methods import Method
from .signals import Signal



class Interface(DIElement):
    """Interface element.

    Arguments:
        namespace (str): The D-Bus namespace path for the D-Bus interface.
        *children (tuple, optional): A tuple of DIElement instances.
        **attributes (dict, optional): dict of `interface` element attributes.

    """

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

    def property(self, *annotations, type_=None, access=READWRITE, signal_on=[]):
        """Decorate a method for use as D-Bus property.
        
        Arguments:
            annotations (*Annotation): One or more Annotation instances.
            type_ (str): D-Bus property |type_signature|.
            access (str, optional): Access type of the property (READ, WRITE,
                READWRITE). Defaults to READWRITE to mimic Python's
                :class:property object.
            
        Returns:
            Property: A Property decorator instance.

        """
        prop = Property(self._namespace, type_, *annotations, access=access, signal_on=signal_on)
        self.append(prop)
        return prop

    def method(self, *children, response=None):
        """Decorate a method for use as a D-Bus method.

        Arguments:
            *children (*DIElement): Child elements such as instances of Arg or Annotation.
            response (str): D-Bus argument |type_signature|.
        
        Returns:
            callable: A decorator that returns the unmodified method.

        """
        children = _pack_response(children, response)
        method = Method(self._namespace, *children)
        self.append(method)
        return method

    def signal(self, *annotations, response=None):
        """Decorate a method to emit a D-Bus signal.

        Arguments:
            *annotations (*Annotation): Annotation instances defining metadata of the signal.
            response (str): D-Bus argument |type_signature|.
        
        Returns:
            callable: A method that can be called to emit a signal.

        """
        args = _pack_response(args, Response(response))
        signal = Signal(self._namespace, *args)
        self.append(signal)
        return signal
