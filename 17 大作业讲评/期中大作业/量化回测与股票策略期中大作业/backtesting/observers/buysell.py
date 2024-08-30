import math

from ..observer import Observer


class BuySell(Observer):
    '''
    This observer keeps track of the individual buy/sell orders (individual
    executions) and will plot them on the chart along the data around the
    execution price level

    Params:
      - ``barplot`` (default: ``False``) Plot buy signals below the minimum and
        sell signals above the maximum.

        If ``False`` it will plot on the average price of executions during a
        bar

      - ``bardist`` (default: ``0.015`` 1.5%) Distance to max/min when
        ``barplot`` is ``True``
    '''
    lines = ('buy', 'sell',)

    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(
        buy=dict(marker='^', markersize=8.0, color='lime',
                 fillstyle='full', ls=''),
        sell=dict(marker='v', markersize=8.0, color='red',
                  fillstyle='full', ls='')
    )

    params = (
        ('barplot', False),  
        ('bardist', 0.015),  
    )

    def next(self):
        buy = list()
        sell = list()

        for order in self._owner._orderspending:
            if order.data is not self.data or not order.executed.size:
                continue

            if order.isbuy():
                buy.append(order.executed.price)
            else:
                sell.append(order.executed.price)

        
        

        
        curbuy = self.lines.buy[0]
        if curbuy != curbuy:  
            curbuy = 0.0
            self.curbuylen = curbuylen = 0
        else:
            curbuylen = self.curbuylen

        buyops = (curbuy + math.fsum(buy))
        buylen = curbuylen + len(buy)

        value = buyops / float(buylen or 'NaN')
        if not self.p.barplot:
            self.lines.buy[0] = value
        elif value == value:  
            pbuy = self.data.low[0] * (1 - self.p.bardist)
            self.lines.buy[0] = pbuy

        
        curbuy = buyops
        self.curbuylen = buylen

        
        cursell = self.lines.sell[0]
        if cursell != cursell:  
            cursell = 0.0
            self.curselllen = curselllen = 0
        else:
            curselllen = self.curselllen

        sellops = (cursell + math.fsum(sell))
        selllen = curselllen + len(sell)

        value = sellops / float(selllen or 'NaN')
        if not self.p.barplot:
            self.lines.sell[0] = value
        elif value == value:  
            psell = self.data.high[0] * (1 + self.p.bardist)
            self.lines.sell[0] = psell

        
        cursell = sellops
        self.curselllen = selllen
