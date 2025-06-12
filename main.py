from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session , send_file, abort
from flask_socketio import SocketIO, emit
import os
import json
import time
import requests 
import random
from datetime import datetime , timedelta
from user_agents import parse
from flask_cors import CORS
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import send_from_directory, make_response

# Initialize app and socket
app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'txt', 'pdf','mp3','wav'}
socketio = SocketIO(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
CORS(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize messages as an empty list, not a dictionary
messages = []  # Store messages locally

API_KEY_EXPIRATION = 10

exam_duration = 20 * 60  # 30 minutes in seconds
exam_start_time = None  # Global variable to store exam start time
exam_started = False  # Флаг начала экзамена
exam_end_time = None


USER_DATA_FILE = "users.json"
MESSAGE_DATA_FILE = "messages.json"
exam_passed = []

AVATAR_FOLDER = "static/avatars"
USER_AVATAR_FILE = "users_avatar.json"

app.config["AVATAR_FOLDER"] = AVATAR_FOLDER
app.config["ALLOWED_IMAGE_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

active_keys = {}
BASE_DIR = os.path.abspath("homework_files")

@app.route('/generate-key', methods=['POST'])
def generate_api_key():
    # Генерация ключа без передачи user_id в payload
    api_key = serializer.dumps({})
    return jsonify({'api_key': api_key, 'expires_in': API_KEY_EXPIRATION})

def verify_api_key(token):
    """Валидация ключа. Возвращает True, если ключ валиден, или False в случае ошибки."""
    try:
        # Проверка валидности токена (не извлекаем user_id)
        payload = serializer.loads(token, max_age=API_KEY_EXPIRATION)
        print(f"Token Payload: {payload}")  # Логируем данные токена
        return True  # Токен валиден
    except SignatureExpired:
        print("Token expired!")
        return 'expired'
    except BadSignature:
        print("Invalid token!")
        return False

@app.route('/api/homework/<unit>', methods=['GET'])
def get_homework(unit):
    # Получаем ключ из заголовка
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing token'}), 403

    token = auth_header.split(' ')[1]
    print(f"Received Token: {token}")  # Логируем токен

    # Проверка валидности токена
    if verify_api_key(token) == 'expired':
        return jsonify({'error': 'Token expired'}), 401
    if not verify_api_key(token):
        return jsonify({'error': 'Invalid token'}), 403

    # Загружаем файл
    filename = f"Unit{unit}.json"
    filepath = os.path.join(BASE_DIR, filename)

    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404

    return send_file(filepath, mimetype='application/json')



@app.route('/api/get_exam_times', methods=['GET'])
def get_exam_times():
    current_time = time.time()  # текущее время в секундах
    return jsonify({
        "current_time": current_time,
        "exam_start_time": exam_start_time,
        "exam_end_time": exam_end_time
    })
        
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)

if not os.path.exists(USER_AVATAR_FILE):
    with open(USER_AVATAR_FILE, "w") as f:
        json.dump({}, f)

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_IMAGE_EXTENSIONS"]
    
def initialize_users_data_file():
    if not os.path.exists(USER_AVATAR_FILE):
        with open(USER_AVATAR_FILE, "w") as f:
            json.dump({}, f)
    try:
        with open(USER_AVATAR_FILE, "r") as f:
            users = json.load(f)
    except json.JSONDecodeError:  # Handle case if the file is corrupted or empty
        with open(USER_AVATAR_FILE, "w") as f:
            json.dump({}, f)  # Reset to an empty object
        users = {}
    return users

PROGRESS_FILE = 'students_progress.json'

# Функция для загрузки данных из JSON файла
def load_progress():
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Функция для сохранения данных в JSON файл
def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Функция для получения прогресса студента
def get_student_progress():
    return load_progress()
    
@app.route('/api/get-leaderboard', methods=['GET'])
def get_leaderboard_myprogress():
    time.sleep(1)
    # Получаем прогресс всех студентов
    progress_data = get_student_progress()

    if not progress_data:
        return jsonify({"error": "No student progress data found"}), 404  # Если данных нет, возвращаем ошибку

    # Подготовка данных для таблицы
    leaderboard = {}

    for student, data in progress_data.items():
        raw_progress = data.get("progress", 0)
        rounded_progress = round(raw_progress, 2)  # Округляем до двух знаков после запятой

        leaderboard[student] = {
            "progress": rounded_progress,
            "start_date": data.get("start_date", None),
            "study_days": data.get("study_days", "odd")  # Default "odd" if not provided
        }

    # Возвращаем все данные о студентах в формате JSON
    return jsonify(leaderboard)
    
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        with open('users.json', 'r') as file:
            users = json.load(file)
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-student-progress', methods=['GET'])
def get_progress():

    # Получаем имя пользователя из параметров запроса
    current_user = request.args.get("username")
    
    if not current_user:
        return jsonify({"error": "Username is required"}), 400  # Если имя не передано, возвращаем ошибку

    # Получаем прогресс всех студентов
    progress_data = get_student_progress()  # Здесь предполагается, что эта функция возвращает словарь всех студентов и их прогресса
    
    # Если пользователь не найден в данных, возвращаем ошибку "notfound"
    if current_user not in progress_data:
        return jsonify({"error": "Student not found"}), 404  # Ошибка 404 если пользователь не найден

    # Получаем прогресс, start_date и study_days для найденного пользователя
    student_data = progress_data[current_user]
    progress = student_data.get("progress", 0)
    start_date = student_data.get("start_date", None)
    study_days = student_data.get("study_days", None)  # Получаем study_days

    # Возвращаем прогресс, start_date и study_days для указанного пользователя
    return jsonify({current_user: {"progress": progress, "start_date": start_date, "study_days": study_days}})
    
@app.route('/api/get-student-names', methods=['GET'])
def get_student_names():
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            student_names = list(data.keys())  # Получаем только ключи (имена студентов)
            return jsonify({"students": student_names})
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Ошибка сервера


@app.route('/api/update-student-progress', methods=['POST'])
def update_progress():
    data = request.json
    username = data.get('username')
    progress = data.get('progress')
    start_date = data.get('start_date')  # Получаем дату начала курса из запроса

    if not username or progress is None:
        return jsonify({'error': 'Invalid input'}), 400

    # Обновляем прогресс студента и start_date (если передан start_date)
    update_student_progress(username, progress, start_date)
    
    return jsonify({'success': True, 'message': 'Progress updated successfully'})

# Функция для обновления прогресса студента и start_date
def update_student_progress(username, progress, start_date):
    progress_data = load_progress()  # Загружаем текущие данные
    
    # Если студент не найден, добавляем его
    if username not in progress_data:
        progress_data[username] = {
            "progress": progress,
            "start_date": start_date  # Если start_date передан, он будет обновлен
        }
    else:
        # Обновляем только прогресс
        progress_data[username]["progress"] = progress
        
        # Если start_date передан, обновляем его
        if start_date:
            progress_data[username]["start_date"] = start_date

    save_progress(progress_data)
    
@app.route('/api/update-student-progress-exam', methods=['POST'])
def update_progress_exam():
    data = request.json
    username = data.get('username')
    progress_increment = data.get('progress')  # Это не новый прогресс, а процент, который нужно добавить

    if not username or progress_increment is None:
        return jsonify({'error': 'Invalid input'}), 400

    progress_data = load_progress()

    # Если студент новый, создаем запись
    if username not in progress_data:
        progress_data[username] = {"progress": 0}

    # Обновляем прогресс (старое значение + новое)
    current_progress = float(progress_data[username]["progress"])
    new_progress = min(100, current_progress + float(progress_increment))  # Ограничиваем 100%

    progress_data[username]["progress"] = new_progress
    save_progress(progress_data)

    return jsonify({'success': True, 'message': 'Progress updated successfully', 'new_progress': new_progress})

    
@socketio.on('typing')
def handle_typing(data):
    emit('user_typing', data, broadcast=True, include_self=False)  # Рассылаем всем, кроме отправителя

# Событие "пользователь перестал печатать"
@socketio.on('stop_typing')
def handle_stop_typing(data):
    emit('user_stopped_typing', data, broadcast=True, include_self=False)

@app.route("/upload_avatar", methods=["POST"])
def upload_avatar():
    if "file" not in request.files or "username" not in request.form:
        return jsonify({"error": "No file or username provided"}), 400

    file = request.files["file"]
    username = request.form["username"]

    if file and allowed_image(file.filename):
        filename = secure_filename(f"{username}_{file.filename}")
        filepath = os.path.join(app.config["AVATAR_FOLDER"], filename)
        file.save(filepath)

        # Load users data and update it
        users = initialize_users_data_file()

        # Update user data with new avatar
        users[username] = f"/static/avatars/{filename}"

        # Save the updated data
        with open(USER_AVATAR_FILE, "w") as f:
            json.dump(users, f, indent=4)

        return jsonify({"message": "Avatar uploaded successfully", "avatar_url": users[username]})

    return jsonify({"error": "Invalid file type"}), 400
    
@app.route("/get_avatar/<username>", methods=["GET"])
def get_avatar(username):
    if not os.path.exists(USER_AVATAR_FILE):
        return jsonify({"avatar_url": None})  # Указываем, что аватарка не найдена

    with open(USER_AVATAR_FILE, "r") as f:
        users = json.load(f)

    avatar_url = users.get(username)

    if avatar_url:
        # Возвращаем ссылку на аватар, если он есть
        return jsonify({"avatar_url": avatar_url})
    
    # Если аватарки нет, возвращаем None
    return jsonify({"avatar_url": None})
        
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def load_bought_themes():
    try:
        with open('bought.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Функция для сохранения купленных тем
def save_bought_themes(data):
    with open('bought.json', 'w') as file:
        json.dump(data, file)

def load_file(file_path, default_value):
    """Load a file or return default value if file is not found."""
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return default_value
    with open(file_path, 'r') as file:
        return json.load(file)
        
def save_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    
TRANSACTIONS_FILE = "users_transactions.json"   
 
def load_balances():
    try:
        with open('balance.json', 'r') as f:
            data = json.load(f)
        return {user: float(balance) for user, balance in data.items()}
    except (FileNotFoundError, ValueError):
        return {}

def store_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f, indent=4) 

def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            return json.load(f)
    return {}

def store_transactions(transactions):
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=4)
        
@app.route('/api/add_transaction', methods=['POST'])
def add_transaction():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    username = data.get("username")
    amount = data.get("amount")
    description = data.get("description", "")

    if not username or amount is None:
        return jsonify({"error": "username and amount are required"}), 400

    balances = load_balances()
    transactions = load_transactions()

    # Если пользователя нет — инициализируем баланс и список транзакций.
    if username not in balances:
        balances[username] = 0.0
    if username not in transactions:
        transactions[username] = []

    # Проверяем, достаточно ли средств при отрицательной транзакции
    if amount < 0 and balances[username] + amount < 0:
        return jsonify({"error": "Insufficient funds"}), 400

    # Обновляем баланс
    balances[username] += amount

    # Создаём запись транзакции
    transaction_record = {
        "amount": amount,
        "description": description,
        "time": datetime.utcnow().isoformat()
    }
    transactions[username].append(transaction_record)

    # Сохраняем обновлённые данные
    store_balances(balances)
    store_transactions(transactions)

    return jsonify({
        "message": "Transaction added",
        "new_balance": balances[username]
    })
    
    
@app.route('/api/get_balance/<username>', methods=['GET'])
def get_balance(username):
    balances = load_balances()
    transactions = load_transactions()
    if username not in balances:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": username,
        "balance": balances[username],
        "transactions": transactions.get(username, [])
    })

