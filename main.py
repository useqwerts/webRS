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

exam_duration = 60 * 60  # 30 minutes in seconds
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


# Initialize loggedUsers from file
loggedUsers = load_file(USER_DATA_FILE, {})
messages = load_file(MESSAGE_DATA_FILE, [])

active_sessions = {}  # Track active sessions by username

current_version = "2025-01-10-v1"

exam_questions = [
    {
        "id": 1,
        "type": "multiple_choice",
        "text": "What does 'absolutely' mean?",
        "options": [
            "used to emphasize that something is completely true",
            "something completely incorrect",
            "a synonym for 'slightly'"
        ],
        "correct": "used to emphasize that something is completely true"
    },
    {
        "id": 2,
        "type": "multiple_choice",
        "text": "What does 'accessible' mean?",
        "options": [
            "a place that can be entered, used, or seen",
            "something that is difficult to find",
            "something that is expensive"
        ],
        "correct": "a place that can be entered, used, or seen"
    },
    {
        "id": 3,
        "type": "multiple_choice",
        "text": "What is an 'action film'?",
        "options": [
            "a film that has a lot of exciting action and adventure",
            "a slow-moving drama film",
            "a film about everyday life"
        ],
        "correct": "a film that has a lot of exciting action and adventure"
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "text": "What is an 'action hero'?",
        "options": [
            "the main character of the film",
            "a side character",
            "a villain in the story"
        ],
        "correct": "the main character of the film"
    },
    {
        "id": 5,
        "type": "multiple_choice",
        "text": "What does 'addicted' mean?",
        "options": [
            "unable to stop using or doing something as a habit, especially something harmful",
            "interested in doing something occasionally",
            "being immune to something harmful"
        ],
        "correct": "unable to stop using or doing something as a habit, especially something harmful"
    },
    {
        "id": 6,
        "type": "multiple_choice",
        "text": "What does 'amusing' mean?",
        "options": [
            "something funny and giving pleasure",
            "something boring",
            "something painful to watch"
        ],
        "correct": "something funny and giving pleasure"
    },
    {
        "id": 7,
        "type": "multiple_choice",
        "text": "What is an 'app'?",
        "options": [
            "a piece of software that you can download to a device",
            "a type of phone call",
            "a network of computers"
        ],
        "correct": "a piece of software that you can download to a device"
    },
    {
        "id": 8,
        "type": "multiple_choice",
        "text": "What does 'appeal' mean?",
        "options": [
            "a quality that makes somebody/something attractive or interesting",
            "something that causes discomfort",
            "a formal complaint"
        ],
        "correct": "a quality that makes somebody/something attractive or interesting"
    },
    {
        "id": 9,
        "type": "multiple_choice",
        "text": "What does 'astonishing' mean?",
        "options": [
            "very surprising; difficult to believe",
            "something very small",
            "something very easy to understand"
        ],
        "correct": "very surprising; difficult to believe"
    },
    {
        "id": 10,
        "type": "multiple_choice",
        "text": "What does 'atmosphere' mean?",
        "options": [
            "the feeling or mood that you have in a particular place or situation",
            "the weather conditions outside",
            "the type of food served in a restaurant"
        ],
        "correct": "the feeling or mood that you have in a particular place or situation"
    },
    {
        "id": 11,
        "type": "multiple_choice",
        "text": "What does 'authentic' mean?",
        "options": [
            "known to be real and what somebody claims it is",
            "a fake version of something",
            "something that is highly decorated"
        ],
        "correct": "known to be real and what somebody claims it is"
    },
    {
        "id": 12,
        "type": "multiple_choice",
        "text": "What is a 'banker'?",
        "options": [
            "the one who works in a bank",
            "someone who manages a farm",
            "a person who sells tickets"
        ],
        "correct": "the one who works in a bank"
    },
    {
        "id": 13,
        "type": "multiple_choice",
        "text": "What does 'base on' mean?",
        "options": [
            "to use an idea, a fact, a situation, etc. as the point from which something can be developed",
            "to remove something from a situation",
            "to misunderstand the original idea"
        ],
        "correct": "to use an idea, a fact, a situation, etc. as the point from which something can be developed"
    },
    {
        "id": 14,
        "type": "multiple_choice",
        "text": "What does 'brilliant' mean?",
        "options": [
            "extremely clever or impressive",
            "something very dark and gloomy",
            "something very ordinary"
        ],
        "correct": "extremely clever or impressive"
    },
    {
        "id": 15,
        "type": "multiple_choice",
        "text": "What does 'cast' mean?",
        "options": [
            "the process of choosing actors to play different parts in a film, play, etc.",
            "the action of performing a play",
            "the script of a movie or play"
        ],
        "correct": "the process of choosing actors to play different parts in a film, play, etc."
    },
    {
        "id": 16,
        "type": "multiple_choice",
        "text": "What does 'character' mean?",
        "options": [
            "a person or an animal in a book, play or film",
            "the plot of a movie",
            "the environment of a story"
        ],
        "correct": "a person or an animal in a book, play or film"
    },
    {
        "id": 17,
        "type": "multiple_choice",
        "text": "What does 'chat' mean?",
        "options": [
            "to talk in a friendly, informal way to somebody",
            "to argue with someone",
            "to give instructions to someone"
        ],
        "correct": "to talk in a friendly, informal way to somebody"
    },
    {
        "id": 18,
        "type": "multiple_choice",
        "text": "What does 'classic' mean?",
        "options": [
            "accepted or deserving to be accepted as one of the best or most important of its kind",
            "something new and experimental",
            "something outdated"
        ],
        "correct": "accepted or deserving to be accepted as one of the best or most important of its kind"
    },
    {
        "id": 19,
        "type": "multiple_choice",
        "text": "What does 'clip' mean?",
        "options": [
            "a short part of a film that is shown separately",
            "a tool used to fasten things together",
            "a section of a movie script"
        ],
        "correct": "a short part of a film that is shown separately"
    },
    {
        "id": 20,
        "type": "multiple_choice",
        "text": "What does 'dash' mean?",
        "options": [
            "an act of going somewhere suddenly and/or quickly",
            "a slow, careful movement",
            "a jump or leap"
        ],
        "correct": "an act of going somewhere suddenly and/or quickly"
    },
    {
        "id": 21,
        "type": "multiple_choice",
        "text": "What does 'fantasise' mean?",
        "options": [
            "to imagine that you are doing something that you would like to do, or that something that you would like to happen is happening, even though this is very unlikely",
            "to think negatively about the future",
            "to daydream about a realistic situation"
        ],
        "correct": "to imagine that you are doing something that you would like to do, or that something that you would like to happen is happening, even though this is very unlikely"
    },
    {
        "id": 22,
        "type": "multiple_choice",
        "text": "What does 'genre' mean?",
        "options": [
            "a particular type or style of literature, art, film or music that you can recognize because of its special features",
            "a specific artist's name",
            "a type of food"
        ],
        "correct": "a particular type or style of literature, art, film or music that you can recognize because of its special features"
    },
    {
        "id": 23,
        "type": "multiple_choice",
        "text": "What does 'grow apart' mean?",
        "options": [
            "to stop having a close relationship with somebody over a period of time",
            "to grow closer to someone",
            "to move away from a place"
        ],
        "correct": "to stop having a close relationship with somebody over a period of time"
    },
    {
        "id": 24,
        "type": "multiple_choice",
        "text": "What does 'hand-held' mean?",
        "options": [
            "a device, especially a computer, that is small enough to be held in the hand while being used",
            "a computer placed on a desk",
            "a device for listening to music"
        ],
        "correct": "a device, especially a computer, that is small enough to be held in the hand while being used"
    },
    {
        "id": 25,
        "type": "multiple_choice",
        "text": "What does 'harmless' mean?",
        "options": [
            "unable or unlikely to cause damage or harm",
            "something dangerous",
            "something that causes harm to others"
        ],
        "correct": "unable or unlikely to cause damage or harm"
    },
    {
        "id": 26,
        "type": "multiple_choice",
        "text": "What does 'modern-day' mean?",
        "options": [
            "of the present time",
            "from the past",
            "related to future technology"
        ],
        "correct": "of the present time"
    },
    {
        "id": 27,
        "type": "multiple_choice",
        "text": "What does 'moving' mean?",
        "options": [
            "causing strong, often sad, feelings about somebody/something",
            "something that stays still",
            "a lighthearted action"
        ],
        "correct": "causing strong, often sad, feelings about somebody/something"
    },
    {
        "id": 28,
        "type": "multiple_choice",
        "text": "What does 'mug' mean?",
        "options": [
            "to violently steal from somebody, especially in a public place",
            "to make something very expensive",
            "to move slowly in a crowd"
        ],
        "correct": "to violently steal from somebody, especially in a public place"
    },
    {
        "id": 29,
        "type": "multiple_choice",
        "text": "What does 'novel' mean?",
        "options": [
            "a story long enough to fill a complete book, in which the characters and events are usually imaginary",
            "a short story told in a film",
            "a brief poem"
        ],
        "correct": "a story long enough to fill a complete book, in which the characters and events are usually imaginary"
    },
    {
        "id": 30,
        "type": "multiple_choice",
        "text": "What does 'on balance' mean?",
        "options": [
            "after considering all the information",
            "the final decision made without consideration",
            "a first impression of something"
        ],
        "correct": "after considering all the information"
    },
    {
        "id": 31,
        "type": "multiple_choice",
        "text": "What does 'original' mean?",
        "options": [
            "existing at the beginning or a particular period, process or activity",
            "something that has been copied",
            "something that is second-hand"
        ],
        "correct": "existing at the beginning or a particular period, process or activity"
    },
    {
        "id": 32,
        "type": "multiple_choice",
        "text": "What does 'performance' mean?",
        "options": [
            "the act of performing a play, concert or some other form of entertainment",
            "the way someone drives a car",
            "the way someone dresses"
        ],
        "correct": "the act of performing a play, concert or some other form of entertainment"
    },
    {
        "id": 33,
        "type": "multiple_choice",
        "text": "What does 'plot' mean?",
        "options": [
            "the series of events that form the story of a novel, play, film, etc.",
            "a section of a screenplay",
            "the audience's reaction to a film"
        ],
        "correct": "the series of events that form the story of a novel, play, film, etc."
    },
    {
        "id": 34,
        "type": "multiple_choice",
        "text": "What does 'post' mean?",
        "options": [
            "to put information or pictures on a website",
            "to read information on a website",
            "to send a letter by mail"
        ],
        "correct": "to put information or pictures on a website"
    },
    {
        "id": 35,
        "type": "multiple_choice",
        "text": "What does 'pothole' mean?",
        "options": [
            "a large rough hole in the surface of a road that is formed by traffic and bad weather",
            "a large crack in a building",
            "a deep hole in the ground used for storage"
        ],
        "correct": "a large rough hole in the surface of a road that is formed by traffic and bad weather"
    },
    {
        "id": 36,
        "type": "multiple_choice",
        "text": "What does 'predictable' mean?",
        "options": [
            "if something is predictable, you know in advance that it will happen or what it will be like",
            "if something is spontaneous and unexpected",
            "something that is fun to watch"
        ],
        "correct": "if something is predictable, you know in advance that it will happen or what it will be like"
    },
    {
        "id": 37,
        "type": "multiple_choice",
        "text": "What is a 'prisoner'?",
        "options": [
            "a person who is kept in prison as a punishment or while waiting for trial",
            "someone who is free from arrest",
            "someone who is on vacation"
        ],
        "correct": "a person who is kept in prison as a punishment or while waiting for trial"
    },
    {
        "id": 38,
        "type": "multiple_choice",
        "text": "What does 'recommend' mean?",
        "options": [
            "to tell somebody that something is good or useful or that somebody would be suitable for a particular job",
            "to criticize someone",
            "to avoid giving advice"
        ],
        "correct": "to tell somebody that something is good or useful or that somebody would be suitable for a particular job"
    },
    {
        "id": 39,
        "type": "multiple_choice",
        "text": "What does 'release' mean?",
        "options": [
            "to let somebody come out of a place where they have been kept or stuck and unable to leave or move",
            "to lock someone in a room",
            "to hide something"
        ],
        "correct": "to let somebody come out of a place where they have been kept or stuck and unable to leave or move"
    },
    {
        "id": 40,
        "type": "multiple_choice",
        "text": "What does 'remake' mean?",
        "options": [
            "a new or different version of an old film or song",
            "a new version of a document",
            "to build a house from scratch"
        ],
        "correct": "a new or different version of an old film or song"
    },
    {
        "id": 41,
        "type": "multiple_choice",
        "text": "What does 'result in' mean?",
        "options": [
            "lead to",
            "prevent",
            "limit"
        ],
        "correct": "lead to"
    },
    {
        "id": 42,
        "type": "multiple_choice",
        "text": "What is a 'rom com'?",
        "options": [
            "a humorous film or TV show that is about love; a romantic comedy",
            "a horror film",
            "a documentary"
        ],
        "correct": "a humorous film or TV show that is about love; a romantic comedy"
    },
    {
        "id": 43,
        "type": "multiple_choice",
        "text": "What does 'salsa' mean?",
        "options": [
            "a type of Latin American dance music",
            "a type of Italian pizza",
            "a type of dessert"
        ],
        "correct": "a type of Latin American dance music"
    },
    {
        "id": 44,
        "type": "multiple_choice",
        "text": "What does 'scene' mean?",
        "options": [
            "a part of a film, play or book in which the action happens in one place or is of one particular type",
            "a part of a song",
            "a collection of events in real life"
        ],
        "correct": "a part of a film, play or book in which the action happens in one place or is of one particular type"
    },
    {
        "id": 45,
        "type": "multiple_choice",
        "text": "What does 'set out' mean?",
        "options": [
            "to leave a place and begin a journey",
            "to stay in one place",
            "to decide not to go anywhere"
        ],
        "correct": "to leave a place and begin a journey"
    },
    {
        "id": 46,
        "type": "multiple_choice",
        "text": "What does 'showcase' mean?",
        "options": [
            "to present somebody's abilities or the good qualities of something in an attractive way",
            "to hide something",
            "to destroy something"
        ],
        "correct": "to present somebody's abilities or the good qualities of something in an attractive way"
    },
    {
        "id": 47,
        "type": "multiple_choice",
        "text": "What does 'silly' mean?",
        "options": [
            "showing a lack of thought, understanding, or judgement",
            "wise and thoughtful",
            "extremely careful"
        ],
        "correct": "showing a lack of thought, understanding, or judgement"
    },
    {
        "id": 48,
        "type": "multiple_choice",
        "text": "What does 'skyscraper' mean?",
        "options": [
            "a very tall building in a city",
            "a type of bridge",
            "a large car"
        ],
        "correct": "a very tall building in a city"
    },
    {
        "id": 49,
        "type": "multiple_choice",
        "text": "What does 'soundtrack' mean?",
        "options": [
            "all the music, speech and sounds that are recorded for a film",
            "the special effects of a film",
            "the background dialogue"
        ],
        "correct": "all the music, speech and sounds that are recorded for a film"
    },
    {
        "id": 50,
        "type": "multiple_choice",
        "text": "What does 'slavery' mean?",
        "options": [
            "the state of being forced to work as a slave",
            "a voluntary job position",
            "the ability to travel freely"
        ],
        "correct": "the state of being forced to work as a slave"
    },
    {
        "id": 51,
        "type": "multiple_choice",
        "text": "What does 'stunning' mean?",
        "options": [
            "extremely attractive or impressive",
            "extremely loud",
            "dangerously quick"
        ],
        "correct": "extremely attractive or impressive"
    },
    {
        "id": 52,
        "type": "multiple_choice",
        "text": "What does 'sweep' mean?",
        "options": [
            "to move quickly and/or smoothly, especially in a way that impresses or is intended to impress other people",
            "to make something dirty",
            "to stop something from moving"
        ],
        "correct": "to move quickly and/or smoothly, especially in a way that impresses or is intended to impress other people"
    },
    {
        "id": 53,
        "type": "multiple_choice",
        "text": "What does 'tend' mean?",
        "options": [
            "to be likely to do something or to happen in a particular way because this is what often or usually happens",
            "to avoid doing something",
            "to ignore something"
        ],
        "correct": "to be likely to do something or to happen in a particular way because this is what often or usually happens"
    },
    {
        "id": 54,
        "type": "multiple_choice",
        "text": "What does 'terrific' mean?",
        "options": [
            "excellent, wonderful",
            "boring, dull",
            "disastrous, terrible"
        ],
        "correct": "excellent, wonderful"
    },
    {
        "id": 55,
        "type": "multiple_choice",
        "text": "What does 'terrifying' mean?",
        "options": [
            "making somebody feel extremely frightened",
            "making somebody feel calm",
            "making somebody feel joyful"
        ],
        "correct": "making somebody feel extremely frightened"
    },
    {
        "id": 56,
        "type": "multiple_choice",
        "text": "What is a 'thriller'?",
        "options": [
            "a book, play or film with an exciting story, especially one about crime or spying",
            "a documentary about animals",
            "a musical performance"
        ],
        "correct": "a book, play or film with an exciting story, especially one about crime or spying"
    },
    {
        "id": 57,
        "type": "multiple_choice",
        "text": "What does 'unexciting' mean?",
        "options": [
            "not interesting; boring",
            "extremely thrilling",
            "extremely loud"
        ],
        "correct": "not interesting; boring"
    },
    {
        "id": 58,
        "type": "multiple_choice",
        "text": "What does 'violent' mean?",
        "options": [
            "involving or caused by physical force that is intended to hurt or kill somebody",
            "calm and peaceful",
            "involving only verbal disagreement"
        ],
        "correct": "involving or caused by physical force that is intended to hurt or kill somebody"
    },
    {
        "id": 59,
        "type": "multiple_choice",
        "text": "What does 'voice' mean?",
        "options": [
            "to produce a sound with a movement of your vocal cords as well as your breath",
            "to listen carefully",
            "to ignore someone's speech"
        ],
        "correct": "to produce a sound with a movement of your vocal cords as well as your breath"
    },
    {
        "id": 60,
        "type": "multiple_choice",
        "text": "What does 'vote' mean?",
        "options": [
            "to show formally by making a paper, raising your hand or using a voting machine, etc. which person or political party you want in an election, or which idea you support",
            "to guess something without any proof",
            "to ignore something in an election"
        ],
        "correct": "to show formally by making a paper, raising your hand or using a voting machine, etc. which person or political party you want in an election, or which idea you support"
    },
    {
        "id": 61,
        "type": "multiple_choice",
        "text": "What does 'world-wide' mean?",
        "options": [
            "widespread around the world",
            "limited to one city",
            "only in one country"
        ],
        "correct": "widespread around the world"
    },
    {
        "id": 62,
        "type": "multiple_choice",
        "text": "What does 'adaptation' mean?",
        "options": [
            "a film, book, play, etc. that has been made from another film, book, play, etc.",
            "a new version of the same product",
            "a work with no changes from the original"
        ],
        "correct": "a film, book, play, etc. that has been made from another film, book, play, etc."
    },
    {
        "id": 63,
        "type": "multiple_choice",
        "text": "What does 'beverage' mean?",
        "options": [
            "a drink of any type",
            "a type of food",
            "a solid snack"
        ],
        "correct": "a drink of any type"
    },
    {
        "id": 64,
        "type": "multiple_choice",
        "text": "What does 'crossover' mean?",
        "options": [
            "the process or result of changing from one activity or style to another",
            "a sudden stop",
            "the exchange of goods"
        ],
        "correct": "the process or result of changing from one activity or style to another"
    },
    {
        "id": 65,
        "type": "multiple_choice",
        "text": "What does 'engagement' mean?",
        "options": [
            "an arrangement to meet someone or do something at a particular time",
            "a feeling of complete boredom",
            "a surprise announcement"
        ],
        "correct": "an arrangement to meet someone or do something at a particular time"
    },
    {
        "id": 66,
        "type": "multiple_choice",
        "text": "What does 'epic' mean?",
        "options": [
            "in the style of an epic; a film, poem or book which is long and contains a lot of action, usually dealing with a historical subject",
            "a short, fast-paced story",
            "an average movie with no special features"
        ],
        "correct": "in the style of an epic; a film, poem or book which is long and contains a lot of action, usually dealing with a historical subject"
    },
    {
        "id": 67,
        "type": "multiple_choice",
        "text": "What does 'gambling' mean?",
        "options": [
            "the activity of betting money, for example in a game or on a horse race",
            "the act of playing board games",
            "a process of calculating odds"
        ],
        "correct": "the activity of betting money, for example in a game or on a horse race"
    },
    {
        "id": 68,
        "type": "multiple_choice",
        "text": "What does 'merchandising' mean?",
        "options": [
            "products connected with a popular film, singer, event, etc., or the selling of these products",
            "a way of producing films",
            "the creation of video games"
        ],
        "correct": "products connected with a popular film, singer, event, etc., or the selling of these products"
    },
    {
        "id": 69,
        "type": "multiple_choice",
        "text": "What does 'parody' mean?",
        "options": [
            "writing, music, art, an act, etc. which humorously imitates the style of someone famous or copies a particular situation, making the features or qualities of the original more noticeable in a way that is humorous",
            "a serious and dramatic performance",
            "an artistic expression with no humor"
        ],
        "correct": "writing, music, art, an act, etc. which humorously imitates the style of someone famous or copies a particular situation, making the features or qualities of the original more noticeable in a way that is humorous"
    },
    {
        "id": 70,
        "type": "multiple_choice",
        "text": "What does 'prequel' mean?",
        "options": [
            "a film, book or play which develops the story of an earlier film, etc. by telling you what happened before the events in the first film",
            "a film, book or play that continues the story of a previous work",
            "a film that takes place at the same time as the original"
        ],
        "correct": "a film, book or play which develops the story of an earlier film, etc. by telling you what happened before the events in the first film"
    },
    {
        "id": 71,
        "type": "multiple_choice",
        "text": "What does 'recreation' mean?",
        "options": [
            "(a way of) enjoying yourself when you are not working",
            "a type of job",
            "a formal event"
        ],
        "correct": "(a way of) enjoying yourself when you are not working"
    },
    {
        "id": 72,
        "type": "multiple_choice",
        "text": "What does 'sequel' mean?",
        "options": [
            "a book, film or play which continues the story of a previous book",
            "a new version of an older story",
            "a prequel to an earlier event"
        ],
        "correct": "a book, film or play which continues the story of a previous book"
    },
    {
        "id": 73,
        "type": "multiple_choice",
        "text": "What does 'wholesome' mean?",
        "options": [
            "good for you, and likely to improve your life either physically, morally or emotionally",
            "harmful or dangerous",
            "something that makes you feel tired"
        ],
        "correct": "good for you, and likely to improve your life either physically, morally or emotionally"
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
    print(f"Temporary ban for {username} for {duration} seconds")
    # Эмиттируем событие обратно клиенту с именем пользователя и длительностью
    socketio.emit('tempBanUser', {'username': username, 'duration': duration})


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

@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the user is banned
        if username in banned_users:
            return render_template('login.html', error="Your account is banned.")

        # Check if the user has accepted the Terms and Conditions
        if username not in Accepted_users:
            return render_template('login.html', error="You must accept the Terms and Conditions to proceed.")

        # Validate username and password
        if username in loggedUsers and loggedUsers[username] == password:
            # Collect device information
            device_info = {
                'User-Agent': request.headers.get('User-Agent'),
                'IP-Address': request.headers.get('X-Forwarded-For', request.remote_addr),
                'Language': request.headers.get('Accept-Language'),
                'Platform': platform.system(),
                'OS': platform.version(),
                'Device-Type': 'Mobile' if 'Mobi' in request.headers.get('User-Agent') else 'Desktop'
            }

            # Manage active sessions
            if username in active_sessions:
                active_sessions[username].append(device_info)
            else:
                active_sessions[username] = [device_info]

            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')
    
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


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
