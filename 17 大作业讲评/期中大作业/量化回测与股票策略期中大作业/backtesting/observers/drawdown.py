import backtesting as bt
from .. import Observer


class DrawDown(Observer):
    '''This observer keeps track of the current drawdown level (plotted) and
    the maxdrawdown (not plotted) levels

    Params:

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    '''
    _stclock = True

    params = (
        ('fund', None),
    )

    lines = ('drawdown', 'maxdrawdown',)

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(maxdrawdown=dict(_plotskip=True,))

    def __init__(self):
        kwargs = self.p._getkwargs()
        self._dd = self._owner._addanalyzer_slave(bt.analyzers.DrawDown,
                                                  **kwargs)

    def next(self):
        self.lines.drawdown[0] = self._dd.rets.drawdown  
        self.lines.maxdrawdown[0] = self._dd.rets.max.drawdown  


class DrawDownLength(Observer):
    '''This observer keeps track of the current drawdown length (plotted) and
    the drawdown max length (not plotted)

    Params: None
    '''
    _stclock = True

    lines = ('len', 'maxlen',)

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(maxlength=dict(_plotskip=True,))

    def __init__(self):
        self._dd = self._owner._addanalyzer_slave(bt.analyzers.DrawDown)

    def next(self):
        self.lines.len[0] = self._dd.rets.len  
        self.lines.maxlen[0] = self._dd.rets.max.len  


class DrawDown_Old(Observer):
    '''This observer keeps track of the current drawdown level (plotted) and
    the maxdrawdown (not plotted) levels

    Params: None
    '''
    _stclock = True

    lines = ('drawdown', 'maxdrawdown',)

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(maxdrawdown=dict(_plotskip='True',))

    def __init__(self):
        super(DrawDown_Old, self).__init__()

        self.maxdd = 0.0
        self.peak = float('-inf')

    def next(self):
        value = self._owner.broker.getvalue()

        
        if value > self.peak:
            self.peak = value

        
        self.lines.drawdown[0] = dd = 100.0 * (self.peak - value) / self.peak

        
        self.lines.maxdrawdown[0] = self.maxdd = max(self.maxdd, dd)
