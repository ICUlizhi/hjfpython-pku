from .lineiterator import LineIterator, ObserverBase, StrategyBase
from backtesting.utils.py3 import with_metaclass


# Observer元类
class MetaObserver(ObserverBase.__class__):
    # 在donew的时候，创建了一个_analyzers属性，设置为空列表
    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaObserver, cls).donew(*args, **kwargs)
        _obj._analyzers = list()  

        return _obj, args, kwargs  

    # 在dopreinit的时候，如果_stclock属性是True的话，就把_clock设置成_obj的父类
    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaObserver, cls).dopreinit(_obj, *args, **kwargs)

        if _obj._stclock:  
            _obj._clock = _obj._owner

        return _obj, args, kwargs


# Observer类
class Observer(with_metaclass(MetaObserver, ObserverBase)):
    # _stclock设置成False
    _stclock = False
    # 拥有的实例
    _OwnerCls = StrategyBase
    # line的类型
    _ltype = LineIterator.ObsType
    # 是否保存到csv等文件中
    csv = True
    # 画图设置选择
    plotinfo = dict(plot=False, subplot=True)

    def prenext(self):
        self.next()

    # 注册analyzer
    def _register_analyzer(self, analyzer):
        self._analyzers.append(analyzer)

    def _start(self):
        self.start()

    def start(self):
        pass
