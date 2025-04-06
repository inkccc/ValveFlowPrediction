"""
阀门数据的类
"""

from datetime import datetime

class ValveData:
    def __init__(self, valve_id):
        """
        初始化阀门数据类
        参数:
            valve_id (str): 阀门编号
        """
        self.valveId = valve_id  # 公共变量，存储阀门编号
        self.__dates = []  # 私有列表，用于存储日期
        self.__times = []  # 私有列表，用于存储时间
        self.__timestamps = []  # 私有列表，用于存储时间戳
        self.__setValveFlowRate = []  # 私有列表，用于存储设定阀门流量
        self.__valveFlowRate = []  # 私有列表，用于存储阀门流量
        self.__valveOpening = []  # 私有列表，用于存储阀门开度
        self.dataSize = 0  # 数据条目数

    def add_entry(self, date, time, sp, pv, op):
        """
        添加新的数据条目
        参数:
            date (str): 日期，格式为"YYYY-MM-DD"
            time (str): 时间，格式为"HH:MM:SS"
            sp (float): 设定阀门流量
            pv (float): 阀门流量
            op (float): 阀门开度
        """
        timestamp = self.__generate_timestamp(date, time)  # 生成时间戳
        self.__dates.append(date)
        self.__times.append(time)
        self.__timestamps.append(timestamp)
        self.__setValveFlowRate.append(sp)
        self.__valveFlowRate.append(pv)
        self.__valveOpening.append(op)
        self.dataSize += 1

    def delete_entry(self, index):
        """
        删除指定索引的数据条目
        参数:
            index (int): 数据条目索引
        """
        if 0 <= index < self.dataSize:
            self.__dates.pop(index)
            self.__times.pop(index)
            self.__timestamps.pop(index)
            self.__setValveFlowRate.pop(index)
            self.__valveFlowRate.pop(index)
            self.__valveOpening.pop(index)
            self.dataSize -= 1
        else:
            raise IndexError("索引超出范围")

    def update_entry(self, index, date=None, time=None, sp=None, pv=None, op=None):
        """
        更新指定索引的数据条目
        参数:
            index (int): 数据条目索引
            date (str): 新的日期
            time (str): 新的时间
            sp (float): 新的设定阀门流量
            pv (float): 新的阀门流量
            op (float): 新的阀门开度
        """
        if 0 <= index < self.dataSize:
            if date is not None:
                self.__dates[index] = date
            if time is not None:
                self.__times[index] = time
            if date is not None or time is not None:
                self.__timestamps[index] = self.__generate_timestamp(self.__dates[index], self.__times[index])
            if sp is not None:
                self.__setValveFlowRate[index] = sp
            if pv is not None:
                self.__valveFlowRate[index] = pv
            if op is not None:
                self.__valveOpening[index] = op
        else:
            raise IndexError("索引超出范围")

    def get_entry(self, index):
        """
        获取指定索引的数据条目
        参数:
            index (int): 数据条目索引
        返回:
            dict: 包含日期、时间、时间戳、设定阀门流量、阀门流量和阀门开度的字典
        """
        if 0 <= index < self.dataSize:
            return {
                "Date": self.__dates[index],
                "Time": self.__times[index],
                "Timestamp": self.__timestamps[index],
                "SetValveFlowRate": self.__setValveFlowRate[index],
                "ValveFlowRate": self.__valveFlowRate[index],
                "ValveOpening": self.__valveOpening[index]
            }
        else:
            raise IndexError("索引超出范围")

    def get_all_entries(self):
        """
        获取所有数据条目
        返回:
            list: 包含所有数据条目的列表，每个条目是一个字典
        """
        return [
            {
                "Date": self.__dates[i],
                "Time": self.__times[i],
                "Timestamp": self.__timestamps[i],
                "SetValveFlowRate": self.__setValveFlowRate[i],
                "ValveFlowRate": self.__valveFlowRate[i],
                "ValveOpening": self.__valveOpening[i]
            } for i in range(self.dataSize)
        ]

    def get_valveOpening(self):
        return self.__valveOpening

    def get_valveFlowRate(self):
        return self.__valveFlowRate

    def sort_by_timestamp(self, ascending=True):
        """
        根据时间戳对所有数据条目进行排序。

        参数:
            ascending (bool, 可选): 是否升序排序，默认为 True (升序)。
                                     如果为 False，则降序排序。
        """
        # 使用 zip 将所有列表打包在一起，然后按时间戳排序
        combined = sorted(zip(self.__timestamps, self.__dates, self.__times,
                              self.__setValveFlowRate, self.__valveFlowRate,
                              self.__valveOpening), key=lambda x: x[0], reverse=not ascending)

        # 解包排序后的数据
        self.__timestamps, self.__dates, self.__times, self.__setValveFlowRate, \
            self.__valveFlowRate, self.__valveOpening = zip(*combined)

    @staticmethod
    def __generate_timestamp(date, time):
        """
        根据日期和时间生成时间戳
        参数:
            date (str): 日期，格式为"YYYY-MM-DD"
            time (str): 时间，格式为"HH:MM:SS"
        返回:
            float: 时间戳
        """
        datetime_str = f"{date} {time}"
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return datetime_obj.timestamp()

"""
样例数据
Date	Time	FIC207.PIDA.SP	FIC207.PIDA.PV	FIC207.PIDA.OP
2014-5-12	9:00:00	53.39	53.36	49.46	
2014-5-12	8:00:00	53.36	53.35	49.43	
2014-5-12	7:00:00	53.28	53.27	49.34	
2014-5-12	6:00:00	53.48	53.49	49.50	
2014-5-12	5:00:00	53.48	53.44	49.50	
2014-5-12	4:00:00	53.44	53.45	49.39	
2014-5-12	3:00:00	53.52	53.54	49.47	
"""