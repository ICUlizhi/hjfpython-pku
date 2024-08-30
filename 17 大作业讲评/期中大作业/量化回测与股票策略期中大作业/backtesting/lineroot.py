import operator

from .utils.py3 import range, with_metaclass

from . import metabase


class MetaLineRoot(metabase.MetaParams):
    '''
    继承元类MetaParams，重写了donew方法
    如果对象obj的创建发生在对象obj_owner的创建过程中，给obj添加实例属性_owner，其值为obj_owner
    '''

    def donew(cls, *args, **kwargs):
        # 首先调用父类的donew方法创建对象_obj
        _obj, args, kwargs = super(MetaLineRoot, cls).donew(*args, **kwargs)
        # findowner用于寻找_obj的父类，属于_obj._OwnerCls或者LineMultiple的实例，同时这个父类还不能是ownerskip
        # owner，其属性值为调用metabase模块中findowner函数的返回值
        # 满足条件1是为了通过设置关键字参数skip排除"主人"人选；
        # 将_obj传递给位置参数owned并满足条件2是为了避免将_obj选为它自己的"主人"；
        # 满足条件3是为了通过位置参数cls来指定"主人"的所属类
        ownerskip = kwargs.pop('_ownerskip', None)
        _obj._owner = metabase.findowner(_obj,
                                         _obj._OwnerCls or LineMultiple,
                                         skip=ownerskip)

        return _obj, args, kwargs


class LineRoot(with_metaclass(MetaLineRoot, object)):
    '''
    为line实例定义一个共同的基类和接口，主要用于周期管理、迭代管理、操作管理和丰富的对比操作。
    需要额外注意的是，with_metaclass(MetaLineRoot,object)创建了一个类：temporary_class,这个类继承了MetaLineRoot和object，LineRoot继承的是temporary_class
    到这里的继承关系如下：LineRoot-->MetaLineRoot-->MetaParams-->MetaBase-->type
    '''
    # 初始化的时候类的属性
    _OwnerCls = None# 默认的父类实例是None
    _minperiod = 1# 最小周期是1
    _opstage = 1# 操作状态默认是1

    # 指标类型、策略类型和观察类型的值分别是0,1,2
    IndType, StratType, ObsType = range(3)

    # 转变操作状态为1
    def _stage1(self):
        self._opstage = 1

    # 转变操作状态为2
    def _stage2(self):
        self._opstage = 2

    # 根据line的操作状态决定调用哪种操作算法
    def _operation(self, other, operation, r=False, intify=False):
        if self._opstage == 1:
            return self._operation_stage1(
                other, operation, r=r, intify=intify)

        return self._operation_stage2(other, operation, r=r)

    # 自身的操作
    def _operationown(self, operation):
        if self._opstage == 1:
            return self._operationown_stage1(operation)

        return self._operationown_stage2(operation)

    # 改变lines去实施最小缓存计划
    def qbuffer(self, savemem=0):
        raise NotImplementedError

    # 需要达到的最小缓存
    def minbuffer(self, size):
        raise NotImplementedError

    # 可以用于在策略中设置最小的周期，可以不用等待指标产生具体的值就开始运行
    def setminperiod(self, minperiod):
        self._minperiod = minperiod

    # 更新最小周期，最小周期可能在其他地方已经计算产生，跟现有的最小周期对比，选择一个最大的作为最小周期
    def updateminperiod(self, minperiod):
        self._minperiod = max(self._minperiod, minperiod)

    # 添加最小周期
    def addminperiod(self, minperiod):
        raise NotImplementedError

    # 增加最小周期
    def incminperiod(self, minperiod):
        raise NotImplementedError

    # 在最小周期内迭代的时候将会调用这个函数
    def prenext(self):
        pass

    # 在最小周期迭代结束的时候，即将开始next的时候调用一次
    def nextstart(self):
        self.next()

    # 最小周期迭代结束后，开始调用next
    def next(self):
        pass

    # 在最小周期迭代的时候调用preonce
    def preonce(self, start, end):
        pass

    # 在最小周期结束的时候运行一次，调用once
    def oncestart(self, start, end):
        self.once(start, end)

    # 当最小周期迭代结束的时候调用用于计算结果
    def once(self, start, end):
        pass

    # 一些算术操作
    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
        raise NotImplementedError

    # 做自身操作
    def _makeoperationown(self, operation, _ownerskip=None):
        raise NotImplementedError

    # 自身操作阶段1
    def _operationown_stage1(self, operation):
        return self._makeoperationown(operation, _ownerskip=self)
    # 自身操作阶段2
    def _operationown_stage2(self, operation):
        return operation(self[0])
    # 右操作
    def _roperation(self, other, operation, intify=False):
        return self._operation(other, operation, r=True, intify=intify)

    # 阶段1操作，判断other是不是包含多个line,如果有多个line，就取出第一个line,然后进行操作
    def _operation_stage1(self, other, operation, r=False, intify=False):
        if isinstance(other, LineMultiple):
            other = other.lines[0]

        return self._makeoperation(other, operation, r, self)

    # 阶段2操作，如果other是一个line，就取出当前值，然后进行操作
    def _operation_stage2(self, other, operation, r=False):
        if isinstance(other, LineRoot):
            other = other[0]

        
        if r:
            return operation(other, self[0])

        return operation(self[0], other)

    def _operationown_stage2(self, operation):
        return operation(self[0])

    def __add__(self, other):
        return self._operation(other, operator.__add__)

    def __radd__(self, other):
        return self._roperation(other, operator.__add__)

    def __sub__(self, other):
        return self._operation(other, operator.__sub__)

    def __rsub__(self, other):
        return self._roperation(other, operator.__sub__)

    def __mul__(self, other):
        return self._operation(other, operator.__mul__)

    def __rmul__(self, other):
        return self._roperation(other, operator.__mul__)

    def __div__(self, other):
        return self._operation(other, operator.__div__)

    def __rdiv__(self, other):
        return self._roperation(other, operator.__div__)

    def __floordiv__(self, other):
        return self._operation(other, operator.__floordiv__)

    def __rfloordiv__(self, other):
        return self._roperation(other, operator.__floordiv__)

    def __truediv__(self, other):
        return self._operation(other, operator.__truediv__)

    def __rtruediv__(self, other):
        return self._roperation(other, operator.__truediv__)

    def __pow__(self, other):
        return self._operation(other, operator.__pow__)

    def __rpow__(self, other):
        return self._roperation(other, operator.__pow__)

    def __abs__(self):
        return self._operationown(operator.__abs__)

    def __neg__(self):
        return self._operationown(operator.__neg__)

    def __lt__(self, other):
        return self._operation(other, operator.__lt__)

    def __gt__(self, other):
        return self._operation(other, operator.__gt__)

    def __le__(self, other):
        return self._operation(other, operator.__le__)

    def __ge__(self, other):
        return self._operation(other, operator.__ge__)

    def __eq__(self, other):
        return self._operation(other, operator.__eq__)

    def __ne__(self, other):
        return self._operation(other, operator.__ne__)

    def __nonzero__(self):
        return self._operationown(bool)

    __bool__ = __nonzero__

    
    
    __hash__ = object.__hash__