# Initialize loggedUsers from file
loggedUsers = load_file(USER_DATA_FILE, {})
messages = load_file(MESSAGE_DATA_FILE, [])

active_sessions = {}  # Track active sessions by username

current_version = "2025-01-10-v1"

exam_questions = [ 

  {
  "id": 1,
  "text": "Section 1. Are the sentences true or false?",
  "type": "listening",
  "audio": "/static/exam-files/LE_listening_A1_Ordering_in_a_cafe.mp3",
  "subquestions": [
    {
      "id": "1.1",
      "type": "true_false",
      "text": "Customer 1 orders a large bottle of orange juice",
      "correct": "False"
    },
    {
      "id": "1.2",
      "type": "true_false",
      "text": "The apple juice costs £3.15",
      "correct": "False"
    },
    {
      "id": "1.3",
      "type": "true_false",
      "text": "Customer 2 is not going to have their tea and cake inside the café",
      "correct": "True"
    },
    {
      "id": "1.4",
      "type": "true_false",
      "text": "Customer 2 pays with a twenty pound note",
      "correct": "False"
    },
    {
      "id": "1.5",
      "type": "true_false",
      "text": "Customer 3 orders something to drink",
      "correct": "False"
    },
    {
      "id": "1.6",
      "type": "true_false",
      "text": "The cookie costs 85p",
      "correct": "False"
    }
  ]
},
    {
 "id": 2,
  "type": "reading",
  "text": "<h1>FINAL EXAM INSTRUCTIONS</h1>\n\n<h2>Poster 1</h2>\n<ul>\n  <li>Doors close 5 minutes before the exam begins.</li>\n  <li>Show your student ID card to examiner when you enter the room.</li>\n  <li>No phones, no books.</li>\n</ul>\n\n<h2>Poster 2</h2>\n<p><strong>BEFORE THE EXAM</strong></p>\n<ul>\n  <li>Have your ID card ready.</li>\n  <li>Listen to the instructions.</li>\n  <li>Arrive 10 minutes before exam.</li>\n</ul>\n<p><strong>IN THE EXAM</strong></p>\n<ul>\n  <li>Mobile phones switched off and put away.</li>\n  <li>ID card visible on the desk.</li>\n  <li>No talking.</li>\n  <li>No food or drinks in exam room.</li>\n</ul>\n\n<h2>Poster 3</h2>\n<ul>\n  <li>Follow the examiner's instructions.</li>\n  <li>If you have a question, raise your hand.</li>\n  <li>No mobile phones, books or bags in the exam.</li>\n  <li>Please use a blue or black pen.</li>\n</ul>",
    "subquestions": [
        {
            "id": "2.1",
            "type": "multiple_choice",
            "text": "No talking.",
            "options": ["You can talk.", "You can't talk."],
            "correct": "You can't talk."
        },
        {
            "id": "2.2",
            "type": "multiple_choice",
            "text": "ID card visible on desk.",
            "options": ["You can see the ID card.", "You can't see the ID card."],
            "correct": "You can see the ID card."
        },
        {
            "id": "2.3",
            "type": "multiple_choice",
            "text": "Mobile phones switched off and put away.",
            "options": ["Don't have your mobile phone on the table.", "It's OK to have your mobile phone on the table."],
            "correct": "Don't have your mobile phone on the table."
        },
        {
            "id": "2.4",
            "type": "multiple_choice",
            "text": "Doors close five minutes before the exam.",
            "options": ["You must arrive early.", "You can be five minutes late."],
            "correct": "You must arrive early."
        },
        {
            "id": "2.5",
            "type": "multiple_choice",
            "text": "If you have a question, raise your hand.",
            "options": ["You can ask questions.", "You can't ask questions."],
            "correct": "You can ask questions."
        }
    ]
},
{
  "id": 3,
  "text": "Section 3. Are the sentences true or false?",
  "type": "listening",
  "audio": "/static/exam-files/Elon.mp3",
  "subquestions": [
    {
      "id": "3.1",
      "type": "true_false",
      "text": "Elon Musk is the co-founder and CEO of Tesla.",
      "correct": "True"
    },
    {
      "id": "3.2",
      "type": "true_false",
      "text": "Elon and his brother rented a large apartment when starting their first company.",
      "correct": "False"
    },
    {
      "id": "3.3",
      "type": "true_false",
      "text": "Elon Musk said if something is important, you should try even if you might fail.",
      "correct": "True"
    },
    {
      "id": "3.4",
      "type": "true_false",
      "text": "Critics told Elon Musk he couldn’t succeed, and he said they were right.",
      "correct": "False"
    },
    {
      "id": "3.5",
      "type": "true_false",
      "text": "Elon Musk encouraged people to take risks while they are young.",
      "correct": "True"
    },
    {
      "id": "3.6",
      "type": "true_false",
      "text": "Elon said he expected his company to succeed from the beginning.",
      "correct": "False"
    }
  ]
}

]
           
