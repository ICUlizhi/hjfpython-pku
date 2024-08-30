import collections

import backtesting as bt
from backtesting import Order, Position


class Transactions(bt.Analyzer):
    '''This analyzer reports the transactions occurred with each an every data in
    the system

    It looks at the order execution bits to create a ``Position`` starting from
    0 during each ``next`` cycle.

    The result is used during next to record the transactions

    Params:

      - headers (default: ``True``)

        Add an initial key to the dictionary holding the results with the names
        of the datas

        This analyzer was modeled to facilitate the integration with
        ``pyfolio`` and the header names are taken from the samples used for
        it::

          'date', 'amount', 'price', 'sid', 'symbol', 'value'

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('headers', False),
        ('_pfheaders', ('date', 'amount', 'price', 'sid', 'symbol', 'value')),
    )

    def start(self):
        super(Transactions, self).start()
        if self.p.headers:
            self.rets[self.p._pfheaders[0]] = [list(self.p._pfheaders[1:])]

        self._positions = collections.defaultdict(Position)
        self._idnames = list(enumerate(self.strategy.getdatanames()))

    def notify_order(self, order):
        # An order could have several partial executions per cycle (unlikely
        # but possible) and therefore: collect each new execution notification
        # and let the work for next

        # We use a fresh Position object for each round to get summary of what
        # the execution bits have done in that round
        if order.status not in [Order.Partial, Order.Completed]:
            return  # It's not an execution

        pos = self._positions[order.data._name]
        for exbit in order.executed.iterpending():
            if exbit is None:
                break  # end of pending reached

            pos.update(exbit.size, exbit.price)

    def next(self):
        # super(Transactions, self).next()  # let dtkey update
        entries = []
        for i, dname in self._idnames:
            pos = self._positions.get(dname, None)
            if pos is not None:
                size, price = pos.size, pos.price
                if size:
                    entries.append([size, price, i, dname, -size * price])

        if entries:
            self.rets[self.strategy.datetime.datetime()] = entries

        self._positions.clear()
