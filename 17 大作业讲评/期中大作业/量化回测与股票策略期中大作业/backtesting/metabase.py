from collections import OrderedDict
import itertools
import sys

import backtesting as bt
from .utils.py3 import zip, string_types, with_metaclass


# 寻找类的所有基类，包括间接的基类，以及最终的顶层基类
#TODO
def findbases(kls, topclass):
    retval = list()
    for base in kls.__bases__:
        if issubclass(base, topclass):
            retval.extend(findbases(base, topclass))
            retval.append(base)
    
    return retval


def findowner(owned, cls, startlevel=2, skip=None):
    # 在堆栈帧中查找拥有特定类实例的对象（通常是类的拥有者）
    # 从指定的帧级别开始查找，可以跳过特定的对象
    # 帧级别从2开始，跳过当前帧和调用者的帧
    # 通过迭代器itertool.count循环调用sys模块的_getframe函数依次获取调用栈第startlevel层至底层的栈帧。
    
    for framelevel in itertools.count(startlevel):
        try:
            frame = sys._getframe(framelevel)
        except ValueError:
            # 帧深度超出范围...没有拥有者...跳出循环
            break
        # 在每层栈帧的局部名称空间中搜寻名称为"self"的变量，若该变量同时满足三个条件：
        # 不是skip，
        # 不是owned，
        # 属于cls类
        # 则findowner函数返回该变量
        #TODO
        self_ = frame.f_locals.get('self', None)
        if skip is not self_:
            if self_ is not owned and isinstance(self_, cls):
                return self_
            
        # 在元类中查找 '_obj'
        # 除了将搜寻的变量名称改为"_obj"，其余代码同之前一样
        #TODO
        obj_ = frame.f_locals.get('_obj', None)
        if skip is not obj_:
            if obj_ is not owned and isinstance(obj_, cls):
                return obj_
        
    # 如果没有找到符合要求的变量，findowner函数返回None
    return None


class MetaBase(type):
    '''
    在MetaBase的__call__方法中，除了创建对象、初始化对象以及返回对象这些最为基础的事情
    重点是将对象的创建和初始化拆分为:
    创建前、创建中、初始化前、初始化中、初始化后五个步骤
    分别由下面五个方法所管控：
    (1)doprenew：cls创建对象前，当前什么也没做；
    (2)donew：调用cls的__new__方法创建对象_obj；
    (3)dopreinit：_obj初始化前，当前什么也没做；
    (4)doinit：调用_obj的__init__方法进行初始化；
    (5)dopostinit：_obj初始化后，当前什么也没做
    '''
    def doprenew(cls, *args, **kwargs):
        return cls, args, kwargs

    def donew(cls, *args, **kwargs):
        _obj = cls.__new__(cls, *args, **kwargs)
        return _obj, args, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
        return _obj, args, kwargs

    def doinit(cls, _obj, *args, **kwargs):
        _obj.__init__(*args, **kwargs)
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        return _obj, args, kwargs

    def __call__(cls, *args, **kwargs):
        cls, args, kwargs = cls.doprenew(*args, **kwargs)
        _obj, args, kwargs = cls.donew(*args, **kwargs)
        _obj, args, kwargs = cls.dopreinit(_obj, *args, **kwargs)
        _obj, args, kwargs = cls.doinit(_obj, *args, **kwargs)
        _obj, args, kwargs = cls.dopostinit(_obj, *args, **kwargs)
        return _obj


