
from lxml.objectify import E

from . import DIElement


class Arg(DIElement):
    """Arg element.
    
    Arguments:
        name (str): The argument name. This should correspond to the name of the
            variable in the method declaration for the sake of sanity. This is
            technically optional according to the D-Bus introspection
            specifications but it is a very goo idea to use.
        type_ (str): D-Bus argument |type_signature|.
        direction (str, optional): The "direction" (input or output) of the argument
            (for output use :class:Response). Defaults to IN.

    """
    
    def __init__(self, name, type_, direction=IN):
        if not type_:
            raise TypeError('need type_ argument as a string.') 
        super().__init__(E.arg, name=name, type_=type_, direction=direction)


class Response(Arg):
    """Arg element tailored for specifying return types.
    
    Arguments:
        type_ (str): D-Bus argument |type_signature| with shortcuts to make declaring the return type brainless.

    """

    def __init__(self, type_):
        super().__init__('response', type_=type_, direction=OUT)
