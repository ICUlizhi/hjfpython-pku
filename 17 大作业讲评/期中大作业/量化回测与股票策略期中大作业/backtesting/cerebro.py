import datetime
import collections
import itertools
import multiprocessing

try:  
    collectionsAbc = collections.abc  
except AttributeError:  
    collectionsAbc = collections 

import backtesting as bt
from .utils.py3 import (map, range, zip, with_metaclass, string_types,
                        integer_types)

from . import linebuffer
from . import indicator
from .brokers import BackBroker
from .metabase import MetaParams
from . import observers
from .utils import OrderedDict, tzparse, num2date, date2num
from .strategy import Strategy, SignalStrategy
from .tradingcal import (TradingCalendarBase, TradingCalendar,
                         PandasMarketCalendar)
from .timer import Timer



class OptReturn(object):
    def __init__(self, params, **kwargs):
        self.p = self.params = params
        for k, v in kwargs.items():
            setattr(self, k, v)


class Cerebro(with_metaclass(MetaParams, object)):
    '''参数:

      - ``preload`` (default: ``True``)

        # preload这个参数默认的是True，就意味着，在回测的时候，默认是先把数据加载之后传给cerebro，在内存中调用，
        # 这个步骤导致的结果就是，加载数据会浪费一部分时间，但是，在回测的时候，速度会快一些，总体上的速度还是有所提高的
        # 所以，建议这个值，使用默认值。

      - ``runonce`` (default: ``True``)

         # 如果runonce设置为True，在计算指标的时候，将会按照向量的方式进行.策略和observers将会按照事件驱动的模式进行

      - ``live`` (default: ``False``)

        # 默认情况是False，意味着，如果我们没有给数据传入"islive"这个方法，默认的就是回测了。
        # 如果把live设置成True了，那么，默认就会不使用preload 和 runonce,这样，一般回测速度就会变慢。

      - ``maxcpus`` (default: None -> all available cores)

        # 优化参数的时候使用的参数，我一般不用这个优化功能，使用的我自己写的多进程回测的模式，优化参数这个地方有bug，有的策略正常，有的策略出错
        # 不建议使用，如果要使用的时候，建议把maxcpus设置成自己电脑的cpu数目减去一，要不然，可能容易死机。

      - ``stdstats`` (default: ``True``)

         # 控制是否会加载observer的参数，默认是True，加载Broker的Cash和Value，Trades and BuySell
        # 我一般默认的都是True,画图的时候用的，我其实可以取消，因为不怎么用cerebro.plot()画出来图形来观察买卖点

      - ``oldbuysell`` (default: ``False``)

        # 如果stdstats设置成True了，如果``oldbuysell``是默认值False，画图的时候，买卖点的位置就会画在K线的
        # 最高点和最低点之外，避免画到K线上

        # 如果stdstats设置成True了，如果``oldbuysell``是True,就会把买卖信号画在成交时候的平均价的地方，会在K线上
        # 比较难辨认。

      - ``oldtrades`` (default: ``False``)

        # 也和画图相关，oldtrades是True的时候，同一方向的交易没有区别，oldtrades是False的时候,
        # 不同的交易使用不同的标记


      - ``exactbars`` (default: ``False``)


        # 储存多少个K线的数据在记忆中

        # 当exactbars的值是True或者是1的时候，只保存满足最小需求的K线的数据，这会取消preload,runonce,plotting

        # 当exactbars的值是-1的时候，数据、指标、运算结果会保存下来，但是指标运算内的中间变量不会保存，这个会取消掉runonce

        # 当exactbars的值是-2的时候，数据、指标、运算结果会保存下来，但是指标内的，指标间的变量，如果没有使用self进行保存，就会消失
        # 可以验证下，-2的结果是否是对的

      - ``objcache`` (default: ``False``)

        # 缓存，如果设置成True了，在指标计算的过程中，如果上面已经计算过了，形成了一个line，
        # 下面要用到指标是同样名字的,就不再计算，而是使用上面缓存中的指标

      - ``writer`` (default: ``False``)
      
         # writer 如果设置成True，输出的信息将会保存到一个默认的文件中

      - ``tradehistory`` (default: ``False``)
      
        # 如果tradehistory设置成了True，这将会激活这样一个功能，在所有策略中，每次交易的信息将会被log
        # 这个也可以在每个策略层面上，使用set_tradehistory来实现。

      - ``optdatas`` (default: ``True``)

        # optdatas设置成True，如果preload和runonce也是True的话，数据的预加载将会只进行一次，在
        # 优化参数的时候，可以节省很多的时间


      - ``optreturn`` (default: ``True``)

        # optreturn,设置成True之后，在优化参数的时候，返回的结果中，只包含参数和analyzers,为了提高速度，
        # 舍弃了数据，指标，observers,这可以提高优化的速度。

      - ``oldsync`` (default: ``False``)

        # 当这个参数设置成False的时候，可以允许数据有不同的长度。如果想要返回旧版本那种，
        # 用data0作为主数据的方式，就可以把这个参数设置成True

      - ``tz`` (default: ``None``)

        # 给策略添加时区
        # 如果忽略的话，tz就是None，就默认使用的是UTC时区
        # 如果是pytz的实例，是一个时区的话，就会把UTC时区转变为选定的新的时区
        # 如果是一个字符串，将会尝试转化为一个pytz实例
        # 如果是一个整数，将会使用某个数据的时区作为时区，如0代表第一个加载进去的数据的时区

      - ``cheat_on_open`` (default: ``False``)

        # 为了方便使用开盘价计算手数设计的，默认是false，我们下单的时候不知道下个bar的open的开盘价，
        # 如果要下特定金额的话，只能用收盘价替代，如果下个交易日开盘之后高开或者低开，成交的金额可能离
        # 我们的目标金额很大。
        # 如果设置成True的话，我们就可以实现这个功能。在每次next之后，在next_open中进行下单，在next_open的时候
        # 还没有到next,系统还没有机会执行订单，指标还未能够重新计算，但是我们已经可以获得下个bar的开盘价了，并且可以
        # 更加精确的计算相应的手数了。

      - ``broker_coo`` (default: ``True``)

        # 这个参数是和上个参数cheat_on_open一块使用的

      - ``quicknotify`` (default: ``False``)

        # quicknotify，控制broker发送通知的时间，如果设置成False，那么，只有在next的时候才会发送
        # 设置成True的时候，产生就会立刻发送。

    '''

    params = (
        ('preload', True),
        ('runonce', True),
        ('maxcpus', None),
        ('stdstats', True),
        ('oldbuysell', False),
        ('oldtrades', False),
        ('lookahead', 0),
        ('exactbars', False),
        ('optdatas', True),
        ('optreturn', True),
        ('objcache', False),
        ('live', False),
        ('writer', False),
        ('tradehistory', False),
        ('oldsync', False),
        ('tz', None),
        ('cheat_on_open', False),
        ('broker_coo', True),
        ('quicknotify', False),
    )

    # 初始化
    def __init__(self):
        # 是否是实盘，初始化的时候，默认不是实盘
        self._dolive = False
        # 是否replay,初始化的时候，默认不replay
        self._doreplay = False
        # 是否优化，初始化的时候，默认不优化
        self._dooptimize = False
        self.stores = list()
        self.feeds = list()
        self.datas = list()
        # 默认有序字典，根据名字保存数据
        self.datasbyname = collections.OrderedDict()
        self.strats = list()
        self.optcbs = list()  
        self.observers = list()
        self.analyzers = list()
        self.indicators = list()
        self.sizers = dict()
        self.writers = list()
        self.storecbs = list()
        self.datacbs = list()
        self.signals = list()
        self._signal_strat = (None, None, None)
        # 是否允许在有信号没有成交的时候继续执行新的信号，默认不允许
        self._signal_concurrent = False
        # 是否允许在有持仓的时候，继续执行信号，默认不允许
        self._signal_accumulate = False

        # data的标示号，dataid
        self._dataid = itertools.count(1)

        # 使用哪一个broker
        self._broker = BackBroker()
        self._broker.cerebro = self

        self._tradingcal = None 

        self._pretimers = list()
        self._ohistory = list()
        self._fhistory = None

    # 这个函数会把可迭代对象中的每个元素变成都是可迭代的
    @staticmethod
    def iterize(iterable):
        niterable = list()
        for elem in iterable:
            if isinstance(elem, string_types):
                elem = (elem,)
            elif not isinstance(elem, collectionsAbc.Iterable):  
                elem = (elem,)

            niterable.append(elem)

        return niterable

    def set_fund_history(self, fund):
        self._fhistory = fund

    # 设置fund历史，其中fund是一个可迭代对象，每个元素包含三个元素，时间，每份价值，净资产价值
    def add_order_history(self, orders, notify=True):
        '''
            增加order历史，orders是一个可迭代对象，每个元素是包含时间、大小、价格三个变量，还可以额外加入data变量
            data可能是第一个数据，也可能是一个整数，代表在datas中的index,也可能是一个字符串，代表添加数据的名字
            notify如果设置的是True的话，cerebro中添加的第一个策略将会通知订单信息
        '''
        self._ohistory.append((orders, notify))

    # 定时器信息通知
    def notify_timer(self, timer, when, *args, **kwargs):
        pass

    # 添加定时器
    def _add_timer(self, owner, when,
                   offset=datetime.timedelta(), repeat=datetime.timedelta(),
                   weekdays=[], weekcarry=False,
                   monthdays=[], monthcarry=True,
                   allow=None,
                   tzdata=None, strats=False, cheat=False,
                   *args, **kwargs):
   

        timer = Timer(
            tid=len(self._pretimers),
            owner=owner, strats=strats,
            when=when, offset=offset, repeat=repeat,
            weekdays=weekdays, weekcarry=weekcarry,
            monthdays=monthdays, monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata, cheat=cheat,
            *args, **kwargs
        )

        self._pretimers.append(timer)
        return timer

    def add_timer(self, when,
                  offset=datetime.timedelta(), repeat=datetime.timedelta(),
                  weekdays=[], weekcarry=False,
                  monthdays=[], monthcarry=True,
                  allow=None,
                  tzdata=None, strats=False, cheat=False,
                  *args, **kwargs):
        '''
        计划一个定时器以调用notify_timer函数
        参数:
            when: 可以是以下之一：
                datetime.time 实例（见下面的tzdata）
                bt.timer.SESSION_START 表示会话开始
                bt.timer.SESSION_END 表示会话结束
                
            offset 必须是 datetime.timedelta 实例
                用于偏移when的值。在与SESSION_START和SESSION_END结合使用时有意义，用于表示会话开始后15分钟后调用定时器等情况。
                
            repeat 必须是 datetime.timedelta 实例
                指示在第一次调用后，是否在同一会话内按照预定的repeat时间间隔调度进一步调用
                一旦定时器超过会话结束时间，它将被重置为when的原始值
                
            weekdays: 一个排序的可迭代对象，其中的整数表示实际可以调用定时器的星期几（ISO代码，星期一为1，星期日为7）
                如果未指定，则定时器将在所有日期上都有效
                
            weekcarry（默认值：False）。如果为True，并且未观察到星期几（例如交易假日），则定时器将在下一天执行（即使是新的一周）
            
            monthdays: 一个排序的可迭代对象，其中的整数表示要执行定时器的月份日期。例如，每月的第15天
                如果未指定，则定时器将在所有日期上都有效
                
            monthcarry（默认值：True）。如果未观察到日期（周末、交易假日），则定时器将在下一个可用日期执行。
            
            allow（默认值：None）。一个回调函数，接收一个datetime.date实例，并返回True如果日期允许用于定时器，否则返回False
            
            tzdata 可以是 None（默认值），一个pytz实例或一个data feed实例。
            
            None: when按字面值解释（即使它不是），将其视为UTC处理。
            
            pytz 实例: when将被解释为指定时区实例的本地时间。
            
            data feed 实例: when将被解释为指定数据源实例的tz参数指定的本地时间。
            
            注意：如果when是SESSION_START或SESSION_END且tzdata为None，系统中的第一个数据源（即self.data0）将用作查找会话时间的参考
            
            strats（默认值：False）还调用策略的notify_timer函数
            
            cheat（默认值为False）如果为True，定时器将在经纪人有机会评估订单之前被调用。这为例如在会话开始前根据开盘价发出订单的机会。
            
            *args: 任何额外的参数将传递给notify_timer
            
            **kwargs: 任何额外的关键字参数将传递给notify_timer
        返回值:
            创建的定时器

        '''
        return self._add_timer(
            owner=self, when=when, offset=offset, repeat=repeat,
            weekdays=weekdays, weekcarry=weekcarry,
            monthdays=monthdays, monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata, strats=strats, cheat=cheat,
            *args, **kwargs)
        
    # tz的参数和add_timer中比较类似
    def addtz(self, tz):
        self.p.tz = tz

    # 增加日历，具体参数可以参考
    # cal可以是字符串，TradingCalendar的实例，pandas_market_calendars的实例，或者TradingCalendar的子类
    def addcalendar(self, cal):

        # 如果是字符串或者具有valid_days属性，使用PandasMarketCalendar实例化
        if isinstance(cal, string_types):
            cal = PandasMarketCalendar(calendar=cal)
        elif hasattr(cal, 'valid_days'):
            cal = PandasMarketCalendar(calendar=cal)

        # 如果是TradingCalendarBase的子类，直接实例化，如果已经是一个实例，忽略
        else:
            try:
                if issubclass(cal, TradingCalendarBase):
                    cal = cal()
            except TypeError:  
                pass

        # 给_tradingcal赋值
        self._tradingcal = cal

    # 增加信号，这些信号会在后面添加到SignalStrategy中
    def add_signal(self, sigtype, sigcls, *sigargs, **sigkwargs):
        self.signals.append((sigtype, sigcls, sigargs, sigkwargs))

    # 信号策略及其参数
    def signal_strategy(self, stratcls, *args, **kwargs):
        self._signal_strat = (stratcls, args, kwargs)

    # 是否允许在订单没有成交的时候执行新的信号或者订单
    def signal_concurrent(self, onoff):
        self._signal_concurrent = onoff

    # 是否允许在有持仓的情况下执行新的订单
    def signal_accumulate(self, onoff):
        self._signal_accumulate = onoff

    # 增加新的store
    def addstore(self, store):
        if store not in self.stores:
            self.stores.append(store)

    # 增加新的writer
    def addwriter(self, wrtcls, *args, **kwargs):
        self.writers.append((wrtcls, args, kwargs))

    # 设置sizer,sizer只能有一个
    def addsizer(self, sizercls, *args, **kwargs):
        self.sizers[None] = (sizercls, args, kwargs)

    # 根据策略的顺序添加sizer,策略和sizer是根据idx对应的，各个sizer会应用到对应的策略中
    def addsizer_byidx(self, idx, sizercls, *args, **kwargs):
        self.sizers[idx] = (sizercls, args, kwargs)

    # 添加指标
    def addindicator(self, indcls, *args, **kwargs):
        self.indicators.append((indcls, args, kwargs))

    # 添加analyzer
    def addanalyzer(self, ancls, *args, **kwargs):
        self.analyzers.append((ancls, args, kwargs))

    # 添加observer
    def addobserver(self, obscls, *args, **kwargs):
        self.observers.append((False, obscls, args, kwargs))

    # 给每个数据都增加一个observer
    def addobservermulti(self, obscls, *args, **kwargs):
        self.observers.append((True, obscls, args, kwargs))

    # 增加一个callback用于获取notify_store方法处理的信息
    def addstorecb(self, callback):
        self.storecbs.append(callback)

    # 通知store的信息
    def _notify_store(self, msg, *args, **kwargs):
        for callback in self.storecbs:
            callback(msg, *args, **kwargs)

        self.notify_store(msg, *args, **kwargs)

    # 通知store的信息，可以在cerebro的子类中重写
    def notify_store(self, msg, *args, **kwargs):
        pass

    # 对store中的信息进行通知，并传递到每个运行的策略中
    def _storenotify(self):
        for store in self.stores:
            for notif in store.get_notifications():
                msg, args, kwargs = notif

                self._notify_store(msg, *args, **kwargs)
                for strat in self.runningstrats:
                    strat.notify_store(msg, *args, **kwargs)

    # 增加一个callable用于获取notify_data通知的信息
    def adddatacb(self, callback):
        self.datacbs.append(callback)

    # 数据信息通知
    def _datanotify(self):
        for data in self.datas:
            for notif in data.get_notifications():
                status, args, kwargs = notif
                self._notify_data(data, status, *args, **kwargs)
                for strat in self.runningstrats:
                    strat.notify_data(data, status, *args, **kwargs)

    # 通知数据信息
    def _notify_data(self, data, status, *args, **kwargs):
        for callback in self.datacbs:
            callback(data, status, *args, **kwargs)

        self.notify_data(data, status, *args, **kwargs)

    # 通知数据信息
    def notify_data(self, data, status, *args, **kwargs):
        pass

    # 增加数据，这个是比较常用的功能
    def adddata(self, data, name=None):
        # 如果name不是None的话，就把name赋值给data._name
        if name is not None:
            data._name = name

        # data._id每次增加一个数据，就会增加一个
        data._id = next(self._dataid)
        # 设置data的环境
        data.setenvironment(self)

        # 把data追加到self.datas
        self.datas.append(data)
        # 根据data._name和data分别作为字典的key和value
        self.datasbyname[data._name] = data
        # 从data中得到feed
        feed = data.getfeed()
        # 如果feed不是None,并且feed没有在feeds中
        if feed and feed not in self.feeds:
            # 把feed追加到self.feeds中
            self.feeds.append(feed)

        # 如果data是实时数据，把_dolive的值变为True
        if data.islive():
            self._dolive = True

        return data

    # chaindata的使用方法，把几个数据拼接起来
    def chaindata(self, *args, **kwargs):
        dname = kwargs.pop('name', None)
        if dname is None:
            dname = args[0]._dataname
        d = bt.feeds.Chainer(dataname=dname, *args)
        self.adddata(d, name=dname)

        return d

    # rollover的用法，满足一定条件之后，在不同数据之间切换
    def rolloverdata(self, *args, **kwargs):
        dname = kwargs.pop('name', None)
        if dname is None:
            dname = args[0]._dataname
        d = bt.feeds.RollOver(dataname=dname, *args, **kwargs)
        self.adddata(d, name=dname)

        return d

    # replay的使用
    def replaydata(self, dataname, name=None, **kwargs):
        if any(dataname is x for x in self.datas):
            dataname = dataname.clone()

        dataname.replay(**kwargs)
        self.adddata(dataname, name=name)
        self._doreplay = True

        return dataname

    # resample的使用
    def resampledata(self, dataname, name=None, **kwargs):
        if any(dataname is x for x in self.datas):
            dataname = dataname.clone()

        dataname.resample(**kwargs)
        self.adddata(dataname, name=name)
        self._doreplay = True

        return dataname

    # 优化的callback
    def optcallback(self, cb):
        self.optcbs.append(cb)

    # 优化策略，不推荐使用这个方法，大家考虑忽略
    def optstrategy(self, strategy, *args, **kwargs):
        self._dooptimize = True
        args = self.iterize(args)
        optargs = itertools.product(*args)

        optkeys = list(kwargs)

        vals = self.iterize(kwargs.values())
        optvals = itertools.product(*vals)

        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)

        optkwargs = map(dict, okwargs1)

        it = itertools.product([strategy], optargs, optkwargs)
        self.strats.append(it)

    # 添加策略
    def addstrategy(self, strategy, *args, **kwargs):
        self.strats.append([(strategy, args, kwargs)])
        return len(self.strats) - 1

    # 设置broker
    def setbroker(self, broker):
        self._broker = broker
        broker.cerebro = self
        return broker

    # 获取broker
    def getbroker(self):
        return self._broker

    broker = property(getbroker, setbroker)

    # 画图，backtrader的画图主要是基于matplotlib,需要考虑升级换代，
    def plot(self, plotter=None, numfigs=1, iplot=True, start=None, end=None,
             width=16, height=9, dpi=300, tight=True, use=None,
             **kwargs):
        if self._exactbars > 0:
            return

        if not plotter:
            from . import plot
            if self.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use)

                figs.append(rfig)

            plotter.show()

        return figs

    # 在优化的时候传递给多进程的模块
    def __call__(self, iterstrat):

        predata = self.p.optdatas and self._dopreload and self._dorunonce
        return self.runstrategies(iterstrat, predata=predata)

    # 删除runstrats,
    def __getstate__(self):

        rv = vars(self).copy()
        if 'runstrats' in rv:
            del(rv['runstrats'])
        return rv

    # 当在策略内部或者其他地方调用这个函数的时候，将会很快停止执行
    def runstop(self):
        self._event_stop = True  
        
    # 执行回测的核心方法，任何传递的参数将会影响其中的标准参数，如果没有添加数据，将会立即停止
    # 根据是否是优化参数，返回的结果不同def run(self, **kwargs):
    def run(self, **kwargs):
        self._event_stop = False 
        
        # 如果没有数据，直接返回空的列表
        if not self.datas:
            return []  

        pkeys = self.params._getkeys()
        for key, val in kwargs.items():
            if key in pkeys:
                setattr(self.params, key, val)
                
        # 管理对象的缓存
        linebuffer.LineActions.cleancache()  
        indicator.Indicator.cleancache()  

        linebuffer.LineActions.usecache(self.p.objcache)
        indicator.Indicator.usecache(self.p.objcache)

        # 是否是_dorunonce,_dopreload,_exactbars
        self._dorunonce = self.p.runonce
        self._dopreload = self.p.preload
        self._exactbars = int(self.p.exactbars)

        # 如果_exactbars的值不是0的话，_dorunonce需要是False,如果_dopreload是True,并且_exactbars小于1的话，_dopreload设置成True
        if self._exactbars:
            self._dorunonce = False  
            self._dopreload = self._dopreload and self._exactbars < 1

        # 如果_doreplay是True或者数据中有任何一个具有replaying属性值是True的话，就把_doreplay设置成True
        self._doreplay = self._doreplay or any(x.replaying for x in self.datas)
        # 如果_doreplay,需要把_dopreload设置成False
        if self._doreplay:
            self._dopreload = False

        # 如果_dolive或者live,需要把_dorunonce和_dopreload设置成False
        if self._dolive or self.p.live:
            self._dorunonce = False
            self._dopreload = False

        # writer的列表
        self.runwriters = list()

        # 如果writer参数是True的话，增加默认的writer
        if self.p.writer is True:
            wr = WriterFile()
            self.runwriters.append(wr)

        # 如果具有其他的writer的话，实例化之后添加到runwriters中
        for wrcls, wrargs, wrkwargs in self.writers:
            wr = wrcls(*wrargs, **wrkwargs)
            self.runwriters.append(wr)

        # 如果那个writer需要全部的csv的输出，把结果保存到文件中
        self.writers_csv = any(map(lambda x: x.p.csv, self.runwriters))

        # 运行的策略列表
        self.runstrats = list()

        # 如果signals不是None等，处理signalstrategy相关的问题
        if self.signals:  
            signalst, sargs, skwargs = self._signal_strat
            if signalst is None:
                try:
                    signalst, sargs, skwargs = self.strats.pop(0)
                except IndexError:
                    pass  
                else:
                    if not isinstance(signalst, SignalStrategy):
                        self.strats.insert(0, (signalst, sargs, skwargs))
                        signalst = None  

            if signalst is None:  
                signalst, sargs, skwargs = SignalStrategy, tuple(), dict()

            self.addstrategy(signalst,
                             _accumulate=self._signal_accumulate,
                             _concurrent=self._signal_concurrent,
                             signals=self.signals,
                             *sargs,
                             **skwargs)

        # 如果策略列表是空的话，添加策略
        if not self.strats:  
            self.addstrategy(Strategy)

        # 迭代策略
        iterstrats = itertools.product(*self.strats)
        # 如果不是优化参数，或者使用的cpu核数是1
        if not self._dooptimize or self.p.maxcpus == 1:
            # 遍历策略
            for iterstrat in iterstrats:
                # 运行策略
                runstrat = self.runstrategies(iterstrat)
                # 把运行的策略添加到运行策略的列表中
                self.runstrats.append(runstrat)
                # 如果是优化参数
                if self._dooptimize:
                    # 遍历所有的optcbs，以便返回停止策略的结果
                    for cb in self.optcbs:
                        cb(runstrat)  
        # 如果是优化参数
        else:
            # 如果optdatas是True,并且_dopreload，并且_dorunonce
            if self.p.optdatas and self._dopreload and self._dorunonce:
                # 遍历每个data,进行reset,如果_exactbars小于1，对数据进行extend处理
                # 开始数据
                # 如果数据_dopreload的话，对数据调用preload
                for data in self.datas:
                    data.reset()
                    if self._exactbars < 1:  
                        data.extend(size=self.params.lookahead)
                    data._start()
                    if self._dopreload:
                        data.preload()

            # 开启进程池
            pool = multiprocessing.Pool(self.p.maxcpus or None)
            for r in pool.imap(self, iterstrats):
                self.runstrats.append(r)
                for cb in self.optcbs:
                    cb(r)  

            # 关闭进程词
            pool.close()

            # 如果optdatas是True,并且_dopreload，并且_dorunonce，遍历数据，并停止数据
            if self.p.optdatas and self._dopreload and self._dorunonce:
                for data in self.datas:
                    data.stop()

        # 如果不是参数优化
        if not self._dooptimize:
            return self.runstrats[0]

        return self.runstrats

    # 初始化计数
    def _init_stcount(self):
        self.stcount = itertools.count(0)
        
    # 调用下个计数
    def _next_stid(self):
        return next(self.stcount)

    # 运行策略
    def runstrategies(self, iterstrat, predata=False):
        # 初始化计数
        self._init_stcount()

        # 初始化运行的策略为空列表
        self.runningstrats = runstrats = list()
        # 遍历store，并开始
        for store in self.stores:
            store.start()

        # 如果cheat_on_open和broker_coo，给broker进行相应的设置
        if self.p.cheat_on_open and self.p.broker_coo:
            if hasattr(self._broker, 'set_coo'):
                self._broker.set_coo(True)

        # 如果fund历史不是None的话，需要设置fund history
        if self._fhistory is not None:
            self._broker.set_fund_history(self._fhistory)

        # 遍历order的历史
        for orders, onotify in self._ohistory:
            self._broker.add_order_history(orders, onotify)

        # broker开始
        self._broker.start()

        # feed开始
        for feed in self.feeds:
            feed.start()

        # 如果需要保存writer中的数据
        if self.writers_csv:
            wheaders = list()
            # 遍历数据，如果数据的csv属性值是True的话，获取数据中的需要保存的headers
            for data in self.datas:
                if data.csv:
                    wheaders.extend(data.getwriterheaders())

            # 保存writer中的headers
            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addheaders(wheaders)

        # 如果没有predata的话，需要提前预处理数据，和run中预处理数据的方法很相似
        if not predata:
            for data in self.datas:
                data.reset()
                if self._exactbars < 1:  
                    data.extend(size=self.params.lookahead)
                data._start()
                if self._dopreload:
                    data.preload()

        # 循环策略
        for stratcls, sargs, skwargs in iterstrat:
            # 把数据添加到策略参数
            sargs = self.datas + list(sargs)
            # 实例化策略
            try:
                strat = stratcls(*sargs, **skwargs)
            except bt.errors.StrategySkipError:
                continue  

            # 旧的数据同步方法
            if self.p.oldsync:
                strat._oldsync = True  
            # 是否保存交易历史数据
            if self.p.tradehistory:
                strat.set_tradehistory()
            # 添加策略
            runstrats.append(strat)

        # 获取时区信息，如果时区信息是整数，那么就获取该整数对应的index的时区，如果不是整数，就使用tzparse解析时区
        tz = self.p.tz
        if isinstance(tz, integer_types):
            tz = self.datas[tz]._tz
        else:
            tz = tzparse(tz)

        # 如果runstrats不是空的列表的话
        if runstrats:
            # 获取默认的sizer
            defaultsizer = self.sizers.get(None, (None, None, None))
            # 对于每个策略
            for idx, strat in enumerate(runstrats):
                # 如果stdstats是True的话，会增加几个observer
                if self.p.stdstats:
                    # 增加observer的broker
                    strat._addobserver(False, observers.Broker)
                    if self.p.oldbuysell:
                        strat._addobserver(True, observers.BuySell)
                    else:
                        strat._addobserver(True, observers.BuySell,
                                           barplot=True)

                    # 增加observer的trade
                    if self.p.oldtrades or len(self.datas) == 1:
                        strat._addobserver(False, observers.Trades)
                    else:
                        strat._addobserver(False, observers.DataTrades)

                # 把observers中的observer及其参数增加到策略中
                for multi, obscls, obsargs, obskwargs in self.observers:
                    strat._addobserver(multi, obscls, *obsargs, **obskwargs)

                # 把indicators中的indicator增加到策略中
                for indcls, indargs, indkwargs in self.indicators:
                    strat._addindicator(indcls, *indargs, **indkwargs)

                # 把analyzers中的analyzer增加到策略中
                for ancls, anargs, ankwargs in self.analyzers:
                    strat._addanalyzer(ancls, *anargs, **ankwargs)

                sizer, sargs, skwargs = self.sizers.get(idx, defaultsizer)
                if sizer is not None:
                    strat._addsizer(sizer, *sargs, **skwargs)

                # 设置时区
                strat._settz(tz)
                # 策略开始
                strat._start()

                # 对于正在运行的writer来说，如果csv参数是True的话，把策略中需要保存的数据保存到writer中
                for writer in self.runwriters:
                    if writer.p.csv:
                        writer.addheaders(strat.getwriterheaders())

            # 如果predata是False，没有提前加载数据
            if not predata:
                # 循环每个策略，调用qbuffer缓存数据
                for strat in runstrats:
                    strat.qbuffer(self._exactbars, replaying=self._doreplay)

            # 循环每个writer,开始writer
            for writer in self.runwriters:
                writer.start()

            # 准备timers
            self._timers = []
            self._timerscheat = []
            # 循环timer
            for timer in self._pretimers:
                # 启动timer
                timer.start(self.datas[0])

                # 如果timer的参数cheat是True的话，就把timer增加到self._timerscheat，否则就增加到self._timers
                if timer.params.cheat:
                    self._timerscheat.append(timer)
                else:
                    self._timers.append(timer)

            # 如果_dopreload 和 _dorunonce是True的话
            if self._dopreload and self._dorunonce:
                # 如果是旧的数据对齐和同步方式，使用_runonce_old，否则使用_runonce
                if self.p.oldsync:
                    self._runonce_old(runstrats)
                else:
                    self._runonce(runstrats)
            # 如果_dopreload 和 _dorunonce并不都是True的话
            else:
                # 如果是旧的数据对齐和同步方式，使用_runnext_old，否则使用_runnext
                if self.p.oldsync:
                    self._runnext_old(runstrats)
                else:
                    self._runnext(runstrats)

            # 遍历策略并停止运行
            for strat in runstrats:
                strat._stop()

        # 停止broker
        self._broker.stop()

        # 如果predata是False的话，遍历数据并停止每个数据
        if not predata:
            for data in self.datas:
                data.stop()

        # 遍历每个feed,并停止feed
        for feed in self.feeds:
            feed.stop()

        # 遍历每个store,并停止store
        for store in self.stores:
            store.stop()

        # 停止writer
        self.stop_writers(runstrats)

        # 如果是做参数优化，并且optreturn是True的话，获取策略运行后的结果，并添加到results,返回该结果
        if self._dooptimize and self.p.optreturn:
            results = list()
            for strat in runstrats:
                for a in strat.analyzers:
                    a.strategy = None
                    a._parent = None
                    for attrname in dir(a):
                        if attrname.startswith('data'):
                            setattr(a, attrname, None)

                oreturn = OptReturn(strat.params, analyzers=strat.analyzers, strategycls=type(strat))
                results.append(oreturn)

            return results

        return runstrats

    # 停止writer
    def stop_writers(self, runstrats):
        cerebroinfo = OrderedDict()
        datainfos = OrderedDict()

        # 获取每个数据的信息，保存到datainfos中，然后保存到cerebroinfo
        for i, data in enumerate(self.datas):
            datainfos['Data%d' % i] = data.getwriterinfo()

        cerebroinfo['Datas'] = datainfos

        stratinfos = dict()
        for strat in runstrats:
            stname = strat.__class__.__name__
            stratinfos[stname] = strat.getwriterinfo()

        cerebroinfo['Strategies'] = stratinfos

        for writer in self.runwriters:
            writer.writedict(dict(Cerebro=cerebroinfo))
            writer.stop()

    # 通知broker信息
    def _brokernotify(self):
        # 调用broker的next
        self._broker.next()
        while True:
            # 获取要通知的order信息，如果order是None,跳出循环，如果不是None,获取order的owner.如果owner是None的话，默认是第一个策略
            order = self._broker.get_notification()
            if order is None:
                break

            owner = order.owner
            if owner is None:
                owner = self.runningstrats[0]  

            # 通过第一个策略通知order信息
            owner._addnotification(order, quicknotify=self.p.quicknotify)

    # 就得runnext方法，和runnext很相似
    def _runnext_old(self, runstrats):
        data0 = self.datas[0]
        d0ret = True
        while d0ret or d0ret is None:
            lastret = False
            self._storenotify()
            if self._event_stop:  
                return
            self._datanotify()
            if self._event_stop: 
                return

            d0ret = data0.next()
            if d0ret:
                for data in self.datas[1:]:
                    if not data.next(datamaster=data0):  
                        data._check(forcedata=data0)  
                        data.next(datamaster=data0) 

            elif d0ret is None:
                data0._check()
                for data in self.datas[1:]:
                    data._check()
            else:
                lastret = data0._last()
                for data in self.datas[1:]:
                    lastret += data._last(datamaster=data0)

                if not lastret:
                    break

            self._datanotify()
            if self._event_stop:  
                return

            self._brokernotify()
            if self._event_stop: 
                return

            if d0ret or lastret: 
                for strat in runstrats:
                    strat._next()
                    if self._event_stop: 
                        return

                    self._next_writers(runstrats)

        self._datanotify()
        if self._event_stop:  
            return
        self._storenotify()
        if self._event_stop: 
            return

    def _runonce_old(self, runstrats):
        for strat in runstrats:
            strat._once()

        data0 = self.datas[0]
        datas = self.datas[1:]
        for i in range(data0.buflen()):
            data0.advance()
            for data in datas:
                data.advance(datamaster=data0)

            self._brokernotify()
            if self._event_stop: 
                return

            for strat in runstrats:
                strat._oncepost(data0.datetime[0])
                if self._event_stop:  
                    return

                self._next_writers(runstrats)

    # 运行writer的next
    def _next_writers(self, runstrats):
        if not self.runwriters:
            return

        if self.writers_csv:
            wvalues = list()
            for data in self.datas:
                if data.csv:
                    wvalues.extend(data.getwritervalues())

            for strat in runstrats:
                wvalues.extend(strat.getwritervalues())

            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addvalues(wvalues)

                    writer.next()

    # 禁止runonce
    def _disable_runonce(self):
        self._dorunonce = False

    def _runnext(self, runstrats):
        # 对数据的时间周期进行排序
        datas = sorted(self.datas,
                       key=lambda x: (x._timeframe, x._compression))
        # 其他数据
        datas1 = datas[1:]
        # 主数据
        data0 = datas[0]
        d0ret = True

        # resample的index
        rs = [i for i, x in enumerate(datas) if x.resampling]
        # replaying的index
        rp = [i for i, x in enumerate(datas) if x.replaying]
        rsonly = [i for i, x in enumerate(datas)
                  if x.resampling and not x.replaying]
        # 仅仅只做resample,不做replay得index
        onlyresample = len(datas) == len(rsonly)
        # 判断是否没有需要resample的数据
        noresample = not rsonly

        # 克隆的数据量
        clonecount = sum(d._clone for d in datas)
        # 数据的数量
        ldatas = len(datas)
        # 没有克隆的数据量
        ldatas_noclones = ldatas - clonecount
        lastqcheck = False
        # 默认dt0在最大时间
        dt0 = date2num(datetime.datetime.max) - 2  
        while d0ret or d0ret is None:
            # 如果有任何实时数据的话，newqcheck是False
            newqcheck = not any(d.haslivedata() for d in datas)
            # 如果存在实时数据
            if not newqcheck:
                livecount = sum(d._laststatus == d.LIVE for d in datas)
                newqcheck = not livecount or livecount == ldatas_noclones

            lastret = False
            # 通知store相关的信息
            self._storenotify()
            if self._event_stop:
                return
            # 通知data相关的信息
            self._datanotify()
            if self._event_stop: 
                return

            # 记录开始的时间，并且通知feed从qcheck中减去qlapse的时间
            drets = []
            qstart = datetime.datetime.utcnow()
            for d in datas:
                qlapse = datetime.datetime.utcnow() - qstart
                d.do_qcheck(newqcheck, qlapse.total_seconds())
                drets.append(d.next(ticks=False))

            # 遍历drets,如果d0ret是False,并且存在dret是None的话，d0ret是None
            d0ret = any((dret for dret in drets))
            if not d0ret and any((dret is None for dret in drets)):
                d0ret = None

            # 如果d0ret不是None的话
            if d0ret:
                # 获取时间
                dts = []
                for i, ret in enumerate(drets):
                    dts.append(datas[i].datetime[0] if ret else None)

                # 获取最小的时间
                if onlyresample or noresample:
                    dt0 = min((d for d in dts if d is not None))
                else:
                    dt0 = min((d for i, d in enumerate(dts)
                               if d is not None and i not in rsonly))

                # 获取主数据，及时间
                dmaster = datas[dts.index(dt0)]  
                self._dtmaster = dmaster.num2date(dt0)
                self._udtmaster = num2date(dt0)

                for i, ret in enumerate(drets):
                    # 如果ret不是None的话，继续下一个ret
                    if ret:  
                        continue

                    # 获取数据，并尝试给dts设置时间
                    d = datas[i]
                    d._check(forcedata=dmaster)  
                    if d.next(datamaster=dmaster, ticks=False): 
                        dts[i] = d.datetime[0]  
                    else:
                        pass

                for i, dti in enumerate(dts):
                    # 如果dti不是None
                    if dti is not None:
                        # 获取数据
                        di = datas[i]
                        rpi = False and di.replaying   
                        if dti > dt0:
                            if not rpi:  
                                di.rewind()  
                        elif not di.replaying:
                            di._tick_fill(force=True)


            # 如果d0ret是None的话，遍历每个数据，调用_check()
            elif d0ret is None:
                for data in datas:
                    data._check()
            # 如果是其他情况
            else:
                lastret = data0._last()
                for data in datas1:
                    lastret += data._last(datamaster=data0)

                if not lastret:
                    break

            # 通知数据信息
            self._datanotify()
            if self._event_stop:  
                return

            # 检查timer和遍历策略并调用_next_open()进行运行
            if d0ret or lastret: 
                self._check_timers(runstrats, dt0, cheat=True)
                if self.p.cheat_on_open:
                    for strat in runstrats:
                        strat._next_open()
                        if self._event_stop: 
                            return

            # 通知broker
            self._brokernotify()
            if self._event_stop:
                return

            # 通知timer,并且遍历策略并运行
            if d0ret or lastret: 
                self._check_timers(runstrats, dt0, cheat=False)
                for strat in runstrats:
                    strat._next()
                    if self._event_stop: 
                        return

                    self._next_writers(runstrats)

        # 通知数据信息
        self._datanotify()
        if self._event_stop:  
            return
        # 通知store信息
        self._storenotify()
        if self._event_stop:  
            return

    def _runonce(self, runstrats):

        # 遍历策略，调用_once和reset
        for strat in runstrats:
            strat._once()
            strat.reset()  


        # 对数据进行排序，从小周期开始到大周期
        datas = sorted(self.datas,
                       key=lambda x: (x._timeframe, x._compression))

        while True:
            # 对于每个数据调用advance_peek(),取得最小的一个时间作为第一个
            dts = [d.advance_peek() for d in datas]
            dt0 = min(dts)
            if dt0 == float('inf'):
                break  

            # 第一个策略现在的长度slen
            slen = len(runstrats[0])
            # 对于每个数据的时间，如果时间小于即将到来的最小的时间，数据向前一位，否则，忽略
            for i, dti in enumerate(dts):
                if dti <= dt0:
                    datas[i].advance()
                else:
                    pass

            # 检查timer
            self._check_timers(runstrats, dt0, cheat=True)

            # 如果是cheat_on_open，对于每个策略调用_oncepost_open()
            if self.p.cheat_on_open:
                for strat in runstrats:
                    strat._oncepost_open()
                    # 如果调用了stop，就停止
                    if self._event_stop: 
                        return

            # 调用_brokernotify()
            self._brokernotify()
            # 如果调用了stop，就停止
            if self._event_stop: 
                return

            # 检查timer
            self._check_timers(runstrats, dt0, cheat=False)

            for strat in runstrats:
                strat._oncepost(dt0)
                if self._event_stop:  
                    return

                self._next_writers(runstrats)

    # 检查timer
    def _check_timers(self, runstrats, dt0, cheat=False):
        # 如果cheat是False的话，timers等于self._timers，否则就等于self._timerscheat
        timers = self._timers if not cheat else self._timerscheat
        # 对于timers中的timer
        for t in timers:
            # 使用timer.check(dt0),如果返回是True,就进入下面，否则，检查下个timer
            if not t.check(dt0):
                continue

            # 通知timer
            t.params.owner.notify_timer(t, t.lastwhen, *t.args, **t.kwargs)

            # 如果需要策略使用timer(t.params.strats是True）的时候，循环策略，调用notify_timer
            if t.params.strats:
                for strat in runstrats:
                    strat.notify_timer(t, t.lastwhen, *t.args, **t.kwargs)
