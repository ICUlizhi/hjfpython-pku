import calendar
import datetime

import backtesting as bt
from .. import Observer, TimeFrame

from backtesting.utils.py3 import MAXINT


class TimeReturn(Observer):
    '''This observer stores the *returns* of the strategy.

    Params:

      - ``timeframe`` (default: ``None``)
        If ``None`` then the complete return over the entire backtested period
        will be reported

        Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
        time constraints

      - ``compression`` (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Remember that at any moment of a ``run`` the current values can be checked
    by looking at the *lines* by name at index ``0``.

    '''
    _stclock = True

    lines = ('timereturn',)
    plotinfo = dict(plot=True, subplot=True)
    plotlines = dict(timereturn=dict(_name='Return'))

    params = (
        ('timeframe', None),
        ('compression', None),
        ('fund', None),
    )

    def _plotlabel(self):
        return [
            
            TimeFrame.getname(self.treturn.timeframe,
                              self.treturn.compression),
            str(self.treturn.compression)
        ]

    def __init__(self):
        self.treturn = self._owner._addanalyzer_slave(bt.analyzers.TimeReturn,
                                                      **self.p._getkwargs())

    def next(self):
        self.lines.timereturn[0] = self.treturn.rets.get(self.treturn.dtkey,
                                                         float('NaN'))