# Путь к файлу с балансами
BALANCE_FILE = 'balance.json'

# Загрузка баланса из файла
def load_balance():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

# Сохранение баланса в файл
def save_balance(balance):
    with open(BALANCE_FILE, 'w') as f:
        json.dump(balance, f)
        
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    balance_data = load_balance()

    # Преобразуем в список [(имя, баланс)] и сортируем по убыванию монет
    sorted_balances = sorted(balance_data.items(), key=lambda x: x[1], reverse=True)

    # ТОП-3 и остальные
    top_3 = sorted_balances[:3]  # Берем только 3 лучших
    others = sorted_balances[3:]  # Остальные

    leaderboard = {
        "top_3": [{"name": user, "coins": coins} for user, coins in top_3],
        "others": [{"name": user, "coins": coins} for user, coins in others]
    }

    return jsonify(leaderboard)
    
@socketio.on('tempBanUser')
def handle_temp_ban(data):
    username = data.get('username')
    duration = data.get('duration')
    # Эмиттируем событие обратно клиенту с именем пользователя и длительностью
    socketio.emit('tempBanUser', {'username': username, 'duration': duration})
    
@socketio.on('unblockUser')
def handle_unblock_user(data):
    username = data.get('username')
    # Эмиттируем событие обратно клиенту с именем пользователя
    socketio.emit('unblockUser', {'username': username})

@socketio.on('unblockUserRequest')
def handle_unblock(data):
    print("Unblock request received.")
    # Если нужно отправить событие всем клиентам, можно использовать аргумент room='all' 
    # или вручную перебрать sid-ы, но в большинстве случаев достаточно обычного emit:
    socketio.emit('unblockUser', {})  # отправляем всем подключенным клиентам


# Получение баланса для пользователя
@socketio.on('get_balance')
def get_balance(username):
    balance = load_balance()
    if username in balance:
        emit('balance', {'success': True, 'coins': balance[username]})
    else:
        emit('balance', {'success': False, 'message': 'User not found'})

@socketio.on('add_coins')
def add_coins(data):
    username = data['username']
    coins = data['coins']
    balance = load_balance()
    
    # Если пользователя нет в файле, создаем запись с 0 монетами
    if username not in balance:
        balance[username] = 0
    
    balance[username] += coins
    
    save_balance(balance)  # Сохраняем обновленный баланс
    
    # Отправляем обновленный баланс всем клиентам
    emit('coins_added', {'success': True, 'username': username, 'coins': balance[username]}, broadcast=True)
    
