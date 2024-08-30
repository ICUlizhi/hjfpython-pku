from datetime import datetime, date, timedelta

from .dataseries import TimeFrame, _Bar
from .utils.py3 import with_metaclass
from . import metabase
from .utils.date import date2num, num2date


# 这个类仅仅用在了_checkbarover这样一个函数中
class DTFaker(object):
   
    # 初始化
    def __init__(self, data, forcedata=None):
        # 数据
        self.data = data

        self.datetime = self
        self.p = self

        # 如果forcedata是None的话
        if forcedata is None:
            # 获取现在的utc时间，并且加上数据的时间补偿
            _dtime = datetime.utcnow() + data._timeoffset()
            # 把计算得到的utc时间转化成数字
            self._dt = dt = date2num(_dtime)  
            # 把数字时间转化成本地的时间格式的时间
            self._dtime = data.num2date(dt)  
        # 如果forcedata不是None的话
        else:
            # 直接从forcedata的列datatime中获取相应的时间作为utc时间
            self._dt = forcedata.datetime[0] 
            # 直接从forcedata中获取本地时间
            self._dtime = forcedata.datetime.datetime() 
        # 一天交易结束时间
        self.sessionend = data.p.sessionend

    # 长度
    def __len__(self):
        return len(self.data)
    # 调用的时候返回本地化的日期和时间
    def __call__(self, idx=0):
        return self._dtime  

    # datetime返回本地化日期和时间
    def datetime(self, idx=0):
        return self._dtime

    # 返回本地化的日期
    def date(self, idx=0):
        return self._dtime.date()

    # 返回本地化的时间
    def time(self, idx=0):
        return self._dtime.time()

    # 返回数据的日历
    @property
    def _calendar(self):
        return self.data._calendar

    # 如果idx=0,返回utc的数字格式的时间，否则，返回-inf
    def __getitem__(self, idx):
        return self._dt if idx == 0 else float('-inf')

    # 数字转化成日期和时间
    def num2date(self, *args, **kwargs):
        return self.data.num2date(*args, **kwargs)

    # 日期和时间转化成数字
    def date2num(self, *args, **kwargs):
        return self.data.date2num(*args, **kwargs)

    # 获取交易日结束的时间
    def _getnexteos(self):
        return self.data._getnexteos()