class LineMultiple(LineRoot):
    '''
    LineMultiple-->LineRoot-->MetaLineRoot-->MetaParams-->MetaBase-->type
    # 这个类继承自LineRoot，用于操作line多于1条的类
    '''
    # 重置
    def reset(self):
        self._stage1()
        self.lines.reset()

    # 对每一条line设置为操作状态1
    def _stage1(self):
        super(LineMultiple, self)._stage1()
        for line in self.lines:
            line._stage1()

    # 对每一条line设置为操作状态2
    def _stage2(self):
        super(LineMultiple, self)._stage2()
        for line in self.lines:
            line._stage2()

    # 对每一条line增加一个最小周期
    def addminperiod(self, minperiod):
        for line in self.lines:
            line.addminperiod(minperiod)

    # 对每一条line增加最小周期，但是这个在LineRoot里面好没有实施
    def incminperiod(self, minperiod):
        for line in self.lines:
            line.incminperiod(minperiod)

    # 多条line操作的时候是对第一条line进行操作
    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
        return self.lines[0]._makeoperation(other, operation, r, _ownerskip)

    # 多条line操作的时候是对第一条line的自身进行操作
    def _makeoperationown(self, operation, _ownerskip=None):
        return self.lines[0]._makeoperationown(operation, _ownerskip)

    # 对多条line设置qbuffer
    def qbuffer(self, savemem=0):
        for line in self.lines:
            line.qbuffer(savemem=1)

    # 对多条line设置最小的缓存量
    def minbuffer(self, size):
        for line in self.lines:
            line.minbuffer(size)


class LineSingle(LineRoot):
    '''
    LineSingle-->LineRoot-->MetaLineRoot-->MetaParams-->MetaBase-->type
    # 这个类继承自LineRoot，用于操作line是一条的类
    '''
    # 增加minperiod，增加的时候需要减去初始化设置的时候self._minperiod=1的设置
    def addminperiod(self, minperiod):
        self._minperiod += minperiod - 1

    # 增加minperiod,不考虑初始的self._minperiod的值
    def incminperiod(self, minperiod):
        self._minperiod += minperiod
