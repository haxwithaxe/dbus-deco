
from . import DIElement, E

class Method(DIElement):
    """Method element.

    Arguments:
        namespace (str): The D-Bus namespace path for the method.
        *children (tuple): A tuple of DIElement instances.
        **attributes (dict): dict of 'method' element attributes.

    """

    def __init__(self, namespace, *children, **attributes):
        super().__init__(E.method, *children, **attributes)
        self._namespace = namespace
