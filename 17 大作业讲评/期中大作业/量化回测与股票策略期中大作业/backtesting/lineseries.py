import sys

from .utils.py3 import map, range, string_types, with_metaclass

from .linebuffer import LineBuffer, LineActions, LinesOperation, LineDelay, NAN
from .lineroot import LineRoot, LineSingle, LineMultiple
from .metabase import AutoInfoClass
from . import metabase


class LineAlias(object):
    ''' Descriptor就是一类实现了__get__(), __set__(), __delete__()方法的对象
    这个类的是通过初始化一个"line",这个line是一个整数，在请求的时候会返回obj.lines[line]
    __set__用于设置line在0处的值

    参数:
        line (int): 索引在owner的line缓存中被返回的那一条line
    '''

    def __init__(self, line):
        # 初始化，self.line是一个整数
        self.line = line

    def __get__(self, obj, cls=None):
        # 返回obj.lines[整数]，返回的应该是一个line的类型
        return obj.lines[self.line]

    def __set__(self, obj, value):
        '''
        一个line在被创建之后就不能set了， 但是内部的值可以通过添加binding来set.
        '''
        # 如果值是多条line的数据结构，就取第一条line
        if isinstance(value, LineMultiple):
            value = value.lines[0]

        # 如果value是一个line，但是这个line还不是LineActions的子类的话，就把value转换成LineDelay结构
        if not isinstance(value, LineActions):
            value = value(0)

        # 给value这个line增加一个line，obj.lines[self.line]，到value.blindings,然后给line增加最小周期
        value.addbinding(obj.lines[self.line])


