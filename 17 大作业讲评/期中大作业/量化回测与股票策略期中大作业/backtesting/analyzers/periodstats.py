import backtesting as bt
from backtesting.utils.py3 import itervalues
from backtesting.mathsupport import average, standarddev
from . import TimeReturn


__all__ = ['PeriodStats']


class PeriodStats(bt.Analyzer):
    '''Calculates basic statistics for given timeframe

    Params:

      - ``timeframe`` (default: ``Years``)
        If ``None`` the ``timeframe`` of the 1st data in the system will be
        used

        Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
        time constraints

      - ``compression`` (default: ``1``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior


    ``get_analysis`` returns a dictionary containing the keys:

      - ``average``
      - ``stddev``
      - ``positive``
      - ``negative``
      - ``nochange``
      - ``best``
      - ``worst``

    If the parameter ``zeroispos`` is set to ``True``, periods with no change
    will be counted as positive
    '''

    params = (
        ('timeframe', bt.TimeFrame.Years),
        ('compression', 1),
        ('zeroispos', False),
        ('fund', None),
    )

    def __init__(self):
        self._tr = TimeReturn(timeframe=self.p.timeframe,
                              compression=self.p.compression, fund=self.p.fund)

    def stop(self):
        trets = self._tr.get_analysis()  # dict key = date, value = ret
        pos = nul = neg = 0
        trets = list(itervalues(trets))
        for tret in trets:
            if tret > 0.0:
                pos += 1
            elif tret < 0.0:
                neg += 1
            else:
                if self.p.zeroispos:
                    pos += tret == 0.0
                else:
                    nul += tret == 0.0

        self.rets['average'] = avg = average(trets)
        self.rets['stddev'] = standarddev(trets, avg)

        self.rets['positive'] = pos
        self.rets['negative'] = neg
        self.rets['nochange'] = nul

        self.rets['best'] = max(trets)
        self.rets['worst'] = min(trets)
