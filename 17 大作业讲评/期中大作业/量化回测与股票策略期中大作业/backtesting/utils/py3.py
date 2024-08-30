import itertools
import sys

try:
    import winreg
except ImportError:
    winreg = None

MAXINT = sys.maxsize
MININT = -sys.maxsize - 1

MAXFLOAT = sys.float_info.max
MINFLOAT = sys.float_info.min

string_types = str,
integer_types = int,

filter = filter
map = map
range = range
zip = zip
long = int

def cmp(a, b): return (a > b) - (a < b)

def bytes(x): return x.encode('utf-8')

def bstr(x): return str(x)

from io import StringIO

from urllib.request import (urlopen, ProxyHandler, build_opener,
                            install_opener)
from urllib.parse import quote as urlquote

def iterkeys(d): return iter(d.keys())

def itervalues(d): return iter(d.values())

def iteritems(d): return iter(d.items())

def keys(d): return list(d.keys())

def values(d): return list(d.values())

def items(d): return list(d.items())

import queue as queue



def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""

    class metaclass(meta):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, str('temporary_class'), (), {})
