import mysql.connector

from include.DataProcessing import predict_flow


def get_valves(config):
    """获取所有阀门列表"""
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT Valve_Id FROM Valve_Info")
        return [row['Valve_Id'] for row in cursor.fetchall()]
    except Exception as e:
        print(f"数据库查询失败: {str(e)}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_valve_info(config, valve_id):
    """获取单个阀门基本信息"""
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Valve_Info WHERE Valve_Id = %s", (valve_id,))
        return cursor.fetchone() or {}
    except Exception as e:
        print(f"阀门信息查询失败: {str(e)}")
        return {}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_recent_data(config, valve_id, limit=1000):
    """获取最新阀门数据"""
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)

        # 获取实际数据
        cursor.execute("""
            SELECT Timestamp, PV, OP 
            FROM Valve_Data 
            WHERE Valve_Id = %s 
            ORDER BY Timestamp DESC 
            LIMIT %s
        """, (valve_id, limit))
        actual = [{
            'timestamp': row['Timestamp'],
            'pv': float(row['PV']),
            'op': float(row['OP'])
        } for row in cursor.fetchall()]

        # 获取预测数据
        cursor.execute("""
            SELECT Timestamp, PV, OP 
            FROM Valve_Data_Pre 
            WHERE Valve_Id = %s 
            ORDER BY Timestamp DESC 
            LIMIT %s
        """, (valve_id, limit))
        predicted = [{
            'timestamp': row['Timestamp'],
            'pv': float(row['PV']),
            'op': float(row['OP'])
        } for row in cursor.fetchall()]

        return {
            'actual': actual,
            'predicted': predicted
        }
    except Exception as e:
        print(f"数据查询失败: {str(e)}")
        return {'actual': [], 'predicted': []}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def trigger_prediction(config, valve_id):
    """触发指定阀门的预测流程"""
    try:
        from include.Database_predicted_data import mysql_get_prediction_data, mysql_save_prediction_data
        from include.DataProcessing import find_best_model, Data_homogenization_SegmentedResampling

        # 获取需要预测的数据
        valve_data_list = mysql_get_prediction_data(config, valve_id)

        for valve_data in valve_data_list:
            # 数据均匀化处理
            homogenized_data = Data_homogenization_SegmentedResampling(
                valve_data,
                segments=10,
                target_count=1000
            )

            # 找到最佳模型
            equation = find_best_model(
                homogenized_data.get_valveOpening(),
                homogenized_data.get_valveFlowRate()
            )

            # 进行预测并保存
            predicted_data = predict_flow(valve_data, equation)
            if predicted_data:
                mysql_save_prediction_data(predicted_data, config)

        return True
    except Exception as e:
        print(f"预测过程出错: {str(e)}")
        return False