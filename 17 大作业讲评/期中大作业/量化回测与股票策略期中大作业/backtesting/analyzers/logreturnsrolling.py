import collections
import math

import backtesting as bt


__all__ = ['LogReturnsRolling']


class LogReturnsRolling(bt.TimeFrameAnalyzerBase):
    '''This analyzer calculates rolling returns for a given timeframe and
    compression

    Params:

      - ``timeframe`` (default: ``None``)
        If ``None`` the ``timeframe`` of the 1st data in the system will be
        used

        Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
        time constraints

      - ``compression`` (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - ``data`` (default: ``None``)

        Reference asset to track instead of the portfolio value.

        .. note:: this data must have been added to a ``cerebro`` instance with
                  ``addata``, ``resampledata`` or ``replaydata``

      - ``firstopen`` (default: ``True``)

        When tracking the returns of a ``data`` the following is done when
        crossing a timeframe boundary, for example ``Years``:

          - Last ``close`` of previous year is used as the reference price to
            see the return in the current year

        The problem is the 1st calculation, because the data has** no
        previous** closing price. As such and when this parameter is ``True``
        the *opening* price will be used for the 1st calculation.

        This requires the data feed to have an ``open`` price (for ``close``
        the standard [0] notation will be used without reference to a field
        price)

        Else the initial close will be used.

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''

    params = (
        ('data', None),
        ('firstopen', True),
        ('fund', None),
    )

    def start(self):
        super(LogReturnsRolling, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        self._values = collections.deque([float('Nan')] * self.compression,
                                         maxlen=self.compression)

        if self.p.data is None:
            # keep the initial portfolio value if not tracing a data
            if not self._fundmode:
                self._lastvalue = self.strategy.broker.getvalue()
            else:
                self._lastvalue = self.strategy.broker.fundvalue

    def notify_fund(self, cash, value, fundvalue, shares):
        if not self._fundmode:
            self._value = value if self.p.data is None else self.p.data[0]
        else:
            self._value = fundvalue if self.p.data is None else self.p.data[0]

    def _on_dt_over(self):
        # next is called in a new timeframe period
        if self.p.data is None or len(self.p.data) > 1:
            # Not tracking a data feed or data feed has data already
            vst = self._lastvalue  # update value_start to last
        else:
            # The 1st tick has no previous reference, use the opening price
            vst = self.p.data.open[0] if self.p.firstopen else self.p.data[0]

        self._values.append(vst)  # push values backwards (and out)

    def next(self):
        # Calculate the return
        super(LogReturnsRolling, self).next()
        self.rets[self.dtkey] = math.log(self._value / self._values[0])
        self._lastvalue = self._value  # keep last value