# resampler的基类
class _BaseResampler(with_metaclass(metabase.MetaParams, object)):
    # 参数
    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', True),
        ('boundoff', 0),
        ('timeframe', TimeFrame.Days),
        ('compression', 1),
        ('takelate', True),
        ('sessionend', True),
    )

    # 初始化
    def __init__(self, data):
        # 如果时间周期小于日，但是大于tick,subdays就是True，subdays代表是日内的时间周期
        self.subdays = TimeFrame.Ticks < self.p.timeframe < TimeFrame.Days
        # 如果时间周期小于周，subweeks就是True
        self.subweeks = self.p.timeframe < TimeFrame.Weeks
        # 如果不是subdays，并且数据的时间周期等于参数的时间周期，并且参数的周期数除以数据周期数余数是0，componly是True
        self.componly = (not self.subdays and
                         data._timeframe == self.p.timeframe and
                         not (self.p.compression % data._compression))
        # 创建一个对象，用于保存bar的数据
        self.bar = _Bar(maxdate=True)  # bar holder
        # 产生的bar的数目，用于控制周期数
        self.compcount = 0  # count of produced bars to control compression
        # 是否是第一个bar
        self._firstbar = True
        # 如果bar2edge、adjbartime、subweeks都是True的话，doadjusttime就是True
        self.doadjusttime = (self.p.bar2edge and self.p.adjbartime and
                             self.subweeks)
        # 该交易日的结束时间
        self._nexteos = None

        # Modify data information according to own parameters
        # 初始化的时候，根据参数修改data的属性
        # 数据的resampling是1
        data.resampling = 1
        # replaying等于replaying
        data.replaying = self.replaying
        # 数据的时间周期等于参数的时间周期
        data._timeframe = self.p.timeframe
        # 数据的周期数等于参数的周期数
        data._compression = self.p.compression

        self.data = data

    # 晚到的数据怎么处理，如果不是subdays，返回False,如果data长度大于1并且现在时间小于等于上一个时间，返回True
    def _latedata(self, data):
        if not self.subdays:
            return False

        return len(data) > 1 and data.datetime[0] <= data.datetime[-1]

    # 是否检查bar结束
    def _checkbarover(self, data, fromcheck=False, forcedata=None):
        # 检查的数据，如果fromcheck是True的话，使用DTFaker生成实例，否则使用data
        chkdata = DTFaker(data, forcedata) if fromcheck else data
        # 是否结束
        isover = False
        # 如果不是componly，并且_barover(chkdata)是False的话，返回False
        if not self.componly and not self._barover(chkdata):
            return isover
        # 如果是日内的话，并且bar2edge是True的话，返回True
        if self.subdays and self.p.bar2edge:
            isover = True
        # 如果fromcheck是False的话
        elif not fromcheck: 
            # compcount+1
            self.compcount += 1
            # 如果compcount除以周期数等于0，返回True
            if not (self.compcount % self.p.compression):
                isover = True

        return isover

    # 判断data数据是否结束
    def _barover(self, data):
        # 时间周期
        tframe = self.p.timeframe
        # 如果时间周期等于tick,返回bar.isopen()
        if tframe == TimeFrame.Ticks:
            # Ticks is already the lowest level
            return self.bar.isopen()
        # 如果时间周期小于day,调用_barover_subdays(data)
        elif tframe < TimeFrame.Days:
            return self._barover_subdays(data)
        # 如果时间周期等于day,调用_barover_days(data)
        elif tframe == TimeFrame.Days:
            return self._barover_days(data)
        # 如果时间周期等于week,调用_barover_weeks(data)
        elif tframe == TimeFrame.Weeks:
            return self._barover_weeks(data)
        # 如果时间周期等于月，调用_barover_months(data)
        elif tframe == TimeFrame.Months:
            return self._barover_months(data)
        # 如果时间周期等于年，调用_barover_years(data)
        elif tframe == TimeFrame.Years:
            return self._barover_years(data)
    # 设置session结束的时间
    def _eosset(self):
        if self._nexteos is None:
            self._nexteos, self._nextdteos = self.data._getnexteos()
            return
    # 检查session结束的时间
    def _eoscheck(self, data, seteos=True, exact=False):
        # 如果seteos是True的话，直接调用_eosset计算session结束的时间
        if seteos:
            self._eosset()
        # 对比当前的数据时间和session结束的时间
        equal = data.datetime[0] == self._nextdteos
        grter = data.datetime[0] > self._nextdteos
        # 如果exact是True的话，ret就等于equal,
        # 如果不是的话,如果grter是True的话，如果bar.isopen()是True,bar.datetime小于下一个结束时间，ret等于True
        # 否则，ret就等于equal
        if exact:
            ret = equal
        else:
            if grter:
                ret = (self.bar.isopen() and
                       self.bar.datetime <= self._nextdteos)
            else:
                ret = equal
        # 如果ret是True的话，_lasteos等于_nexteos,_lastdteos等于_nextdteos
        # 并把_nexteos和_nextdteos分别设置成None和-inf
        if ret:
            self._lasteos = self._nexteos
            self._lastdteos = self._nextdteos
            self._nexteos = None
            self._nextdteos = float('-inf')

        return ret

    # 检查日
    def _barover_days(self, data):
        return self._eoscheck(data)

    # 检查周
    def _barover_weeks(self, data):
        # 如果数据的_calendar是None的话
        if self.data._calendar is None:
            # 根据日期得到具体的年，周数目和日
            year, week, _ = data.num2date(self.bar.datetime).date().isocalendar()
            # 得到bar的周数目
            yearweek = year * 100 + week
            # 得到数据的年、周数目和日，并得到数据的周数目
            baryear, barweek, _ = data.datetime.date().isocalendar()
            bar_yearweek = baryear * 100 + barweek
            # 如果数据的周数目大于bar的周数目，返回True,否则，返回False
            return bar_yearweek > yearweek
        # 如果数据的_calendar不是None的话，调用last_weekday
        else:
            return data._calendar.last_weekday(data.datetime.date())
    # 检查月
    def _barover_months(self, data):
        dt = data.num2date(self.bar.datetime).date()
        yearmonth = dt.year * 100 + dt.month

        bardt = data.datetime.datetime()
        bar_yearmonth = bardt.year * 100 + bardt.month

        return bar_yearmonth > yearmonth

    # 检查年
    def _barover_years(self, data):
        return (data.datetime.datetime().year >
                data.num2date(self.bar.datetime).year)

    # 获取时间的点数
    def _gettmpoint(self, tm):
        '''
          - Ex 1: 00:05:00 in minutes -> point = 5
          - Ex 2: 00:05:20 in seconds -> point = 5 * 60 + 20 = 320
        '''
        # 分钟点数
        point = tm.hour * 60 + tm.minute
        # 剩余点数
        restpoint = 0
        # 如果时间周期小于分钟
        if self.p.timeframe < TimeFrame.Minutes:
            # 秒的点数
            point = point * 60 + tm.second
            # 如果时间周期小于秒
            if self.p.timeframe < TimeFrame.Seconds:
                # point转化成微秒数
                point = point * 1e6 + tm.microsecond
            # 如果时间周期不小于秒，剩余点数为微秒数
            else:
                restpoint = tm.microsecond
        # 如果时间周期不小于分钟，剩余点数为秒数和微秒数
        else:
            restpoint = tm.second + tm.microsecond
        # 点数加上boundoff
        point += self.p.boundoff

        return point, restpoint

    # 日内bar结束
    def _barover_subdays(self, data):
        # 如果_eoscheck(data)返回True,那么，函数返回True
        if self._eoscheck(data):
            return True
        # 如果数据的时间小于bar的时间，返回False
        if data.datetime[0] < self.bar.datetime:
            return False

        # 获取bar的和data的时间
        tm = num2date(self.bar.datetime).time()
        bartm = num2date(data.datetime[0]).time()
        # 分别获取self.bar的时间的点数，data的时间的点数
        point, _ = self._gettmpoint(tm)
        barpoint, _ = self._gettmpoint(bartm)
        # 设置ret等于False
        ret = False
        # 如果data的时间的点数小于bar的时间的点数，返回False
        # 如果data的时间的点数大于bar的时间的点数，进一步分析
        if barpoint > point:
            # 如果bar2edge是False的话，返回True
            if not self.p.bar2edge:
                ret = True
            # 如果周期数是1的话，返回True
            elif self.p.compression == 1:
                ret = True
            # 如果bar2edge是True的话，并且compression不等于1的话，计算两个的点数除以周期数之后的余数
            # 如果数据的点数的余数大于bar的点数的余数，返回True
            else:
                point_comp = point // self.p.compression
                barpoint_comp = barpoint // self.p.compression

                if barpoint_comp > point_comp:
                    ret = True

        return ret

    # 检查是否在数据还没有向前移动的情况下提交当前存储的bar
    def check(self, data, _forcedata=None):
        '''Called to check if the current stored bar has to be delivered in
        spite of the data not having moved forward. If no ticks from a live
        feed come in, a 5 second resampled bar could be delivered 20 seconds
        later. When this method is called the wall clock (incl data time
        offset) is called to check if the time has gone so far as to have to
        deliver the already stored data
        '''
        if not self.bar.isopen():
            return

        return self(data, fromcheck=True, forcedata=_forcedata)

    # 判断数据是否是快要形成bar了
    def _dataonedge(self, data):
        # 如果subweek是False的话，如果data._calendar是None的话，返回False和True
        if not self.subweeks:
            if data._calendar is None:
                return False, True  # nothing can be done
            # 时间周期
            tframe = self.p.timeframe
            # ret设置成False
            ret = False
            # 如果时间周期等于周，调用last_weekday判断
            # 如果时间周期等于月，调用last_monthday判断
            # 如果时间周期等于年，调用last_yearday判断
            if tframe == TimeFrame.Weeks:  # Ticks is already the lowest
                ret = data._calendar.last_weekday(data.datetime.date())
            elif tframe == TimeFrame.Months:
                ret = data._calendar.last_monthday(data.datetime.date())
            elif tframe == TimeFrame.Years:
                ret = data._calendar.last_yearday(data.datetime.date())
            # 如果ret是True
            if ret:
                # docheckover设置成False
                docheckover = False
                # compcount+1
                self.compcount += 1
                # 如果compcount除以compression余数等于0，返回True,否则，返回False
                ret = not (self.compcount % self.p.compression)
            # 如果ret等于False的话，docheckover等于True
            else:
                docheckover = True
            # 返回ret , docheckover
            return ret, docheckover
        # _eoscheck检查，返回两个True
        if self._eoscheck(data, exact=True):
            return True, True
        # 如果是日内的话
        if self.subdays:
            # 获取数据的点数和剩余的点数
            point, prest = self._gettmpoint(data.datetime.time())
            # 如果剩余点数不为0，返回False和True
            if prest:
                return False, True 

            # 计算boundary和剩余的boundary
            bound, brest = divmod(point, self.p.compression)

            # 如果divmod计算的结果余数为0，返回两个Trye
            return (brest == 0 and point == (bound * self.p.compression), True)

        # 这段不会运行
        if False and self.p.sessionend:
            bdtime = data.datetime.datetime()
            bsend = datetime.combine(bdtime.date(), data.p.sessionend)
            return bdtime == bsend
        # 如果前面都没有运行到return,返回False,True
        return False, True  

    # 计算调整的时间
    def _calcadjtime(self, greater=False):
        if self._nexteos is None:
            return self._lastdteos  

        dt = self.data.num2date(self.bar.datetime)

        tm = dt.time()
        point, _ = self._gettmpoint(tm)

        point = point // self.p.compression

        point += self.p.rightedge

        point *= self.p.compression

        extradays = 0
        if self.p.timeframe == TimeFrame.Minutes:
            ph, pm = divmod(point, 60)
            ps = 0
            pus = 0
        elif self.p.timeframe == TimeFrame.Seconds:
            ph, pm = divmod(point, 60 * 60)
            pm, ps = divmod(pm, 60)
            pus = 0
        elif self.p.timeframe <= TimeFrame.MicroSeconds:
            ph, pm = divmod(point, 60 * 60 * 1e6)
            pm, psec = divmod(pm, 60 * 1e6)
            ps, pus = divmod(psec, 1e6)
        elif self.p.timeframe == TimeFrame.Days:
            eost = self._nexteos.time()
            ph = eost.hour
            pm = eost.minute
            ps = eost.second
            pus = eost.microsecond

        if ph > 23:  
            extradays = ph // 24
            ph %= 24

        dt = dt.replace(hour=int(ph), minute=int(pm),
                        second=int(ps), microsecond=int(pus))
        if extradays:
            dt += timedelta(days=extradays)
        dtnum = self.data.date2num(dt)
        return dtnum

    # 调整bar的时间
    def _adjusttime(self, greater=False, forcedata=None):

        dtnum = self._calcadjtime(greater=greater)
        if greater and dtnum <= self.bar.datetime:
            return False

        self.bar.datetime = dtnum
        return True