class Lines(object):
    '''
    Lines类是用于管理多根数据线的数据结构
    '''
    # Lines用于定义lines的array，并且拥有LineBuffer的大多数接口方法
    # 这些接口方法被传递到self保存的lines上
    # 这个类可以通过_derive自动子类化，用于按照预先定义的次序保存新的lines
    
    # 初始状态返回值都是空或者0，能达到想要的效果是因为调用了Lines类的_derive方法进行信息迭代
    # 类方法，返回空元组
    # 获取父类提供的数据线名称集合
    _getlinesbase = classmethod(lambda cls: ())
    # 类方法，返回空元组
    # 获取当前类和父类提供的数据线名称集合
    _getlines = classmethod(lambda cls: ())
    # 类方法，返回0
    # 获取当前类和父类指定可以额外添加的数据线的数量总和
    _getlinesextra = classmethod(lambda cls: 0)
    # 类方法，返回0
    # 获取父类指定可以额外添加的数据线的数量总和
    _getlinesextrabase = classmethod(lambda cls: 0)

    # Lines类的类方法_derive在元类MetaLineSeries的__new__方法中被调用
    @classmethod
    def _derive(cls, name, lines, extralines, otherbases, linesoverride=False,
                lalias=None):
        '''
        实现了以下四个功能：
        (1)派生Lines类的子类；
        (2)整合当前类和父类的数据线信息；
        (3)为Lines对象添加名为数据线名称的属性，返回对应的LineBuffer对象；
        (4)为Lines对象添加名为数据线别名的属性，返回对应的LineBuffer对象。
        '''
        # 创建这个class的子类，这个子类将会包含这个class的lines,extralines, otherbases的lines
        # name将会用于最终类的名字的后缀
        # linesoverride：如果这个参数是真的，所有bases的lines将会被丢弃，并且baseclass将会成为最高等级的Lines类
        #                这个用于创建一个新的等级
        
        # 其他类的lines，默认是空元组
        obaseslines = ()
        # 其他类的额外的lines，默认是0
        obasesextralines = 0
        
        # 通过遍历otherbases并获取其元素的数据线信息，
        # obaseslines和obasesextralines分别整合了除第一顺位以外其它父类提供的数据线名称和额外可添加的数据线数量
        # 对其他的bases进行循环
        for otherbase in otherbases:
            # 如果otherbase是元组，直接添加到obaseslines中去
            if isinstance(otherbase, tuple):
                obaseslines += otherbase
            # 如果不是元组，就通过_getlines获取具体的lines,添加到obaseslines，然后通过_getlinesextra获取额外的lines,添加到obasesextralines
            else:
                obaseslines += otherbase._getlines()
                obasesextralines += otherbase._getlinesextra()

        # 如果参数linesoverride为False，则表示不覆盖父类的数据线信息，
        # 此时变量baselines和baseextralines分别整合了所有父类提供的数据线名称和额外可添加的数据线数量
        if not linesoverride:
            baselines = cls._getlines() + obaseslines
            baseextralines = cls._getlinesextra() + obasesextralines
        else:  # 否则, 变量baselines和baseextralines分别赋值为空元组和0。
            baselines = ()
            baseextralines = 0

        # 在baselines和baseextralines的基础之上，
        # 变量clslines和clsextralines分别添加了当前类提供的数据线名称和额外可添加的数据线数量
        clslines = baselines + lines
        # class的额外的lines，整数
        clsextralines = baseextralines + extralines
        # 要添加的lines,包含穿进来的其他类的lines和lines
        lines2add = obaseslines + lines

        
        # 如果不对lines进行重置，那么基类就是cls本身，否则就是Lines
        basecls = cls if not linesoverride else Lines

        # 动态创建类，名字是cls的名字加上name作为后缀，继承自basecls
        newcls = type(str(cls.__name__ + '_' + name), (basecls,), {})
        # 并添加到cls所在的模块
        # 这里实现了_derive方法的第一个功能：派生Lines类的子类
        clsmodule = sys.modules[cls.__module__]
        # 设置newcls的__module__
        newcls.__module__ = cls.__module__
        # 设置clsmodule的newcls的名字的属性为newcls
        setattr(clsmodule, str(cls.__name__ + '_' + name), newcls)

        # 给newcls设置类方法属性_getlines，返回clslines
        # setattr(newcls, '_getlinesextrabase', classmethod(lambda cls: clslines)) # 原先出错的地方
        setattr(newcls, '_getlinesbase', classmethod(lambda cls: baselines))
        # 给newcls设置类方法属性_getlines，返回baseextralines
        setattr(newcls, '_getlines', classmethod(lambda cls: clslines))

        # 给newcls设置类方法属性_getlinesextra，返回clsextralines
        setattr(newcls, '_getlinesextrabase',
                classmethod(lambda cls: baseextralines))
        setattr(newcls, '_getlinesextra',
                classmethod(lambda cls: clsextralines))

        # line开始，如果line不重写的话，开始的数字就是cls的line的数量，否则就是0
        l2start = len(cls._getlines()) if not linesoverride else 0
        l2add = enumerate(lines2add, start=l2start)
        l2alias = {} if lalias is None else lalias._getkwargsdefault()
        # 返回一个enumerate对象，从l2start开始返回迭代的index和值，既然l2add只用到了下面的循环，直接写到后面的循环就好
        # l2add = enumerate(lines2add, start=l2start)  
        # 如果lalias是None，l2alias是空的字典，否则返回lalias._getkwargsdefault()
        # l2alias = {} if lalias is None else lalias._getkwargsdefault() ，在这里面没用，移动到下面
        
        # 使用描述器LineAlias实现了_derive方法的第三个功能：为Lines对象添加名为数据线名称的属性，返回对应的LineBuffer对象
        for line, linealias in l2add:
            # line是一个整数，linealias如果不是字符串，那么和可能是元组或者列表，第一个就是它的名字
            if not isinstance(linealias, string_types):
                linealias = linealias[0]

            # 创建一个LineAlias的类
            desc = LineAlias(line)  
            # 在newcls中绑定linealias属性值为desc，个人感觉是方便数字和line名字的转换
            setattr(newcls, linealias, desc)

        # 同样使用描述器LineAlias实现了_derive方法的第四个功能：为Lines对象添加名为数据线别名的属性，返回对应的LineBuffer对象
        # 如果l2alias不是空的话，有需要设置，会运行下面的代码进行设置。这个逻辑写的并不是很高效，应该先判断下l2alias是否是空的，如果是空的话，就忽略，不运行
        # 如果lalias不是None的 情况下，l2alias才不是空
        for line, linealias in enumerate(newcls._getlines()):
            if not isinstance(linealias, string_types):
                
                linealias = linealias[0]

                # 给newcls设置alias属性，属性值为desc
            desc = LineAlias(line)  
            if linealias in l2alias:
                extranames = l2alias[linealias]
                if isinstance(linealias, string_types):
                    extranames = [extranames]

                for ename in extranames:
                    setattr(newcls, ename, desc)

        return newcls

    @classmethod
    def _getlinealias(cls, i):
        '''
        返回索引i对应的line的别名
        '''
        # 类方法，根据具体的index i 返回line的名字
        lines = cls._getlines()
        if i >= len(lines):
            return ''
        linealias = lines[i]
        return linealias

    @classmethod
    def getlinealiases(cls):
        # 类方法，返回cls的所有的line
        return cls._getlines()

    def itersize(self):
        # 生成lines中0到self.size的切片的迭代器
        return iter(self.lines[0:self.size()])

    def __init__(self, initlines=None):
        '''
        为Lines对象添加了一个名为lines的实例属性，该属性是一个列表
        根据数据线的数量 (即_getlines方法返回的元组的长度)，相应数量的LineBuffer对象将被添加到这个列表中
        如果额外可添加数据线的数量 (即_getlinesextra方法的返回值) 不为零，默认情况下相应数量的LineBuffer对象将被添加到列表中
        '''
        # 初始化lines,设定lines是一个列表
        self.lines = list()
        for line, linealias in enumerate(self._getlines()):
            kwargs = dict()
            self.lines.append(LineBuffer(**kwargs))

        # 添加额外的line，如果不初始化line的话，直接使用LineBuffer,如果初始化line的话，就使用initlines[i]进行初始化
        # 然后添加到self.lines
        for i in range(self._getlinesextra()):
            if not initlines:
                self.lines.append(LineBuffer())
            else:
                self.lines.append(initlines[i])

    def __len__(self):
        '''
        返回一条line的长度
        '''
        return len(self.lines[0])

    def size(self):
        return len(self.lines) - self._getlinesextra()

    def fullsize(self):
        return len(self.lines)

    def extrasize(self):
        return self._getlinesextra()

    def __getitem__(self, line):
        '''
        根据整数line作为yindex获取具体的line对象
        '''
        return self.lines[line]

    def get(self, ago=0, size=1, line=0):
        '''
        根据整数line作为index获取某条line，然后获取包含ago在内的之前的size个数量的数据
        '''
        return self.lines[line].get(ago, size=size)

    def __setitem__(self, line, value):
        '''
        给self设置属性，self._getlinealias(line)返回的是line的名字，value是设置的值
        '''
        setattr(self, self._getlinealias(line), value)

    def forward(self, value=NAN, size=1):
        '''
        实现将对数据容器的操作推广到Lines对象的实例属性lines中的每个LineBuffer对象
        '''
        for line in self.lines:
            line.forward(value, size=size)

    def backwards(self, size=1, force=False):
        '''
        实现将对数据容器的操作推广到Lines对象的实例属性lines中的每个LineBuffer对象
        '''
        for line in self.lines:
            line.backwards(size, force=force)

    def rewind(self, size=1):
        '''
        把line的idx和lencount减少size
        '''
        for line in self.lines:
            line.rewind(size)

    def extend(self, value=NAN, size=0):
        '''
        把line.array向前扩展size个值
        '''
        for line in self.lines:
            line.extend(value, size)

    def reset(self):
        '''
        重置line
        '''
        for line in self.lines:
            line.reset()

    def home(self):
        '''
        返回到最开始
        '''
        for line in self.lines:
            line.home()

    def advance(self, size=1):
        '''
        把line的idx和lencount增加size
        '''
        for line in self.lines:
            line.advance(size)

    def buflen(self, line=0):
        '''
        返回line缓存的数据的长度
        '''
        return self.lines[line].buflen()


