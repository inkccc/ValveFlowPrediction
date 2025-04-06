"""
处理数据的类
"""

import os
from .Class_Valve import ValveData

class GetData:
    @staticmethod
    def FileType1(file_path):
        """
        打开文件并读取数据到 ValveData 类。
        参数:
            file_path (str): 文件的绝对路径。
        返回:
            ValveData: 包含文件数据的阀门数据类。
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件路径无效: {file_path}")

        # 提取文件名作为阀门编号
        file_name = os.path.basename(file_path)
        valve_id = os.path.splitext(file_name)[0].split('.')[0]  # 移除扩展名
        valve_data = ValveData(valve_id)

        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            # 清除行尾的换行符并按制表符分割
            fields = line.strip().split('\t')

            # 跳过标题行
            if i == 0 and fields[0].lower() == "date":
                continue

            try:
                # 按列解析并添加数据
                date, time, sp, pv, op = fields[:5]
                sp, pv, op = float(sp), float(pv), float(op)
                valve_data.add_entry(date, time, sp, pv, op)
            except (ValueError, IndexError) as e:
                pass
                #print(f"跳过无效数据行 {i + 1}: {line.strip()} ({e})")

        valve_data.sort_by_timestamp()
        return valve_data

def Data_homogenization_SegmentedResampling(valve_data:ValveData, segments, target_count):
    """
    对阀门数据进行分段和重采样。

    参数:
        valve_data (ValveData): 包含阀门数据的对象。
        segments (int): 分段数量。
        target_count (int): 每个分段需要达到的数据量。

    返回:
        ValveData: 重采样后的阀门数据类。
    """
    # 提取原始数据
    entries = valve_data.get_all_entries()
    entries.sort(key=lambda x: x['Timestamp'])  # 按时间戳排序

    # 获取最大和最小开度
    max_op = max(entry['ValveOpening'] for entry in entries)
    min_op = min(entry['ValveOpening'] for entry in entries)

    # 计算每个分段的范围
    step = (max_op - min_op) / segments
    ranges = [(min_op + i * step, min_op + (i + 1) * step) for i in range(segments)]

    # 按分段划分数据
    segmented_data = [[] for _ in range(segments)]
    for entry in entries:
        for i, (low, high) in enumerate(ranges):
            if low <= entry['ValveOpening'] <= high:
                segmented_data[i].append(entry)
                break

    # 重采样
    resampled_data = []
    for segment in segmented_data:
        if len(segment) < target_count:
            # 数据不足时，重复数据到目标数量
            multiplier = (target_count + len(segment) - 1) // len(segment)
            extended_segment = segment * multiplier
            resampled_segment = extended_segment[:target_count]
        else:
            # 数据过多时，均匀抽取到目标数量
            step = len(segment) / target_count
            resampled_segment = [segment[int(i * step)] for i in range(target_count)]

        resampled_data.extend(resampled_segment)

    # 按时间戳排序
    resampled_data.sort(key=lambda x: x['Timestamp'])

    # 创建新的 ValveData 对象
    new_valve_data = ValveData(valve_data.valveId)
    for entry in resampled_data:
        new_valve_data.add_entry(
            entry['Date'],
            entry['Time'],
            entry['SetValveFlowRate'],
            entry['ValveFlowRate'],
            entry['ValveOpening']
        )

    return new_valve_data

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error

def find_best_model(opening, flow):
    """
    拟合五种回归模型，并返回 MAE 最小的模型的 equation 列表。

    Args:
        opening: 阀门开度列表。
        flow: 阀门流量列表。

    Returns:
        MAE 最小的模型的 equation 列表。
    """

    opening = np.array(opening).reshape(-1, 1)  # 将开度转换为二维数组，sklearn要求
    flow = np.array(flow)

    best_mae = float('inf')  # 初始化最佳 MAE 为无穷大，用于比较
    best_equation = None

    # 定义要拟合的模型列表，包含模型对象和模型类型编号
    models = [
        (LinearRegression(fit_intercept=False), 1),  # 线性回归 (y = kx)
        (LinearRegression(), 2),  # 带截距线性回归 (y = kx + b)
        (PolynomialFeatures(degree=2), 3),  # 二次回归 (y = ax² + bx + c)
        (PolynomialFeatures(degree=3), 4),  # 三次回归 (y = ax³ + bx² + cx + d)
        (PolynomialFeatures(degree=4), 5)  # 四次回归 (y = ax⁴ + bx³ + cx² + dx + e)
    ]

    for model, model_type in models:
        if isinstance(model, PolynomialFeatures):  # 如果是多项式回归，需要先进行特征转换
            opening_poly = model.fit_transform(opening)  # 生成多项式特征
            reg = LinearRegression()  # 使用线性回归器拟合多项式特征
            reg.fit(opening_poly, flow)
            predictions = reg.predict(opening_poly)  # 预测
            # 根据模型类型构建 equation 列表，注意系数的顺序
            if model_type == 3:
                equation = [2, reg.coef_[2], reg.coef_[1], reg.intercept_]
            elif model_type == 4:
                equation = [3, reg.coef_[3], reg.coef_[2], reg.coef_[1], reg.intercept_]
            else:
                equation = [4, reg.coef_[4], reg.coef_[3], reg.coef_[2], reg.coef_[1], reg.intercept_]

        else:  # 如果是线性回归，直接拟合
            reg = model
            reg.fit(opening, flow)
            predictions = reg.predict(opening)
            if model_type == 1:
                equation = [0, reg.coef_[0]]  # 没有截距
            else:
                equation = [1, reg.coef_[0], reg.intercept_]  # 有截距

        mae = mean_absolute_error(flow, predictions)  # 计算平均绝对误差

        if mae < best_mae:  # 如果当前模型的 MAE 更小，则更新最佳模型
            best_mae = mae
            best_equation = equation

    return best_equation

def equation_to_string(equation):
    """
    将 equation 列表转换为数学表达式字符串。

    Args:
        equation: equation 列表。

    Returns:
        数学表达式字符串。
    """
    model_type = equation[0]
    if model_type == 0:
        return f"y = {equation[1]:.2f}x"
    elif model_type == 1:
        return f"y = {equation[1]:.2f}x + {equation[2]:.2f}"
    elif model_type == 2:
        return f"y = {equation[1]:.2f}x² + {equation[2]:.2f}x + {equation[3]:.2f}"
    elif model_type == 3:
        return f"y = {equation[1]:.2f}x³ + {equation[2]:.2f}x² + {equation[3]:.2f}x + {equation[4]:.2f}"
    elif model_type == 4:
        return f"y = {equation[1]:.2f}x⁴ + {equation[2]:.2f}x³ + {equation[3]:.2f}x² + {equation[4]:.2f}x + {equation[5]:.2f}"
    else:
        return "未知模型类型"

def calculate_y(x, equation):
    """
    根据 x 和 equation 列表计算 y 值。

    Args:
        x: x 值。
        equation: equation 列表。

    Returns:
        计算得到的 y 值。如果模型类型未知，则返回 None。
    """
    model_type = equation[0]
    if model_type == 0:
        return equation[1] * x
    elif model_type == 1:
        return equation[1] * x + equation[2]
    elif model_type == 2:
        return equation[1] * x ** 2 + equation[2] * x + equation[3]
    elif model_type == 3:
        return equation[1] * x ** 3 + equation[2] * x ** 2 + equation[3] * x + equation[4]
    elif model_type == 4:
        return equation[1] * x ** 4 + equation[2] * x ** 3 + equation[3] * x ** 2 + equation[4] * x + equation[5]
    else:
        return None  # 处理未知模型类型

def predict_flow(valve_data, equation):
    """
    使用给定的 equation 预测阀门流量，并返回新的 ValveData 对象。

    Args:
        valve_data: 包含原始数据的 ValveData 对象。
        equation: 回归模型的 equation 列表。

    Returns:
        一个新的 ValveData 对象，其中阀门流量已根据 equation 预测更新。
        如果输入数据为空或出现其他错误，则返回 None。
    """
    if not valve_data.get_all_entries():
        print("输入阀门数据为空，无法进行预测。")
        return None

    try:
        new_valve_data = ValveData(valve_data.valveId)  # 创建新的 ValveData 对象

        openings = [entry["ValveOpening"] for entry in valve_data.get_all_entries()]
        dates = [entry["Date"] for entry in valve_data.get_all_entries()]
        times = [entry["Time"] for entry in valve_data.get_all_entries()]
        sps = [entry["SetValveFlowRate"] for entry in valve_data.get_all_entries()]
        # timestamps = [entry["Timestamp"] for entry in valve_data.get_all_entries()]

        predicted_flows = [calculate_y(opening, equation) for opening in openings]

        if None in predicted_flows:
            print("计算预测流量时出现错误，请检查模型类型是否正确。")
            return None

        for i in range(valve_data.dataSize):
            new_valve_data.add_entry(dates[i], times[i], sps[i], predicted_flows[i], openings[i])

        return new_valve_data

    except Exception as e:
        print(f"预测过程中发生错误：{e}")
        return None