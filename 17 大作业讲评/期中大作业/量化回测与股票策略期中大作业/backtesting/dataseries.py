import datetime as _datetime
from datetime import datetime
import inspect

from .utils.py3 import range, with_metaclass
from .lineseries import LineSeries
from .utils import AutoOrderedDict, OrderedDict, date2num


class TimeFrame(object):
    # 给TimeFrame这个类增加9个属性，用于区分交易的周期
    (Ticks, MicroSeconds, Seconds, Minutes,
     Days, Weeks, Months, Years, NoTimeFrame) = range(1, 10)

    # 增加一个names属性值
    Names = ['', 'Ticks', 'MicroSeconds', 'Seconds', 'Minutes',
             'Days', 'Weeks', 'Months', 'Years', 'NoTimeFrame']

    names = Names  

    # 类方法，获取Timeframe的周期类型
    @classmethod
    def getname(cls, tframe, compression=None):
        tname = cls.Names[tframe]
        if compression > 1 or tname == cls.Names[-1]:
            return tname  

        
        # 如果compression是1的话，会返回一个单数的交易周期
        return cls.Names[tframe][:-1]

    # 类方法，获取交易周期名字的值
    @classmethod
    def TFrame(cls, name):
        return getattr(cls, name)

    # 类方法，根据交易周期的值返回交易周期的名字
    @classmethod
    def TName(cls, tframe):
        return cls.Names[tframe]


class DataSeries(LineSeries):
    # 设置plotinfo相关的值
    plotinfo = dict(plot=True, plotind=True, plotylimited=True)

    # 设置dataseries的_name属性，通常在策略中可以直接使用data._name获取data具体的值
    _name = ''
    # 设置_compression属性，默认是1,意味着交易周期是单数的，比如1秒，1分钟，1天，1周这样的
    _compression = 1
    # 设置_timeframe属性，默认是天
    _timeframe = TimeFrame.Days

    # 给dataseries设置常用的7个属性及他们的值
    Close, Low, High, Open, Volume, OpenInterest, DateTime = range(7)

    # dataseries中line的顺序
    LineOrder = [DateTime, Open, High, Low, Close, Volume, OpenInterest]

    # 获取dataseries的header的变量名称，
    def getwriterheaders(self):
        headers = [self._name, 'len']

        for lo in self.LineOrder:
            headers.append(self._getlinealias(lo))

        morelines = self.getlinealiases()[len(self.LineOrder):]
        headers.extend(morelines)

        return headers

    # 获取values
    def getwritervalues(self):
        l = len(self)
        values = [self._name, l]

        if l:
            values.append(self.datetime.datetime(0))
            for line in self.LineOrder[1:]:
                values.append(self.lines[line][0])
            for i in range(len(self.LineOrder), self.lines.size()):
                values.append(self.lines[i][0])
        else:
            values.extend([''] * self.lines.size())  

        return values

    # 获取写入的信息
    def getwriterinfo(self):
        
        info = OrderedDict()
        info['Name'] = self._name
        info['Timeframe'] = TimeFrame.TName(self._timeframe)
        info['Compression'] = self._compression

        return info

# 数据线最为重要的信息是它的名称。 在使用backtrader时，我们通常会同时处理多根数据线，这就需要通过名称进行区分和标识
# 用户可以通过类变量lines来提供数据线的名称
class OHLC(DataSeries):
    # 继承DataSeries，lines剔除了datetime只剩下6条
    lines = ('close', 'low', 'high', 'open', 'volume', 'openinterest',)


class OHLCDateTime(OHLC):
    # 继承DataSeries，lines只保留了datetime
    lines = (('datetime'),)


class SimpleFilterWrapper(object):
    # 这是一个增加过滤器的类，可以根据过滤器的需要对数据进行一定的操作比如去除
    # 这个过滤器通常是类或者是函数
    def __init__(self, data, ffilter, *args, **kwargs):
        if inspect.isclass(ffilter):
            ffilter = ffilter(data, *args, **kwargs)
            args = []
            kwargs = {}

        self.ffilter = ffilter
        self.args = args
        self.kwargs = kwargs

    def __call__(self, data):
        if self.ffilter(data, *self.args, **self.kwargs):
            data.backwards()
            return True

        return False


class _Bar(AutoOrderedDict):
    # 这个bar是具有标准line的DataBase的占位符,常用于把小周期K线合成大周期K线。
   
    replaying = False

    
    
    MAXDATE = date2num(_datetime.datetime.max) - 2

    def __init__(self, maxdate=False):
        super(_Bar, self).__init__()
        self.bstart(maxdate=maxdate)

    def bstart(self, maxdate=False):
        # 准备开始前，先初始化
        
        self.close = float('NaN')
        self.low = float('inf')
        self.high = float('-inf')
        self.open = float('NaN')
        self.volume = 0.0
        self.openinterest = 0.0
        self.datetime = self.MAXDATE if maxdate else None

    def isopen(self):
        # 判断是否已经更新过了
        
        o = self.open
        return o == o  

    def bupdate(self, data, reopen=False):
        # 更新具体的bar
        
        if reopen:
            self.bstart()

        self.datetime = data.datetime[0]

        self.high = max(self.high, data.high[0])
        self.low = min(self.low, data.low[0])
        self.close = data.close[0]

        self.volume += data.volume[0]
        self.openinterest = data.openinterest[0]

        o = self.open
        if reopen or not o == o:
            self.open = data.open[0]
            return True  

        return False
