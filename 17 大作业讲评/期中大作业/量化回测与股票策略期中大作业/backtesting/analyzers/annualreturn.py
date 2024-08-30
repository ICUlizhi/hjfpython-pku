from collections import OrderedDict

from backtesting.utils.py3 import range
from backtesting import Analyzer


class AnnualReturn(Analyzer):
    '''
    This analyzer calculates the AnnualReturns by looking at the beginning
    and end of the year

    Params:

      - (None)

    Member Attributes:

      - ``rets``: list of calculated annual returns

      - ``ret``: dictionary (key: year) of annual returns

    **get_analysis**:

      - Returns a dictionary of annual returns (key: year)
    '''

    def stop(self):
        # Must have stats.broker
        cur_year = -1

        value_start = 0.0
        value_cur = 0.0
        value_end = 0.0

        self.rets = list()
        self.ret = OrderedDict()

        for i in range(len(self.data) - 1, -1, -1):
            dt = self.data.datetime.date(-i)
            value_cur = self.strategy.stats.broker.value[-i]

            if dt.year > cur_year:
                if cur_year >= 0:
                    annualret = (value_end / value_start) - 1.0
                    self.rets.append(annualret)
                    self.ret[cur_year] = annualret

                    # changing between real years, use last value as new start
                    value_start = value_end
                else:
                    # No value set whatsoever, use the currently loaded value
                    value_start = value_cur

                cur_year = dt.year

            # No matter what, the last value is always the last loaded value
            value_end = value_cur

        if cur_year not in self.ret:
            # finish calculating pending data
            annualret = (value_end / value_start) - 1.0
            self.rets.append(annualret)
            self.ret[cur_year] = annualret

    def get_analysis(self):
        return self.ret
      
      
class MyAnnualReturn(Analyzer):
    '''
    This analyzer calculates the AnnualReturns by looking at the beginning
    and end of the year

    Params:

      - (None)

    Member Attributes:

      - ``rets``: list of calculated annual returns

      - ``ret``: dictionary (key: year) of annual returns

    **get_analysis**:

      - Returns a dictionary of annual returns (key: year)
    '''

    def stop(self):
        # 保存数据的容器---字典
        self.ret =OrderedDict()
        # 获取数据的时间，并转化为date
        dt_list = self.data.datetime.get(0, size=len(self.data))
        dt_list =[num2date(i) for i in dt_list]
        # 获取账户的资产
        value_list = self.strategy.stats.broker.value.get(0, size=len(self.data))
        # 转化为pandas格式
        df = pd.DataFrame([dt_list,value_list]).T
        df.columns=['datetime','value']
        df['pre_value']=df['value'].shift(1)
        # 计算每年的持有获得的简单收益率
        df['year']=[i.year for i in df['datetime']]
        for year,data in df.groupby("year"):
          begin_value = list(data['pre_value'])[0]
          end_value = list(data['value'])[-1]
          annual_return = (end_value/begin_value)-1
          self.ret[year]=annual_return
        
    def get_analysis(self):
        return self.ret
