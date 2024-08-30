from math import fsum

from . import BaseApplyN


__all__ = ['PercentRank', 'PctRank']


class PercentRank(BaseApplyN):
    '''
    Measures the percent rank of the current value with respect to that of
    period bars ago
    '''
    alias = ('PctRank',)
    lines = ('pctrank',)
    params = (
        ('period', 50),
        ('func', lambda d: fsum(x < d[-1] for x in d) / len(d)),
    )