@app.route('/add_coins', methods=['POST'])
def add_coins_api():
    try:
        data = request.get_json()
        username = data.get("username")
        coins = data.get("coins", 0)

        if not username or not isinstance(coins, int) or coins <= 0:
            return jsonify({"error": "Invalid data"}), 400

        balance = load_balance()
        balance[username] = balance.get(username, 0) + coins
        save_balance(balance)

        # Отправляем обновленный баланс через WebSocket
        socketio.emit('coins_added', {'success': True, 'username': username, 'coins': balance[username]})

        return jsonify({"success": True, "username": username, "coins": balance[username]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@socketio.on('pay_for_ban_reduction')
def pay_for_ban_reduction(data):
    username = data['username']
    count_blocks = data['countBlocks']
    cost_per_violation = 100  # 100 монет за одно нарушение

    balance = load_balance()

    # Проверяем, есть ли у пользователя достаточно монет
    if username in balance and balance[username] >= cost_per_violation:
        # Списываем 100 монет за одно нарушение
        balance[username] -= cost_per_violation
        save_balance(balance)

        # Уменьшаем количество нарушений (countBlocks) на 1
        new_count_blocks = max(count_blocks - 1, 0)

        # Отправляем обновленное количество нарушений обратно на клиент
        emit('ban_reduction_success', {'success': True, 'new_count_blocks': new_count_blocks, 'coins': balance[username]})
    else:
        emit('ban_reduction_failed', {'success': False, 'message': 'Not enough coins'})

@app.route('/ping', methods=['GET'])
def ping():
    return '', 204  # Возвращает пустой успешный ответ

@app.route('/create_exam', methods=['POST'])
def create_exam():
    try:
        data = request.get_json()
        questions = data.get('questions', [])

        if not questions:
            return jsonify({"error": "No questions provided"}), 400

        # Set the exam start time and store duration
        #exam_start_time = time.time()
        global exam_start_time
        #exam_start_time = None  # Track the time when exam starts, comment this line if not needed

        # Store questions
        exam_questions.clear()
        #exam_passed.clear()
        
        for question in questions:
            question_data = {
                "id": question['id'],
                "text": question['text'],
                "type": question['type'],
                "correct": question['correct']
            }

            if question['type'] == 'multiple_choice' and 'options' in question:
                question_data["options"] = question['options']

            exam_questions.append(question_data)

        return jsonify({"success": True, "exam_duration": exam_duration})

    except Exception as e:
        app.logger.error(f"Error occurred in create_exam: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
        
@app.route('/create_homework_exam', methods=['POST'])
def create_homework_exam():
    try:
        data = request.get_json()
        questions = data.get('questions', [])

        if not questions:
            return jsonify({"error": "No questions provided"}), 400

        exam_questions.clear()

        for q in questions:
            question_data = {
                "id": q["id"],
                "text": q["text"],
                "type": q["type"]
            }

            if "audio" in q:
                question_data["audio"] = q["audio"]

            if "images" in q:
                question_data["images"] = q["images"]

            # If it has subquestions, add them
            if "subquestions" in q:
                question_data["subquestions"] = q["subquestions"]
            else:
                # Otherwise, must have correct + options if applicable
                question_data["correct"] = q["correct"]
                if q["type"] == "multiple_choice" and "options" in q:
                    question_data["options"] = q["options"]

            exam_questions.append(question_data)

        return jsonify({"success": True})

    except Exception as e:
        app.logger.error(f"Error in create_homework_exam: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/get_homework_questions', methods=['GET'])
def get_homework_questions():
    username = request.args.get('username')  # you can still log or ignore this
    if not exam_questions:
        return jsonify({"error": "No questions available"}), 404

    # Always return current questions
    return jsonify({"questions": exam_questions})


# Helper function to save homework submission data
def save_homework_submission(result):
    try:
        # Load existing homework submissions
        try:
            with open('done_homework.json', 'r') as file:
                done_homework = json.load(file)
        except FileNotFoundError:
            done_homework = []

        # Append new result to done_homework list
        done_homework.append(result)

        # Save the updated data back to the JSON file
        with open('done_homework.json', 'w') as file:
            json.dump(done_homework, file, indent=4)

    except Exception as e:
        app.logger.error(f"Error saving homework submission: {e}")
        raise  # Re-raise the exception so it can be handled later

@app.route('/submit_homework', methods=['POST'])
def submit_homework():
    try:
        # Получаем данные с клиента
        data = request.get_json()
        answers = data.get("answers")
        username = data.get("username")
        unit = data.get("unit")

        if not answers or not username:
            return jsonify({"error": "Missing data"}), 400

        # Проверка, что вопросный банк существует
        if not exam_questions:
            return jsonify({"error": "No homework exam created"}), 404

        # Загружаем предыдущие результаты, если они есть
        try:
            with open('done_homework.json', 'r') as file:
                done_homework = json.load(file)
        except FileNotFoundError:
            done_homework = []

        # Проверяем, сдавал ли уже пользователь экзамен для выбранного юнита
        for record in done_homework:
            if record["username"] == username and record["unit"] == unit:
                return jsonify({"error": "You have already submitted homework for this unit"}), 403

        correct = 0
        incorrect = 0
        skipped = 0
        results = []

        # Обработка вопросов и под-вопросов
        for question in exam_questions:
            if "subquestions" in question:
                # Обрабатываем под-вопросы
                for subq in question["subquestions"]:
                    subq_id = f"q{subq['id']}"
                    answer = answers.get(subq_id)

                    if not answer or answer.strip() == "":
                        skipped += 1
                        results.append({
                            "question_type": subq["type"],
                            "question_id": subq["id"],
                            "question": subq["text"],
                            "user_answer": answer,
                            "correct_answer": subq["correct"],
                            "is_correct": False
                        })
                        continue

                    is_correct = answer.strip().lower() == subq["correct"].strip().lower()
                    if is_correct:
                        correct += 1
                    else:
                        incorrect += 1

                    results.append({
                        "question_type": subq["type"],
                        "question_id": subq["id"],
                        "question": subq["text"],
                        "user_answer": answer,
                        "correct_answer": subq["correct"],
                        "is_correct": is_correct
                    })
            else:
                # Обработка обычных вопросов без под-вопросов
                question_id = f"q{question['id']}"
                answer = answers.get(question_id)

                if not answer or answer.strip() == "":
                    skipped += 1
                    results.append({
                        "question_type": question["type"],
                        "question_id": question["id"],
                        "question": question["text"],
                        "user_answer": answer,
                        "correct_answer": question["correct"],
                        "is_correct": False
                    })
                    continue

                is_correct = answer.strip().lower() == question["correct"].strip().lower()
                if is_correct:
                    correct += 1
                else:
                    incorrect += 1

                results.append({
                    "question_type": question["type"],
                    "question_id": question["id"],
                    "question": question["text"],
                    "user_answer": answer,
                    "correct_answer": question["correct"],
                    "is_correct": is_correct
                })

        # Подсчитываем общее количество вопросов
        total_questions = sum(
            len(question["subquestions"]) if "subquestions" in question else 1
            for question in exam_questions
        )
        correct_percentage = (correct / total_questions) * 100 if total_questions > 0 else 0
        coins = 15 if correct_percentage >= 80 else 0

        # Сохраняем результаты
        time_finished = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        done_homework.append({
            "username": username,
            "unit": unit,
            "correct": correct,
            "incorrect": incorrect,
            "skipped": skipped,
            "total_questions": total_questions,
            "correct_percentage": correct_percentage,
            "coins": coins,
            "time_finished": time_finished,
            "results": results
        })

        # Сохраняем обновленные данные
        with open('done_homework.json', 'w') as file:
            json.dump(done_homework, file, indent=4)

        return jsonify({
            "correct": correct,
            "incorrect": incorrect,
            "skipped": skipped,
            "total_questions": total_questions,
            "correct_percentage": correct_percentage,
            "coins": coins,
            "time_finished": time_finished
        })

    except Exception as e:
        app.logger.error(f"Error in submit_homework: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/check_homework_status')
def check_homework_status():
    username = request.args.get('username')
    unit = request.args.get('unit')

    if not username or not unit:
        return jsonify({"error": "Missing 'username' or 'unit' parameter"}), 400

    try:
        unit = int(unit)
    except ValueError:
        return jsonify({"error": "'unit' must be a number"}), 400

    file_path = 'done_homework.json'
    if not os.path.exists(file_path):
        return jsonify({"error": "Data file not found"}), 500

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Ищем по имени пользователя и юниту
    for entry in data:
        if entry.get('username') == username and entry.get('unit') == unit:
            return jsonify({"isCompleted": True})

    return jsonify({"isCompleted": False})

@socketio.on('exam_started')
def handle_exam_started():
    global exam_started
    exam_started = True
    emit('exam_started', {'message': 'Exam has started'}) 

import json
import os

@app.route('/api/start-exam', methods=['POST'])
def start_exam():
    global exam_start_time, exam_end_time, exam_passed

    # Время начала экзамена
    exam_start_time = time.time()

    # Рассчитываем время окончания экзамена + 10 секунд
    exam_end_time = exam_start_time + exam_duration + 10  

    # Очищаем список пользователей, которые прошли экзамен
    exam_passed.clear()

    # Очищаем файл с результатами экзамена
    try:
        with open('exam_results.json', 'w') as f:
            json.dump({}, f)  # или [] в зависимости от структуры файла
    except Exception as e:
        return jsonify({"error": f"Failed to clear exam_results.json: {str(e)}"}), 500

    # Отправляем сообщение о старте экзамена
    socketio.emit('exam_started', {'message': 'Exam has started'})

    return jsonify({"message": "Exam has started and the passed list is cleared."}), 200

    
@socketio.on('exam_ended')
def handle_exam_ended():
    global exam_started
    exam_started = False
    emit('exam_ended', {'message': 'Exam has ended, settings have been reset.'})

@app.route('/api/end-exam', methods=['POST'])
def end_exam():
    global exam_start_time, exam_end_time, exam_started, exam_passed

    # Сброс переменных экзамена к заводским настройкам
    exam_start_time = None
    exam_end_time = None
    exam_started = False

    # Очищаем список пользователей, которые прошли экзамен
    exam_passed.clear()

    # Отправляем сообщение о завершении экзамена
    socketio.emit('exam_ended', {'message': 'Exam has ended and settings have been reset to factory defaults.'})

    return jsonify({"message": "Exam ended and settings reset."}), 200

@app.route('/get_remaining_time', methods=['GET'])
def get_remaining_time():
    if exam_start_time is None:
        return jsonify({"error": "Exam has not been started yet."}), 400

    # Calculate how much time has passed
    time_elapsed = time.time() - exam_start_time
    remaining_time = max(0, exam_duration - time_elapsed)  # Ensure no negative time

    return jsonify({"remaining_time": remaining_time})


def calculate_score(user_answers):
    correct_count = 0
    for question_id, user_answer in user_answers.items():
        # Поиск вопроса по ID
        question = next((q for q in exam_questions if q["id"] == question_id), None)
        
        # Если вопрос найден и ответ совпадает
        if question and user_answer == question["correct"]:
            correct_count += 1

    return (correct_count / len(exam_questions)) * 100 if exam_questions else 0


@app.route('/get_exam_questions_result', methods=['GET'])
def get_exam_questions_result():

    return jsonify({"questions": exam_questions})

@app.route('/get_exam_questions', methods=['GET'])
def get_exam_questions():
    time.sleep(1)

    username = request.args.get("username")  # Получаем имя пользователя из запроса

    if username in exam_passed:
        return jsonify({"error": "You have already passed the exam."}), 403  # Ошибка для уже прошедших

    if not exam_questions:
        return jsonify({"error": "No upcoming exams."}), 404

    if exam_start_time is None:
        return jsonify({"error": "Exam has not started yet."}), 403  # Ошибка, если экзамен ещё не начался

    current_time = time.time()
    exam_end_time = exam_start_time + exam_duration

    if current_time > exam_end_time:
        return jsonify({"error": "Exam time has expired."}), 403  # Ошибка, если время истекло

    return jsonify({"questions": exam_questions})

@app.route('/api/get_exam_results', methods=['GET'])
def get_exam_results():
    try:
        time.sleep(2)
        # Проверяем, существует ли файл с результатами
        if not os.path.exists('exam_results.json'):
            return jsonify({"error": "No exam results found"}), 404

        # Открываем и читаем файл с результатами
        with open('exam_results.json', 'r') as f:
            exam_results = json.load(f)

        # Возвращаем все данные в формате JSON
        return jsonify(exam_results)

    except Exception as e:
        app.logger.error(f"Error in get_exam_results: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    try:
        # Проверка на истечение времени экзамена
        current_time = time.time()  # Получаем текущее время
        if current_time > exam_end_time:
            return jsonify({"error": "Exam time has expired."}), 403  # Ошибка, если время истекло

        data = request.get_json(silent=True)
        answers = data.get("answers")
        username = data.get("username")

        if not username:
            return jsonify({"error": "Missing data"}), 400

        if username in exam_passed:
            return jsonify({"error": "You have already passed the exam."}), 403

        correct = 0
        incorrect = 0
        skipped = 0
        results = []

        # Обработка вопросов и под-вопросов
        for question in exam_questions:
            if "subquestions" in question:
                # Обрабатываем только под-вопросы, основной текст не считается
                for subq in question["subquestions"]:
                    subq_id = f"q{subq['id']}"
                    answer = answers.get(subq_id)
                    if not answer or answer.strip() == "":
                        skipped += 1
                        results.append({
                            "question_type": subq["type"],
                            "question_id": subq["id"],
                            "question": subq["text"],
                            "user_answer": answer,
                            "correct_answer": subq["correct"],
                            "is_correct": False
                        })
                        continue

                    is_correct = answer.strip().lower() == subq["correct"].strip().lower()
                    if is_correct:
                        correct += 1
                    else:
                        incorrect += 1

                    results.append({
                        "question_type": subq["type"],
                        "question_id": subq["id"],
                        "question": subq["text"],
                        "user_answer": answer,
                        "correct_answer": subq["correct"],
                        "is_correct": is_correct
                    })
            else:
                # Обработка обычных вопросов (без под-вопросов)
                if 'id' not in question:
                    app.logger.error(f"Missing 'id' in question: {question}")
                    continue

                question_id = f"q{question['id']}"
                answer = answers.get(question_id)

                if not answer or answer.strip() == "":
                    skipped += 1
                    results.append({
                        "question_type": question["type"],
                        "question_id": question["id"],
                        "question": question["text"],
                        "user_answer": answer,
                        "correct_answer": question["correct"],
                        "is_correct": False
                    })
                    continue

                is_correct = answer.strip().lower() == question["correct"].strip().lower()
                if is_correct:
                    correct += 1
                else:
                    incorrect += 1

                results.append({
                    "question_type": question["type"],
                    "question_id": question["id"],
                    "question": question["text"],
                    "user_answer": answer,
                    "correct_answer": question["correct"],
                    "is_correct": is_correct
                })

        # Подсчитываем общее количество вопросов:
        # Если у вопроса есть под-вопросы, считаем только их, иначе считаем сам вопрос.
        total_questions = sum(
            len(question["subquestions"]) if "subquestions" in question else 1
            for question in exam_questions
        )
        correct_percentage = (correct / total_questions) * 100 if total_questions > 0 else 0
        coins = 15 if correct_percentage >= 80 else 0 

        exam_passed.append(username)
        time_finished = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Сохраняем результаты в файл
        exam_results = {}
        if os.path.exists('exam_results.json'):
            with open('exam_results.json', 'r') as f:
                exam_results = json.load(f)

        exam_results[username] = {
            "correct": correct,
            "incorrect": incorrect,
            "skipped": skipped,
            "total_questions": total_questions,
            "correct_percentage": correct_percentage,
            "rewarded": coins > 0,
            "coins": coins,
            "time_finished": time_finished,
            "results": results
        }

        with open('exam_results.json', 'w') as f:
            json.dump(exam_results, f, indent=4)

        return jsonify({
            "correct": correct,
            "incorrect": incorrect,
            "skipped": skipped,
            "total_questions": total_questions,
            "correct_percentage": correct_percentage,
            "rewarded": coins > 0,
            "time_finished": time_finished,
            "coins": coins
        })

    except Exception as e:
        app.logger.error(f"Error in submit_exam: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@socketio.on('submitted_exam')
def handle_submitted_exam():
    emit('update-results', broadcast=True)  # broadcast=True => всем

@app.route("/app")
def app_remake():
    return render_template("app.html")

@app.route("/chatCRM")
def crm():
    return render_template("chatCRM.html")
    
@app.route("/CRM-platform")
def crm_system():
    return render_template("CRM-platform.html")

@app.route("/release-update", methods=["POST"])
def release_update():
    global current_version

    # Разбиваем текущую версию на дату и номер версии
    date, version = current_version.split("-v")
    try:
        # Преобразуем номер версии в целое число и увеличиваем на 1
        next_version = f"{date}-v{int(version) + 1}"
    except ValueError:
        # Если произошла ошибка при преобразовании версии, отправляем ошибку
        return jsonify({"error": "Invalid version format"}), 400

    # Обновляем текущую версию
    current_version = next_version

    # Уведомляем всех подключённых клиентов об обновлении
    socketio.emit("updateReleased", {"version": current_version})  # Убираем to='all'

    # Возвращаем успешный ответ с новой версией
    return jsonify({"success": True, "version": current_version})
    
@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    return jsonify(tracks)

@app.route('/')
def login():
    return render_template('loginv2.html')
    
ACCEPTED_USERS_FILE = "accepted_users.json"

# Initialize Accepted_users by loading from the JSON file (if it exists)
def load_accepted_users():
    if os.path.exists(ACCEPTED_USERS_FILE):
        with open(ACCEPTED_USERS_FILE, 'r') as f:
            data = json.load(f)
            return set(data)  # Convert the loaded list back to a set
    else:
        # If the file doesn't exist, start with the default set
        return {"Admin"}

# Save Accepted_users to the JSON file
def save_accepted_users(users):
    with open(ACCEPTED_USERS_FILE, 'w') as f:
        json.dump(list(users), f)  # Convert set to list for JSON serialization

# Load Accepted_users at startup
Accepted_users = load_accepted_users()

# File to store banned users
BANNED_USERS_FILE = 'banned_users.json'

def save_banned_users(banned_users):
    with open(BANNED_USERS_FILE, 'w') as f:
        json.dump(banned_users, f, indent=2)

def load_banned_users():
    if os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, 'r') as f:
            try:
                banned_users = json.load(f)
            except json.JSONDecodeError:
                print("Error reading banned_users.json — invalid JSON format")
                return {}

            current_time = datetime.now()
            users_to_remove = []
            for username, data in banned_users.items():
                try:
                    ban_end = datetime.fromisoformat(data['ban_end_date'])
                    if current_time > ban_end:
                        users_to_remove.append(username)
                except Exception as e:
                    print(f"Error processing ban end date for user {username}: {e}")

            for username in users_to_remove:
                del banned_users[username]

            if users_to_remove:
                save_banned_users(banned_users)

            return banned_users
    return {}

@app.route('/ban-user/<username>', methods=['POST'])
def ban_user(username):
    banned_users = load_banned_users()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided', 'status': 'error'}), 400
        
        duration_days = int(data.get('duration_days', 7))  # Default 7 days
        reason = data.get('reason', 'No reason provided')
        offensive_item = data.get('offensive_item')
        
        ban_end_date = datetime.now() + timedelta(days=duration_days)
        
        banned_users[username] = {
            'ban_end_date': ban_end_date.isoformat(),
            'reason': reason,
            'banned_at': datetime.now().isoformat(),
            'offensive_item': offensive_item
        }
        
        save_banned_users(banned_users)

        # Удаляем все активные сессии пользователя из active_sessions
        if username in active_sessions:
            del active_sessions[username]

        # Если текущий запрос от забаненного пользователя, удаляем его сессию
        if 'username' in session and session['username'] == username:
            session.pop('username', None)

        return jsonify({'message': f'User {username} banned until {ban_end_date.isoformat()}', 'status': 'success'}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to ban user: {str(e)}', 'status': 'error'}), 400


# Get ban details for a user
@app.route('/ban-details/<username>', methods=['GET'])
def ban_details(username):
    banned_users = load_banned_users()
    
    if username in banned_users:
        details = banned_users[username]
        
        # Format dates into human-readable strings
        def format_date(date_str):
            try:
                dt = datetime.fromisoformat(date_str)
                return dt.strftime('%B %d, %Y at %I:%M %p')
            except Exception:
                return date_str  # fallback to original if parsing fails
        
        return jsonify({
            'username': username,
            'ban_end_date': format_date(details['ban_end_date']),
            'reason': details['reason'],
            'banned_at': format_date(details['banned_at']),
            'offensive_item': details.get('offensive_item')
        }), 200
    
    return jsonify({'message': f'User {username} is not banned', 'status': 'error'}), 404
    
@app.route('/banned-users', methods=['GET'])
def get_banned_users():
    banned_users = load_banned_users()
    return jsonify({
        'status': 'success',
        'users': [
            {
                'username': username,
                'ban_end_date': details['ban_end_date'],
                'reason': details['reason'],
                'banned_at': details['banned_at'],
                'offensive_item': details.get('offensive_item')
            } for username, details in banned_users.items()
        ]
    }), 200

# Reactivate a banned user
@app.route('/banned-user-reactivate/<username>', methods=['POST'])
def reactivate_user(username):
    banned_users = load_banned_users()
    
    if username in banned_users:
        del banned_users[username]
        save_banned_users(banned_users)
        return jsonify({'message': f'User {username} reactivated', 'status': 'success'}), 200
    return jsonify({'message': f'User {username} is not banned', 'status': 'error'}), 404

@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    banned_users = load_banned_users()
    current_time = datetime.now()

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username') if data else None
        password = data.get('password') if data else None
        
        time.sleep(2)

        if not username or not password:
            return render_template('loginv2.html', error="Please provide username and password.")

        if username in banned_users:
            ban_end_date = datetime.fromisoformat(banned_users[username]['ban_end_date'])
            banned_at_dt = datetime.fromisoformat(banned_users[username]['banned_at'])
            
            ban_notice = {
                'title': f'Banned for {int((ban_end_date - banned_at_dt).days)} Day{"s" if (ban_end_date - banned_at_dt).days > 1 else ""}',
                'reviewed_date': banned_at_dt.strftime('%Y-%m-%d %H:%M:%S'),  # форматируем дату в строку
                'reason': banned_users[username]['reason'],
                'offensive_item': banned_users[username].get('offensive_item'),
                'expired': current_time > ban_end_date,
                'username': username
            }

            return render_template('loginv2.html', ban_notice=ban_notice)

        if username in loggedUsers and loggedUsers[username] == password:
            user_agent_str = request.headers.get('User-Agent', '')
            user_agent = parse(user_agent_str)

            device_info = {
                'Timestamp': datetime.utcnow().isoformat(),
                'User-Agent': user_agent_str,
                'IP-Address': request.headers.get('X-Forwarded-For', request.remote_addr),
                'Language': request.headers.get('Accept-Language', ''),
                'Device-Type': (
                    'Mobile' if user_agent.is_mobile else
                    'Tablet' if user_agent.is_tablet else
                    'PC' if user_agent.is_pc else
                    'Other'
                ),
                'Browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
                'OS': f"{user_agent.os.family} {user_agent.os.version_string}",
                'Platform': user_agent.device.family
            }

            if username in active_sessions:
                active_sessions[username].append(device_info)
            else:
                active_sessions[username] = [device_info]

            session['username'] = username
            return '', 200
        else:
            return render_template('loginv2.html', error="Invalid username or password")

    # Handle GET requests
    return render_template('loginv2.html')

    
@app.route('/accept_terms', methods=['POST'])
def accept_terms():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({'success': False, 'message': 'Username is required'}), 400

    # Add the user to Accepted_users
    Accepted_users.add(username)
    # Save the updated set to the JSON file
    save_accepted_users(Accepted_users)
    return jsonify({'success': True, 'message': f'{username} has accepted the Terms and Conditions'})

@app.route('/check_terms/<username>', methods=['GET'])
def check_terms(username):
    # Check if the user has accepted the Terms and Conditions
    accepted = username in Accepted_users
    return jsonify({'accepted': accepted})

@app.route('/sessions')
def get_sessions():
    sessions_data = []

    # Пройдем по всем пользователям и их сессиям
    for username, devices in active_sessions.items():
        for device in devices:
            sessions_data.append({
                'deviceType': device.get('Device-Type', 'Unknown'),
                'platform': device.get('Platform', 'Unknown'),
                'os': device.get('OS', 'Unknown'),
                'browser': device.get('User-Agent', 'Unknown').split(' ')[0],  # Получаем только имя браузера
                'ipAddress': device.get('IP-Address', 'Unknown'),
                'language': device.get('Language', 'Unknown')
            })
    
    return jsonify({'sessions': sessions_data})
    
@app.route('/api/sessions/')
def get_sessions_api():
    sessions_data = []

    # Iterate through all users and their sessions
    for username, devices in active_sessions.items():
        for device in devices:
            sessions_data.append({
                'username': username,  # Include username in the response
                'deviceType': device.get('Device-Type', 'Unknown'),
                'platform': device.get('Platform', 'Unknown'),
                'os': device.get('OS', 'Unknown'),
                'browser': device.get('User-Agent', 'Unknown').split(' ')[0],  # Get only browser name
                'ipAddress': device.get('IP-Address', 'Unknown'),
                'language': device.get('Language', 'Unknown')
            })
    
    return jsonify({'sessions': sessions_data})

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Load banned users
    banned_users = load_banned_users()
    
    # Check if the username is banned
    username = session.get('username', '')
    if username in banned_users:
        ban_end_date = datetime.fromisoformat(banned_users[username]['ban_end_date'])
        if ban_end_date > datetime.now():  # Check if ban is still active
            session.pop('username', None)  # Clear session for banned user
            return redirect(url_for('login'))
    
    return render_template('index.html', username=session.get('username', ''))
    
@app.route('/logout', methods=['POST'])
def logout():
    username = session.pop('username', None)
    user_agent = request.headers.get('User-Agent')

    if username and user_agent:
        if username in active_sessions:
            devices = active_sessions[username]
            device_to_remove = None

            for device_info in devices:
                if device_info.get('User-Agent') == user_agent:
                    device_to_remove = device_info
                    break

            if device_to_remove:
                devices.remove(device_to_remove)

            if not devices:
                del active_sessions[username]

    # Вместо редиректа возвращаем JSON
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Use original filename or generate a unique name without timestamp prefix
        filename = secure_filename(file.filename)  # Use original filename with security
        # Optionally, add a unique identifier to avoid overwriting (e.g., UUID)
        import uuid
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Broadcast file info
        message = {
            'type': 'file',
            'filename': file.filename,  # Use original filename for display
            'url': f'/uploads/{unique_filename}',  # Use unique filename for storage
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'username': session.get('username', 'Anonymous')
        }
        messages.append(message)
        socketio.emit('new_message', message)

        return jsonify({'success': True, 'url': f'/uploads/{unique_filename}'})

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('connect')
def handle_connect():
    if 'username' in session:
        # Отправляем сохранённые сообщения
        emit('load_messages', messages)

        # Отправляем текущую версию
        emit('updateReleased', {'version': current_version})


@socketio.on('send_message')
def handle_message(data):
    if 'username' not in session:
        return

    message = {
        'type': 'text',
        'text': data['text'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'username': session.get('username', 'Anonymous')
    }
    messages.append(message)
    emit('new_message', message, broadcast=True)

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    username = session.get('username')

    if loggedUsers.get(username) != current_password:
        return jsonify({'error': 'Incorrect current password'})

    loggedUsers[username] = new_password
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(loggedUsers, f)

    return jsonify({'message': 'Password updated successfully'})
    
DATA_FILE = 'historyofprogress.json'

def read_history_from_file():
    """Читаем историю из JSON-файла."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_history_to_file(data):
    """Записываем историю в JSON-файл."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
@app.route('/api/update-history', methods=['POST'])
def update_history():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Загружаем всю историю
    all_data = read_history_from_file()
    today_str = datetime.now().strftime('%Y-%m-%d')
    user_history = all_data.get(username, [])

    # Ищем запись за сегодня или создаём новую, если её нет
    existing_today = next((r for r in user_history if r.get("date") == today_str), None)
    if not existing_today:
        # Если в запросе передано инкрементальное обновление, создаём запись только с нужным полем
        if "updateType" in data and "progressIncrease" in data:
            if data["updateType"] == "finalExam":
                existing_today = {"date": today_str, "finalExam": 0}
            elif data["updateType"] == "weeklyExams":
                existing_today = {"date": today_str, "weeklyExams": 0}
            else:
                existing_today = {"date": today_str}
        else:
            # Полное обновление – инициализируем обе оценки
            existing_today = {"date": today_str, "finalExam": 0, "weeklyExams": 0}
        user_history.append(existing_today)

    # Если переданы updateType и progressIncrease, делаем инкрементальное обновление только указанного поля
    if "updateType" in data and "progressIncrease" in data:
        update_type = data["updateType"]
        try:
            progress_increase = float(data["progressIncrease"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid progressIncrease value"}), 400

        if update_type == "finalExam":
            current = float(existing_today.get("finalExam", 0))
            new_value = current + progress_increase
            existing_today["finalExam"] = min(new_value, 30)
        elif update_type == "weeklyExams":
            current = float(existing_today.get("weeklyExams", 0))
            new_value = current + progress_increase
            existing_today["weeklyExams"] = min(new_value, 70)
        else:
            return jsonify({"error": "Invalid updateType. Must be 'finalExam' or 'weeklyExams'."}), 400
    else:
        # Полное обновление: обновляем оба поля, если они переданы
        final_exam = data.get("finalExam", 0)
        weekly_exams = data.get("weeklyExams", 0)

        try:
            final_exam = float(final_exam)
            weekly_exams = float(weekly_exams)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid exam scores provided"}), 400

        existing_today["finalExam"] = min(final_exam, 30)
        existing_today["weeklyExams"] = min(weekly_exams, 70)

    all_data[username] = user_history
    write_history_to_file(all_data)

    return jsonify({"message": "History updated successfully"}), 200


@app.route('/api/get-history', methods=['GET'])
def get_history():

    time.sleep(2)
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username not provided"}), 400

    all_data = read_history_from_file()
    user_history = all_data.get(username, [])
    return jsonify(user_history), 200


@app.route('/api/get-student-progress-history', methods=['GET'])
def get_student_progress_history():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username not provided"}), 400

    all_data = read_history_from_file()
    user_history = all_data.get(username, [])
    if not user_history:
        # Если у пользователя нет записей, вернём нули
        return jsonify({
            username: {
                "finalExam": "0.00%",
                "weeklyExams": "0.00%",
                "totalScore": "0.00%"
            }
        }), 200

    # Суммируем значения weeklyExams и finalExam по всем записям
    total_weekly_exams = sum(record.get("weeklyExams", 0) for record in user_history)
    total_final_exam = sum(record.get("finalExam", 0) for record in user_history)
    total_score = total_final_exam + total_weekly_exams

    # Форматирование значений с двумя знаками после запятой и добавлением знака '%'
    final_exam_formatted = f"{total_final_exam:.2f}%"
    weekly_exams_formatted = f"{total_weekly_exams:.2f}%"
    total_score_formatted = f"{total_score:.2f}%"

    return jsonify({
        username: {
            "finalExam": final_exam_formatted,
            "weeklyExams": weekly_exams_formatted,
            "totalScore": total_score_formatted
        }
    }), 200
    
@app.route('/vocabulary/<int:unit_number>', methods=['GET'])
def get_vocabulary(unit_number):
    base_path = os.path.join('static', 'Vocabulary', f'Unit {unit_number}')
    words_file = os.path.join(base_path, 'words.json')

    if not os.path.exists(words_file):
        return jsonify({"error": "Файл не найден"}), 404

    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify(data)

exam_data = {}

# Path to the directory with random photos
PHOTO_DIR = os.path.join('static', 'exam-files', 'speaking')


@app.route('/api/start-speaking-exam/<ID>', methods=['POST'])
def start_speaking_exam(ID):
    print(f"\n📥 [LOG] Request to start exam for ID = {ID}")

    try:
        if ID in exam_data:
            print(f"⚠️ Exam already started for ID = {ID}")
            return jsonify({"message": "Exam already started"}), 400

        print(f"📁 Checking directory: {PHOTO_DIR}")
        if not os.path.isdir(PHOTO_DIR):
            print("❌ Photo directory does not exist.")
            return jsonify({"error": "Photo directory not found"}), 500

        files_in_dir = os.listdir(PHOTO_DIR)
        print(f"📂 Files in directory: {files_in_dir}")

        valid_photos = []
        allowed_extensions = ('.jpg', '.jpeg', '.png')

        for filename in files_in_dir:
            if filename.lower().endswith(allowed_extensions):
                photo_path = os.path.join(PHOTO_DIR, filename)
                base_name = os.path.splitext(filename)[0]
                json_filename = base_name + '.json'
                json_path = os.path.join(PHOTO_DIR, json_filename)

                if os.path.isfile(photo_path) and os.path.isfile(json_path):
                    valid_photos.append(filename)

        print(f"✅ Valid image+JSON pairs: {valid_photos}")

        if not valid_photos:
            print("❌ No valid image+JSON pairs found.")
            return jsonify({"error": "No valid photo/question pairs found"}), 500

        chosen_photo = random.choice(valid_photos)
        base_name = os.path.splitext(chosen_photo)[0]
        json_path = os.path.join(PHOTO_DIR, base_name + '.json')

        print(f"🎯 Selected image: {chosen_photo}")
        print(f"📄 Expected JSON file: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            print(f"✅ Questions loaded: {questions}")
        except json.JSONDecodeError:
            print("❌ Invalid JSON format.")
            traceback.print_exc()
            return jsonify({"error": "Invalid JSON format in questions file"}), 500
        except Exception as e:
            print(f"❌ Error reading questions file: {str(e)}")
            traceback.print_exc()
            return jsonify({"error": f"Error reading questions file: {str(e)}"}), 500

        exam_data[ID] = {
            "status": "started",
            "photo": chosen_photo,
            "questions": questions
        }

        print(f"📝 Exam started for ID = {ID}")
        return jsonify({
            "message": "Exam started",
            "photo_assigned": chosen_photo,
            "questions": questions
        })

    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/get-status-sp-exam/<ID>', methods=['GET'])
def get_status_sp_exam(ID):
    """
    Возвращает статус экзамена для данного ID:
     - 'started', если запущен;
     - 'not started', если не найдена запись.
    """
    entry = exam_data.get(ID)
    if not entry:
        return jsonify({"status": "not started"})
    return jsonify({"status": entry["status"]})

@app.route('/api/get-sp-details/<ID>', methods=['GET'])
def get_sp_details(ID):
    """
    Возвращает детали экзамена:
     - Если запись для ID не существует — возвращает 404.
     - Если фото не назначено — возвращает 500.
     - Возвращает фото и вопросы в заголовках ответа.
    """
    entry = exam_data.get(ID)
    if not entry:
        return jsonify({"error": "Exam not started"}), 404

    photo_file = entry.get("photo")
    if not photo_file:
        return jsonify({"error": "Photo not assigned"}), 500

    questions_data = entry.get("questions", {})
    questions = questions_data.get("questions", [])  # Extract the array from the dict
    if not questions:
        return jsonify({"error": "No questions assigned"}), 500

    # Отправляем файл без кеширования
    response = make_response(
        send_from_directory(PHOTO_DIR, photo_file, as_attachment=False)
    )
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    print(f"Setting X-Questions header: {questions}")  # Debug log
    response.headers['X-Questions'] = json.dumps(questions, ensure_ascii=False)

    return response
    
@app.route('/api/speaking-exam-end/<ID>', methods=['POST'])
def speaking_exam_end(ID):
    """
    Завершает экзамен, сохраняет score (20,40,60,80 или 100) и выставляет статус = 'completed'
    """
    data = request.get_json() or {}
    score = data.get('score')
    if ID not in exam_data:
        return jsonify({"error": "Exam not started"}), 404
    if score not in (20, 40, 60, 80, 100):
        return jsonify({"error": "Invalid score"}), 400

    exam_data[ID]['status'] = 'completed'
    exam_data[ID]['score'] = score
    return jsonify({"message": "Exam ended", "score": score})
    
UPLOAD_DIR = os.path.join('static', 'speaking-files')
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/api/upload-speaking/<ID>', methods=['POST'])
def upload_speaking(ID):
    if ID not in exam_data:
        return jsonify({"error": "Exam not started"}), 404

    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400

    filename = f"{ID}.webm"
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)

    # сохраняем путь или флаг, если нужно
    exam_data[ID]['audio'] = filename
    return jsonify({"message": "File uploaded"}), 200

@app.route('/api/get-score-sp-exam/<ID>', methods=['GET'])
def get_score_sp_exam(ID):
    time.sleep(4)
    entry = exam_data.get(ID)
    if not entry or 'score' not in entry:
        # если оценка ещё не назначена, вернём 0
        return jsonify({"score": 0})
    return jsonify({"score": entry['score']})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
