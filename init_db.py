from include.Class_Valve import ValveData
from include.DataProcessing import *
from include.Plot import *
from include.Database_add_new_data import *
from include.Database_predicted_data import *

config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'valve'
}

if __name__ == "__main__":
    # file_path = r"files/FIC207.OP.SP.PV.txt"
    # valve_data = GetData.FileType1(file_path)
    # t=Data_homogenization_SegmentedResampling(valve_data, 10, 1000)
    # t_equation=find_best_model(t.get_valveOpening(),t.get_valveFlowRate())

    mysql_init(config)