class AutoInfoClass(object):
    '''
    对有序字典OrderedDict的封装，实现了一些方法，比如获取参数的默认值、获取参数的键值对等
    具体而言，每一个AutoInfoClass类都封装着两个OrderedDict对象，分别可以通过类方法_getpairsbase和_getpairs获取
    （1）params所属类的名称以AutoInfoClass开头，并以下划线依次连接继承链上的类名
    （2）params调用_getpairsbase返回包含当前类所有父类参数信息的OrderedDict；
    （3）params调用_getpairs返回包含当前类和当前类所有父类参数信息的OrderedDict。
    '''
    _getpairsbase = classmethod(lambda cls: OrderedDict())
    _getpairs = classmethod(lambda cls: OrderedDict())
    _getrecurse = classmethod(lambda cls: False)

    @classmethod
    def _derive(cls, name, info, otherbases, recurse=False):
        # 通过_getpairs方法获取了类cls提供的所有参数信息，并将其赋值给变量baseinfo
        baseinfo = cls._getpairs().copy()
        # 变量obasesinfo起初是一个空的OrderedDict对象
        obasesinfo = OrderedDict()
        # 依次获取otherbases中的类提供的参数信息，并顺次更新obasesinfo
        # 调用有序字典的update方法
        # 该方法可以让一个元组 (该元组的元素为键值对构成的元组)、字典或者有序字典中所包含的键值对去更新己有字典
        # 遵循的原则是：如果遇到重复的键则覆盖对应的值，如果没有遇到重复的键则添加键值对。
        # 如果涉及多继承，顺位靠后父类的参数信息会更新顺位靠前父类的参数信息(如果不是万不得已，不要使用多继承)
        #TODO 
        for obase in otherbases:
            if isinstance(obase, (tuple, dict)):
                obasesinfo.update(obase)
            else:
                obasesinfo.update(obase._getpairs())
            

         # 用otherbases提供的参数信息obasesinfo去更新类cls提供的参数信息baseinfo
        # 从而，baseinfo完成了类cls和otherbases参数信息的整合
        baseinfo.update(obasesinfo)

        
        # 变量clsinfo起初被赋值类cls和otherbases参数信息baseinfo的复制。
        # 接下来，用提供的参数信息info去更新类clsinfo
        # 从而，clsinfo完成了类cls、info和otherbases的参数信息的整合
        # 子类的参数信息会更新父类的参数信息
        clsinfo = baseinfo.copy()
        clsinfo.update(info)

        # 这个变量保存了除了cls之外所需要添加的参数信息，包括otherbases和info中的参数信息
        info2add = obasesinfo.copy()
        info2add.update(info)
        # derive方法的返回值是一个类，这几行代码完成了对这个类的取名和创建的工作
        # 这里的cls取值为AutoInfoClass类，那么，变量clsmodule则被赋值AutoInfoClass类所在的模块，也就是metabase模块
        # 暂定一个类名，构成方法是cls的类名 (取值'AutoInfoClass') 和参数name通过下划线的拼接，即'AutoInfoClass_name'，并赋值给变量newclsname
        clsmodule = sys.modules[cls.__module__]
        newclsname = str(cls.__name__ + '_' + name)  

        # 在clsmodule中搜寻是否已经对名为newclsname的变量进行了定义：如果有，则通过while循环在newclsname后依次添加正自然数列的元素构成新的newclsname，直至clsmodule中没有对名为newclsname的变量进行过定义；
        namecounter = 1
        

        # 由type创建一个类名为newclsname，父类为cls的类，赋值给newcls，并在模块clsmodule中将名为newclsname的变量定义为newcls
        newcls = type(newclsname, (cls,), {})
        setattr(clsmodule, newclsname, newcls)
        # 为新创建的类newcls添加类方法_getpairsbase和_getpairs
        # 返回值分别为生成的变量baseinfo和clsinfo
        setattr(newcls, '_getpairsbase',
                classmethod(lambda cls: baseinfo.copy()))
        setattr(newcls, '_getpairs', classmethod(lambda cls: clsinfo.copy()))
        setattr(newcls, '_getrecurse', classmethod(lambda cls: recurse))

        for infoname, infoval in info2add.items():
            if recurse:
                recursecls = getattr(newcls, infoname, AutoInfoClass)
                infoval = recursecls._derive(name + '_' + infoname,
                                             infoval,
                                             [])

            setattr(newcls, infoname, infoval)

        #将在以上步骤中创建并修改后的newcls返回
        return newcls

    # 用以判断是否存在修改默认参数值的情形
    def isdefault(self, pname):
        return self._get(pname) == self._getkwargsdefault()[pname]

    # 用以判断是否存在修改默认参数值的情形
    def notdefault(self, pname):
        return self._get(pname) != self._getkwargsdefault()[pname]

    def _get(self, name, default=None):
        return getattr(self, name, default)

    # 以列表返回cls.params中包含的参数信息
    @classmethod
    def _getkwargsdefault(cls):
        return cls._getpairs()

    @classmethod
    def _getkeys(cls):
        return cls._getpairs().keys()

    @classmethod
    def _getdefaults(cls):
        return list(cls._getpairs().values())

    @classmethod
    def _getitems(cls):
        return cls._getpairs().items()

    @classmethod
    def _gettuple(cls):
        return tuple(cls._getpairs().items())

    def _getkwargs(self, skip_=False):
        l = [
            (x, getattr(self, x))
            for x in self._getkeys() if not skip_ or not x.startswith('_')]
        return OrderedDict(l)

    def _getvalues(self):
        return [getattr(self, x) for x in self._getkeys()]

    def __new__(cls, *args, **kwargs):
        obj = super(AutoInfoClass, cls).__new__(cls, *args, **kwargs)

        if cls._getrecurse():
            for infoname in obj._getkeys():
                recursecls = getattr(cls, infoname)
                setattr(obj, infoname, recursecls())

        return obj


