from .interface import Interface


class Introspector(Interface):


    def __init__(self, namespace, *interfaces, **attributes):
        super().__init__(dot_notation(namespace), *interfaces, **attributes)

    def __call__(self, cls):
        """ Class decorator. 
        
        Set the 'name' attribute of the element `cls`, and wrap the `__init__` method in a function that will set the
        `dbus` property of `cls` to the generated introspection XML.
        
        """
        interface_class = super().__call__(cls)
        if hasattr(interface_class, '__init__'):
            # If __init__ exists copy it off to prevent recursively calling it
            undecorated__init__ = interface_class.__init__
        else:
            # Otherwise create a noop to simplify things later
            undecorated__init__ = lambda *_, **__: None
        def decorating__init__(slf, *args, **kwargs):
            if 'namespace' in kwargs:
                raise TypeError(
                    '`namespace` is set in the Introspector '
                    'it must not be set again in this service'
                    )
            self._set_introspection_xml(interface_class)
            undecorated__init__(slf, *args, **kwargs)
        interface_class.__init__ = decorating__init__
        return interface_class

    def _set_introspection_xml(self, service):
        xml_doc = E.node(super().__xml__, name=self._namespace)
        service.dbus = etree.tostring(xml_doc, pretty_print=True).decode()


if __name__ == '__main__':
    from .properties import PropertyEmitsChangedSignal
    logging.basicConfig(level=logging.DEBUG)
    introspector = Introspector('com.example.service')

    @introspector
    class ExampleService:

        @introspector.method(response='s')
        def HelloWorld(self):
            return 'Hello!'
        
        @introspector.method(Arg('message', 's'), response='s')
        def Echo(self, message):
            return message

        @introspector.property(type_='b', access='read')
        def Status(self):
            return True

        @introspector.property(type_='i', signal_on=[PropertyEmitsChangedSignal.name])
        def Count(self):
            return 100

        @Count.setter
        def Count(self, value):
            print(value)

    example_service = ExampleService()
    print(example_service.dbus)


    loop = GObject.MainLoop()
    bus = pydbus.SessionBus()
    bus.publish('com.example.service', example_service)
    loop.run()
