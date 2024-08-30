import backtesting as bt


class PositionsValue(bt.Analyzer):
    '''This analyzer reports the value of the positions of the current set of
    datas

    Params:

      - timeframe (default: ``None``)
        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - headers (default: ``False``)

        Add an initial key to the dictionary holding the results with the names
        of the datas ('Datetime' as key

      - cash (default: ``False``)

        Include the actual cash as an extra position (for the header 'cash'
        will be used as name)

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('headers',  False),
        ('cash', False),
    )

    def start(self):
        if self.p.headers:
            headers = [d._name or 'Data%d' % i
                       for i, d in enumerate(self.datas)]
            self.rets['Datetime'] = headers + ['cash'] * self.p.cash

        tf = min(d._timeframe for d in self.datas)
        self._usedate = tf >= bt.TimeFrame.Days

    def next(self):
        pvals = [self.strategy.broker.get_value([d]) for d in self.datas]
        if self.p.cash:
            pvals.append(self.strategy.broker.get_cash())

        if self._usedate:
            self.rets[self.strategy.datetime.date()] = pvals
        else:
            self.rets[self.strategy.datetime.datetime()] = pvals
