import backtesting as bt
from backtesting.indicators import SumN, TrueLow, TrueRange


class UltimateOscillator(bt.Indicator):
    '''
    Formula:
      
      BP = Close - Minimum(Low or Prior Close)

      
      TR = Maximum(High or Prior Close)  -  Minimum(Low or Prior Close)

      Average7 = (7-period BP Sum) / (7-period TR Sum)
      Average14 = (14-period BP Sum) / (14-period TR Sum)
      Average28 = (28-period BP Sum) / (28-period TR Sum)

      UO = 100 x [(4 x Average7)+(2 x Average14)+Average28]/(4+2+1)

    See:

      - https://en.wikipedia.org/wiki/Ultimate_oscillator
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:ultimate_oscillator
    '''
    lines = ('uo',)

    params = (
        ('p1', 7),
        ('p2', 14),
        ('p3', 28),
        ('upperband', 70.0),
        ('lowerband', 30.0),
    )

    def _plotinit(self):
        baseticks = [10.0, 50.0, 90.0]
        hlines = [self.p.upperband, self.p.lowerband]

        
        self.plotinfo.plotyhlines = hlines
        
        self.plotinfo.plotyticks = baseticks + hlines

    def __init__(self):
        bp = self.data.close - TrueLow(self.data)
        tr = TrueRange(self.data)

        av7 = SumN(bp, period=self.p.p1) / SumN(tr, period=self.p.p1)
        av14 = SumN(bp, period=self.p.p2) / SumN(tr, period=self.p.p2)
        av28 = SumN(bp, period=self.p.p3) / SumN(tr, period=self.p.p3)

        
        factor = 100.0 / (4.0 + 2.0 + 1.0)
        uo = (4.0 * factor) * av7 + (2.0 * factor) * av14 + factor * av28
        self.lines.uo = uo

        super(UltimateOscillator, self).__init__()
