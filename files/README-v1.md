# Valve



1.  首先 介绍项目背景 和 项目需要做什么事

    -   这个项目的背景是 化工工厂的阀门 经过长时间的使用后 会出现老化 破损等问题
    -   这个项目的目的是 通过给定的阀门开度 和 阀门流量 等数据 检测阀门是否正常工作 如果出现了问题 能够及时预警 并检测出是什么原因

2.  然后 介绍项目具体要怎么做

    1.  首先 拿到数据

        我会得到化工工厂检修之后 两个月内 工厂内所有阀门的所有数据(不一定是两个月 但我们确定这些数据是在阀门正常运作下得到的数据 此时阀门没有出现任何问题)
        我来介绍一下这些数据的组成部分 拿单个阀门的单条数据来举例 ->

        1.  阀门编号ValveNumber(每个阀门都会有一个唯一的编号)
        2.  数据日期DataDate(该条数据在录入的时候的日期)
        3.  数据时间DataTime(该条数据在录入的时候的时间)
        4.  数据时间戳DataTimestamp(通过数据日期和数据时间 我们能计算出一个唯一的时间戳)
        5.  阀门设定流量DataSP(阀门预期流量)
        6.  阀门流量DataPV(阀门实际流量)
        7.  阀门开度DataOP(阀门实际开度)

        以上是单个阀门单条数据的构成
        接下来我简单介绍一下为什么会存在第五条数据 阀门设定流量
        在化工工厂中 阀门的流量通常由自动化系统完成 而PID控制器是其中最常用的一种算法 控制器通过调节控制信号使被控变量达到设定值 在拿到的数据中 控制器会通过调节阀门开度 使阀门流量达到流量设定值 如果实际流量小于设定流量 控制器会一直调节阀门开度 直到SP和PV在允许误差内

    2.  然后 预测模型

        我们能通过拿到的数据 可以通过阀门开度 阀门流量 得到一个预测模型 也就是在阀门开度x时 通过预测模型的计算 会得到一个阀门流量y

        接下来 我解释一下这个预测模型有什么作用 同时也是这个项目主要的内容

        我们拿到检修之后的阀门数据 我们通过这个阀门数据计算出一个预测模型 当化工工厂正常运作的时候 我们可以通过预测模型 预测出当前开度下的阀门流量 如果预测出来的阀门流量 和实际阀门流量在允许误差范围内 那我们认为这个阀门没有出现问题 如果预测流量和实际流量存在巨大误差 那可以基本确认 当前这个阀门可能是出现了某种故障 然后可以提出预警 让工作人员来排查问题(当然不排除预测模型比较差的情况 我们这里暂时先不考虑这种情况)

        这里 我介绍一下我们这个模型的设计 以及模型的运算方式

        根据给定的阀门开度和对应的阀门流量 我们能画出一个二维散点图

        然后我们使用线性回归的方法 计算出最后的预测模型

        1.  下面是目前设计的模型介绍 ->

            1.  线性回归 (y = kx)
            2.  截线性回归 (y = kx + b)
            3.  二次回归 (y = ax² + bx + c)
            4.  三次回归 (y = ax³ + bx² + cx + d)
            5.  四次回归 (y = ax⁴ + bx³ + cx² + dx + e)

        2.  下面是模型的存储方式介绍 ->

            equation 存储方式
            equation 是一个 vector\<double\>，用于存储回归模型的系数。
            第一个元素表示模型的类型（0 到 4 对应五种模型），
            后续元素依次存储该模型的系数。
            例如：

            1.  对于线性回归 y = kx：equation = {0, k}
            2.  对于带截线性回归 y = kx + b：equation = {1, k, b}
            3.  对于二次回归 y = ax² + bx + c：equation = {2, a, b, c}

        3.  下面是线性回归评估模型方式的介绍 ->

            对于每个数据点 计算实际阀门流量与回归模型预测的阀门流量之间的差值的绝对值 并对所有绝对值求和

            总和越小 表示模型的拟合度越好

        4.  下面是数据均匀化的介绍 ->

            前言 通过前几次的预测 发现 如果使用线性回归的方法 且 数据不均匀的情况下 举个例子 阀门开度0-50的数据点有50个 阀门开度50-100的数据点有50000个 这个时候 线性回归得到的模型 会优先拟合数据点多的部分 以至于数据点少的部分拟合不上 如果拿这样的预测模型去预测的话 会发现 当预测模型预测50-100开度下的流量的话 拟合效果会比较好 当预测模型预测0-50开度下的流量的话 拟合效果会很差

            这个时候 我们要通过数据均匀化的方法 让每一个开度段下的数据点分布均匀 这样 最终得到的预测模型 会在每个开度下 得到的阀门流量会比较均匀 不会存在 某个开度区间拟合效果特别好 某个开度区间拟合效果特别差的情况

            实现方法 目前设计的 数据均匀化的方法如下

            给定阀门数据ValveData 设定分段seg 预期数据量count

            通过阀门数据中的阀门开度 将阀门开度分为seg个开度段 每个开度段需要达到count的数据量

            如果当前开度段的数据量不足以达到预期数据量 则使用重采样的方法 将该开度段的数据重采样 直到达到预期数据量为止

            如果当前开度段的数据量大于预期数据量 则使用下采样的方法 通过按照固定间隔丢弃部分数据 来降低采样率 间隔可以通过预期数据量和开度段的实际数据量进行动态计算

        最后 我们会拿到一个预测模型

    3.  其次 数据库

        我们要将阀门数据 写入到数据库 实现预测端和数据端 Web端分离

        我先来简单介绍一下这个流程 假设我们现在有电脑A,B,C,D

        电脑A是数据库 用于存放数据

        电脑B是写入数据(将数据写入到A数据库中 模拟化工工厂实时写入数据)

        电脑C是预测数据(从A数据库中取出数据 和预测模型 根据预测模型对数据进行预测 将预测出来的数据写入到A数据库中)

        电脑D是Web端(从A数据库中取出数据 将实时数据和预测数据 在Web网页端实时呈现且实时更新)

        接下来是 数据库设计

        -   Valve_Info(主要记录阀门信息 以及阀门编号)
            -   Valve_Id
        -   Valve_Data(记录阀门实际数据)
            -   Valve_Id
            -   Date
            -   Time
            -   Timestamp
            -   SP
            -   PV
            -   OP
        -   Valve_Data_Pre(记录阀门预测数据)
            -   Valve_Id
            -   Timestamp
            -   PV
            -   OP
            -   Mod_Version
        -   Valve_Mod(记录阀门预测模型)
            -   Valve_Id
            -   Valve_OP_Min
            -   Valve_OP_Max
            -   Equation
            -   Mod_version
        -   Valve_Timestamp(记录写入数据和预测数据两个机器最后访问的数据 的时间戳)
            -   Valve_Id
            -   W_Timestamp (Write)
            -   P_Timestamp (Predict)
            -   R_Timestamp (Read)

    接下来介绍一下 数据库的逻辑

    当有新阀门数据要写入 会先在Valve_info里面查找 该Valve_Id是否存在 如果不存在 则写入Valve_Id 如果存在 则无需改动 然后到Valve_Data里 把所有数据写入 然后更新Valve_Timestamp里面的W_Timestamp为最新时间戳

    然后预测数据的机器 去Valve_Timestamp里面查找 如果发现有存在W_Timestamp大于P_Timestamp 则记录Valve_Id 和 P_Timestamp 然后到Valve_Data里面查找 所有Valve_Id相等 Timestamp大于P_timestamp的数据 然后到Valve_Mod中取出所有模型 根据模型对数据进行预测 然后把数据写入到Valve_Data_Pre里

    最后是Web端的机器 从Valve_Timestamp中取出Valve_Id 和 R_Timestamp 然后分别到 Valve_Data 和 Valve_Data_Pre中取出所有Valve_Id相同 时间戳大于R_Timestamp的所有数据 然后在Web端 使用 横轴是timestamp 纵轴是PV 的散点图 实时更新

