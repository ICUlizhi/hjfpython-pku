import nest_asyncio
nest_asyncio.apply() 
# 这是为了在Jupyter Notebook中能够顺利运行代码
# 无需理解其具体含义

import asyncio, random

async def factory(transfer_center, products):
    '''
    参数说明：
        - transfer_center: 是一个Queue, 用于模拟转运中心
        - products: 是一个元素为str的列表, 表示工厂所需生产的所有产品名称
    '''

    ###############################
    #--- Your code starts here ---#
    ###############################

    for product in products:
        await transfer_center.put(product)
        await asyncio.sleep(random.randint(1, 3))
    

    ###############################
    #---  Your code ends here  ---#
    ###############################
    
    print('工厂生产完毕')
    await transfer_center.join()
    

async def supermarket(transfer_center):

    while True:

        ###############################
        #--- Your code starts here ---#
        ###############################

        # TODO: 模仿课件上的例子，补充作为消费者的supermarket的行为
        # 对每一个产品，
        #       1. 生成1~3秒的随机数表示接收用时，使用asyncio.sleep模拟接受过程
        #       2. 打印下面这句话："超市接收：<产品名字>"
        #       3. 从转运中心获取产品
        # 请注意添加退出循环的判断条件
        
        try:
            product = await transfer_center.get()
            print(f'超市接收：{product}')
            await asyncio.sleep(random.randint(1, 3))
            transfer_center.task_done()
        except asyncio.CancelledError:
            break
        
        ###############################
        #---  Your code ends here  ---#
        ###############################

    print('超市接收完毕')


transfer_center = asyncio.Queue()

factory_crt = factory(transfer_center, ['商品' + str(i) for i in range(1, 11)])
supermarket_crt = supermarket(transfer_center)

loop = asyncio.get_event_loop()
tasks = [asyncio.create_task(factory_crt), asyncio.create_task(supermarket_crt)]
_ = loop.run_until_complete(asyncio.wait(tasks))

# 以上实现的是工厂生产用时与超市接受用时均值相同时的情况
# 观察输出，可以发现工厂和超市的输出是近似交替出现的
# 可以思考一下当生产用时大于/小于接受用时的时候，输出情况将会如何
# 可以修改上面代码中随机生成时间的范围并运行，验证你的猜想