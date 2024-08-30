from backtesting.utils.py3 import MAXINT, with_metaclass

from backtesting.metabase import MetaParams


# 固定大小过滤，订单执行的时候只能成交当前成交量，需要下单量和size中最小的一个，如果size是None的话，忽略size
class FixedSize(with_metaclass(MetaParams, object)):
    '''
    返回使用柱状图中的*百分比*作为限制条件的给定订单的执行大小。

    该百分比由参数``perc``设置。

    参数:

      - ``size``（默认值：``None``）：要执行的最大大小。如果实际执行时的柱状图体积小于此大小，则体积本身也是一个限制条件。

        如果此参数的值为False，则将使用整个柱状图的体积来匹配订单。
    '''
    params = (('size', None),)

    def __call__(self, order, price, ago):
        size = self.p.size or MAXINT
        return min((order.data.volume[ago], abs(order.executed.remsize), size))


# 固定百分比，用当前成交量的一定的百分比和需要下单的量对比，选择最小的进行交易
class FixedBarPerc(with_metaclass(MetaParams, object)):
    '''
    返回使用柱状图体积的*百分比*来执行给定订单的执行大小。

    该百分比由参数``perc``设置。

    参数：

      - ``perc``（默认值：``100.0``）（有效值：``0.0 - 100.0``）

        用于执行订单的柱状图体积的百分比。
    '''
    params = (('perc', 100.0),)

    def __call__(self, order, price, ago):
        
        maxsize = (order.data.volume[ago] * self.p.perc) // 100
        
        return min(maxsize, abs(order.executed.remsize))


class BarPointPerc(with_metaclass(MetaParams, object)):
    '''
    返回给定订单的执行大小。体积将在*high*-*low*范围内均匀分布，使用``minmov``进行划分。

    从给定价格的分配体积中，将使用``perc``百分比。

    参数：

      - ``minmov``（默认值：``0.01``）

        最小价格变动。用于将*high*-*low*范围划分为可能价格之间的比例分配体积。

      - ``perc``（默认值：``100.0``）（有效值：``0.0 - 100.0``）

        分配给订单执行价格的体积的百分比，用于匹配。
    '''
    params = (
        ('minmov', None),
        ('perc', 100.0),
    )

    def __call__(self, order, price, ago):
        data = order.data
        minmov = self.p.minmov

        parts = 1
        if minmov:
            
            parts = (data.high[ago] - data.low[ago] + minmov) // minmov

        alloc_vol = ((data.volume[ago] / parts) * self.p.perc) // 100.0

        
        return min(alloc_vol, abs(order.executed.remsize))
