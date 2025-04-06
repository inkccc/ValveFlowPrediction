import numpy as np
import matplotlib.pyplot as plt
from .Class_Valve import ValveData
from .DataProcessing import *

def plot_op_pv(data:ValveData)->None:
    plt.scatter(data.get_valveOpening(),data.get_valveFlowRate(),color="red",s=1)
    plt.title(data.valveId)
    plt.xlabel("Opening")
    plt.ylabel("FlowRate")
    plt.grid(True)
    plt.show()

def plot_op_pv_curve(data:ValveData , precision=1e-3)->None:
    plt.scatter(data.get_valveOpening(), data.get_valveFlowRate(), color="red", s=1)
    plt.title(data.valveId)
    plt.xlabel("Opening")
    plt.ylabel("FlowRate")
    data_equation = find_best_model(data.get_valveOpening(), data.get_valveFlowRate())
    print(data.valveId+" - equation: "+equation_to_string(data_equation))
    # 使用 np.arange 生成 x 值序列，步长由精度控制
    x = np.arange(min(data.get_valveOpening()), max(data.get_valveOpening()) + precision, precision)  # 包含右端点
    y = [calculate_y(xi, data_equation) for xi in x]
    # 绘制曲线
    plt.plot(x, y)
    # 显示网格（可选）
    plt.grid(True)
    plt.show()