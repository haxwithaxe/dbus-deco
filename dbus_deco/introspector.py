
from . import E, tostring, _dot_notation

# Convenience imports
from . import READ, READWRITE, WRITE
from .interface import Interface
from .args import Arg, Response
from .signals import Events, Signal
from .annotations import WellKnown


class Introspector(Interface):
	"""The Grand Introspector!

	Using an instance of this class a D-Bus interface introspection XML document can be created to match the code it is
	meant to describe without remembering to fiddle with XML.

	Arguments:
		namespace (str): The namespace of the service (one step above the full path to the interface).
		*interfaces (*Interface, optional): A list of Interface instances in the even this is a root node with more than one interface.
		**attributes (dict, optional): Attributes for the root node element.

	"""

	def __init__(self, namespace, *interfaces, **attributes):
		super().__init__(_dot_notation(namespace), *interfaces, **attributes)

	def __call__(self, cls):
		""" Class decorator. 
		
		Set the 'name' attribute of the element `cls`, and wrap the `__init__` method in a function that will set the
		`dbus` property of `cls` to the generated introspection XML.
		
		"""
		super().__call__(cls)
		if hasattr(self._interface_class, '__init__'):
			# If __init__ exists copy it off to prevent recursively calling it
			undecorated__init__ = self._interface_class.__init__
		else:
			# Otherwise create a noop to simplify things later
			undecorated__init__ = lambda *_, **__: None
		def decorating__init__(slf, *args, **kwargs):
			if 'namespace' in kwargs:
				raise TypeError(
					'`namespace` is set in the Introspector '
					'it must not be set again in this service'
					)
			self.load_class_methods(slf)
			self._set_introspection_xml(self._interface_class)
			undecorated__init__(slf, *args, **kwargs)
		self._interface_class.__init__ = decorating__init__
		return self._interface_class

	def _set_introspection_xml(self, service):
		xml_doc = E.node(super().__xml__, name=self._namespace)
		setattr(service, 'dbus', tostring(xml_doc, pretty_print=True).decode())
