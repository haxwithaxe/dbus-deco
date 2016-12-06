
from functools import partial

import pydbus

from . import DIElement, DIElementGroup, E, annotations


class _Signal:

	def __init__(self):
		self.map = {}
		self.__self__ = None
		self.__qualname__ = '<some signal>' # function uses <lambda> ;)
		self.__doc__ = 'Special signal.'

	@property
	def callbacks(self):
		return self.map[self.__self__]

	def connect(self, callback):
		"""Subscribe to the signal."""
		return pydbus.generic.subscription(self.map.setdefault(self.__self__, []), callback)

	def emit(self, *args):
		"""Emit the signal."""
		for cb in self.map.get(self.__self__, []):
			cb(*args)

	def __call__(self, instance, *args):
		"""Emit the signal."""
		self.__self__ = instance
		self.emit(*args)

	def __repr__(self):
		return '<bound signal ' + self.__qualname__ + ' of ' + repr(self.__self__) + '>'


class PropertiesChangedSignal(_Signal):
	"""Preloaded pydbus.generic.signal with the namespace."""

	def __init__(self, namespace=None, getter=None):
		super().__init__()
		self.namespace = namespace
		self.getter = getter

	def __call__(self, instance, *args, **kwargs):
		changed = {}
		for change in kwargs.get('changed', []):
			changed[change] = self.getter(change)
		invalidatated = kwargs.get('invalidatated', [])
		super().__call__(instance, self.namespace, changed, invalidatated)
		

class EmitSignal(Exception):
	"""Tell a parent scope that there is a signal to emit.
	
	Arguments:
		args (tuple): pydbus.generic.signal callback arguments.
		return_value (optional): The return value that would have been given had this exception not been thrown.

	"""

	def __init__(self, *args, return_value=None):
		super().__init__('Emit a signal')


class Events:
	ON_PROPERTY_CHANGE = annotations.PropertyEmitsChangedSignal.name


class Signal(DIElement):
	"""Signal element.

	Arguments:
		namespace (str): The D-Bus namespace path for the D-Bus interface.
		*children (tuple): A tuple of DIElement instances.
		response (str): 
		**attributes (dict): dict of `method` element attributes.

	"""

	def __init__(self, namespace, *children, response=None, **attributes):
		super().__init__(E.signal, *children, **attributes)
		if response:
			self.append(Response(response))
		self._namespace = namespace
		self.on_signal_callback = None

	def __call__(self, func=None):
		""" Decorator. """
		if self.on_signal_callback:
			func = self.on_signal_callback
		elif not func:
			raise TypeError(
							'Either the `func` argument to __call__ or the '
							'`on_signal_callback` keyword argument to the '
							'constructor must be set.'
							)
		super().__call__(func)
		self.attributes['name'] = func.__name__
		return _Signal()
