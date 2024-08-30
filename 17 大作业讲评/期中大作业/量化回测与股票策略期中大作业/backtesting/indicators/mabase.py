from ..utils.py3 import with_metaclass

from . import Indicator


class MovingAverage(object):
    '''MovingAverage (alias MovAv)

    A placeholder to gather all Moving Average Types in a single place.

    Instantiating a SimpleMovingAverage can be achieved as follows::

      sma = MovingAverage.Simple(self.data, period)

    Or using the shorter aliases::

      sma = MovAv.SMA(self.data, period)

    or with the full (forwards and backwards) names:

      sma = MovAv.SimpleMovingAverage(self.data, period)

      sma = MovAv.MovingAverageSimple(self.data, period)

    '''
    _movavs = []

    @classmethod
    def register(cls, regcls):
        if getattr(regcls, '_notregister', False):
            return

        cls._movavs.append(regcls)

        clsname = regcls.__name__
        setattr(cls, clsname, regcls)

        clsalias = ''
        if clsname.endswith('MovingAverage'):
            clsalias = clsname.split('MovingAverage')[0]
        elif clsname.startswith('MovingAverage'):
            clsalias = clsname.split('MovingAverage')[1]

        if clsalias:
            setattr(cls, clsalias, regcls)


class MovAv(MovingAverage):
    pass  


class MetaMovAvBase(Indicator.__class__):
    
    

    def __new__(meta, name, bases, dct):
        
        cls = super(MetaMovAvBase, meta).__new__(meta, name, bases, dct)

        MovingAverage.register(cls)

        
        return cls


class MovingAverageBase(with_metaclass(MetaMovAvBase, Indicator)):
    params = (('period', 30),)
    plotinfo = dict(subplot=False)