class MetaLineSeries(LineMultiple.__class__):
    '''
    这个类是给LineSeries做一些预处理工作，主要是获取plotinfo、lines、plotlines等相关的属性
    然后创建一个_obj并给它增加相应的属性并赋值

      - 其__new__方法的核心功能是整合数据线信息:
        具体来说，假设类Cls是由元类MetaLineSeries或其子类所创建
        那么，用户可以在定义类Cls时通过特定的类变量输入数据线的相关信息
        接下来，元类MetaLineSeries的__new__方法会对这些类变量进行加工

      - 其donew方法的核心是为实例化的对象整合参数信息
        假设类Cls由元类MetaLineSeries或其子类所创建，对象obj由类Cls所创建
        元类MetaLineSeries的donew方法实现的功能为：
        (1)为对象obj添加实例属性lines (别名为l)、plotinfo、plotlines，属性值分别为类Cls的类变量lines、plotinfo、plotlines的实例对象；
        (2)为对象obj添加实例属性line，属性值为列表obj.lines.lines中的第一个LineBuffer对象；为对象obj添加实例属性line{d}和line_{d}，其中d为整数，属性值为obj.lines.lines列表中的第d+1个LineBuffer对象
    '''   


    def __new__(meta, name, bases, dct):
        '''
        整合数据线信息
        '''
        # 给dct增加一个alias,aliased的key，并设定默认值是(),"",其中aliases的值是一个空的列表，aliased的值是空的字符串。字典的具体用法
        aliases = dct.setdefault('alias', ())
        aliased = dct.setdefault('aliased', '')

        # 从参数dct中剥离在当前类中通过类变量lines、linesoveride、extralines和linealias输入的数据线信息
        # 并分别存放在变量newlines、linesoverride、extralines和newlalias中
        # 这么做的目的是避免覆盖当前类的父类同名类变量所包含的数据线信息
        
        # 从字典中删除linesoverride的key，并用linesoverride接收这个值，如果不存在这个key，就返回一个False
        linesoverride = dct.pop('linesoverride', False)
        newlines = dct.pop('lines', ())
        # 删除dct中的extralines，并把具体的值保存到extralines中，如果没有extralines的值，返回0
        extralines = dct.pop('extralines', 0)
        # 删除dct中的lines，并把具体的值保存到newlines中，如果没有lines的值，返回空元组

        newlalias = dict(dct.pop('linealias', {}))

        
        # 删除dct中的plotinfo，并把具体的值保存到newplotinfo中，如果没有plotinfo的值，返回空的字典
        newplotinfo = dict(dct.pop('plotinfo', {}))
        newplotlines = dict(dct.pop('plotlines', {}))

        
        # 调用type的__new__方法来创建一个新的类cls，其中参数name表示类名，bases表示父类，dct是一个字典对象，存储着类的属性和方法
        cls = super(MetaLineSeries, meta).__new__(meta, name, bases, dct)

        # 这几行代码为类cls添加了名为linealias的类变量，其属性值是一个AutoInfoClass类 (或其子类)，并通过调用它的_derive方法整合了当前类和其父类中类变量linealias所包含的信息
        # 整合结果同时储存在变量la中
        # 获取cls的linealias属性值，如果不存在，就返回AutoInfoClass类
        lalias = getattr(cls, 'linealias', AutoInfoClass)
        # 获取其他base的linealias
        oblalias = [x.linealias for x in bases[1:] if hasattr(x, 'linealias')]
        # AutoInfoClass类的_derive方法创建一个对象，给cls的linealias赋值
        cls.linealias = la = lalias._derive('la_' + name, newlalias, oblalias)
        # 为类cls添加了名为lines的类变量，其属性值是一个Lines类 (或其子类)，并通过调用它的_derive方法整合了当前类的和其父类中有关数据线的信息
        # 从cls获取lines属性值，如果没有返回Lines类
        lines = getattr(cls, 'lines', Lines)

        morebaseslines = [x.lines for x in bases[1:] if hasattr(x, 'lines')]
        # 使用autoinfoclass的_derive创建一个对象，赋值给cls的plotinfo属性
        cls.lines = lines._derive(name, newlines, extralines, morebaseslines,
                                  linesoverride, lalias=la)

        
        plotinfo = getattr(cls, 'plotinfo', AutoInfoClass)
        plotlines = getattr(cls, 'plotlines', AutoInfoClass)

        morebasesplotinfo = \
            [x.plotinfo for x in bases[1:] if hasattr(x, 'plotinfo')]
        # 使用autoinfoclass的_derive创建一个对象，赋值给cls的plotlines属性
        cls.plotinfo = plotinfo._derive('pi_' + name, newplotinfo,
                                        morebasesplotinfo)

        for line in newlines:
            newplotlines.setdefault(line, dict())

        morebasesplotlines = \
            [x.plotlines for x in bases[1:] if hasattr(x, 'plotlines')]
        cls.plotlines = plotlines._derive(
            'pl_' + name, newplotlines, morebasesplotlines, recurse=True)

        # 给alias属性赋值
        for alias in aliases:
            newdct = {'__doc__': cls.__doc__,
                      '__module__': cls.__module__,
                      'aliased': cls.__name__}

            if not isinstance(alias, string_types):
                
                aliasplotname = alias[1]
                alias = alias[0]
                newdct['plotinfo'] = dict(plotname=aliasplotname)

            newcls = type(str(alias), (cls,), newdct)
            clsmodule = sys.modules[cls.__module__]
            setattr(clsmodule, alias, newcls)

        
        return cls

    def donew(cls, *args, **kwargs):
        '''
        假设类Cls由元类MetaLineSeries或其子类所创建，对象obj由类Cls所创建
        元类MetaLineSeries的donew方法实现的功能为：
        (1)为对象obj添加实例属性lines (别名为l)、plotinfo、plotlines，属性值分别为类Cls的类变量lines、plotinfo、plotlines的实例对象；
        (2)为对象obj添加实例属性line，属性值为列表obj.lines.lines中的第一个LineBuffer对象；为对象obj添加实例属性line{d}和line_{d}，其中d为整数，属性值为obj.lines.lines列表中的第d+1个LineBuffer对象
        '''
        # 创建一个_obj,保存lines,plotinfo,plotlines相关的属性，并给lines增加别名
        
        # plotinfo的cls
        plotinfo = cls.plotinfo()

        # 给plotinfo增加具体的属性和相应的值
        for pname, pdef in cls.plotinfo._getitems():
            setattr(plotinfo, pname, kwargs.pop(pname, pdef))

        
        # 创建一个_obj,并设置plotinfo等于plotinfo
        _obj, args, kwargs = super(MetaLineSeries, cls).donew(*args, **kwargs)

        _obj.plotinfo = plotinfo
        
        # 给_obj的lines属性赋值
        _obj.lines = cls.lines()

        # 增加一个l属性，和lines等同
        _obj.plotlines = cls.plotlines()

        
        # 增加一个l属性，和lines等同
        _obj.l = _obj.lines
        # _obj的line属性，返回lines中的第一条，如果lines的数量是大于0的话
        if _obj.lines.fullsize():
            _obj.line = _obj.lines[0]
        # 迭代_obj中的lines，设置line的别名
        # self.line_1,self.line1,self.line_xxx是等同的
        for l, line in enumerate(_obj.lines):
            setattr(_obj, 'line_%s' % l, _obj._getlinealias(l))
            setattr(_obj, 'line_%d' % l, line)
            setattr(_obj, 'line%d' % l, line)
        return _obj, args, kwargs


