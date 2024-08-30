import backtesting as bt

__all__ = ['PercentSizer', 'AllInSizer', 'PercentSizerInt', 'AllInSizerInt']


class PercentSizer(bt.Sizer):
    '''This sizer return percents of available cash

    Params:
      - ``percents`` (default: ``20``)
    '''

    params = (
        ('percents', 20),
        ('retint', False),  
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        else:
            size = position.size

        if self.p.retint:
            size = int(size)

        return size


class AllInSizer(PercentSizer):
    '''This sizer return all available cash of broker

     Params:
       - ``percents`` (default: ``100``)
     '''
    params = (
        ('percents', 100),
    )


class PercentSizerInt(PercentSizer):
    '''This sizer return percents of available cash in form of size truncated
    to an int

    Params:
      - ``percents`` (default: ``20``)
    '''

    params = (
        ('retint', True),  
    )


class AllInSizerInt(PercentSizerInt):
    '''This sizer return all available cash of broker with the
    size truncated to an int

     Params:
       - ``percents`` (default: ``100``)
     '''
    params = (
        ('percents', 100),
    )
