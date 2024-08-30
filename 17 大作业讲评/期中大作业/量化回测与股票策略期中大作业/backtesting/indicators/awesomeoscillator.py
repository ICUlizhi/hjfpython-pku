import backtesting as bt
from . import MovAv


__all__ = ['AwesomeOscillator', 'AwesomeOsc', 'AO']


class AwesomeOscillator(bt.Indicator):
    '''
    Awesome Oscillator (AO) is a momentum indicator reflecting the precise
    changes in the market driving force which helps to identify the trend’s
    strength up to the points of formation and reversal.


    Formula:
     - median price = (high + low) / 2
     - AO = SMA(median price, 5)- SMA(median price, 34)

    See:
      - https://www.metatrader5.com/en/terminal/help/indicators/bw_indicators/awesome
      - https://www.ifcmarkets.com/en/ntx-indicators/awesome-oscillator

    '''
    alias = ('AwesomeOsc', 'AO')
    lines = ('ao',)

    params = (
        ('fast', 5),
        ('slow', 34),
        ('movav', MovAv.SMA),
    )

    plotlines = dict(ao=dict(_method='bar', alpha=0.50, width=1.0))

    def __init__(self):
        median_price = (self.data.high + self.data.low) / 2.0
        sma1 = self.p.movav(median_price, period=self.p.fast)
        sma2 = self.p.movav(median_price, period=self.p.slow)
        self.l.ao = sma1 - sma2

        super(AwesomeOscillator, self).__init__()
