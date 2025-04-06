import mysql.connector
from decimal import Decimal
from .Class_Valve import ValveData
from .DataProcessing import *

config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'valve'
}


def mysql_get_prediction_data(config, valve_id=None) -> list[ValveData]:
    """获取指定阀门未更新的预测数据"""
    try:
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor(dictionary=True)
        valve_data_list = []

        # 修改查询逻辑，支持指定阀门
        query = "SELECT Valve_Id, P_Timestamp, W_Timestamp FROM Valve_Timestamp"
        params = []
        if valve_id:
            query += " WHERE Valve_Id = %s"
            params.append(valve_id)

        mycursor.execute(query, params)
        results = mycursor.fetchall()

        for row in results:
            current_valve_id = row['Valve_Id']
            # 当指定阀门时跳过其他阀门
            if valve_id and current_valve_id != valve_id:
                continue

            p_timestamp = row['P_Timestamp']
            w_timestamp = row['W_Timestamp']

            if p_timestamp < w_timestamp:
                valve_data = ValveData(current_valve_id)
                sql = """SELECT Date, Time, Timestamp, SP, PV, OP 
                          FROM Valve_Data 
                          WHERE Valve_Id = %s AND Timestamp > %s"""
                mycursor.execute(sql, (current_valve_id, p_timestamp))

                for data_row in mycursor:
                    valve_data.add_entry(
                        str(data_row['Date']),
                        str(data_row['Time']),
                        float(data_row['SP']),
                        float(data_row['PV']),
                        float(data_row['OP'])
                    )

                if valve_data.dataSize > 0:
                    valve_data_list.append(valve_data)

        return valve_data_list

    except mysql.connector.Error as err:
        print(f"获取预测数据出错: {err}")
        return []
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()


def mysql_save_prediction_data(valve_data: ValveData, config, mod_version=0):
    """
    将预测数据存储到数据库并更新Valve_Timestamp表。
    """
    if not valve_data or not hasattr(valve_data, 'get_all_entries'):
        print("错误：无效的阀门数据对象")
        return

    try:
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()

        all_entries = valve_data.get_all_entries()

        for entry in all_entries:
            # 确保所有数值类型正确
            sql = """
                INSERT INTO Valve_Data_Pre
                (Valve_Id, Timestamp, PV, OP, Mod_Version)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    PV = VALUES(PV),
                    OP = VALUES(OP),
                    Mod_Version = VALUES(Mod_Version)
            """
            val = (
                valve_data.valveId,
                float(entry['Timestamp']),
                float(entry['ValveFlowRate']),
                float(entry['ValveOpening']),
                int(mod_version)
            )
            mycursor.execute(sql, val)

            # 使用最大时间戳更新
            update_sql = """
                UPDATE Valve_Timestamp
                SET P_Timestamp = GREATEST(P_Timestamp, %s)
                WHERE Valve_Id = %s
            """
            mycursor.execute(update_sql, (entry['Timestamp'], valve_data.valveId))

        mydb.commit()

    except mysql.connector.Error as err:
        print(f"保存预测数据出错: {err}")
        mydb.rollback()

    except Exception as e:
        print(f"发生未知错误: {str(e)}")
        mydb.rollback()

    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()