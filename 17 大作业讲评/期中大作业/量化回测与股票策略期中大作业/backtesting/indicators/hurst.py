from . import PeriodN


__all__ = ['HurstExponent', 'Hurst']


class HurstExponent(PeriodN):
    '''
    References:

      - https://www.quantopian.com/posts/hurst-exponent
      - https://www.quantopian.com/posts/some-code-from-ernie-chans-new-book-implemented-in-python

   Interpretation of the results

      1. Geometric random walk (H=0.5)
      2. Mean-reverting series (H<0.5)
      3. Trending Series (H>0.5)

    Important notes:

      - The default period is ``40``, but experimentation by users has shown
        that it would be advisable to have at least 2000 samples (i.e.: a
        period of at least 2000) to have stable values.

      - The `lag_start` and `lag_end` values will default to be ``2`` and
        ``self.p.period / 2`` unless the parameters are specified.

        Experimentation by users has also shown that values of around ``10``
        and ``500`` produce good results

    The original values (40, 2, self.p.period / 2) are kept for backwards
    compatibility

    '''
    frompackages = (
        ('numpy', ('asarray', 'log10', 'polyfit', 'sqrt', 'std', 'subtract')),
    )

    alias = ('Hurst',)
    lines = ('hurst',)
    params = (
        ('period', 40),  
        ('lag_start', None),  
        ('lag_end', None),  
    )

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self._lag_start]
        plabels += [self._lag_end]
        return plabels

    def __init__(self):
        super(HurstExponent, self).__init__()
        
        self._lag_start = lag_start = self.p.lag_start or 2
        self._lag_end = lag_end = self.p.lag_end or (self.p.period // 2)
        self.lags = asarray(range(lag_start, lag_end))
        self.log10lags = log10(self.lags)

    def next(self):
        
        ts = asarray(self.data.get(size=self.p.period))

        
        tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in self.lags]

        
        poly = polyfit(self.log10lags, log10(tau), 1)

        
        self.lines.hurst[0] = poly[0] * 2.0
