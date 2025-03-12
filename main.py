from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session 
from flask_socketio import SocketIO, emit
import os
import json
import platform
import time
import requests 
from datetime import datetime , timedelta
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Initialize app and socket
app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'txt', 'pdf','mp3','wav'}
socketio = SocketIO(app)
CORS(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize messages as an empty list, not a dictionary
messages = []  # Store messages locally

exam_duration = 10 * 60  # 30 minutes in seconds
exam_start_time = None  # Global variable to store exam start time
exam_started = False  # Флаг начала экзамена
exam_end_time = None

tracks = [
    {'title': 'Karina va Jambul Buxoro Yigitlari', 'url': '/static/music/BuxoroYigitlari.mp3'},
    {'title': 'Ziyoda - Tor Kocha', 'url': '/static/music/Ziyoda_Tor_kocha.mp3'},
    {'title': 'Ziyoda - Meni deb', 'url': '/static/music/Ziyoda_Menideb.mp3'},
    {'title': 'Yulduz Usmonova Biyo Biyo', 'url': '/static/music/YulduzBiyo.mp3'},
    {'title': 'Billie Eilish - WILDFLOWER ', 'url': '/static/music/Billie_Eilish_WILDFLOWER.mp3'},
    {'title': 'Billie Eilish - BIRDS OF A FEATHER ', 'url': '/static/music/Billie_Eilish_BIRDS_OF_A_FEATHER.mp3'}, 
    {'title': 'Lenka - Everything At Once', 'url': '/static/music/Lenka - Everything At Once.mp3'},
    {'title': 'Jambul Madam', 'url': '/static/music/Jambul Madam.mp3'},
    {'title': 'Ozoda - Dilbarim', 'url': '/static/music/Ozoda - Dilbarim.mp3'},
    {'title': 'Shawn Mendes - Señorita', 'url': '/static/music/Shawn Mendes Senorita.mp3'},
    {'title': 'Andreea Bostanica feat.  HAVANA & Yaar - Supergirl', 'url': '/static/music/Andreea Bostanica feat.  HAVANA & Yaar - Supergirl.mp3'},
    {'title': 'YAAR feat KAiiA & ADEN - Shıkıdım', 'url': '/static/music/YAAR feat KAiiA & ADEN - Shıkıdım.mp3'},
    {'title': 'Bruninho Mars - Bonde do Brunao', 'url': '/static/music/Bruninho Mars - Bonde do Brunao.mp3'},
]

USER_DATA_FILE = "users.json"
MESSAGE_DATA_FILE = "messages.json"
banned_users = []
exam_passed = []

AVATAR_FOLDER = "static/avatars"
USER_AVATAR_FILE = "users_avatar.json"

app.config["AVATAR_FOLDER"] = AVATAR_FOLDER
app.config["ALLOWED_IMAGE_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

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
    time.sleep(2)  # Simulate delay, you can adjust or remove this

    # Получаем прогресс всех студентов
    progress_data = get_student_progress()  # Предполагается, что эта функция возвращает словарь всех студентов и их прогресса

    if not progress_data:
        return jsonify({"error": "No student progress data found"}), 404  # Если данных нет, возвращаем ошибку

    # Подготовка данных для таблицы
    leaderboard = {}

    for student, data in progress_data.items():
        leaderboard[student] = {
            "progress": data.get("progress", 0),
            "start_date": data.get("start_date", None),
            "study_days": data.get("study_days", "odd")  # Default "odd" if not provided
        }

    # Возвращаем все данные о студентах в формате JSON
    return jsonify(leaderboard)

@app.route('/api/get-student-progress', methods=['GET'])
def get_progress():
    time.sleep(2)
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


@socketio.on('ban_user')
def handle_ban_user(username):
    if username:
        if username not in banned_users:
            banned_users.append(username)
            emit('user_banned', {'success': True, 'username': username}, broadcast=True)  # Сообщение всем клиентам
            print(f'User {username} has been banned')
        else:
            emit('user_banned', {'success': False, 'message': 'User is already banned'}, to=request.sid)  # Только отправителю
    else:
        emit('user_banned', {'success': False, 'message': 'Username is required'}, to=request.sid)  # Только отправителю

@app.route('/api/check-ban-status', methods=['POST'])
def check_ban_status():
    try:
        data = request.get_json()
        username = data.get('username')

        if not username:
            return jsonify({'error': 'Username is required'}), 400

        if username in banned_users:  # Проверяем, есть ли пользователь в списке
            return jsonify({'banned': True}), 200
        else:
            return jsonify({'banned': False}), 200

    except Exception as e:
        print(f"Error checking ban status: {e}")
        return jsonify({'error': 'An error occurred'}), 500
        
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
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            return json.load(f)
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

    # If user does not exist, initialize balance and transaction list.
    if username not in balances:
        balances[username] = 0.0
    if username not in transactions:
        transactions[username] = []

    # Update balance
    balances[username] += amount

    # Create a transaction record
    transaction_record = {
        "amount": amount,
        "description": description,
        "time": datetime.utcnow().isoformat()
    }
    transactions[username].append(transaction_record)

    # Save the updated data back to their respective files.
    store_balances(balances)
    store_transactions(transactions)

    return jsonify({
        "message": "Transaction added",
        "new_balance": balances[username]
    })

# Initialize loggedUsers from file
loggedUsers = load_file(USER_DATA_FILE, {})
messages = load_file(MESSAGE_DATA_FILE, [])

active_sessions = {}  # Track active sessions by username

current_version = "2025-01-10-v1"

exam_questions = [
    {
        "id":
        1,
        "text":
        "Listen and choose correct answer.",
        "type":
        "listening",  # Вопрос на аудирование
        "audio":
        "/static/exam/ElonMusk.mp3",  # Путь к файлу mp3, который нужно будет проигрывать на клиенте.
        "subquestions": [{
            "id": "1.1",
            "type": "multiple_choice",
            "text": "Who is this?",
            "options": ["Elon", "Elon Musk", "Tesla"],
            "correct": "Elon Musk"
        }, {
            "id": "1.2",
            "type": "true_false",
            "text": "Tesla's Founder and not a CEO",
            "correct": "False"
        }, {
            "id": "1.3",
            "type": "question",
            "text": "Elon is ______ ( One word only )",
            "correct": "inventor"
        }, {
            "id": "1.4",
            "type": "true_false",
            "text": "Is ELon genuise human?",
            "correct": "True"
        }, {
            "id":
            "1.5",
            "type":
            "multiple_choice",
            "text":
            "When critics say 'you can't do this' what did you answer Elon? ",
            "options":
            ["We have done it", "We've did it", "None of this answers."],
            "correct":
            "We have done it"
        }]
    },
    {
        "id":
        2,
        "text":
        "Listen and choose correct answer.",
        "type":
        "listening",  # Вопрос на аудирование
        "audio":
        "/static/exam/four.mp3",  # Путь к файлу mp3, который нужно будет проигрывать на клиенте.
        "subquestions": [{
            "id": "2.1",
            "type": "multiple_choice",
            "text": "What do you hear?",
            "options": ["49", "94", "iPhone", "fortnite"],
            "correct": "fortnite"
        }]
    },
    {
        "id":
        3,
        "type":
        "reading",
        "text":
        """ Section 1. Reading Passage
        <h1>Traditions around the world</h1>

<h2>The Kukeri Festival</h2>
<p>
  The Kukeri Festival is one of the oldest traditions in Bulgaria. It happens every year in winter. Men wear special costumes and wear big, scary masks that look like animals. The men dance and make loud noises with bells. They do this to scare away bad spirits and bring good luck for the new year. The Kukeri Festival is very colourful and exciting. People come from around the world to see it. The festival is a big part of Bulgarian culture and helps keep old traditions alive.
</p>

<h2>The Day of the Dead</h2>
<p>
  The Day of the Dead is a special holiday in Mexico. It happens every year on November 1st and 2nd. People remember and honour their family members who have died. They believe that on these days, their spirits come back to visit. Families make altars with photos, flowers, candles, and food. Bread of the Dead is a popular recipe. Some people also paint their faces to look like skeletons and dress in colourful clothes. The Day of the Dead is a happy celebration, not a sad one. It is a way to celebrate life and remember the past.
</p>

<h2>La Tomatina</h2>
<p>
  Every year, on the last Wednesday of August, the quiet village of Buñol, Spain, becomes busy and full of people. Everyone goes out to the streets to throw tomatoes at each other. It is a big, fun food fight! The festival lasts about one hour, and everyone gets very dirty, so they all wear old clothes. Before the tomato fight, there are other activities, like parades and music. After the battle, the streets are covered in tomato juice, but they get cleaned.
</p>
""",
        "subquestions": [{
            "id": "3.1",
            "type": "question",
            "text": "Which festival celebrates the visit of spirits?",
            "correct": "The Day of the Dead"
        }, {
            "id": "3.2",
            "type": "question",
            "text": "At which festival do people hide their faces?",
            "correct": "The Kukeri Festival"
        }, {
            "id": "3.3",
            "type": "question",
            "text": "Which festival is popular among tourists?",
            "correct": "The Kukeri Festival"
        }, {
            "id": "3.4",
            "type": "question",
            "text": "Which festival is the shortest?",
            "correct": "La Tomatina"
        }, {
            "id": "3.5",
            "type": "question",
            "text": "Which festival happens at the beginning of the year?",
            "correct": "The Kukeri Festival"
        }, {
            "id":
            "3.6",
            "type":
            "multiple_choice",
            "text":
            "Which festival is about the past?",
            "options":
            ["The Kukeri Festival", "The Day of the Dead", "La Tomatina"],
            "correct":
            "The Day of the Dead"
        }]
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "text": "If today is Wednesday, what day will it be in 10 days?",
        "options": ["Saturday", "Sunday", "Monday"],
        "correct": "Monday"
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


@socketio.on('apply_theme')
def apply_theme(data):
    username = data['username']
    theme = data['theme']
    price = data['price']
    
    balance = load_balance()
    bought_themes = load_bought_themes()
    
    if username in balance and balance[username] >= price:
        # Если тема не куплена ранее
        if username not in bought_themes:
            bought_themes[username] = []

        if theme not in bought_themes[username]:
            # Если у пользователя еще нет этой темы, списываем монеты
            balance[username] -= price
            bought_themes[username].append(theme)  # Добавляем тему в список купленных
            save_balance(balance)
            save_bought_themes(bought_themes)  # Сохраняем обновленные данные

            # Отправляем подтверждение клиенту
            emit('theme_applied', {'success': True, 'coins': balance[username], 'theme': theme}, room=request.sid)
        else:
            # Если тема уже куплена, применяем ее без списания монет
            emit('theme_applied', {'success': True, 'coins': balance[username], 'theme': theme, 'already_purchased': True}, room=request.sid)
    else:
        emit('theme_applied', {'success': False, 'message': 'Not enough coins.'}, room=request.sid)

# Получение списка купленных тем при открытии модального окна
@socketio.on('get_bought_themes')
def get_bought_themes(data):
    username = data['username']
    bought_themes = load_bought_themes()

    if username in bought_themes:
        emit('bought_themes', {'success': True, 'themes': bought_themes[username]})
    else:
        emit('bought_themes', {'success': False, 'message': 'No themes purchased yet.'})

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
        exam_passed.clear()
        
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

@socketio.on('exam_started')
def handle_exam_started():
    global exam_started
    exam_started = True
    emit('exam_started', {'message': 'Exam has started'}) 

@app.route('/api/start-exam', methods=['POST'])
def start_exam():
    global exam_start_time, exam_end_time, exam_passed

    # Время начала экзамена
    exam_start_time = time.time()

    # Рассчитываем время окончания экзамена + 10 секунд
    exam_end_time = exam_start_time + exam_duration + 10  

    # Очищаем список пользователей, которые прошли экзамен
    exam_passed.clear()

    # Отправляем сообщение о старте экзамена
    socketio.emit('exam_started', {'message': 'Exam has started'})  # Исправленный emit

    return jsonify({"message": "Exam has started and the passed list is cleared."}), 200


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
    time.sleep(1)  # Имитация задержки загрузки

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

        time.sleep(1)
        data = request.get_json(silent=True)
        answers = data.get("answers")
        username = data.get("username")

        if not answers or not username:
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



@app.route("/chatCRM")
def crm():
    return render_template("chatCRM.html")

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
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Проверка на заблокированных пользователей
    if username in banned_users:
        return render_template('login.html', error="Your account is banned.")  # Ошибка, если пользователь заблокирован

    # Проверка на правильность введенного имени и пароля
    if username in loggedUsers and loggedUsers[username] == password:
        # Собираем более подробную информацию о устройстве
        device_info = {
            'User-Agent': request.headers.get('User-Agent'),
            'IP-Address': request.headers.get('X-Forwarded-For', request.remote_addr),
            'Language': request.headers.get('Accept-Language'),
            'Platform': platform.system(),  # Используем платформу из Python
            'OS': platform.version(),  # Версия операционной системы
            'Device-Type': 'Mobile' if 'Mobi' in request.headers.get('User-Agent') else 'Desktop'
        }

        # Если пользователь уже в системе, но с другого устройства
        if username in active_sessions:
            active_sessions[username].append(device_info)  # Добавляем информацию об устройстве
        else:
            active_sessions[username] = [device_info]  # Добавляем пользователя и информацию об устройстве

        session['username'] = username
        return redirect(url_for('chat'))
    else:
        return render_template('login.html', error="Invalid username or password")

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

@app.route('/chat')
def chat():
    if 'username' not in session:
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
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Broadcast file info
        message = {
            'type': 'file',
            'filename': filename,
            'url': f'/uploads/{filename}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'username': session.get('username', 'Anonymous')
        }
        messages.append(message)
        socketio.emit('new_message', message)

        return jsonify({'success': True, 'url': f'/uploads/{filename}'})

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
                "finalExam": 0,
                "weeklyExams": 0,
                "totalScore": 0
            }
        }), 200

    # Берём последнюю запись
    last_record = user_history[-1]
    final_exam = last_record.get("finalExam", 0)
    weekly_exams = last_record.get("weeklyExams", 0)
    total_score = final_exam + weekly_exams

    return jsonify({
        username: {
            "finalExam": final_exam,
            "weeklyExams": weekly_exams,
            "totalScore": total_score
        }
    }), 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
