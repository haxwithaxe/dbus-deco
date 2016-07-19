
__author__ = 'haxwithaxe <spam@haxwithaxe.net>'
__copyright__ = 'Copyright haxwithaxe 2016'
__license__ = 'GPLv3'


def extrapolate_service_path(service_name):
    """Take a guess at the service path by replacing all '.' with '/' and prepending a '/'."""
    return '/'+service_name.replace('.', '/')


def fix_class_name(cls, name):
    """Adjust cls.__name__ and cls.__qualname__ to use name"""
    cls.__name__ = name
    qualname = cls.__qualname__.split('.')
    qualname.pop()
    qualname.append(name)
    cls.__qualname__ = '.'.join(qualname)
