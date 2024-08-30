import backtesting as bt


class FixedSize(bt.Sizer):
    '''
    This sizer simply returns a fixed size for any operation.
    Size can be controlled by number of tranches that a system
    wishes to use to scale into trades by specifying the ``tranches``
    parameter.


    Params:
      - ``stake`` (default: ``1``)
      - ``tranches`` (default: ``1``)
    '''

    params = (('stake', 1),
              ('tranches', 1))

    def _getsizing(self, comminfo, cash, data, isbuy):
        if self.p.tranches > 1:
            return abs(int(self.p.stake / self.p.tranches))
        else:
            return self.p.stake

    def setsizing(self, stake):
        if self.p.tranches > 1:
            self.p.stake = abs(int(self.p.stake / self.p.tranches))
        else:
            self.p.stake = stake  


SizerFix = FixedSize


class FixedReverser(bt.Sizer):
    '''This sizer returns the needes fixed size to reverse an open position or
    the fixed size to open one

      - To open a position: return the param ``stake``

      - To reverse a position: return 2 * ``stake``

    Params:
      - ``stake`` (default: ``1``)
    '''
    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.strategy.getposition(data)
        size = self.p.stake * (1 + (position.size != 0))
        return size


class FixedSizeTarget(bt.Sizer):
    '''
    This sizer simply returns a fixed target size, useful when coupled
    with Target Orders and specifically ``cerebro.target_order_size()``.
    Size can be controlled by number of tranches that a system
    wishes to use to scale into trades by specifying the ``tranches``
    parameter.


    Params:
      - ``stake`` (default: ``1``)
      - ``tranches`` (default: ``1``)
    '''

    params = (('stake', 1),
              ('tranches', 1))

    def _getsizing(self, comminfo, cash, data, isbuy):
        if self.p.tranches > 1:
            size = abs(int(self.p.stake / self.p.tranches))
            return min((self.strategy.position.size + size), self.p.stake)
        else:
            return self.p.stake

    def setsizing(self, stake):
        if self.p.tranches > 1:
            size = abs(int(self.p.stake / self.p.tranches))
            self.p.stake = min((self.strategy.position.size + size),
                               self.p.stake)
        else:
            self.p.stake = stake  