# 把小周期的数据抽样形成大周期的数据
class Resampler(_BaseResampler):
    '''This class resamples data of a given timeframe to a larger timeframe.

    Params

      - bar2edge (default: True)

        resamples using time boundaries as the target. For example with a
        "ticks -> 5 seconds" the resulting 5 seconds bars will be aligned to
        xx:00, xx:05, xx:10 ...

        # 在抽样的时候使用时间边界作为目标，比如如果是ticks数据想要抽样程5秒钟，那么将会在xx:00,xx:05,xx:10这样的时间形成bar

      - adjbartime (default: True)

        Use the time at the boundary to adjust the time of the delivered
        resampled bar instead of the last seen timestamp. If resampling to "5
        seconds" the time of the bar will be adjusted for example to hh:mm:05
        even if the last seen timestamp was hh:mm:04.33

        .. note::

           Time will only be adjusted if "bar2edge" is True. It wouldn't make
           sense to adjust the time if the bar has not been aligned to a
           boundary
        # 调整bar最后一个bar的最后的时间，在bar2edge是True的时候，使用最后的边界作为最后一个bar的时间

      - rightedge (default: True)

        Use the right edge of the time boundaries to set the time.

        If False and compressing to 5 seconds the time of a resampled bar for
        seconds between hh:mm:00 and hh:mm:04 will be hh:mm:00 (the starting
        boundary

        If True the used boundary for the time will be hh:mm:05 (the ending
        boundary)
        # 是否使用右边的时间边界，比如时间边界是hh:mm:00：hh:mm:05，如果设置成True的话，将会使用hh:mm:05
        # 设置成False,将会使用hh:mm:00
    '''
    # 参数
    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', True),
    )

    replaying = False

    # 在数据不再产生bar的时候调用，可以被调用多次，有机会在必须传递bar的时候产生额外的bar
    def last(self, data):
        if self.bar.isopen():
            if self.doadjusttime:
                self._adjusttime()

            data._add2stack(self.bar.lvalues())
            self.bar.bstart(maxdate=True) 
            return True

        return False

    # 调用resampler的时候使用
    def __call__(self, data, fromcheck=False, forcedata=None):
        consumed = False
        onedge = False
        docheckover = True
        if not fromcheck:
            if self._latedata(data):
                if not self.p.takelate:
                    data.backwards()
                    return True 

                self.bar.bupdate(data) 
                self.bar.datetime = data.datetime[-1] + 0.000001
                data.backwards()  
                return True

            if self.componly: 
                _, self._lastdteos = self.data._getnexteos()
                consumed = True

            else:
                onedge, docheckover = self._dataonedge(data)  
                consumed = onedge

        if consumed:
            self.bar.bupdate(data)  
            data.backwards()  

        cond = self.bar.isopen()
        if cond: 
            if not onedge:  
                if docheckover:
                    cond = self._checkbarover(data, fromcheck=fromcheck,
                                              forcedata=forcedata)
        if cond:
            dodeliver = False
            if forcedata is not None:
                tframe = self.p.timeframe
                if tframe == TimeFrame.Ticks: 
                    dodeliver = True
                elif tframe == TimeFrame.Minutes:
                    dtnum = self._calcadjtime(greater=True)
                    dodeliver = dtnum <= forcedata.datetime[0]
                elif tframe == TimeFrame.Days:
                    dtnum = self._calcadjtime(greater=True)
                    dodeliver = dtnum <= forcedata.datetime[0]
            else:
                dodeliver = True

            if dodeliver:
                if not onedge and self.doadjusttime:
                    self._adjusttime(greater=True, forcedata=forcedata)

                data._add2stack(self.bar.lvalues())
                self.bar.bstart(maxdate=True)  

        if not fromcheck:
            if not consumed:
                self.bar.bupdate(data) 
                data.backwards() 

        return True

