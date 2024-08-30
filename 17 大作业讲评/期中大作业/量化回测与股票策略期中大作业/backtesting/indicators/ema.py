from . import MovingAverageBase, ExponentialSmoothing


class ExponentialMovingAverage(MovingAverageBase):
    '''
    A Moving Average that smoothes data exponentially over time.

    It is a subclass of SmoothingMovingAverage.

      - self.smfactor -> 2 / (1 + period)
      - self.smfactor1 -> `1 - self.smfactor`

    Formula:
      - movav = prev * (1.0 - smoothfactor) + newdata * smoothfactor

    See also:
      - http://en.wikipedia.org/wiki/Moving_average
    '''
    alias = ('EMA', 'MovingAverageExponential',)
    lines = ('ema',)

    def __init__(self):
        
        
        self.lines[0] = es = ExponentialSmoothing(
            self.data,
            period=self.p.period,
            alpha=2.0 / (1.0 + self.p.period))

        self.alpha, self.alpha1 = es.alpha, es.alpha1

        super(ExponentialMovingAverage, self).__init__()
