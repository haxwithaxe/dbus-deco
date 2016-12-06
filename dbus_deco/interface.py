
from types import MethodType

from . import DIElement, E, READWRITE, _join_path
from .args import Response
from .properties import Property
from .methods import Method
from .signals import Signal, PropertiesChangedSignal


def _pack_response(args, response):
	if response:
		args = list(args) + [Response(response)]
	return args


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
		self._interface_class = None
		self.__interface_class_attrs = {}
		self.__interface_class_methods = {}

	def load_class_attr(self):
		for attr, value in self.__interface_class_attrs.items():
			setattr(self._interface_class, attr, value)

	def load_class_methods(self, instance):
		for attr, value in self.__interface_class_methods.items():
			setattr(self._interface_class, attr, MethodType(value, instance))

	def __call__(self, cls):
		""" Class decorator. 
		
		Set the 'name' attribute of the element `cls`.
		
		"""
		self._interface_class = cls
		self.load_class_attr()
		self._namespace = _join_path(self._namespace, self._interface_class.__name__)
		self.attributes['name'] = self._namespace
		return self._interface_class

	def decorate_attr(self, attr, value):
		self.__interface_class_attrs[attr] = value

	def decorate_methods(self, method, value):
		self.__interface_class_methods[method] = value

	def _change_getter(self, property_name):
		return getattr(self._interface_class, property_name)

	def property(self, *annotations, type_=None, access=READWRITE, signal_on_change=False):
		"""Decorate a method for use as D-Bus property.
		
		Arguments:
			annotations (*Annotation): One or more Annotation instances.
			type_ (str): D-Bus property |type_signature|.
			access (str, optional): Access type of the property (READ, WRITE,
				READWRITE). Defaults to READWRITE to mimic Python's
				:class:property object.
			signal_on_change (bool, optional): Set org.freedesktop.DBus.Property.EmitsChangedSignal Annotation if True. Defaults to False
			
		Returns:
			Property: A Property decorator instance.

		"""
		if signal_on_change:
			self._set_properties_changed()
		prop = Property(self, self._namespace, type_, *annotations, access=access, signal_on_change=signal_on_change)
		self.append(prop)
		return prop

	def _set_properties_changed(self):
		onchange = PropertiesChangedSignal(namespace=self._namespace, getter=self._change_getter)
		self.decorate_methods('PropertiesChanged', onchange)

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
		args = _pack_response(annotations, Response(response))
		signal = Signal(self._namespace, *args)
		self.append(signal)
		return signal
