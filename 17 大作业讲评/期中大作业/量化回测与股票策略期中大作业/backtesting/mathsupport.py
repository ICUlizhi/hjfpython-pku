import math


def average(x, bessel=False):
    '''
    参数:
      x: 长度已知的可迭代对象

      bessel: (默认为 ``False``) 是否使用贝塞尔校正，即在计算平均值时，将长度减一

    返回:
      x元素的平均值（浮点数）
    '''
    return math.fsum(x) / (len(x) - bessel)


def variance(x, avgx=None):
    '''
    参数:
      x: 长度已知的可迭代对象

    返回:
      x每个元素的方差列表
    '''
    if avgx is None:
        avgx = average(x)
    return [pow(y - avgx, 2.0) for y in x]


def standarddev(x, avgx=None, bessel=False):
    '''
    参数:
      x: 长度已知的可迭代对象

      bessel: (默认为 ``False``) 是否应用贝塞尔校正（Bessel's correction），即在计算平均值时除以 ``N - 1``

    返回:
      x元素的标准差（浮点数）
    '''
    return math.sqrt(average(variance(x, avgx), bessel=bessel))
