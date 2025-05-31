from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session , send_file, abort
from flask_socketio import SocketIO, emit
import os
import json
import platform
import time
import requests 
import random
from datetime import datetime , timedelta
from flask_cors import CORS
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import send_from_directory, make_response

# Initialize app and socket
app = Flask(__name__)
app.secret_key = os.urandom(32)
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

exam_duration = 90 * 60  # 30 minutes in seconds
exam_start_time = None  # Global variable to store exam start time
exam_started = False  # Флаг начала экзамена
exam_end_time = None


USER_DATA_FILE = "users.json"
MESSAGE_DATA_FILE = "messages.json"
banned_users = []
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
  "text": "Section 1. Listen and complete the information about the day trip.",
  "type": "listening",
  "audio": "/static/exam-files/Preliminary1_test3_audio3.mp3",
  "subquestions": [
    {
      "id": "1.14",
      "type": "write-in-blank",
      "text": "Bus leaves at: (14) ____ a.m.",
      "correct": "8.15"
    },
    {
      "id": "1.15",
      "type": "write-in-blank",
      "text": "Meet before trip at: hotel (15) ____",
      "correct": "entrance"
    },
    {
      "id": "1.16",
      "type": "write-in-blank",
      "text": "First stop: ruin of a (16) ____",
      "correct": "palace"
    },
    {
      "id": "1.17",
      "type": "write-in-blank",
      "text": "Lunch at: The (17) ____ Restaurant",
      "correct": "Wakizi"
    },
    {
      "id": "1.18",
      "type": "write-in-blank",
      "text": "Afternoon activity: (18) ____ or beach volleyball",
      "correct": "diving"
    },
    {
      "id": "1.19",
      "type": "write-in-blank",
      "text": "Bring: (19) ____",
      "correct": "sun cream"
    }
  ]
},
    {
  "id": 2,
  "type": "reading",
  "text": "<h1>A Town that Lives in One Building</h1>\n<p>Located in the beautiful state of Alaska, a little town called Whittier is tucked away in a picturesque area surrounded by mountains and the ocean. This hidden gem is hard to reach: the only ways to and from Whittier are either by ferry or through a one-lane tunnel that cuts through the mountains. This tunnel is unique because it is shared by both vehicles and trains, necessitating a precisely managed schedule to accommodate both modes of transportation and both directions of traffic.</p>\n\n<p>Whittier’s economy thrives on its port, the town’s main source of employment, where cargo ships drop off their containers for rail transportation across Alaska. The town also has a grocery store, a museum, two hotels, and various other job opportunities for all its citizens: police officers, municipal workers, educators at the local school, and marina staff. Tourism has grown over the last few years to become an alternative source of income, drawing visitors to attractions such as the Anton Anderson Memorial Tunnel, glacier jet ski tours, and scenic boat excursions that offer breathtaking views of marine wildlife and icebergs.</p>\n\n<p>But the most fascinating aspect of Whittier is perhaps the fact that nearly all of its 200-odd residents live under the same roof. The Begich Towers, a 14-story building, is more than just an apartment complex; it’s a self-contained town! The harsh winter weather helps to explain the convenience of this unusual way of living. Whittier’s winter months are known for their heavy snowfalls and fierce winds. By having all the necessary facilities and services in one building, the residents don’t have to brave the cold weather every time they need to run an errand or go to church. Not even the children need to step outside to attend school, which is in an adjacent building connected through a tunnel. It’s an ingenious solution that makes life in such an extreme climate much more manageable.</p>\n\n<p>However, the origins of Whittier’s unique living situation date back to the early last century when the area was chosen for a military base. Shielded by towering mountains and situated by a bay with unfreezing waters, this location offered an ideal strategic position. Initially, wooden camps housed the soldiers, but as the need for more permanent structures grew with the increasing population, two significant buildings were erected: the once largest building in Alaska, the Buckner Building, and the Begich Towers. The construction of the tunnel in the 1940s, intended to provide railway access, marked Whittier’s transformation into an essential cargo and passenger port. After the military left in the 1960s, the Buckner Building was abandoned, and the Begich Towers became the main residential and communal space for the town’s inhabitants.</p>\n\n<p>Nowadays, Whittier’s residents just need to hop on the elevator to go grocery shopping, visit the police station, or eat ‘out’—though in this case, ‘eat in’ might be more accurate. There’s even a health clinic, which is far from being a hospital but more than enough for minor ailments. In essence, everything the residents may need is a few steps away from their homes. Living in Begich Towers offers a sense of community and convenience that is hard to find elsewhere. The close proximity of homes and businesses fosters a strong bond among the residents. Whether they’re sharing a cup of coffee at the café on the ground floor or attending a community meeting, the people of Whittier have created a unique and supportive environment.</p>\n\n<p>Whittier might be small, but it’s a remarkable example of adaptability and community spirit. Its single-building town, surrounded by Alaska’s breathtaking landscape, is a testament to human ingenuity and resilience.</p>",
  "subquestions": [
    {
      "id": "2.1",
      "type": "multiple_choice",
      "text": "Which adjective would better describe Whittier?",
      "options": ["remote", "reachable", "mountainous"],
      "correct": "remote"
    },
    {
      "id": "2.2",
      "type": "multiple_choice",
      "text": "If you are going to Whittier through the tunnel...",
      "options": [
        "your only option is to take a train.",
        "you can't use the tunnel while other people are leaving.",
        "you can go by car at any time."
      ],
      "correct": "you can't use the tunnel while other people are leaving."
    },
    {
      "id": "2.3",
      "type": "multiple_choice",
      "text": "Most people in Whittier work in...",
      "options": ["the shipping industry", "tourism", "services"],
      "correct": "the shipping industry"
    },
    {
      "id": "2.4",
      "type": "multiple_choice",
      "text": "According to the text,...",
      "options": [
        "having a town in one building is not ideal.",
        "the school is in the same building.",
        "the town's church is in the Begich Towers."
      ],
      "correct": "the town's church is in the Begich Towers."
    },
    {
      "id": "2.5",
      "type": "multiple_choice",
      "text": "The towers were built...",
      "options": [
        "to protect the soldiers from the weather.",
        "to accommodate an expanding population.",
        "to mark Whittier's transformation."
      ],
      "correct": "to accommodate an expanding population."
    },
    {
      "id": "2.6",
      "type": "multiple_choice",
      "text": "Which of these can you NOT find in Begich Towers?",
      "options": ["a restaurant", "a hospital", "a supermarket"],
      "correct": "a hospital"
    }
  ]
},
{
  "id": 3,
  "type": "reading",
  "text": "<h1>Actors who died on set</h1>\n\n<p><strong>Brandon Lee</strong><br>Brandon Lee, son of the famous martial artist and actor Bruce Lee, died in 1993, while filming “The Crow”. He was acting as the main character in a scene where his character gets shot, but no one knew that a small piece of a real bullet got stuck in the gun. When the gun was fired, the piece of the bullet came out and hit Brandon in the stomach. Even though doctors tried to help him, Lee passed away later that day. This accident made people think more about how to keep actors safe on movie sets.</p>\n\n<p><strong>Vic Morrow</strong><br>Vic Morrow’s death happened during the filming of “Twilight Zone: The Movie” in 1982. He portrayed a character in the Vietnam War. In this scene, Morrow was carrying two child actors across a river while being chased by a helicopter. During filming, explosives were used, causing the helicopter to crash in the river. As a result, Morrow and the two young actors lost their lives immediately and six passengers onboard were injured. During the investigation, the film director was found guilty of having children working near explosives illegally.</p>\n\n<p><strong>Jon-Erik Hexum</strong><br>The accidental death of Jon-Erik Hexum occurred on the TV show “Cover Up” in 1984. During a break from filming, the actor was playing with a gun used in one of the scenes pointing it at his head and pulled the trigger as a joke. Even though the gun did not have real bullets, the force was strong enough to hurt him badly. A piece of bone from his head went into his brain. He was taken to the hospital immediately, but despite emergency surgery, he was pronounced brain dead six days later.</p>\n\n<p><strong>Roy Kinnear</strong><br>Roy Kinnear’s tragic accident took place while he was filming “The Return of the Musketeers” in 1989. During a scene with horse riding, Kinnear fell from his horse and broke a bone near one of his hips. Despite the severity of his injury, Kinnear was determined to continue filming and completed his scenes. However, his health conditions got worse and ended up affecting his heart. Sadly, Kinnear passed away from a heart attack caused by these complications.</p>\n\n<p><strong>Steve Irwin</strong><br>Steve Irwin, known as “The Crocodile Hunter,” was working on a documentary called “Ocean’s Deadliest” in 2006 off the coast of Queensland, Australia when tragedy struck. While filming a segment about dangerous fish, Irwin approached a stingray – a type of flat fish with long, sharp tails – in shallow water. The stingray felt it was in danger and attacked the man. The fish had used its sharp tail to poke Steve Irwin in the chest, and the pointy part went into his heart. His crew and emergency services tried to save him, but Irwin didn’t survive. His sudden death shocked the world and left millions of fans upset for the loss of a man who was truly passionate about the natural world.</p>",
  "subquestions": [
    {
      "id": "3.1",
      "type": "multiple_choice",
      "text": "_____ kept on working after being badly hurt.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Roy Kinnear"
    },
    {
      "id": "3.2",
      "type": "multiple_choice",
      "text": "_____ had a father who was a well-known actor and sportsman.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Brandon Lee"
    },
    {
      "id": "3.3",
      "type": "multiple_choice",
      "text": "_____ was famous for his interest in animals and the environment.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Steve Irwin"
    },
    {
      "id": "3.4",
      "type": "multiple_choice",
      "text": "_____ died in a tragic accident that affected other actors.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Vic Morrow"
    },
    {
      "id": "3.5",
      "type": "multiple_choice",
      "text": "_____ officially died almost a week after his accident.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Jon-Erik Hexum"
    },
    {
      "id": "3.6",
      "type": "multiple_choice",
      "text": "_____ died as a result of his careless behavior with a dangerous object.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Jon-Erik Hexum"
    },
    {
      "id": "3.7",
      "type": "multiple_choice",
      "text": "_____ had an accident while he was filming in the sea.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Steve Irwin"
    },
    {
      "id": "3.8",
      "type": "multiple_choice",
      "text": "_____ was killed in an accident that showed behaviors against the law.",
      "options": ["Brandon Lee", "Vic Morrow", "Jon-Erik Hexum", "Roy Kinnear", "Steve Irwin"],
      "correct": "Vic Morrow"
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

exam_data = {}

# Path to the directory with random photos
PHOTO_DIR = os.path.join('static', 'exam-files', 'speaking')

@app.route('/api/start-speaking-exam/<ID>', methods=['POST'])
def start_speaking_exam(ID):
    """
    Запускает экзамен:
     - Если для ID уже есть запись — возвращает 400.
     - Иначе выбирает случайное фото, сохраняет статус = 'started', photo = filename.
    """
    # Проверяем, не запускали ли уже
    if ID in exam_data:
        return jsonify({"message": "Exam already started"}), 400

    # Убедимся, что папка с фото существует
    if not os.path.isdir(PHOTO_DIR):
        return jsonify({"error": "Photo directory not found"}), 500

    # Получаем список файлов
    photos = [
        f for f in os.listdir(PHOTO_DIR)
        if os.path.isfile(os.path.join(PHOTO_DIR, f))
    ]
    if not photos:
        return jsonify({"error": "No photos available"}), 500

    # Выбираем случайное фото и сохраняем запись
    chosen = random.choice(photos)
    exam_data[ID] = {
        "status": "started",
        "photo": chosen
    }

    return jsonify({
        "message": "Exam started",
        "photo_assigned": chosen
    })

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
    entry = exam_data.get(ID)
    if not entry:
        return jsonify({"error": "Exam not started"}), 404

    photo_file = entry.get("photo")
    if not photo_file:
        return jsonify({"error": "Photo not assigned"}), 500

    # Отправляем файл без кеширования
    response = make_response(
        send_from_directory(PHOTO_DIR, photo_file, as_attachment=False)
    )
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
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