# replayer类
class Replayer(_BaseResampler):
    '''This class replays data of a given timeframe to a larger timeframe.

    It simulates the action of the market by slowly building up (for ex.) a
    daily bar from tick/seconds/minutes data

    Only when the bar is complete will the "length" of the data be changed
    effectively delivering a closed bar

    Params

      - bar2edge (default: True)

        replays using time boundaries as the target of the closed bar. For
        example with a "ticks -> 5 seconds" the resulting 5 seconds bars will
        be aligned to xx:00, xx:05, xx:10 ...

      - adjbartime (default: False)

        Use the time at the boundary to adjust the time of the delivered
        resampled bar instead of the last seen timestamp. If resampling to "5
        seconds" the time of the bar will be adjusted for example to hh:mm:05
        even if the last seen timestamp was hh:mm:04.33

        .. note::

           Time will only be adjusted if "bar2edge" is True. It wouldn't make
           sense to adjust the time if the bar has not been aligned to a
           boundary

        .. note:: if this parameter is True an extra tick with the *adjusted*
                  time will be introduced at the end of the *replayed* bar

      - rightedge (default: True)

        Use the right edge of the time boundaries to set the time.

        If False and compressing to 5 seconds the time of a resampled bar for
        seconds between hh:mm:00 and hh:mm:04 will be hh:mm:00 (the starting
        boundary

        If True the used boundary for the time will be hh:mm:05 (the ending
        boundary)
    '''
    params = (
        ('bar2edge', True),
        ('adjbartime', False),
        ('rightedge', True),
    )

    replaying = True
    # 调用类的时候运行
    def __call__(self, data, fromcheck=False, forcedata=None):
        # 消耗
        consumed = False
        # 在生成bar的时间点
        onedge = False
        # 晚到的数据
        takinglate = False
        # 是否检查bar结束
        docheckover = True
        # 如果fromcheck是False的话
        if not fromcheck:
            # 调用_latedata判断，看晚到的数据怎么处理,如果返回True
            if self._latedata(data):
                # 如果takelate是False的话，就生成一个新的bar
                if not self.p.takelate:
                    data.backwards(force=True)
                    return True  # get a new bar
                # 设置这两个参数
                consumed = True
                takinglate = True
            # 如果不是日内的话
            elif self.componly: 
                consumed = True

            else:
                # 调用_dataonedge，用于判断是否在生成bar的时间和bar是否结束
                onedge, docheckover = self._dataonedge(data)  # for subdays
                consumed = onedge

            data._tick_fill(force=True)  # update
        # 如果consumed是True的话，更新数据，如果takinglate是True的话，给bar设置一个新的时间
        if consumed:
            self.bar.bupdate(data)
            if takinglate:
                self.bar.datetime = data.datetime[-1] + 0.000001

        cond = onedge
        # 如果当前不是在生成bar的时间点，如果需要检查，就需要检查bar是否结束
        if not cond:  
            if docheckover:
                cond = self._checkbarover(data, fromcheck=fromcheck)
        # 如果检查结果返回True的话
        if cond:
            # 如果不是正好在生成bar的时候，并且要调整时间
            if not onedge and self.doadjusttime: 
                adjusted = self._adjusttime(greater=True)
                # 如果需要调整，就调整时间，更新bar
                if adjusted:
                    ago = 0 if (consumed or fromcheck) else -1
                    data._updatebar(self.bar.lvalues(), forward=False, ago=ago)
                # 如果不需要检查
                if not fromcheck:
                    # 如果不是消耗模式，就使用_save2stack保存数据
                    if not consumed:
                        self.bar.bupdate(data, reopen=True)
                        data._save2stack(erase=True, force=True)
                    # 如果是消耗模式，data启动，下个bar是第一根bar
                    else:
                        self.bar.bstart(maxdate=True)
                        self._firstbar = True  
                # 如果需要检查
                else: 
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  
                    if adjusted:
                        data._save2stack(erase=True, force=True)
            # 如果不需要检查
            elif not fromcheck:
                if not consumed:
                    self.bar.bupdate(data, reopen=True)
                else:
                    if not self._firstbar:  
                        data.backwards(force=True)
                    data._updatebar(self.bar.lvalues(), forward=False, ago=0)
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  
        # 如果不需要检查
        elif not fromcheck:
            if not consumed:
                self.bar.bupdate(data)

            if not self._firstbar: 
                data.backwards(force=True)

            data._updatebar(self.bar.lvalues(), forward=False, ago=0)
            self._firstbar = False

        return False  


