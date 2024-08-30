from .utils.py3 import with_metaclass

from .metabase import MetaParams

# Sizer类,其他的sizer需要继承这个类并且重写_getsizing类
class Sizer(with_metaclass(MetaParams, object)):
    '''
      # strategy 代表在使用sizer的strategy策略，可以通过strategy调用所有的strategy的api
      # broker 代表使用strategy所在的broker，可以用于获取信息进行计算复杂的手数
    '''
    strategy = None
    broker = None

    # 获取下单使用的具体的手数
    def getsizing(self, data, isbuy):
        comminfo = self.broker.getcommissioninfo(data)
        return self._getsizing(comminfo, self.broker.getcash(), data, isbuy)

    def _getsizing(self, comminfo, cash, data, isbuy):
        '''
        # 这个方法在使用的 时候需要被重写，传入四个参数：
        # comminfo  代表佣金的实例，可以用于获取佣金等信息
        # cash      代表当前可以使用的现金
        # data      代表在那个数据上进行交易
        # isbuy     代表在buy操作的时候是True，sell的时候代表是False

        '''
        raise NotImplementedError

    # 设置策略和broker
    def set(self, strategy, broker):
        self.strategy = strategy
        self.broker = broker

# SizerBase类
SizerBase = Sizer
