# Valve 项目文档

------

## 1. 项目背景与目标

### 背景

在化工工厂中，阀门是关键的设备之一。经过长时间的使用，阀门可能会出现老化、破损等问题，这些问题可能导致生产效率下降甚至安全隐患。为了确保化工工厂的安全和高效运行，必须对阀门的工作状态进行实时监控。

### 目标

本项目旨在通过分析阀门的历史数据（如阀门开度、流量等），构建一个预测模型，用于检测阀门是否正常工作。如果发现异常，系统将及时发出预警，并尝试诊断问题的原因，从而帮助工作人员快速排查和解决问题。

------

## 2. 项目实现方案

### 2.1 数据获取

#### 数据结构

每条阀门数据包含以下字段：

-   **ValveNumber** : 阀门编号（唯一标识）
-   **DataDate** : 数据日期
-   **DataTime** : 数据时间
-   **DataTimestamp** : 时间戳（由日期和时间计算得出）
-   **DataSP** : 阀门设定流量（预期流量）
-   **DataPV** : 阀门实际流量
-   **DataOP** : 阀门实际开度

#### 数据来源

我们将从化工工厂检修后的两个月内收集所有阀门的正常运行数据。这些数据是阀门在无故障状态下生成的，因此可以作为训练预测模型的基础。

#### 数据背景说明

在化工工厂中，阀门的流量通常由自动化系统控制，其中 PID 控制器是最常用的算法。控制器通过调节阀门开度，使实际流量（PV）尽可能接近设定流量（SP）。如果实际流量与设定流量之间的误差超出允许范围，可能表明阀门存在问题。

------

### 2.2 预测模型设计

#### 模型目标

基于历史数据，我们希望构建一个预测模型，能够根据当前阀门开度（OP）预测出对应的流量（PV）。在实际运行中，系统会将预测流量与实际流量进行比较：

-   如果两者差异在允许范围内，则认为阀门正常；
-   如果差异过大，则触发预警，提示可能存在故障。

#### 模型类型

我们设计了以下五种回归模型(后续可新增)：

1.  **线性回归** : *y*=*k**x*
2.  **截线性回归** : *y*=*k**x*+*b*
3.  **二次回归** : *y*=*a**x*2+*b**x*+*c*
4.  **三次回归** : *y*=*a**x*3+*b**x*2+*c**x*+*d*
5.  **四次回归** : *y*=*a**x*4+*b**x*3+*c**x*2+*d**x*+*e*

#### 模型存储方式

模型以 `vector<double>` 的形式存储，具体规则如下：

-   第一个元素表示模型类型（0 到 4 分别对应上述五种模型）；
-   后续元素依次存储模型的系数。

例如：

-   线性回归 *y*=*k**x*: `equation = {0, k}`
-   截线性回归 *y*=*k**x*+*b*: `equation = {1, k, b}`
-   二次回归 *y*=*a**x*2+*b**x*+*c*: `equation = {2, a, b, c}`

#### 模型评估方法

对于每个数据点，计算实际流量与模型预测流量之间的绝对误差，并对所有误差求和。总误差越小，模型的拟合效果越好。

#### 数据均匀化

为了避免数据分布不均导致模型偏向某些区域，我们引入了数据均匀化的方法：

1.  将阀门开度划分为若干段（`seg`），每段的目标数据量为 `count`。
2.  对于数据不足的段，采用**重采样** 补充数据；
3.  对于数据过多的段，采用**下采样** 减少数据。

------

### 2.3 数据库设计

#### 数据表结构

1.  **Valve_Info**
    -   记录阀门的基本信息。
    -   字段：`Valve_Id`
2.  **Valve_Data**
    -   存储阀门的实际运行数据。
    -   字段：`Valve_Id`, `Date`, `Time`, `Timestamp`, `SP`, `PV`, `OP`
3.  **Valve_Data_Pre**
    -   存储阀门的预测数据。
    -   字段：`Valve_Id`, `Timestamp`, `PV`, `OP`, `Mod_Version`
4.  **Valve_Mod**
    -   存储阀门的预测模型。(还没被用上)
    -   字段：`Valve_Id`, `Valve_OP_Min`, `Valve_OP_Max`, `Equation`, `Mod_Version`
5.  **Valve_Timestamp**
    -   记录各机器最后访问的时间戳。
    -   字段：`Valve_Id`, `W_Timestamp`（写入时间戳）, `P_Timestamp`（预测时间戳）, `R_Timestamp`（读取时间戳）

#### 数据库逻辑

1.  **数据写入**
    -   新数据写入时，首先检查 `Valve_Info` 中是否存在该 `Valve_Id`。若不存在，则新增记录。
    -   将数据写入 `Valve_Data` 表，并更新 `Valve_Timestamp` 中的 `W_Timestamp`。
2.  **数据预测**
    -   预测机器定期检查 `Valve_Timestamp`，若发现 `W_Timestamp > P_Timestamp`，则从 `Valve_Data` 中提取未预测的数据。
    -   使用 `Valve_Mod` 中的模型进行预测，并将结果写入 `Valve_Data_Pre`。
3.  **数据展示**
    -   Web 端从 `Valve_Timestamp` 中获取最新时间戳，并从 `Valve_Data` 和 `Valve_Data_Pre` 中提取对应数据，用于实时展示。

------

## 3. Web 实现

### 3.1 主界面设计

主界面包含以下功能：

-   **上传文件按钮** : 用户可通过此按钮上传阀门数据文件。
-   **阀门详情列表** : 展示所有阀门的基本信息，点击可进入详细页面。

### 3.2 子页面设计

子页面包含以下功能：

1.  **数据展示**
    -   使用 Apache ECharts 绘制折线散点图，横轴为时间戳，纵轴为流量值（包括实际数据和预测数据）。
    -   图表每秒自动刷新一次。
2.  **开始预测按钮**
    -   点击后触发预测流程，将未预测的数据提交至后端进行处理。

### 3.3 后端 API 设计

后端框架采用 Flask，并遵循 RESTful API 原则，提供以下接口：

1.  **上传数据**
    -   URL: `/upload`
    -   方法: `POST`
    -   功能: 接收用户上传的数据文件，并模拟实时写入数据库。
2.  **获取阀门数据**
    -   URL: `/api/data/<valve_id>`
    -   方法: `POST`
    -   功能: 根据 `valve_id` 返回该阀门的所有数据。
3.  **启动预测**
    -   URL: `/api/predict/<valve_id>`
    -   方法: `POST`
    -   功能: 根据指定的 `valve_id` 启动预测流程，并将结果写入数据库。

------

## 4. 未完待续...