class MetaParams(MetaBase):
    '''MetaParams也是一个元类。MetaParams重写了__new__方法和donew方法，实现的功能是参数整合。
        我们的回测系统中参数通过类变量params来设定，参数的形式可以是字典或者是元组
        还有一个不太常用的功能：动态加载包和模块
        在创建类的过程中，MetaParams的__new__方法会对继承链上所有类变量packages和frompackages中所包含的信息进行整合
    '''
    def __new__(meta, name, bases, dct):
        '''
        meta接受元类MetaParams；
        name接受类的类名，如字符串'MyClass'；
        bases接受类的父类组成的元组；
        dct接受类的属性名或方法名为键，对应的属性值或函数为值所组成的字典；
        
        (1)将类变量params从字典或元组转化为AutoInfoClass类
        (2)加工后的类变量params不仅囊括当前类中params所包含的参数信息，还整合了它所有父类的params所包含的参数信息
        '''
        
        # 从字典dct中将键'params'剥离出来，并其将对应的值赋值给变量newparams
        newparams = dct.pop('params', ())

        # 通过类变量packages和frompackages以元组的形式来设定拟加载的包和模块的名称及其别名
        packs = 'packages'
        newpackages = tuple(dct.pop(packs, ()))   #删除类定义中的packages，避免继承

        fpacks = 'frompackages'
        fnewpackages = tuple(dct.pop(fpacks, ()))  # 删除类定义中的frompackages，避免继承

        
        # 调用MetaParams的父类type的__new__方法创建一个新的类cls
        # 使用的参数为meta，name，bases和的dct，注意这里的dct已经剔除了键'params'
        cls = super(MetaParams, meta).__new__(meta, name, bases, dct)

        # 获取类的params，因为之前弹出来，所以没有，接下来会去类cls的父类中继续搜寻params属性
        # 如果还是没有，返回默认值：一个初始的AutoInfoClass类，并将其赋值给变量params
        # params含义是类MyClass1第一顺位父类提供的参数信息的封装
        params = getattr(cls, 'params', AutoInfoClass)

        # 获取类的参数类的参数
        packages = tuple(getattr(cls, packs, ()))
        fpackages = tuple(getattr(cls, fpacks, ()))

        # 依次在类cls除了第一顺位以外其它父类中搜寻params属性，并顺次放入列表中
        # 含义是一个列表，其元素依次是类除了第一顺位以外其它父类提供的参数信息
        morebasesparams = [x.params for x in bases[1:] if hasattr(x, 'params')]

        # 继承父类的包
        for y in [x.packages for x in bases[1:] if hasattr(x, packs)]:
            packages += tuple(y)

        for y in [x.frompackages for x in bases[1:] if hasattr(x, fpacks)]:
            fpackages += tuple(y)

        cls.packages = packages + newpackages
        cls.frompackages = fpackages + fnewpackages

        # 变量params调用_derive方法，返回值是AutoInfoClass类的子类，并将该返回值赋值给类cls的类变量params
        # _derive方法是AutoInfoClass类的类方法，也是元类MetaPrams实现参数整合功能的核心
        # 赋值运算符左右两边的params代表不同的含义：右边的params是之前生成的变量，它是一个AutoInfoClass类；左边的params是类cls动态创建的类变量
        cls.params = params._derive(name, newparams, morebasesparams)

        # 将在以上步骤中创建并修改后的cls返回
        return cls

    def donew(cls, *args, **kwargs):
        '''
        元类MetaParams的donew方法是对元类MetaBase的donew方法的重写
        实现了以下与参数相关的功能：
        (0)假设类Cls由元类MetaParams及其子类所创建，对象obj由类Cls所创建
        (1)MetaParams的donew方法，除了实现父类MetaBase的donew方法中Cls创建obj的基础功能之外，还为obj添加了实例属性params：
        (2)它承接了类Cls的类变量params中的参数信息，同时也接受在创建对象obj时输入的关键字参数的修改
        '''
        clsmod = sys.modules[cls.__module__]
        
        for p in cls.packages:
            if isinstance(p, (tuple, list)):
                p, palias = p
            else:
                palias = p

            pmod = __import__(p)

            plevels = p.split('.')
            if p == palias and len(plevels) > 1:  
                setattr(clsmod, pmod.__name__, pmod)  

            else:  
                for plevel in plevels[1:]:  
                    pmod = getattr(pmod, plevel)

                setattr(clsmod, palias, pmod)

        
        for p, frompackage in cls.frompackages:
            if isinstance(frompackage, string_types):
                frompackage = (frompackage,)  

            for fp in frompackage:
                if isinstance(fp, (tuple, list)):
                    fp, falias = fp
                else:
                    fp, falias = fp, fp  

                
                pmod = __import__(p, fromlist=[str(fp)])
                pattr = getattr(pmod, fp)
                setattr(clsmod, falias, pattr)
                for basecls in cls.__bases__:
                    setattr(sys.modules[basecls.__module__], falias, pattr)

        # cls.params已经是被元类MetaParams的__new__方法加工后的产物AutoInfoClass类
        # cls.params() 是AutoInfoClass类的实例对象，在这里赋值给变量params
        params = cls.params()
        # cls.params._getitems() 以列表返回cls.params中包含的参数信息,供pname和pdef遍历参数名和参数值
        # 通过setattr函数为变量params依次添加实例属性：
        # 属性名为pname；如果关键字参数kwargs中包含键pname，属性值为kwargs中键pname对应的值；否则，属性值为pdef
        for pname, pdef in cls.params._getitems():
            setattr(params, pname, kwargs.pop(pname, pdef))
        # 交给MetaParams的父类MetaBase完成由cls创建实例对象_obj的基础工作
        _obj, args, kwargs = super(MetaParams, cls).donew(*args, **kwargs)
        # 接下来，为_obj添加实例属性params
        _obj.params = params
        # 同时为_obj添加实例属性p，作用为实例属性params的别名
        _obj.p = params  
        
        return _obj, args, kwargs


class ParamsBase(with_metaclass(MetaParams, object)):
    pass  


class ItemCollection(object):
    def __init__(self):
        self._items = list()
        self._names = list()

    def __len__(self):
        return len(self._items)

    def append(self, item, name=None):
        setattr(self, name, item)
        self._items.append(item)
        if name:
            self._names.append(name)

    def __getitem__(self, key):
        return self._items[key]

    def getnames(self):
        return self._names

    def getitems(self):
        return zip(self._names, self._items)

    def getbyname(self, name):
        idx = self._names.index(name)
        return self._items[idx]