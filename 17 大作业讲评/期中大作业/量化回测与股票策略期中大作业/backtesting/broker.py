from backtesting.comminfo import CommInfoBase
from backtesting.metabase import MetaParams
from backtesting.utils.py3 import with_metaclass

from . import fillers as fillers
from . import fillers as filler

# broker元类，使得get_cash与getcash,get_value与getvalue方法相同
class MetaBroker(MetaParams):
    def __init__(cls, name, bases, dct):
        super(MetaBroker, cls).__init__(name, bases, dct)
        translations = {
            'get_cash': 'getcash',
            'get_value': 'getvalue',
        }

        for attr, trans in translations.items():
            if not hasattr(cls, attr):
                setattr(cls, name, getattr(cls, trans))

# broker基类
class BrokerBase(with_metaclass(MetaBroker, object)):
    # 参数
    params = (
        ('commission', CommInfoBase(percabs=True)),
    )

    # 初始化
    def __init__(self):
        self.comminfo = dict()
        self.init()

    # 这个init用一个None做key,commission做value
    def init(self):
        if None not in self.comminfo:
            self.comminfo = dict({None: self.p.commission})

    def start(self):
        self.init()

    def stop(self):
        pass

    # 增加历史order
    def add_order_history(self, orders, notify=False):
        raise NotImplementedError

    # 设置历史fund
    def set_fund_history(self, fund):
        raise NotImplementedError

    # 获取佣金信息，如果data._name在佣金信息字典中，获取相应的值，否则用默认的self.p.commission
    def getcommissioninfo(self, data):
        if data._name in self.comminfo:
            return self.comminfo[data._name]

        return self.comminfo[None]

    # 设置佣金
    def setcommission(self,
                      commission=0.0, margin=None, mult=1.0,
                      commtype=None, percabs=True, stocklike=False,
                      interest=0.0, interest_long=False, leverage=1.0,
                      automargin=False,
                      name=None):

        comm = CommInfoBase(commission=commission, margin=margin, mult=mult,
                            commtype=commtype, stocklike=stocklike,
                            percabs=percabs,
                            interest=interest, interest_long=interest_long,
                            leverage=leverage, automargin=automargin)
        self.comminfo[name] = comm

    # 增加佣金信息
    def addcommissioninfo(self, comminfo, name=None):
        self.comminfo[name] = comminfo

    # 获取现金
    def getcash(self):
        raise NotImplementedError

    # 获取市值
    def getvalue(self, datas=None):
        raise NotImplementedError

    # 获取基金份额
    def get_fundshares(self):
        return 1.0  

    fundshares = property(get_fundshares)

    # 获取基金市值
    def get_fundvalue(self):
        return self.getvalue()

    fundvalue = property(get_fundvalue)

    # 设置基金模式
    def set_fundmode(self, fundmode, fundstartval=None):
        pass

    # 获取基金模式
    def get_fundmode(self):
        return False

    fundmode = property(get_fundmode, set_fundmode)

    # 获取持仓
    def getposition(self, data):
        raise NotImplementedError

    def submit(self, order):
        raise NotImplementedError

    def cancel(self, order):
        raise NotImplementedError

    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            **kwargs):

        raise NotImplementedError

    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             **kwargs):

        raise NotImplementedError

    def next(self):
        pass

