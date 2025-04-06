import mysql.connector
from datetime import datetime
from .Class_Valve import ValveData
import time

def mysql_init(config):
    """
    初始化MySQL数据库，如果表存在则删除并重新创建。
    """
    try:
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()

        # 删除已存在的表 (如果存在)
        tables = ["Valve_Info", "Valve_Data", "Valve_Data_Pre", "Valve_Mod", "Valve_Timestamp"]
        for table in tables:
            try:
                mycursor.execute(f"DROP TABLE IF EXISTS {table}")
            except mysql.connector.Error as err:
                print(f"删除表 {table} 出错: {err}")

        # 创建新表
        mycursor.execute("""
            CREATE TABLE Valve_Info (
                Valve_Id VARCHAR(20) PRIMARY KEY
            )
        """)

        mycursor.execute("""
            CREATE TABLE Valve_Data (
                Valve_Id VARCHAR(20),
                Date DATE,
                Time TIME,
                Timestamp BIGINT,
                SP DECIMAL(10, 2),
                PV DECIMAL(10, 2),
                OP DECIMAL(10, 2),
                FOREIGN KEY (Valve_Id) REFERENCES Valve_Info(Valve_Id)
            )
        """)

        mycursor.execute("""
            CREATE TABLE Valve_Data_Pre (
                Valve_Id VARCHAR(20),
                Timestamp BIGINT,
                PV DECIMAL(10, 2),
                OP DECIMAL(10, 2),
                Mod_Version INT,
                FOREIGN KEY (Valve_Id) REFERENCES Valve_Info(Valve_Id)
            )
        """)

        mycursor.execute("""
            CREATE TABLE Valve_Mod (
                Valve_Id VARCHAR(20),
                Valve_OP_Min DECIMAL(10, 2),
                Valve_OP_Max DECIMAL(10, 2),
                Equation TEXT,  -- 可以存储JSON格式的模型参数
                Mod_version INT,
                FOREIGN KEY (Valve_Id) REFERENCES Valve_Info(Valve_Id)
            )
        """)

        mycursor.execute("""
            CREATE TABLE Valve_Timestamp (
                Valve_Id VARCHAR(20) PRIMARY KEY,
                W_Timestamp BIGINT DEFAULT 0,
                P_Timestamp BIGINT DEFAULT 0,
                R_Timestamp BIGINT DEFAULT 0,
                FOREIGN KEY (Valve_Id) REFERENCES Valve_Info(Valve_Id)
            )
        """)

        mydb.commit()
        print("数据库初始化完成")

    except mysql.connector.Error as err:
        print(f"数据库初始化出错: {err}")

    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()


def mysql_add_data(valve_data: ValveData, config, interval=0):
    """
    将ValveData对象的数据添加到MySQL数据库中。
    """

    try:
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()

        # 检查Valve_Id是否已存在于Valve_Info表中
        sql = "SELECT * FROM Valve_Info WHERE Valve_Id = %s"
        val = (valve_data.valveId,)
        mycursor.execute(sql, val)
        result = mycursor.fetchone()

        if result is None:
            # 如果Valve_Id不存在，则添加到Valve_Info表
            sql = "INSERT INTO Valve_Info (Valve_Id) VALUES (%s)"
            mycursor.execute(sql, val)
            mydb.commit()

        # 检查Valve_Id是否已存在于Valve_Timestamp表中
        check_timestamp_sql = "SELECT * FROM Valve_Timestamp WHERE Valve_Id = %s"
        mycursor.execute(check_timestamp_sql, val)
        timestamp_result = mycursor.fetchone()
        if timestamp_result is None:
            # 如果Valve_Id不存在于Valve_Timestamp表，则创建新纪录
            create_timestamp_sql = """
                    INSERT INTO Valve_Timestamp (Valve_Id, W_Timestamp, P_Timestamp, R_Timestamp)
                    VALUES (%s, 0, 0, 0)
                """
            mycursor.execute(create_timestamp_sql, val)
            mydb.commit()

        all_entries = valve_data.get_all_entries()

        for entry in all_entries:
            sql = """
                INSERT INTO Valve_Data (Valve_Id, Date, Time, Timestamp, SP, PV, OP)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                valve_data.valveId,
                entry['Date'],
                entry['Time'],
                entry['Timestamp'],
                entry['SetValveFlowRate'],
                entry['ValveFlowRate'],
                entry['ValveOpening']
            )
            mycursor.execute(sql, val)
            mydb.commit()

            # 更新Valve_Timestamp表的W_Timestamp
            update_timestamp_sql = "UPDATE Valve_Timestamp SET W_Timestamp = %s WHERE Valve_Id = %s"
            update_timestamp_val = (entry['Timestamp'], valve_data.valveId)
            mycursor.execute(update_timestamp_sql, update_timestamp_val)
            mydb.commit()


            if interval > 0:
                time.sleep(interval)

    except mysql.connector.Error as err:
        print(f"添加数据出错: {err}")

    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()