3.  接下来是web的实现部分

    初步的web设计是 一个主界面 包含上传文件 并带有阀门详情

    详情点击进去可以加载详细信息 子页面需要包含开始预测的按钮

    后端框架使用的是Flask 并尽量遵循RESTful API的设计原则

    1.  首先需要获取数据

        主页面需要一个上传数据的按钮 后端需要一个接收数据的api

        /upload , methods=["POST"]

        后端获取到数据 需要间隔一秒将数据写入到数据库中去 -> 这里模拟实时写入的效果

        (未实现)

    2.  然后需要展示阀门数据

        子页面需要展示当前阀门的所有数据 -> 使用横轴为时间轴 纵轴为流量轴的折线散点图 包括实际数据和预测数据(如果有的话) 后端需要提供一个关于阀门id的api 根据阀门id返回所有数据

        /api/data/<valve_id> , methods=["POST"]

        后端接收post请求 返回该valve_id的所有数据

        子页面使用的是Apache的ECharts图标库来实现折线散点图(子页面每一秒会更新一次)

    3.  最后需要预测阀门数据

        子页面需要有一个"开始预测"的按钮 点击之后 和valve_id绑定 将该阀门未预测的数据 全部拿来预测 然后写入到预测数据库中

        /api/predict/<valve_id> , methods=["POST"]

        理论上应该有一个模型选择 -> 还没设计出来

    4.  未完待续...