import backtesting as bt
from backtesting.utils.py3 import iteritems
import pandas as pd

from . import TimeReturn, PositionsValue, Transactions, GrossLeverage


# pyfolio的分析模块
class PyFolio(bt.Analyzer):
    """This analyzer uses 4 children analyzers to collect data and transforms it
    in to a data set compatible with ``pyfolio``

    Children Analyzer

      - ``TimeReturn``

        Used to calculate the returns of the global portfolio value

      - ``PositionsValue``

        Used to calculate the value of the positions per data. It sets the
        ``headers`` and ``cash`` parameters to ``True``

      - ``Transactions``

        Used to record each transaction on a data (size, price, value). Sets
        the ``headers`` parameter to ``True``

      - ``GrossLeverage``

        Keeps track of the gross leverage (how much the strategy is invested)

    Params:
      These are passed transparently to the children

      - timeframe (default: ``bt.TimeFrame.Days``)

        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: `1``)

        If ``None`` then the compression of the 1st data of the system will be
        used

    Both ``timeframe`` and ``compression`` are set following the default
    behavior of ``pyfolio`` which is working with *daily* data and upsample it
    to obtaine values like yearly returns.

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    """
    # 参数
    params = (
        ('timeframe', bt.TimeFrame.Days),
        ('compression', 1)
    )

    # 初始化
    def __init__(self):
        dtfcomp = dict(timeframe=self.p.timeframe,
                       compression=self.p.compression)

        self._returns = TimeReturn(**dtfcomp)
        self._positions = PositionsValue(headers=True, cash=True)
        self._transactions = Transactions(headers=True)
        self._gross_lev = GrossLeverage()

    # 停止的时候，获取几个分析结果
    def stop(self):
        super(PyFolio, self).stop()
        self.rets['returns'] = self._returns.get_analysis()
        self.rets['positions'] = self._positions.get_analysis()
        self.rets['transactions'] = self._transactions.get_analysis()
        self.rets['gross_lev'] = self._gross_lev.get_analysis()

    # 对上面四个analyzer的结果进行调整，以便得到pyfolio需要的输入的信息
    def get_pf_items(self):
        """Returns a tuple of 4 elements which can be used for further processing with
          ``pyfolio``

          returns, positions, transactions, gross_leverage

        Because the objects are meant to be used as direct input to ``pyfolio``
        this method makes a local import of ``pandas`` to convert the internal
        *backtrader* results to *pandas DataFrames* which is the expected input
        by, for example, ``pyfolio.create_full_tear_sheet``

        The method will break if ``pandas`` is not installed
        """
        # 处理returns
        cols = ['index', 'return']
        returns = pd.DataFrame.from_records(iteritems(self.rets['returns']),
                                            index=cols[0], columns=cols)
        returns.index = pd.to_datetime(returns.index)
        returns.index = returns.index.tz_localize('UTC')
        rets = returns['return']
        #
        # Positions
        # 处理position
        pss = self.rets['positions']
        # ps = [[k] + v[-2:] for k, v in iteritems(pss)]
        ps = [[k] + v for k, v in iteritems(pss)]
        cols = ps.pop(0)  # headers are in the first entry
        positions = pd.DataFrame.from_records(ps[1:], columns=cols)
        positions.index = pd.to_datetime(positions['Datetime'])
        del positions['Datetime']
        positions.index = positions.index.tz_localize('UTC')

        #
        # Transactions
        # 处理transcations
        txss = self.rets['transactions']
        txs = list()

        for k, v in iteritems(txss):
            for v2 in v:
                txs.append([k] + v2)

        cols = txs.pop(0)  
        transactions = pd.DataFrame.from_records(txs, index=cols[0], columns=cols)
        transactions.index = pd.to_datetime(transactions.index)
        transactions.index = transactions.index.tz_localize('UTC')

        # 处理leverage
        cols = ['index', 'gross_lev']
        gross_lev = pd.DataFrame.from_records(iteritems(self.rets['gross_lev']),
                                              index=cols[0], columns=cols)

        gross_lev.index = pd.to_datetime(gross_lev.index)
        gross_lev.index = gross_lev.index.tz_localize('UTC')
        glev = gross_lev['gross_lev']

        # 返回所有的结果
        return rets, positions, transactions, glev