class ResamplerTicks(Resampler):
    params = (('timeframe', TimeFrame.Ticks),)


class ResamplerSeconds(Resampler):
    params = (('timeframe', TimeFrame.Seconds),)


class ResamplerMinutes(Resampler):
    params = (('timeframe', TimeFrame.Minutes),)


class ResamplerDaily(Resampler):
    params = (('timeframe', TimeFrame.Days),)


class ResamplerWeekly(Resampler):
    params = (('timeframe', TimeFrame.Weeks),)


class ResamplerMonthly(Resampler):
    params = (('timeframe', TimeFrame.Months),)


class ResamplerYearly(Resampler):
    params = (('timeframe', TimeFrame.Years),)


class ReplayerTicks(Replayer):
    params = (('timeframe', TimeFrame.Ticks),)


class ReplayerSeconds(Replayer):
    params = (('timeframe', TimeFrame.Seconds),)


class ReplayerMinutes(Replayer):
    params = (('timeframe', TimeFrame.Minutes),)


class ReplayerDaily(Replayer):
    params = (('timeframe', TimeFrame.Days),)


class ReplayerWeekly(Replayer):
    params = (('timeframe', TimeFrame.Weeks),)


class ReplayerMonthly(Replayer):
    params = (('timeframe', TimeFrame.Months),)