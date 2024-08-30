import matplotlib.dates as mdates
import matplotlib.ticker as mplticker

from ..utils import num2date


class MyVolFormatter(mplticker.Formatter):
    Suffixes = ['', 'K', 'M', 'G', 'T', 'P']

    def __init__(self, volmax):
        self.volmax = volmax
        magnitude = 0
        self.divisor = 1.0
        while abs(volmax / self.divisor) >= 1000:
            magnitude += 1
            self.divisor *= 1000.0

        self.suffix = self.Suffixes[magnitude]

    def __call__(self, y, pos=0):
        '''Return the label for time x at position pos'''

        if y > self.volmax * 1.20:
            return ''

        y = int(y / self.divisor)
        return '%d%s' % (y, self.suffix)


class MyDateFormatter(mplticker.Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
        '''Return the label for time x at position pos'''
        ind = int(round(x))
        if ind >= self.lendates:
            ind = self.lendates - 1

        if ind < 0:
            ind = 0

        return num2date(self.dates[ind]).strftime(self.fmt)


def patch_locator(locator, xdates):
    def _patched_datalim_to_dt(self):
        dmin, dmax = self.axis.get_data_interval()

        
        dmin, dmax = xdates[int(dmin)], xdates[min(int(dmax), len(xdates) - 1)]

        a, b = num2date(dmin, self.tz), num2date(dmax, self.tz)
        return a, b

    def _patched_viewlim_to_dt(self):
        vmin, vmax = self.axis.get_view_interval()

        
        vmin, vmax = xdates[int(vmin)], xdates[min(int(vmax), len(xdates) - 1)]
        a, b = num2date(vmin, self.tz), num2date(vmax, self.tz)
        return a, b

    
    bound_datalim = _patched_datalim_to_dt.__get__(locator, locator.__class__)
    locator.datalim_to_dt = bound_datalim

    
    bound_viewlim = _patched_viewlim_to_dt.__get__(locator, locator.__class__)
    locator.viewlim_to_dt = bound_viewlim


def patch_formatter(formatter, xdates):
    def newcall(self, x, pos=0):
        if False and x < 0:
            raise ValueError('DateFormatter found a value of x=0, which is '
                             'an illegal date.  This usually occurs because '
                             'you have not informed the axis that it is '
                             'plotting dates, e.g., with ax.xaxis_date()')

        x = xdates[int(x)]
        dt = num2date(x, self.tz)
        return self.strftime(dt, self.fmt)

    bound_call = newcall.__get__(formatter, formatter.__class__)
    formatter.__call__ = bound_call


def getlocator(xdates, numticks=5, tz=None):
    span = xdates[-1] - xdates[0]

    locator, formatter = mdates.date_ticker_factory(
        span=span,
        tz=tz,
        numticks=numticks)

    patch_locator(locator, xdates)
    patch_formatter(formatter, xdates)
    return locator, formatter
