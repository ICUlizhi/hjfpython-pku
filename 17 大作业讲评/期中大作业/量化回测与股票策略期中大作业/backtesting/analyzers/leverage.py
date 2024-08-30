import backtesting as bt


class GrossLeverage(bt.Analyzer):
    '''This analyzer calculates the Gross Leverage of the current strategy
    on a timeframe basis

    Params:

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
        ('fund', None),
    )

    def start(self):
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

    def notify_fund(self, cash, value, fundvalue, shares):
        self._cash = cash
        if not self._fundmode:
            self._value = value
        else:
            self._value = fundvalue

    def next(self):
        # Updates the leverage for "dtkey" (see base class) for each cycle
        # 0.0 if 100% in cash, 1.0 if no short selling and fully invested
        lev = (self._value - self._cash) / self._value
        self.rets[self.data0.datetime.datetime()] = lev
