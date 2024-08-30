from . import Indicator, CmpEx


class PivotPoint(Indicator):
    '''
    Defines a level of significance by taking into account the average of price
    bar components of the past period of a larger timeframe. For example when
    operating with days, the values are taking from the already "past" month
    fixed prices.

    Example of using this indicator:

      data = btfeeds.ADataFeed(dataname=x, timeframe=bt.TimeFrame.Days)
      cerebro.adddata(data)
      cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    In the ``__init__`` method of the strategy:

      pivotindicator = btind.PivotPoiont(self.data1)  

    The indicator will try to automatically plo to the non-resampled data. To
    disable this behavior use the following during construction:

      - _autoplot=False

    Note:

      The example shows *days* and *months*, but any combination of timeframes
      can be used. See the literature for recommended combinations

    Formula:
      - pivot = (h + l + c) / 3  
      - support1 = 2.0 * pivot - high
      - support2 = pivot - (high - low)
      - resistance1 = 2.0 * pivot - low
      - resistance2 = pivot + (high - low)

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:pivot_points
      - https://en.wikipedia.org/wiki/Pivot_point_(technical_analysis)
    '''
    lines = ('p', 's1', 's2', 'r1', 'r2',)
    plotinfo = dict(subplot=False)

    params = (
        ('open', False),  
        ('close', False),  
        ('_autoplot', True),  
    )

    def _plotinit(self):
        
        if self.p._autoplot:
            if hasattr(self.data, 'data'):
                self.plotinfo.plotmaster = self.data.data

    def __init__(self):
        o = self.data.open
        h = self.data.high  
        l = self.data.low  
        c = self.data.close  

        if self.p.close:
            self.lines.p = p = (h + l + 2.0 * c) / 4.0
        elif self.p.open:
            self.lines.p = p = (h + l + c + o) / 4.0
        else:
            self.lines.p = p = (h + l + c) / 3.0

        self.lines.s1 = 2.0 * p - h
        self.lines.r1 = 2.0 * p - l

        self.lines.s2 = p - (h - l)
        self.lines.r2 = p + (h - l)

        super(PivotPoint, self).__init__()  

        if self.p._autoplot:
            self.plotinfo.plot = False  
            self()  


class FibonacciPivotPoint(Indicator):
    '''
    Defines a level of significance by taking into account the average of price
    bar components of the past period of a larger timeframe. For example when
    operating with days, the values are taking from the already "past" month
    fixed prices.

    Fibonacci levels (configurable) are used to define the support/resistance levels

    Example of using this indicator:

      data = btfeeds.ADataFeed(dataname=x, timeframe=bt.TimeFrame.Days)
      cerebro.adddata(data)
      cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    In the ``__init__`` method of the strategy:

      pivotindicator = btind.FibonacciPivotPoiont(self.data1)  

    The indicator will try to automatically plo to the non-resampled data. To
    disable this behavior use the following during construction:

      - _autoplot=False

    Note:

      The example shows *days* and *months*, but any combination of timeframes
      can be used. See the literature for recommended combinations

    Formula:
      - pivot = (h + l + c) / 3  
      - support1 = p - level1 * (high - low)  
      - support2 = p - level2 * (high - low)  
      - support3 = p - level3 * (high - low)  
      - resistance1 = p + level1 * (high - low)  
      - resistance2 = p + level2 * (high - low)  
      - resistance3 = p + level3 * (high - low)  

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:pivot_points
    '''
    lines = ('p', 's1', 's2', 's3', 'r1', 'r2', 'r3')
    plotinfo = dict(subplot=False)
    params = (
        ('open', False),  
        ('close', False),  
        ('_autoplot', True),  
        ('level1', 0.382),
        ('level2', 0.618),
        ('level3', 1.0),
    )

    def _plotinit(self):
        
        if self.p._autoplot:
            if hasattr(self.data, 'data'):
                self.plotinfo.plotmaster = self.data.data

    def __init__(self):
        o = self.data.open
        h = self.data.high  
        l = self.data.low  
        c = self.data.close  

        if self.p.close:
            self.lines.p = p = (h + l + 2.0 * c) / 4.0
        elif self.p.open:
            self.lines.p = p = (h + l + c + o) / 4.0
        else:
            self.lines.p = p = (h + l + c) / 3.0

        self.lines.s1 = p - self.p.level1 * (h - l)
        self.lines.s2 = p - self.p.level2 * (h - l)
        self.lines.s3 = p - self.p.level3 * (h - l)

        self.lines.r1 = p + self.p.level1 * (h - l)
        self.lines.r2 = p + self.p.level2 * (h - l)
        self.lines.r3 = p + self.p.level3 * (h - l)

        super(FibonacciPivotPoint, self).__init__()

        if self.p._autoplot:
            self.plotinfo.plot = False  
            self()  


class DemarkPivotPoint(Indicator):
    '''
    Defines a level of significance by taking into account the average of price
    bar components of the past period of a larger timeframe. For example when
    operating with days, the values are taking from the already "past" month
    fixed prices.

    Example of using this indicator:

      data = btfeeds.ADataFeed(dataname=x, timeframe=bt.TimeFrame.Days)
      cerebro.adddata(data)
      cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    In the ``__init__`` method of the strategy:

      pivotindicator = btind.DemarkPivotPoiont(self.data1)  

    The indicator will try to automatically plo to the non-resampled data. To
    disable this behavior use the following during construction:

      - _autoplot=False

    Note:

      The example shows *days* and *months*, but any combination of timeframes
      can be used. See the literature for recommended combinations

    Formula:
      - if close < open x = high + (2 x low) + close

      - if close > open x = (2 x high) + low + close

      - if Close == open x = high + low + (2 x close)

      - p = x / 4

      - support1 = x / 2 - high
      - resistance1 = x / 2 - low

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:pivot_points
    '''
    lines = ('p', 's1', 'r1',)
    plotinfo = dict(subplot=False)
    params = (
        ('open', False),  
        ('close', False),  
        ('_autoplot', True),  
        ('level1', 0.382),
        ('level2', 0.618),
        ('level3', 1.0),
    )

    def _plotinit(self):
        
        if self.p._autoplot:
            if hasattr(self.data, 'data'):
                self.plotinfo.plotmaster = self.data.data

    def __init__(self):
        x1 = self.data.high + 2.0 * self.data.low + self.data.close
        x2 = 2.0 * self.data.high + self.data.low + self.data.close
        x3 = self.data.high + self.data.low + 2.0 * self.data.close

        x = CmpEx(self.data.close, self.data.open, x1, x2, x3)
        self.lines.p = x / 4.0

        self.lines.s1 = x / 2.0 - self.data.high
        self.lines.r1 = x / 2.0 - self.data.low

        super(DemarkPivotPoint, self).__init__()

        if self.p._autoplot:
            self.plotinfo.plot = False  
            self()  