class LineSeries(with_metaclass(MetaLineSeries, LineMultiple)):
    # 创建一个LineSeries类
    # 给lineseries类增加一个默认的属性plotinfo
    plotinfo = dict(
        plot=True,
        plotmaster=None,
        legendloc=None,
    )

    # csv属性
    csv = True

    @property
    def array(self):
        # 如果调用array，将会返回添加进去的第一条line的数据
        return self.lines[0].array

    def __getattr__(self, name):
        # 返回self.lines的name属性值
        return getattr(self.lines, name)

    def __len__(self):
        # 返回lines的数量
        return len(self.lines)

    def __getitem__(self, key):
        # 根据index获取第一条line的值
        return self.lines[0][key]

    def __setitem__(self, key, value):
        # 给self.lines设置属性及属性值
        setattr(self.lines, self.lines._getlinealias(key), value)

    def __init__(self, *args, **kwargs):
        # 初始化
        super(LineSeries, self).__init__()
        pass

    def plotlabel(self):
        # 画图的标签
        label = self.plotinfo.plotname or self.__class__.__name__
        # 获取参数的值
        sublabels = self._plotlabel()
        # 如果有具体的参数的话
        if sublabels:
            # 遍历对象sublabels，如果其中元素sublabel有plotinfo属性的话，就获取其中的plotname属性值，否则就是sublabel本身的名字
            for i, sublabel in enumerate(sublabels):
                if hasattr(sublabel, 'plotinfo'):
                    try:
                        s = sublabel.plotinfo.plotname
                    except:
                        s = ''
                    sublabels[i] = s or sublabel.__name__

            # 把sublabels按照字符串连接起来
            label += ' (%s)' % ', '.join(map(str, sublabels))
        return label

    def _plotlabel(self):
        # 获取参数的值
        return self.params._getvalues()

    def _getline(self, line, minusall=False):
        # 获取line
        # 如果line是字符串，就从self.lines获取属性值，如果不是字符串而是数字的话
        if isinstance(line, string_types):
            lineobj = getattr(self.lines, line)
        else:
            # 如果line的值是-1的话，如果minusall是False的话，修改line的值为0,返回第一条line，如果minusall是True的话，返回None
            if line == -1:  
                if minusall:  
                    return None
                line = 0
            lineobj = self.lines[line]
        # 返回一条line
        return lineobj

    def __call__(self, ago=None, line=-1):
        '''返回一个LineCoupler或LineDelay对象

        参数: ago (default: None)

          如果ago是None或者是LineRoot的子类的话，将会返回一个LinesCoupler对象

          否则，将会返回一个LineDelay对象

        Param: line (default: -1)
          如果是lineCoupler对象的话，line的值是-1的话，将会返回第一条line，否则返回line

          如果是LineDelay对象的话，line的值是-1的话，将会返回第一条line，否则返回line
        '''
        from .lineiterator import LinesCoupler  
        # 如果ago是None或者是LineRoot的子类的话
        if ago is None or isinstance(ago, LineRoot):
            args = [self, ago]
            lineobj = self._getline(line, minusall=True)
            if lineobj is not None:
                args[0] = lineobj
            # 将会返回一个LinesCoupler
            return LinesCoupler(*args, _ownerskip=self)

        
        # 如果ago不是None，并且不是LineRoot的子类，默认ago是int值，返回一个LineDelay对象
        return LineDelay(self._getline(line), ago, _ownerskip=self)


    # line的常规操作
    def forward(self, value=NAN, size=1):
        self.lines.forward(value, size)

    def backwards(self, size=1, force=False):
        self.lines.backwards(size, force=force)

    def rewind(self, size=1):
        self.lines.rewind(size)

    def extend(self, value=NAN, size=0):
        self.lines.extend(value, size)

    def reset(self):
        self.lines.reset()

    def home(self):
        self.lines.home()

    def advance(self, size=1):
        self.lines.advance(size)


