from flask import Flask, render_template, request, redirect, url_for, jsonify
from include.Database_add_new_data import mysql_add_data
from include.DataProcessing import GetData
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'valve'
}


@app.route('/')
def index():
    from web_utils.db_connector import get_valves
    valves = get_valves(DB_CONFIG)
    return render_template('index.html', valves=valves)


@app.route('/valve/<valve_id>')
def valve_detail(valve_id):
    from web_utils.db_connector import get_valve_info
    valve = get_valve_info(DB_CONFIG, valve_id)
    return render_template('valve_detail.html', valve=valve)


@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        # 保存并处理文件
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # 调用现有处理逻辑
        try:
            valve_data = GetData.FileType1(filename)
            mysql_add_data(valve_data, DB_CONFIG)
        except Exception as e:
            print(f"数据处理失败: {str(e)}")

        os.remove(filename)  # 清理临时文件

    return redirect(url_for('index'))


@app.route('/api/data/<valve_id>')
def get_valve_data(valve_id):
    from web_utils.db_connector import get_recent_data
    data = get_recent_data(DB_CONFIG, valve_id)
    return jsonify(data)


@app.route('/predict/<valve_id>', methods=['POST'])
def trigger_prediction(valve_id):
    from web_utils.db_connector import trigger_prediction
    success = trigger_prediction(DB_CONFIG, valve_id)
    return jsonify({
        'success': success,
        'message': '预测任务已启动' if success else '预测失败'
    })

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'txt', 'csv'}


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5001)