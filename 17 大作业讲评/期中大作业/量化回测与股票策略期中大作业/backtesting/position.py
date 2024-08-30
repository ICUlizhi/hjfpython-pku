from copy import copy

# Position类，保持和更新持仓的大小和价格，和其他的任何资产没有关系，它仅仅保存大小和价格
class Position(object):
    '''
    position具有两个属性值，一个是size，代表当前持仓大小；一个是价格，代表当前持仓的价格。
    position的实例可以通过len(position)来判断size是否是空的
    '''
    # 打印position的时候可以显示的信息
    def __str__(self):
        items = list()
        items.append('--- Position Begin')
        items.append('- Size: {}'.format(self.size))
        items.append('- Price: {}'.format(self.price))
        items.append('- Price orig: {}'.format(self.price_orig))
        items.append('- Closed: {}'.format(self.upclosed))
        items.append('- Opened: {}'.format(self.upopened))
        items.append('- Adjbase: {}'.format(self.adjbase))
        items.append('--- Position End')
        return '\n'.join(items)

    # 根据size和price的不同进行初始化
    def __init__(self, size=0, price=0.0):
        self.size = size
        if size:
            self.price = self.price_orig = price
        else:
            self.price = 0.0

        self.adjbase = None

        self.upopened = size
        self.upclosed = 0
        self.set(size, price)

        self.updt = None

    # 修改position的size和price
    def fix(self, size, price):
        oldsize = self.size
        self.size = size
        self.price = price
        return self.size == oldsize
    # 设置position的size和price
    def set(self, size, price):
        # 如果现在的持仓大于0,并且理论上的size大于当前的size，就意味着要新开仓；
        # 如果理论上的size小于等于当前的持仓，那么开仓量是0和理论上size的最小量；
        # 平仓量等于当前持仓和当前持仓减去理论持仓量最小的一个值
        if self.size > 0:
            if size > self.size:
                self.upopened = size - self.size  # new 10 - old 5 -> 5
                self.upclosed = 0
            else:
                # same side min(0, 3) -> 0 / reversal min(0, -3) -> -3
                self.upopened = min(0, size)
                # same side min(10, 10 - 5) -> 5
                # reversal min(10, 10 - -5) -> min(10, 15) -> 10
                self.upclosed = min(self.size, self.size - size)
        # 当前持仓小于0的时候，有类似的效果
        elif self.size < 0:
            if size < self.size:
                self.upopened = size - self.size  
                self.upclosed = 0
            else:
                self.upopened = max(0, size)
                self.upclosed = max(self.size, self.size - size)
        # 如果当前持仓等于0，新开仓和平仓都等于0
        else:  
            self.upopened = self.size
            self.upclosed = 0
        # 实际持仓大小
        self.size = size
        # 原始价格
        self.price_orig = self.price
        # 如果持仓大小大于0的话，当前价格就等于price，否则当前价格等于0
        if size:
            self.price = price
        else:
            self.price = 0.0

        return self.size, self.price, self.upopened, self.upclosed
    # 调用len(position)的时候，返回持仓的绝对值
    def __len__(self):
        return abs(self.size)
    # 调用bool(position)判断当前size是否等于0
    def __bool__(self):
        return bool(self.size != 0)

    __nonzero__ = __bool__

    # 克隆持仓信息
    def clone(self):
        return Position(size=self.size, price=self.price)

    # 创建一个position实例，然后更新size和价格
    def pseudoupdate(self, size, price):
        return Position(self.size, self.price).update(size, price)

    # 更新size和price
    def update(self, size, price, dt=None):
        '''
        更新当前的持仓和返回更新后的大小、价格和需要开仓和平仓的头寸大小

        Args:
            size (int): 
            更新持仓大小的量，如果size小于0,将会发出一个卖操作，如果size大于0,将会发生一个买操作
            price (float):
            价格，必须总是正数以保持持续性

        Returns:
            # 结果将会返回一个元组，包含下面的一些数据：
            # size 代表新的持仓大小，仅仅是已经有的持仓的大小加上新的持仓增量
            # price 代表新的持仓价格，根据持仓的不同，返回不同的价格
            # opened 代表需要新开的仓位
            # closed 代表需要平仓的仓位
        '''
        # 更新持仓的时间
        self.datetime = dt  # record datetime update (datetime.datetime)
        # 原始的价格
        self.price_orig = self.price
        # 旧的持仓大小
        oldsize = self.size
        # 新的持仓大小
        self.size += size
        # 如果size是0的话
        if not self.size:
            # Update closed existing position
            # 更新开仓、平仓和价格
            opened, closed = 0, size
            self.price = 0.0
        # 如果position的持仓是0的话，需要开仓size的量
        elif not oldsize:
            # Update opened a position from 0
            opened, closed = size, 0
            self.price = price
        # 如果原先position的持仓是0的话
        elif oldsize > 0:  # existing "long" position updated
            # 如果增加的仓位大于0,那么就需要新开仓，并且计算平均持仓价格
            if size > 0:  # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size
            # 如果平掉size之后，持仓仍然大于0,那么就平仓size
            elif self.size > 0:  # reduced position
                opened, closed = 0, size
                # self.price = self.price
            # 其他情况下，就需要开仓self.size,平仓-oldsize
            else:  # self.size < 0 # reversed position form plus to minus
                opened, closed = self.size, -oldsize
                self.price = price
        # 原有的持仓是负数
        else:  # oldsize < 0 - existing short position updated
            # 如果新增加的仓位也是负数，那么就新开size
            if size < 0:  # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size
            # 如果当前self.size小于0,平仓size
            elif self.size < 0:  # reduced position
                opened, closed = 0, size
                # self.price = self.price
            # 其他情况下，就需要开仓self.size,平仓-oldsize
            else:  # self.size > 0 - reversed position from minus to plus
                opened, closed = self.size, -oldsize
                self.price = price
        # 开仓和平仓量
        self.upopened = opened
        self.upclosed = closed

        return self.size, self.price, opened, closed