class LineSeriesStub(LineSeries):
    '''
    根据一条line模拟一个多条line的对象
    '''

    extralines = 1

    def __init__(self, line, slave=False):
        # 初始化,把单个line对象转变为lines对象
        self.lines = self.__class__.lines(initlines=[line])
        self.owner = self._owner = line._owner
        self._minperiod = line._minperiod
        self.slave = slave

    
    def forward(self, value=NAN, size=1):
        if not self.slave:
            super(LineSeriesStub, self).forward(value, size)

    def backwards(self, size=1, force=False):
        if not self.slave:
            super(LineSeriesStub, self).backwards(size, force=force)

    def rewind(self, size=1):
        if not self.slave:
            super(LineSeriesStub, self).rewind(size)

    def extend(self, value=NAN, size=0):
        if not self.slave:
            super(LineSeriesStub, self).extend(value, size)

    def reset(self):
        if not self.slave:
            super(LineSeriesStub, self).reset()

    def home(self):
        if not self.slave:
            super(LineSeriesStub, self).home()

    def advance(self, size=1):
        if not self.slave:
            super(LineSeriesStub, self).advance(size)

    def qbuffer(self):
        if not self.slave:
            super(LineSeriesStub, self).qbuffer()

    def minbuffer(self, size):
        if not self.slave:
            super(LineSeriesStub, self).minbuffer(size)


def LineSeriesMaker(arg, slave=False):
    # 创建lineseries
    if isinstance(arg, LineSeries):
        return arg

    return LineSeriesStub(arg, slave=slave)
