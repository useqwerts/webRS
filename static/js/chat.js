let currentVersion = ''; // Переменная для текущей версии
const currentUser = sessionStorage.getItem('username');

// Функция для показа модального окна
function showUpdateModal() {
    const modal = document.getElementById('updateModal');
    modal.style.display = 'flex'; // Показываем модальное окно
}

// Закрытие модального окна
function closeUpdateModal() {
    const modal = document.getElementById('updateModal');
    modal.style.display = 'none'; // Скрываем модальное окно
}

// Проверка версии сайта
function checkSiteVersion(newVersion) {
    const savedVersion = localStorage.getItem('siteVersion'); // Извлекаем версию из localStorage
    console.log(`Saved version: ${savedVersion}, Current version: ${newVersion}`); // Лог для отладки

    if (savedVersion === null || savedVersion !== newVersion) {
        // Если версия не найдена или версии не совпадают, показываем модальное окно
        showUpdateModal();
        localStorage.setItem('siteVersion', newVersion); // Сохраняем новую версию в localStorage
    }
}

// Функция перезагрузки сайта и сохранения новой версии в localStorage
function reloadSite() {
    // Перезагружаем страницу
    location.reload();
}

// Проверяем версию при загрузке страницы
window.onload = () => {
    // Получаем текущую версию от сервера при подключении
    socket.emit('getVersion', {}, (response) => {
        currentVersion = response.version; // Устанавливаем текущую версию
        checkSiteVersion(currentVersion); // Проверяем версию после получения данных от сервера
    });
};

	
	const socket = io();
    const messagesDiv = document.getElementById('messages');
    const skeletonLoader = document.getElementById('skeleton-loader');
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileInput = document.getElementById('file-input');
    const passwordModal = document.getElementById('passwordModal');
    const closeButton = document.querySelector('.close-button');
    const passwordForm = document.getElementById('password-form');
    const currentPasswordInput = document.getElementById('current-password');
    const newPasswordInput = document.getElementById('new-password');
    const statusContainer = document.getElementById('status-container');
    const updatePasswordButton = document.getElementById('update-password-button');
	const audioModal = document.getElementById('audioModal');
    const audioPlayer = document.getElementById('audioPlayer');
    const closeAudioModal = document.getElementById('closeAudioModal');
    const audioTrackName = document.getElementById('audioTrackName');
    const audioSource = document.getElementById('audioSource');
	const musicPackOption = document.getElementById('music-pack-option');
	const musicModal = document.getElementById('music-modal');
	const playerModal = document.getElementById('player-modal');
	const closeMusicModal = document.getElementById('close-music-modal');
	const closePlayerModal = document.getElementById('close-player-modal');
	const musicList = document.getElementById('music-list');
	const audioElement = document.getElementById('audio-element');
	const playPauseButton = document.getElementById('play-pause');
	const progressBar = document.getElementById('progress-bar');
	const progressBarContainer = document.getElementById('progress-bar-container');
	const currentTimeDisplay = document.getElementById('current-time');
	const totalTimeDisplay = document.getElementById('total-time');
	let currentTrackIndex = 0;
	let tracks = [];  // Массив для хранения треков

// Открытие модального окна списка музыки
if (musicPackOption && musicModal && musicList) {
    musicPackOption.addEventListener('click', () => {
        musicModal.classList.remove('hidden');
        musicModal.classList.add('show');
        loadMusicList();
    });
}

// Закрытие модального окна списка музыки
if (closeMusicModal && musicModal) {
    closeMusicModal.addEventListener('click', () => {
        musicModal.classList.remove('show');
        musicModal.classList.add('hidden');
        // Сброс содержимого списка музыки при закрытии
        setTimeout(() => {
            musicList.innerHTML = '';
        }, 300); // Учитываем время анимации закрытия
    });
}

// Загрузка списка музыки с имитацией загрузки
function loadMusicList() {
    musicList.innerHTML = ` 
        <div class="skeleton-loader">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-line"></div>
            <div class="skeleton skeleton-line"></div>
            <div class="skeleton skeleton-line"></div>
        </div>`;

    // Имитация задержки загрузки
    setTimeout(() => {
        fetchTracks();  // Запрашиваем треки с сервера
    }, 2000); // Задержка 2 секунды
}

// Получаем список треков с сервера

async function fetchTracks() {
    try {
        const response = await fetch('/api/tracks');  // Указываем путь к API сервера Flask
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const tracksData = await response.json();  // Получаем данные в формате JSON
        tracks = tracksData;  // Сохраняем полученные треки в массив tracks
        updateMusicList(tracks);  // Обновляем список музыки на странице
    } catch (error) {
        console.error('Error fetching tracks:', error);
    }
}

// Обновляем список треков на странице
function updateMusicList(tracksData) {
    musicList.innerHTML = '';  // Очистить лоадер

    tracksData.forEach((track, index) => {
        const trackElement = document.createElement('div');
        trackElement.classList.add('track-item-music');
        trackElement.innerHTML = `
            <span>${track.title}</span>
            <button class="play-button-music" data-index="${index}">▶</button>
        `;
        musicList.appendChild(trackElement);
    });
    attachPlayButtons();  // Привязываем кнопки воспроизведения
}

// Функция для привязки кнопок воспроизведения к каждому треку
function attachPlayButtons() {
    const playButtons = document.querySelectorAll('.play-button-music');
    playButtons.forEach(button => {
        button.addEventListener('click', () => {
            const trackIndex = button.getAttribute('data-index');
            playTrack(trackIndex);
        });
    });
}

// Функция для воспроизведения трека
function playTrack(index) {
    if (index < 0 || index >= tracks.length) {
        console.warn("The index of the track is out of range.");
        showToastNotification("The index of the track is out of range.",'error');
        return;
    }

    currentTrackIndex = index; // Сохраняем индекс текущего трека
    const track = tracks[index]; // Получаем трек по индексу

    // Обновляем источник для аудио
    audioElement.src = track.url;

    // Воспроизводим трек
    audioElement.play();

    // Обновляем UI плеера
    updatePlayerUI(track.title);

    // Отображаем модальное окно плеера
    playerModal.classList.add('active');
}


document.getElementById('next-track-button').addEventListener('click', () => {
    if (currentTrackIndex < tracks.length - 1) {
        playTrack(currentTrackIndex + 1); // Переход к следующему треку
    } else {
        showToastNotification("This is the last track.", 'success');
    }
});

// Логика для кнопки Prev Track
document.getElementById('prev-track-button').addEventListener('click', () => {
    if (currentTrackIndex > 0) {
        playTrack(currentTrackIndex - 1); // Переход к предыдущему треку
    } else {
        showToastNotification("This is the first track.",'success');
    }
});

// Обновление UI плеера
function updatePlayerUI(title) {
    document.getElementById('player-title').textContent = `${title}`;
    playPauseButton.textContent = '<i class="fas fa-play"></i>'; // Восстанавливаем иконку воспроизведения
}

// Обновление прогресс-бара и времени
audioElement.addEventListener('timeupdate', () => {
    const progress = (audioElement.currentTime / audioElement.duration) * 100;
    progressBar.style.width = `${progress}%`;
    currentTimeDisplay.textContent = formatTime(audioElement.currentTime);
    totalTimeDisplay.textContent = formatTime(audioElement.duration || 0);
});

// Форматирование времени
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
}

// Кнопка воспроизведения/паузы
playPauseButton.addEventListener('click', () => {
    if (audioElement.paused) {
        // Показываем спиннер внутри кнопки с 1-секундной задержкой
        playPauseButton.innerHTML = '<div class="lds-ring"><div></div><div></div><div></div></div>';

        // Задержка перед воспроизведением
        setTimeout(() => {
            audioElement.play().then(() => {
                // После начала воспроизведения убираем спиннер и показываем паузу
                playPauseButton.innerHTML = '<i class="fas fa-pause"></i>';
            }).catch((error) => {
                console.error('Ошибка при воспроизведении:', error);
            });
        }, 1000); // Задержка в 1 секунду
    } else {
        audioElement.pause();
        playPauseButton.innerHTML = '<i class="fas fa-play"></i>'; // Восстанавливаем иконку воспроизведения
    }
});

// Событие завершения трека
audioElement.addEventListener('ended', () => {
	if (isAutoplayEnabled) {
        playNextTrack(); // Переход к следующему треку
    }
    playPauseButton.innerHTML = '<i class="fas fa-play"></i>'; // Восстанавливаем иконку после завершения
    progressBar.style.width = '0%'; // Сбрасываем прогресс-бар
});

// Событие буферизации
audioElement.addEventListener('waiting', () => {
    playPauseButton.innerHTML = '<div class="lds-ring"><div></div><div></div><div></div></div>'; // Показываем спиннер
});

// Событие "готово к воспроизведению"
audioElement.addEventListener('playing', () => {
    playPauseButton.innerHTML = '<i class="fas fa-pause"></i>'; // Возвращаем иконку паузы
});

let isAutoplayEnabled = false; // Изначально автоплей выключен

// Получаем элемент тумблера
const autoplayToggle = document.getElementById('autoplay-toggle');

// Обработчик изменения состояния тумблера
autoplayToggle.addEventListener('change', (event) => {
    isAutoplayEnabled = event.target.checked; // Сохраняем состояние (включен/выключен)
    showToastNotification(`Autoplay is now ${isAutoplayEnabled ? 'enabled' : 'disabled'}`);
});

function playNextTrack() {
    if (currentTrackIndex < tracks.length - 1) {
        playTrack(currentTrackIndex + 1); // Воспроизводим следующий трек
    } else {
		showToastNotification("This is the last track.", 'success');
        console.log('Конец плейлиста');
    }
}

// Закрытие плеера
closePlayerModal.addEventListener('click', () => {
    playerModal.classList.remove('active');
    audioElement.pause();
});

// Управление воспроизведением через прогресс-бар
let isMouseDown = false; // Для отслеживания, когда пользователь перетаскивает

progressBarContainer.addEventListener('mousedown', (e) => {
    isMouseDown = true;
    updateProgressBar(e);
});

document.addEventListener('mousemove', (e) => {
    if (isMouseDown) {
        updateProgressBar(e);
    }
});

document.addEventListener('mouseup', () => {
    isMouseDown = false;
});

function updateProgressBar(e) {
    const rect = progressBarContainer.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const percentage = (offsetX / progressBarContainer.offsetWidth) * 100;
    progressBar.style.width = `${percentage}%`; // Обновляем визуальную ширину прогресс-бара

    // Изменяем currentTime аудио в зависимости от места клика на прогресс-баре
    audioElement.currentTime = (percentage / 100) * audioElement.duration;
}

		function scrollToBottom() {
		messagesDiv.scrollTop = messagesDiv.scrollHeight;
		}
		
		const accountIcon = document.getElementById('account-icon');
		const accountMenu = document.getElementById('account-menu');
		const changePasswordOption = document.getElementById('change-password-option');
		const logoutOption = document.getElementById('logout-option');


function showToastNotification(message, type = 'success', duration = 5000) {
    const toastContainer = document.getElementById('toast-container');
    
    // Удаляем все текущие уведомления перед показом нового
    const existingToasts = toastContainer.querySelectorAll('.toast');
    existingToasts.forEach(toast => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 0);
    });

    // Создание элементов уведомления
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const toastContent = document.createElement('div');
    toastContent.className = 'toast-content';
    
    const toastIcon = document.createElement('div');
    toastIcon.className = `toast-check ${type}`;
    toastIcon.innerHTML = type === 'success' ? '&#10004;' : '&#10006;';
    
    const messageContainer = document.createElement('div');
    messageContainer.className = 'messageToast';
    
    const messageText = document.createElement('span');
    messageText.className = 'messageToast-text text-1';
    messageText.textContent = message;
    
    const closeButton = document.createElement('span');
    closeButton.className = 'toast-close';
    closeButton.onclick = () => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 500);
    };

    // Сборка уведомления
    messageContainer.appendChild(messageText);
    toastContent.appendChild(toastIcon);
    toastContent.appendChild(messageContainer);
    toast.appendChild(toastContent);
    toast.appendChild(closeButton);
    toastContainer.appendChild(toast);
    
    // Активация уведомления с анимацией
    setTimeout(() => {
        toast.classList.add('active');
    }, 10);
    
    // Удаление уведомления после завершения
    setTimeout(() => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 500);
    }, duration);
}



accountIcon.addEventListener('click', () => {
    if (accountMenu.classList.contains('show')) {
        // Удаляем класс "show" для запуска анимации скрытия
        accountMenu.classList.remove('show');
        setTimeout(() => {
            accountMenu.style.display = 'none'; // После завершения анимации скрываем элемент
        }, 300); // Должно совпадать с длительностью transition
    } else {
        accountMenu.style.display = 'block'; // Отображаем элемент перед добавлением анимации
        setTimeout(() => {
            accountMenu.classList.add('show'); // Добавляем класс "show" для появления
        }, 10); // Небольшая задержка для срабатывания анимации
    }
});

// Открыть окно смены пароля
changePasswordOption.addEventListener('click', () => {
    passwordModal.style.display = 'flex';
    accountMenu.style.display = 'none'; // Закрыть меню после клика
});

document.getElementById('logout-option').addEventListener('click', function() {
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to log out. Response status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) { 
            sessionStorage.removeItem('username');
            window.location.href = '/login';
        } else {
            throw new Error('Logout failed: Server did not confirm success.');
        }
    })
    .catch(error => {
        console.error('Error logging out:', error);
        alert('Ошибка выхода! Попробуйте еще раз.');
    });
});

        // Close the modal
        closeButton.addEventListener('click', () => {
            passwordModal.style.display = 'none';
            currentPasswordInput.value = '';
            newPasswordInput.value = '';
            statusContainer.innerHTML = ''; // Clear status messages
        });

        // Handle form submission
        passwordForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const currentPassword = currentPasswordInput.value;
            const newPassword = newPasswordInput.value;

            // Show skeleton loading animation
            statusContainer.innerHTML = '<div class="skeleton"></div>';

            // Simulate server request
            fetch('/change_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    currentPassword,
                    newPassword
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove skeleton animation
                statusContainer.innerHTML = '';
                if (data.error) {
                    statusContainer.innerHTML = `<div class="status-message error">${data.error}</div>`;
					showToastNotification(data.error, 'error');
                } else {
                    statusContainer.innerHTML = `<div class="status-message success">${data.message}</div>`;
					showToastNotification(data.message, 'success');
                    // Clear form fields after success
                    currentPasswordInput.value = '';
                    newPasswordInput.value = '';
                }
            })
            .catch(error => {
                statusContainer.innerHTML = `<div class="status-message error">An error occurred. Please try again.</div>`;
                console.error('Error:', error);
            });
        });
		
// Обработка обновления версии
socket.on('updateReleased', (data) => {
    const newVersion = data.version;
    console.log('New version released:', newVersion);

    // Если версия изменилась, показываем модальное окно с обновлением
    if (newVersion !== localStorage.getItem('siteVersion')) {
        showUpdateModal();
        localStorage.setItem('siteVersion', newVersion); // Сохраняем новую версию
    }
});

socket.on('load_messages', (loadedMessages) => {
    skeletonLoader.style.display = 'none';

    if (loadedMessages.length === 0) {
        const noMessages = document.createElement('div');
        noMessages.classList.add('no-messages');

        const animationContainer = document.createElement('div');
        animationContainer.classList.add('animation-container');

        noMessages.appendChild(animationContainer);

        lottie.loadAnimation({
            container: animationContainer,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: '/static/animations/NoMessages.json'
        });

        messagesDiv.appendChild(noMessages);
    } else {
        loadedMessages.forEach((message) => {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message');

            const header = document.createElement('div');
            header.classList.add('message-header');

            // Контейнер для аватарки
            const avatarContainer = document.createElement('div');
            avatarContainer.classList.add('avatar-container');

            const username = message.username;

            // Показать первую букву имени сразу, если аватарки нет
            const avatarPlaceholder = document.createElement('div');
            avatarPlaceholder.classList.add('avatar-placeholder');
            avatarPlaceholder.textContent = username.charAt(0).toUpperCase();
            avatarContainer.appendChild(avatarPlaceholder);

            // Загрузить аватарку пользователя
            fetch(`/get_avatar/${username}`)
                .then(response => response.json())
                .then(data => {
                    if (data.avatar_url) {
                        // Если аватарка существует, заменяем её
                        const avatarImg = document.createElement('img');
                        avatarImg.src = data.avatar_url;
                        avatarImg.alt = username;
                        avatarImg.classList.add('avatar-image');
                        avatarContainer.innerHTML = ''; // Очищаем контейнер от placeholder
                        avatarContainer.appendChild(avatarImg);
                    } else {
                        // Если аватарки нет, оставляем первую букву
                        avatarContainer.innerHTML = ''; // Очищаем контейнер от placeholder
                        avatarContainer.appendChild(avatarPlaceholder);
                    }
                })
                .catch(error => {
                    console.error("Ошибка загрузки аватара:", error);
                    // В случае ошибки тоже показываем первую букву имени
                    avatarContainer.innerHTML = ''; // Очищаем контейнер от placeholder
                    avatarContainer.appendChild(avatarPlaceholder);
                });

            const usernameElement = document.createElement('span');
            usernameElement.classList.add('message-username');
            usernameElement.textContent = username;

            const timestampElement = document.createElement('span');
            timestampElement.classList.add('message-timestamp');
            timestampElement.textContent = message.timestamp;

            header.appendChild(avatarContainer);
            header.appendChild(usernameElement);
            header.appendChild(timestampElement);

            const content = document.createElement('div');
            content.classList.add('message-content');

            if (message.type === 'text') {
                content.textContent = message.text;
            } else if (message.type === 'file') {
                if (message.filename.match(/\.(jpeg|jpg|gif|png)$/i)) {
                    // Создаем обертку для изображения
                    const imageWrapper = document.createElement('div');
                    imageWrapper.classList.add('image-wrapper');
                    
                    // Создаем блок для анимации спиннера
                    const imgLoadingSpinner = document.createElement('div');
                    imgLoadingSpinner.classList.add('lds-dual-ring'); // Применяем новый класс для спиннера
                    content.appendChild(imgLoadingSpinner); // Добавляем спиннер в message-content
                    
                    // Создаем само изображение
                    const image = document.createElement('img');
                    image.src = message.url;
                    image.alt = message.filename;
                    image.classList.add('message-image');
                    
                    // Скрываем изображение до того, как оно загрузится
                    image.style.display = 'none';

                    // Когда изображение загружено, скрываем спиннер и показываем изображение
                    image.onload = () => {
                        imgLoadingSpinner.style.display = 'none'; // Скрываем спиннер
                        image.style.display = 'block'; // Показываем изображение
                    };

                    // Если ошибка при загрузке изображения
                    image.onerror = () => {
                        imgLoadingSpinner.style.display = 'none'; // Скрыть спиннер
                        content.innerHTML = 'Ошибка загрузки изображения'; // Показать ошибку
                    };

                    // Добавляем изображение в обертку
                    imageWrapper.appendChild(image);
                    content.appendChild(imageWrapper); // Добавляем обертку в message-content
                } else if (message.type === 'file' && message.filename.match(/\.(mp4|webm|ogg)$/i)) {
        // Создаем кастомный видеоплеер
        const customPlayer = createCustomVideoPlayer(message.url);
        content.appendChild(customPlayer);
    }  else if (message.filename.match(/\.(mp3)$/i)) {
                    const audioWrapper = document.createElement('div');
                    audioWrapper.classList.add('audio-wrapper');

                    const playIcon = document.createElement('span');
                    playIcon.classList.add('play-icon');
                    playIcon.innerHTML = '▶';

                    const trackName = document.createElement('span');
                    trackName.classList.add('track-name');
                    trackName.textContent = message.filename;

                    const audioElement = document.createElement('audio');
                    audioElement.src = message.url;
                    audioElement.classList.add('message-audio');
                    audioElement.controls = false;

                    playIcon.addEventListener('click', () => {
                        openAudioModal(message.url);
                    });

                    audioWrapper.appendChild(playIcon);
                    audioWrapper.appendChild(trackName);
                    audioWrapper.appendChild(audioElement);
                    content.appendChild(audioWrapper);
                } else {
                    content.innerHTML = `<a href="${message.url}" target="_blank">${message.filename}</a>`;
                }
            }

            messageElement.appendChild(header);
            messageElement.appendChild(content);
            messagesDiv.appendChild(messageElement);
        });
    }
    scrollToBottom();
});



const personalAccountSection = document.getElementById("personal-account-section");
const changeAvatarOption = document.getElementById("change-avatar-option");
const avatarModal = document.getElementById("avatar-modal");
const avatarUploadInput = document.getElementById("avatar-upload-input");
const uploadAvatarButton = document.getElementById("upload-avatar-button");
const closeAvatarModal = document.getElementById("close-avatar-modal");

// Display the Personal Account options when clicked
personalAccountSection.addEventListener("click", () => {
    const personalAccountOptions = personalAccountSection.querySelector(".personal-account-options");
    personalAccountOptions.style.display = (personalAccountOptions.style.display === "none" || personalAccountOptions.style.display === "") ? "block" : "none";
});

// Handling the avatar change option
changeAvatarOption.addEventListener("click", () => {
    avatarModal.style.display = "flex"; // Show the avatar upload modal
    accountMenu.style.display = "none"; // Hide the account menu
});

// Handling the avatar upload button
// Обработчик события для кнопки загрузки аватара
uploadAvatarButton.addEventListener("click", () => {
    const file = avatarUploadInput.files[0];
    if (file) {
        // Вызываем функцию uploadAvatar, передавая имя пользователя и файл
        uploadAvatar(currentUser, file);
    } else {
        alert("Пожалуйста, выберите аватар для загрузки.");
    }
});

// Функция загрузки аватара
function uploadAvatar(username, file) {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("file", file);

    fetch("/upload_avatar", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.avatar_url) {
            // Убираем строку, которая обновляла аватар на странице
            // document.getElementById("user-avatar").src = data.avatar_url;
            showToastNotification("Successfully uploaded photo");
        } else {
            showToastNotification("Ошибка загрузки: " + data.error);
        }
    })
    .catch(error => showToastNotification("Ошибка: " + error));
}


// Close the avatar upload modal
closeAvatarModal.addEventListener("click", () => {
    avatarModal.style.display = "none"; // Hide the avatar modal
    accountMenu.style.display = "block"; // Show the account menu again
});

// Handling the password change option
changePasswordOption.addEventListener("click", () => {
    passwordModal.style.display = 'flex'; // Show the password change modal
    accountMenu.style.display = 'none'; // Close the account menu
});

let messageTimestamps = []; // Массив для хранения времени отправки сообщений
const maxMessages = 2; // Максимальное количество сообщений за промежуток времени
const timeFrame = 4000; // Промежуток времени в миллисекундах (5 секунд)
const cooldownTime = 30; // Время блокировки в секундах
const blockScreen = document.getElementById("block-screen");
const timerElement = document.getElementById("timer");
let isBlocked = false; // Флаг блокировки


// Функция отправки сообщения
function sendMessage() {
	let countBlocks = localStorage.getItem('countBlocks') ? parseInt(localStorage.getItem('countBlocks')) : 0;
    if (isBlocked) {
        return; // Блокируем отправку, если пользователь уже заблокирован
    }

    const now = Date.now();
    messageTimestamps.push(now);

    // Удаляем старые записи, которые выходят за пределы заданного времени
    messageTimestamps = messageTimestamps.filter(
        (timestamp) => now - timestamp <= timeFrame
    );

    if (messageTimestamps.length > maxMessages) {
        ++countBlocks;
        blockUser(30 * countBlocks);
        localStorage.setItem('countBlocks', countBlocks); // Сохраняем обновленное значение в localStorage
    } else {
        console.log("Message sent"); // Здесь код отправки сообщения
    }
}

const backgroundMusic = new Audio('/static/music/DeepSleep.mp3');
    backgroundMusic.loop = true; // Зацикливаем музыку

    // Функция для воспроизведения музыки
    function playSpecialMusic() {
      backgroundMusic.play();
      console.log('Music started');
    }

    // Функция для остановки музыки
    function stopSpecialMusic() {
      backgroundMusic.pause();
      backgroundMusic.currentTime = 0; // Сброс к началу трека
      console.log('Music stopped');
    }


function blockUser(duration) {
	// Блокируем взаимодействие с элементами страницы
    document.body.style.pointerEvents = 'none';
	playSpecialMusic(); // Запускаем музыку
	disableMessageInput(); // Блокируем ввод сообщений
    isBlocked = true;
    const blockEndTime = Date.now() + duration * 1000;

    // Сохраняем время окончания блокировки в localStorage
    localStorage.setItem("blockEndTime", blockEndTime);

    let timeLeft = duration;

    // Показать экран блокировки
    blockScreen.classList.add("visible");
    timerElement.textContent = formatTime(timeLeft); // Отображаем начальное время

    // Таймер обратного отсчета
    const interval = setInterval(() => {
        timeLeft--;

        // Обновляем отображение времени
        timerElement.textContent = formatTime(timeLeft);

        // Если время истекло, разблокируем пользователя
        if (timeLeft <= 0) {
            clearInterval(interval);
            unblockUser(); // Разблокировка
        }
    }, 1000);
}

// Форматирование времени в MM:SS
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60); // Округляем секунды до целых чисел
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Проверка при загрузке страницы (если пользователь был заблокирован)
document.addEventListener("DOMContentLoaded", () => {
    const blockEndTime = localStorage.getItem("blockEndTime");

    if (blockEndTime) {
        const remainingTime = Math.max(0, Math.floor((blockEndTime - Date.now()) / 1000));

        if (remainingTime > 0) {
            blockUser(remainingTime); // Продолжить блокировку
        } else {
            localStorage.removeItem("blockEndTime"); // Если время истекло, очистить запись
        }
    }
});

// Функция для разблокировки пользователя
function unblockUser() {
	document.body.style.pointerEvents = 'auto';
	stopSpecialMusic();
	enableMessageInput();
    isBlocked = false;
    localStorage.removeItem("blockEndTime"); // Удалить блокировку из localStorage
    blockScreen.classList.remove("visible"); // Скрыть экран блокировки
    messageTimestamps = []; // Сбросить историю сообщений
}

// Обработчик для нового сообщения
socket.on('new_message', (message) => {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');

    // Создание контейнера для имени пользователя и времени
    const header = document.createElement('div');
    header.classList.add('message-header');

    const usernameElement = document.createElement('span');
    usernameElement.classList.add('message-username');
    usernameElement.textContent = message.username;

    const timestampElement = document.createElement('span');
    timestampElement.classList.add('message-timestamp');
    timestampElement.textContent = message.timestamp;

    header.appendChild(usernameElement);
    header.appendChild(timestampElement);

    // Создание контейнера для аватарки
    const avatarContainer = document.createElement('div');
    avatarContainer.classList.add('avatar-container');

    // Загрузка аватарки пользователя
    fetch(`/get_avatar/${message.username}`)
        .then(response => response.json())
        .then(data => {
            const avatarPlaceholder = document.createElement('div');
            avatarPlaceholder.classList.add('avatar-placeholder');
            avatarPlaceholder.textContent = message.username.charAt(0).toUpperCase(); // Первая буква

            if (data.avatar_url) {
                const avatarImg = document.createElement('img');
                avatarImg.src = data.avatar_url;
                avatarImg.alt = message.username;
                avatarImg.classList.add('avatar-image');
                avatarContainer.innerHTML = ''; // Очищаем контейнер от placeholder
                avatarContainer.appendChild(avatarImg);
            } else {
                avatarContainer.innerHTML = ''; // Очищаем контейнер от placeholder
                avatarContainer.appendChild(avatarPlaceholder);
            }
        })
        .catch(error => {
            console.error("Ошибка загрузки аватара:", error);
            const avatarPlaceholder = document.createElement('div');
            avatarPlaceholder.classList.add('avatar-placeholder');
            avatarPlaceholder.textContent = message.username.charAt(0).toUpperCase(); // Первая буква
            avatarContainer.innerHTML = ''; // Очищаем контейнер от placeholder
            avatarContainer.appendChild(avatarPlaceholder);
        });

    // Добавляем аватарку в header
    header.insertBefore(avatarContainer, usernameElement);

    // Создание содержимого сообщения
    const content = document.createElement('div');
    content.classList.add('message-content');

    if (message.type === 'text') {
        content.textContent = message.text;
    } else if (message.type === 'file') {
        if (message.filename.match(/\.(jpeg|jpg|gif|png)$/i)) {
            // Создаем обертку для изображения
            const imageWrapper = document.createElement('div');
            imageWrapper.classList.add('image-wrapper');

            // Создаем блок для анимации спиннера
            const imgLoadingSpinner = document.createElement('div');
            imgLoadingSpinner.classList.add('lds-dual-ring'); // Применяем новый класс для спиннера
            content.appendChild(imgLoadingSpinner); // Добавляем спиннер в message-content

            // Создаем само изображение
            const image = document.createElement('img');
            image.src = message.url;
            image.alt = message.filename;
            image.classList.add('message-image');
            
            // Скрыть изображение до его загрузки
            image.style.display = 'none';

            // Когда изображение загружено, скрыть спиннер и показать изображение
            image.onload = () => {
                imgLoadingSpinner.style.display = 'none'; // Скрыть спиннер
                image.style.display = 'block'; // Показать изображение
            };

            // Если ошибка при загрузке изображения
            image.onerror = () => {
                imgLoadingSpinner.style.display = 'none'; // Скрыть спиннер
                content.innerHTML = 'Ошибка загрузки изображения'; // Показать ошибку
            };

            imageWrapper.appendChild(image);
            content.appendChild(imageWrapper); // Добавляем обертку с изображением в message-content
        }
        else if (message.type === 'file' && message.filename.match(/\.(mp4|webm|ogg)$/i)) {
        // Создаем кастомный видеоплеер
        const customPlayer = createCustomVideoPlayer(message.url);
        content.appendChild(customPlayer);
    }
        else if (message.filename.match(/\.(mp3)$/i)) {
            const audioWrapper = document.createElement('div');
            audioWrapper.classList.add('audio-wrapper');

            const playIcon = document.createElement('span');
            playIcon.classList.add('play-icon');
            playIcon.innerHTML = '▶'; // Иконка play (треугольник)

            const trackName = document.createElement('span');
            trackName.classList.add('track-name');
            trackName.textContent = message.filename; // Имя трека

            const audioElement = document.createElement('audio');
            audioElement.src = message.url;
            audioElement.classList.add('message-audio');
            audioElement.controls = false;

            playIcon.addEventListener('click', () => {
                openAudioModal(message.url);
            });

            audioWrapper.appendChild(playIcon);
            audioWrapper.appendChild(trackName);
            audioWrapper.appendChild(audioElement);
            content.appendChild(audioWrapper);
        } else {
            content.innerHTML = `<a href="${message.url}" target="_blank">${message.filename}</a>`;
        }
    }

    messageElement.appendChild(header);
    messageElement.appendChild(content);

    messagesDiv.appendChild(messageElement);
    scrollToBottom();
});

function createCustomVideoPlayer(videoUrl) {
    const player = document.createElement('div');
    player.classList.add('custom-video-player');

    const video = document.createElement('video');
    video.classList.add('video-element');
    video.src = videoUrl;
    video.preload = 'none'; // Отменить предварительную загрузку

    const controls = document.createElement('div');
    controls.classList.add('controls');

    const playBtn = document.createElement('button');
    playBtn.classList.add('play-btn');
    playBtn.innerHTML = '<i class="fas fa-play"></i>';  // Иконка воспроизведения

    const progressBar = document.createElement('input');
    progressBar.type = 'range';
    progressBar.classList.add('progress-bar');
    progressBar.value = 0;

    const timeDisplay = document.createElement('span');
    timeDisplay.classList.add('time');
    timeDisplay.textContent = '00:00';

    // Добавляем кнопки для перемотки
    const rewindBtn = document.createElement('button');
    rewindBtn.classList.add('seek-btn');
    rewindBtn.innerHTML = '<i class="fas fa-backward"></i>'; // Иконка перемотки назад

    const forwardBtn = document.createElement('button');
    forwardBtn.classList.add('seek-btn');
    forwardBtn.innerHTML = '<i class="fas fa-forward"></i>'; // Иконка перемотки вперед

    // Кнопка полноэкранного режима
    const fullscreenBtn = document.createElement('button');
    fullscreenBtn.classList.add('fullscreen-btn');
    fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>'; // Иконка полноэкранного режима

    controls.appendChild(playBtn);
    controls.appendChild(rewindBtn);
    controls.appendChild(forwardBtn);
    controls.appendChild(progressBar);
    controls.appendChild(timeDisplay);
    controls.appendChild(fullscreenBtn);

    player.appendChild(video);
    player.appendChild(controls);

    // Вставляем плеер в DOM
    document.body.appendChild(player);

    // Спиннер для загрузки
    const loadingSpinner = document.createElement('div');
    loadingSpinner.classList.add('lds-ring');
    for (let i = 0; i < 4; i++) {
        const spinnerElement = document.createElement('div');
        loadingSpinner.appendChild(spinnerElement);
    }
    player.appendChild(loadingSpinner);
    loadingSpinner.style.display = 'none'; // Скрыть спиннер изначально

    let hideControlsTimeout;
    function resetControlsTimeout() {
        clearTimeout(hideControlsTimeout);
        controls.style.opacity = '1';
        hideControlsTimeout = setTimeout(() => {
            controls.style.opacity = '0';
        }, 3000);
    }

    player.addEventListener('mousemove', resetControlsTimeout);
    player.addEventListener('click', resetControlsTimeout);
    video.addEventListener('play', resetControlsTimeout);
    video.addEventListener('pause', resetControlsTimeout);

    resetControlsTimeout();

    // Воспроизведение и пауза
    playBtn.addEventListener('click', () => {
        if (video.paused) {
            // Загружаем видео только после нажатия на play
            video.load();
            video.play();
            playBtn.innerHTML = '<i class="fas fa-pause"></i>'; // Иконка паузы
            loadingSpinner.style.display = 'none'; // Скрыть спиннер после начала воспроизведения
        } else {
            video.pause();
            playBtn.innerHTML = '<i class="fas fa-play"></i>'; // Иконка воспроизведения
        }
    });

    // Перемотка на -5 секунд
    rewindBtn.addEventListener('click', () => {
        video.currentTime = Math.max(video.currentTime - 5, 0); // Не даем перемотать в отрицательное время
    });

    // Перемотка на +5 секунд
    forwardBtn.addEventListener('click', () => {
        video.currentTime = Math.min(video.currentTime + 5, video.duration); // Не даем перемотать за конец видео
    });

    // Полноэкранный режим
    fullscreenBtn.addEventListener('click', () => {
        if (video.requestFullscreen) {
            video.requestFullscreen();
        } else if (video.mozRequestFullScreen) { // Для Firefox
            video.mozRequestFullScreen();
        } else if (video.webkitRequestFullscreen) { // Для Chrome и Safari
            video.webkitRequestFullscreen();
        } else if (video.msRequestFullscreen) { // Для Internet Explorer
            video.msRequestFullscreen();
        }
    });

    // Обновление прогресса видео
    video.addEventListener('timeupdate', () => {
        const progress = (video.currentTime / video.duration) * 100;
        progressBar.value = progress;

        const currentMinutes = Math.floor(video.currentTime / 60);
        const currentSeconds = Math.floor(video.currentTime % 60);
        timeDisplay.textContent = `${String(currentMinutes).padStart(2, '0')}:${String(currentSeconds).padStart(2, '0')}`;
    });

    // Изменение времени видео при перемещении прогресс-бара
    progressBar.addEventListener('input', () => {
        video.currentTime = (progressBar.value / 100) * video.duration;
    });

    // Показываем спиннер, если видео загружается (событие waiting)
    video.addEventListener('waiting', () => {
        playBtn.innerHTML = '<div class="lds-ring"><div></div><div></div><div></div></div>'; // Показываем спиннер
    });

    // Скрываем спиннер, когда видео начнется воспроизводиться
    video.addEventListener('playing', () => {
        playBtn.innerHTML = '<i class="fas fa-pause"></i>'; // Возвращаем иконку паузы
    });

    return player;
}


function openAudioModal(audioUrl, trackName) {
        audioTrackName.textContent = trackName; // Устанавливаем имя трека
        audioSource.src = audioUrl; // Устанавливаем источник для аудио
        audioPlayer.load(); // Перезагружаем плеер
        audioModal.style.display = 'block'; // Показываем модальное окно
    }

    // Закрытие модального окна
    closeAudioModal.onclick = function() {
        audioModal.style.display = 'none';
        audioPlayer.pause(); // Останавливаем аудио при закрытии
    }

    // Закрытие модального окна при клике вне его
    window.onclick = function(event) {
        if (event.target === audioModal) {
            audioModal.style.display = 'none';
            audioPlayer.pause();
        }
    }

        // Send text message
        document.getElementById('message-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('message-input');
            const text = input.value;
            if (text.trim() !== '') {
				sendMessage();
                socket.emit('send_message', { text });
                input.value = '';
            }
        });

const uploadStatus = document.getElementById('upload-status');
const progressFill = document.getElementById('progress-fill');
const progressPercent = document.getElementById('progress-percent');
const progressText = document.getElementById('progress-text');

fileUploadButton.addEventListener('click', () => {
    fileInput.click(); // Открыть окно выбора файла
});

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];

    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);

        // Показать прогресс-бар с анимацией
        uploadStatus.classList.remove('hidden');
        uploadStatus.style.opacity = '1';
        uploadStatus.style.transform = 'translateY(0)';

        // Обновлять прогресс
        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);
                progressFill.style.width = `${percentComplete}%`;
                progressPercent.textContent = `${percentComplete}%`;
                progressText.textContent = `${percentComplete}%`; // Текст внутри прогресс-бара
            }
        };

        xhr.onload = () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    showToastNotification(response.error, 'error');
                } else {
                    showToastNotification('File uploaded successfully!', 'success');
                }
            } else {
                showToastNotification('Failed to upload the file.', 'error');
            }
            // Скрыть прогресс-бар с анимацией
            setTimeout(() => {
                uploadStatus.style.opacity = '0';
                uploadStatus.style.transform = 'translateY(-20px)';
                setTimeout(() => uploadStatus.classList.add('hidden'), 300);
            }, 1000);
            progressFill.style.width = '0%';
            progressPercent.textContent = '0%';
            progressText.textContent = '';
        };

        xhr.onerror = () => {
            showToastNotification('An error occurred during file upload.', 'error');
            uploadStatus.style.opacity = '0';
            uploadStatus.style.transform = 'translateY(-20px)';
            setTimeout(() => uploadStatus.classList.add('hidden'), 300);
        };

        xhr.send(formData);
    }
});

		
		/*
        // Logout functionality
        document.getElementById('logout-button').addEventListener('click', () => {
            fetch('/logout')
                .then(() => {
                    window.location.href = '/';
                })
                .catch((error) => console.error('Error during logout:', error));
        });
		*/

// Получить элемент message-input
const messageInput = document.getElementById('message-input');

// Функция для отключения messageInput
function disableMessageInput() {
    messageInput.disabled = true; // Отключает элемент
    messageInput.style.opacity = 0.5; // Для визуального эффекта
    messageInput.style.cursor = "not-allowed"; // Указывает, что элемент неактивен
}

// Функция для включения messageInput
function enableMessageInput() {
    messageInput.disabled = false; // Включает элемент
    messageInput.style.opacity = 1; // Возвращает нормальный вид
    messageInput.style.cursor = "text"; // Указывает, что можно вводить текст
}

// Пример вызова
disableMessageInput(); // Отключить
setTimeout(enableMessageInput, 0700); // Включить через 2 секунд


document.addEventListener("DOMContentLoaded", () => {
	
	const sessionUsername = sessionStorage.getItem('username'); // Получаем имя пользователя из sessionStorage

    // Проверяем, существует ли session 'username' и соответствует ли currentUser
    if (!sessionUsername || sessionUsername !== currentUser) {
        // Если нет сессии или пользователь не совпадает, перенаправляем на страницу логина
        window.location.href = '/login';
    } else {
        console.log(`Access granted for user: ${sessionUsername}`);
        // Продолжаем загрузку чата (можно добавить другие действия, если нужно)
    }
	
    // Убедитесь, что экран блокировки скрыт при загрузке
    if (!isBlocked) {
        blockScreen.classList.add("hidden");
    }
	if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }
	const blockEndTime = localStorage.getItem("blockEndTime");

    if (blockEndTime) {
        const timeLeft = Math.floor((blockEndTime - Date.now()) / 1000);

        if (timeLeft > 0) {
            // Если блокировка еще активна, восстановить ее
            blockUser(timeLeft);
        } else {
            // Если время блокировки истекло, удалить запись
            localStorage.removeItem("blockEndTime");
        }
    }
});

showToastNotification('Welcome ' + currentUser, 'success', 5000);

document.getElementById('sessionsButton').addEventListener('click', function() {
    // Делаем запрос на сервер для получения информации о сессиях
    fetch('/sessions')
        .then(response => response.json())  // Получаем данные в формате JSON
        .then(data => {
            const sessionModal = document.getElementById('sessionsModal');
            const sessionsList = document.getElementById('sessionsList');
            
            // Очищаем список сессий перед добавлением новых
            sessionsList.innerHTML = '';

            if (data.sessions && data.sessions.length > 0) {
                // Отображаем сессии пользователя
                data.sessions.forEach(session => {
                    const listItem = document.createElement('li');
                    
                    // Создаем содержимое для каждой сессии
                    listItem.innerHTML = `
                        <strong>Device:</strong> ${session.deviceType || 'Unknown'} <br>
                        <strong>Platform:</strong> ${session.platform || 'Unknown'} <br>
                        <strong>OS:</strong> ${session.os || 'Unknown'} <br>
                        <strong>Browser:</strong> ${session.browser || 'Unknown'} <br>
                        <strong>IP Address:</strong> ${session.ipAddress || 'Unknown'} <br>
                        <strong>Language:</strong> ${session.language || 'Unknown'}
                    `;

                    sessionsList.appendChild(listItem);
                });
            } else {
                // Если сессий нет, показываем сообщение
                const listItem = document.createElement('li');
                listItem.textContent = 'No active sessions found.';
                sessionsList.appendChild(listItem);
            }
            
            // Показываем модальное окно с сессиями
            sessionModal.style.display = 'flex'; // Показываем модальное окно
        })
        .catch(error => {
            console.error('Error fetching sessions:', error);
        });
});

// Открыть модальное окно выбора темы сообщений
document.getElementById('messages-themes-button').addEventListener('click', function() {
    document.getElementById('messages-themes-modal').style.display = 'flex';
});

// Закрыть модальное окно выбора темы сообщений
function closeMessagesThemesModal() {
    document.getElementById('messages-themes-modal').style.display = 'none';
}

const coinDisplay = document.getElementById('coinDisplay');
const coinBalance = document.getElementById('coinBalance');
const coinIcon = document.getElementById('coinIcon');

function updateCoinBalance(newBalance) {
    const coinBalance = document.getElementById('coinBalance');
    const goingUpIcon = document.getElementById('goingUpIcon');

    if (!coinBalance) return;

    const currentBalance = parseInt(coinBalance.textContent, 10) || 0;

    if (newBalance > currentBalance) {
        goingUpIcon.style.display = 'inline-block';
    } else {
        goingUpIcon.style.display = 'none';
    }

    coinBalance.classList.add('updated');

    const duration = 3000; // Длительность анимации в мс
    const stepTime = 100; // Интервал обновления в мс
    const steps = duration / stepTime;
    const increment = (newBalance - currentBalance) / steps;

    let animatedBalance = currentBalance;
    let count = 0;

    const interval = setInterval(() => {
        animatedBalance += increment;
        count++;

        if (count >= steps) {
            clearInterval(interval);
            animatedBalance = newBalance;
            coinBalance.classList.remove('updated');
            goingUpIcon.style.display = 'none';
        }

        coinBalance.textContent = Math.round(animatedBalance);
    }, stepTime);
}


// Функция для показа контейнера с монетами
function showCoinDisplay() {
    if (coinDisplay) {
        coinDisplay.classList.add('show');
    }
}

// Запрашиваем баланс при загрузке страницы
socket.emit('get_balance', currentUser); // Пример имени пользователя

// Слушаем ответ от сервера
// В событии получения баланса
socket.on('balance', (data) => {
    console.log('Received balance:', data);
    if (data.success) {
        updateCoinBalance(data.coins);
		currentBalance = data.coins; 
        showCoinDisplay();
    } else {
        console.error(data.message);
    }
});

socket.on('coins_added', (data) => {
    console.log('Coins added response:', data);

    // Проверяем, соответствует ли имя пользователя
    if (data.username === currentUser) {
        if (data.success) {
            updateCoinBalance(data.coins); // Обновляем баланс только для текущего пользователя
        } else {
            console.error('Failed to add coins:', data.message);
        }
    } else {
        console.log(`Balance update ignored for ${data.username}, not the current user.`);
    }
});

socket.on('bought_themes', (data) => {
    if (data.success) {
        const boughtThemes = data.themes;
        const themeItems = document.querySelectorAll('.theme-item');  // Все элементы с темами

        themeItems.forEach(item => {
            const themeName = item.getAttribute('data-theme');
            
            // Если тема уже куплена, показываем, что её можно применить без траты монет
            if (boughtThemes.includes(themeName)) {
                item.classList.add('purchased');
                item.textContent = `${themeName} (Purchased)`;
            }
        });
    } else {
        console.error('Error:', data.message);
    }
});

// Запрашиваем купленные темы при открытии модального окна
socket.emit('get_bought_themes', { username: currentUser });

// Функция для применения темы
function applyMessagesTheme(theme, price) {
    if (currentBalance >= price) {
        socket.emit('apply_theme', { username: currentUser, theme: theme, price: price });

        // Применяем выбранную тему в UI
        document.body.classList.add(theme);  // Применяем выбранную тему
    } else {
        showToastNotification('You do not have enough coins to apply this theme.','error');
    }
}

// Слушаем ответ от сервера при успешном применении темы
socket.on('theme_applied', (data) => {
    if (data.success) {
        if (data.already_purchased) {
            showToastNotification(`You have already purchased the ${data.theme} theme. It has been applied!`);
        } else {
            currentBalance = data.coins;  // Обновляем баланс
            showToastNotification(`Theme ${data.theme} applied successfully! Your new balance: ${currentBalance} Coins`);
        }
    } else {
        showToastNotification('Error: ' + data.message);
    }
});
// Получаем элементы
const banStatusModal = document.getElementById('ban-status-modal');
const violationsCountElement = document.getElementById('violations-count');
const remainingTimeElement = document.getElementById('remaining-time');
const payBanButton = document.getElementById('pay-ban');
const closeBanModalButton = document.getElementById('close-ban-modal');

// Функция для открытия модального окна и отображения информации
function openBanStatusModal() {
    const countBlocks = parseInt(localStorage.getItem('countBlocks')) || 0;
    const remainingTime = countBlocks * 30;  // Например, 30 секунд на одно нарушение

    // Отображаем количество нарушений и оставшееся время
    violationsCountElement.textContent = countBlocks;
    remainingTimeElement.textContent = remainingTime;

    // Открываем модальное окно
    banStatusModal.classList.add('active');
}

// Закрытие модального окна
closeBanModalButton.addEventListener('click', () => {
    banStatusModal.classList.remove('active');
});

// Открываем модальное окно при клике на пункт "My Ban Status"
document.getElementById('my-ban-status-option').addEventListener('click', openBanStatusModal);

// Слушаем событие на успешное списание монет и обновление countBlocks
socket.on('ban_reduction_success', (data) => {
    if (data.success) {
        // Обновляем countBlocks в localStorage
        localStorage.setItem('countBlocks', data.new_count_blocks);

        // Обновляем UI
        violationsCountElement.textContent = data.new_count_blocks;
        remainingTimeElement.textContent = data.new_count_blocks * 30;

        showToastNotification(`Successfully reduced ban. New violation count: ${data.new_count_blocks}`);
    } else {
        alert('Failed to reduce ban.');
    }
});

// Слушаем событие на ошибку списания монет
socket.on('ban_reduction_failed', (data) => {
    if (!data.success) {
        showToastNotification(data.message || 'Error occurred while reducing ban.');
    }
});

// Слушаем клик по кнопке "Pay" для списания монет и уменьшения нарушений
payBanButton.addEventListener('click', () => {
    const User = currentUser; // Имя текущего пользователя
    const countBlocks = parseInt(localStorage.getItem('countBlocks')) || 0;

    if (countBlocks > 0) {
        // Отправляем событие на сервер для списания монет
        socket.emit('pay_for_ban_reduction', { username: User, countBlocks });

        // Закрываем модальное окно после отправки
        banStatusModal.classList.remove('active');
    } else {
        showToastNotification('No violations to pay for.','error');
    }
});

function updatePing() {
    const pingIcon = document.getElementById('ping-icon');
    const pingValue = document.getElementById('ping-value');

    const start = Date.now();
    fetch('/ping')
        .then(() => {
            const latency = Date.now() - start;
            pingValue.textContent = `${latency} ms`;

            // Меняем цвет иконки в зависимости от пинга
            if (latency < 100) {
                pingIcon.style.color = '#4caf50'; // Зеленый
            } else if (latency < 200) {
                pingIcon.style.color = '#ffc107'; // Желтый
            } else {
                pingIcon.style.color = '#f44336'; // Красный
            }
        })
        .catch(() => {
            pingValue.textContent = 'Error';
            pingIcon.style.color = '#f44336'; // Красный при ошибке
        });
}

// Обновляем пинг каждые 5 секунд
setInterval(updatePing, 30000);

// Обновляем сразу после загрузки страницы
updatePing();

socket.on('user_banned', (data) => {
    if (data.success) {
        setTimeout(() => { // Задержка перед перенаправлением
            window.location.href = '/';
        }, 1000); // Задержка в 1.5 секунды (можно изменить)
    } else {
    }
});

async function checkBanStatus(username) {  // Передаем имя пользователя в функцию
    try {
        const response = await fetch('/api/check-ban-status', {
            method: 'POST',  // Указываем метод POST
            headers: {
                'Content-Type': 'application/json'  // Указываем тип контента
            },
            body: JSON.stringify({ username: username })  // Отправляем имя пользователя в теле запроса
        });

        if (!response.ok) {
            const errorData = await response.json();  // Получаем JSON с ошибкой с сервера
            throw new Error(`${response.status}: ${errorData.error}`);  // Генерируем ошибку с сообщением с сервера
        }

        const data = await response.json();
        return data.banned;  // Возвращаем true, если пользователь заблокирован, и false, если нет

    } catch (error) {
        console.error('Error checking ban status:', error);
        return false;  // Возвращаем false в случае ошибки
    }
}

// Пример использования:
const usernameToCheck = currentUser;  // Или любое другое имя пользователя
checkBanStatus(usernameToCheck)
    .then(isBanned => {
        if (isBanned) {
            console.log(`${usernameToCheck} is banned`);
            window.location.href = '/';  // Перенаправляем на главную страницу
        } else {
            // console.log(`${usernameToCheck} is not banned`);
            // Продолжаем работу
        }
    });
	

// Универсальная функция для обработки ошибок
function handleError(errorMessage) {
    const examContainer = document.getElementById('examQuestions');
    const examHeader = document.getElementById('examTitle');
    const finishExamButton = document.getElementById('finishExam');

    examHeader.style.display = 'none';
    finishExamButton.style.display = 'none';
    examContainer.innerHTML = `
        <div class="no-exams">
            <i class="fas fa-exclamation-circle"></i> ${errorMessage}
        </div>
    `;
}

// Делегирование события для обновления стилей при выборе радио
document.getElementById('examQuestions').addEventListener('change', function(event) {
    if (event.target && event.target.type === 'radio') {
        // Получаем имя текущего вопроса
        const questionName = event.target.name;

        // Находим все элементы label для этого вопроса
        const labels = document.querySelectorAll(`input[name="${questionName}"] + label`);
        
        // Убираем стили с предыдущего выбранного варианта
        labels.forEach(label => {
            label.style.borderColor = '#ddd';
            label.style.backgroundColor = '#f9f9f9';
            label.style.color = '#333';
        });

        // Находим label, связанный с выбранным радио
        const selectedRadio = event.target;
        const selectedLabel = document.querySelector(`label[for="${selectedRadio.id}"]`);

        if (selectedLabel) {
            // Применяем стили только к выбранному варианту
            selectedLabel.style.borderColor = '#4CAF50';
            selectedLabel.style.backgroundColor = '#4CAF50';
            selectedLabel.style.color = 'white';
        }
    }
});

async function addCoins(username, coins) {
    try {
        const response = await fetch('/add_coins', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, coins })
        });

        const data = await response.json();
        if (data.success) {
            console.log(`✅ ${username} получил(а) ${coins} монет. Новый баланс: ${data.coins}`);
        } else {
            console.error("Ошибка:", data.error);
        }
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}

 function handleVisibilityChange() {
        if (document.hidden) {
            blockUser(180);
        }
    }
	
function disableCopyPasteAndRightClick() {
    // Блокируем копирование
    document.addEventListener('copy', function(event) {
        event.preventDefault();
        showToastNotification("Copying is disabled.", "error");
    });

    // Блокируем вставку
    document.addEventListener('paste', function(event) {
        event.preventDefault();
        showToastNotification("Pasting is disabled.", "error");
    });

    // Блокируем правый клик мыши
    document.addEventListener('contextmenu', function(event) {
        event.preventDefault();
        showToastNotification("Right-clicking is disabled.", "error");
    });
}

// Функция для инициализации и деактивации безопасности
function initExamSecurity(enable = true) {
    if (enable) {
        // Включаем безопасность, блокируем копирование, вставку и правый клик
        document.addEventListener('visibilitychange', handleVisibilityChange);  // Отслеживаем смену видимости страницы

        // Блокируем копирование, вставку и правый клик
        document.addEventListener('copy', function(event) {
            event.preventDefault();
            showToastNotification("Copying is disabled.", "error");
        });

        document.addEventListener('paste', function(event) {
            event.preventDefault();
            showToastNotification("Pasting is disabled.", "error");
        });

        document.addEventListener('contextmenu', function(event) {
            event.preventDefault();
            showToastNotification("Right-clicking is disabled.", "error");
        });

        showToastNotification("Anti Cheating system is active.", "success");
    } else {
        // Включаем все действия и восстанавливаем нормальную работу
        document.removeEventListener('visibilitychange', handleVisibilityChange);

        document.removeEventListener('copy', function(event) {
            event.preventDefault();
            showToastNotification("Copying is disabled.", "error");
        });

        document.removeEventListener('paste', function(event) {
            event.preventDefault();
            showToastNotification("Pasting is disabled.", "error");
        });

        document.removeEventListener('contextmenu', function(event) {
            event.preventDefault();
            showToastNotification("Right-clicking is disabled.", "error");
        });

        showToastNotification("Anti Cheating system is disabled.", "success");
    }
}

document.getElementById('examTaskOption').addEventListener('click', function() {

    const examContainer = document.getElementById('examQuestions');
    const examHeader = document.getElementById('examTitle');
    const finishExamButton = document.getElementById('finishExam');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const examTimerDisplay = document.getElementById('exam-timer');

    examHeader.style.display = 'none';
    finishExamButton.style.display = 'none';
    examTimerDisplay.style.display = 'none';
    loadingSpinner.style.display = 'block';

    document.getElementById('examModal').style.display = 'flex';
    loadingSpinner.style.display = 'inline-block';
    examContainer.innerHTML = '';
	enableFinishButton();
    const url = `/get_exam_questions?username=${currentUser}`;

    fetch(url)
    .then(response => {
        console.log("Response Status:", response.status); // Логируем статус ответа
        if (!response.ok) {
            return response.json().then(errorData => {
                // Показываем только сообщение ошибки без статуса
                throw new Error(errorData.error || 'Unknown error');
            });
        }
        return response.json();
    })
    .then(data => {
        // Проверка на ошибки в данных
        if (data.error) {
            handleError(data.error);  // Покажем ошибку как уведомление или на странице
            loadingSpinner.style.display = 'none';
            return;
        }

        loadingSpinner.style.display = 'none';
        examHeader.style.display = 'block';
        finishExamButton.style.display = 'block';
        examTimerDisplay.style.display = 'block';
		initExamSecurity(true);

        data.questions.forEach((question, index) => {
            let instruction = "";

            switch (question.type) {
                case "true_false":
                    instruction = `<p> <i class="fas fa-exclamation-circle"></i> Choose True or False.</p>`;
                    break;
                case "multiple_choice":
                    instruction = `<p> <i class="fas fa-check-circle"></i> Select the correct answer.</p>`;
                    break;
                case "fill_gaps":
                    instruction = `<p> <i class="fas fa-pencil-alt"></i> Fill in the blank.</p>`;
                    break;
                case "unscramble":
                    instruction = `<p> <i class="fas fa-random"></i> Unscramble the word.</p>`;
                    break;
                case "reading":
                    instruction = `<p> <i class="fas fa-book"></i> Read the passage and answer.</p>`;
                    break;
                case "listening":
                    instruction = `<p> <i class="fas fa-headphones"></i> Listen to the audio and write the missing word.</p>`;
                    break;
            }

            let questionHtml = `<p>${index + 1}. ${question.text}</p>${instruction}`;

            if (question.type === 'true_false') {
                questionHtml += `
                    <input type="radio" name="q${index}" value="True" id="true${index}">
                    <label for="true${index}">True</label>
                    <input type="radio" name="q${index}" value="False" id="false${index}">
                    <label for="false${index}">False</label>
                `;
            } else if (question.type === 'multiple_choice' && Array.isArray(question.options)) {
                question.options.forEach(option => {
                    const optionId = `${option.replace(/\s+/g, '')}${index}`;
                    questionHtml += `<input type="radio" name="q${index}" value="${option}" id="${optionId}">
                                      <label for="${optionId}">${option}</label>`;
                });
            } else if (['fill_gaps', 'unscramble', 'reading', 'listening'].includes(question.type)) {
                questionHtml += `<input type="text" name="q${index}" autocomplete="off" spellcheck="false">`;
            }

            examContainer.innerHTML += `<div class="exam-question exam-${question.type}">${questionHtml}</div>`;
        });

        return fetch('/get_remaining_time');
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                // Покажем только сообщение ошибки без статуса
                throw new Error(errorData.error || 'Unknown error');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.remaining_time) {
            let remainingTime = data.remaining_time * 1000;

            function updateTimer() {
                if (remainingTime <= 0) {
                    finishExam();
                    return;
                }
                let minutes = Math.floor(remainingTime / 60000);
                let seconds = Math.floor((remainingTime % 60000) / 1000);
                examTimerDisplay.innerHTML = `<i class="fas fa-clock"></i> ${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
                remainingTime -= 1000;
            }

            let timerInterval = setInterval(updateTimer, 1000);

            function finishExam() {
                clearInterval(timerInterval);
                showToastNotification('Time is up! The exam will be automatically finished.');
                finishExamButton.click();
            }
			finishExamButton.addEventListener('click', function() {
			const examQuestions = document.querySelectorAll('.exam-question');
			let answeredCount = 0;

			examQuestions.forEach((question) => {
			const inputs = question.querySelectorAll('input[type="radio"], input[type="text"]');
        
			// Проверка, есть ли хотя бы один выбранный ответ (для радиокнопок или текстовых полей)
			inputs.forEach(input => {
            if ((input.type === "radio" && input.checked) || (input.type === "text" && input.value.trim() !== "")) {
                answeredCount++;
            }
        });
    });

    if (answeredCount === 0) {
        // Если ни один вопрос не был отвечен
        showToastNotification("Please answer at least one question before finishing the exam.", "error");
    } else {
        // Если хотя бы один вопрос был отвечен
        const loadingFinishExam = document.getElementById('loadingFinishExam');
        loadingFinishExam.style.display = 'flex';
        finishExamButton.disabled = true;
        clearInterval(timerInterval);
        submitExamResults();
    }
	});

        }
    })
    .catch(error => {
        console.error('Error:', error.message);  // Логирование ошибки
        handleError(error.message);  // Отображаем только текст ошибки
        loadingSpinner.style.display = 'none';
    });

});


function fetchExamQuestions() {
    // Fetch exam questions from the server
    return fetch('/get_exam_questions_result')
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                console.error(result.error);
                showToastNotification(result.error);
                return null;
            }
            return result.questions; // Return the questions
        })
        .catch(error => {
            console.error('Error fetching exam questions:', error);
            showToastNotification('Failed to fetch questions. Please try again.');
            return null;
        });
}

function submitExamResults() {
    const answers = {};
    const examResultsHtml = [];

    // Fetch the questions before submitting the answers
    fetchExamQuestions().then(examQuestions => {
        if (!examQuestions) {
            return; // If questions are not available, return
        }

        // Collect the answers from the user
        document.querySelectorAll('.exam-question').forEach((question, index) => {
            const selectedOption = question.querySelector('input:checked') || question.querySelector('input[type="text"]');
            if (selectedOption && selectedOption.value) {
                answers[`q${index + 1}`] = selectedOption.value;
            }
        });

		/*
        if (Object.keys(answers).length === 0) {
            showToastNotification("Please answer all questions before finishing the exam.");
            document.getElementById('loadingFinishExam').style.display = 'none'; // Hide loading animation in case of error
            document.getElementById('finishExam').disabled = false; // Re-enable the button
            return;
        }*/

        // Send answers to the server
        fetch('/submit_exam', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: currentUser, answers: answers })
        })
        .then(response => response.json())
        .then(result => {
            document.getElementById('loadingFinishExam').style.display = 'none'; // Hide loading animation
            document.getElementById('finishExam').disabled = false; // Re-enable the button
            document.removeEventListener("visibilitychange", handleVisibilityChange);

            if (result.error) {
                showToastNotification(`Error: ${result.error}`);
                return;
            }

			initExamSecurity(false);
            // Display the correct, incorrect, and skipped answers
            document.getElementById('correctAnswers').textContent = result.correct;
            document.getElementById('incorrectAnswers').textContent = result.incorrect;
            document.getElementById('skippedAnswers').textContent = result.skipped;
			document.getElementById('coinsReward').style.display = 'none';
			document.getElementById('coinCount').textContent = '';

            let totalQuestions = result.correct + result.incorrect + result.skipped;
            let percentage = totalQuestions > 0 ? (result.correct / totalQuestions) * 100 : 0;
            document.getElementById('progressBar').style.width = `${percentage}%`;
            document.getElementById('progressText').textContent = `${Math.round(percentage)}%`;

			let motivationText = "Keep pushing forward!";
        if (percentage >= 80) {
            document.getElementById('coinsReward').style.display = 'flex';
            document.getElementById('coinCount').textContent = '10';
            addCoins(currentUser, 10);
            motivationText = "Great job! You achieved 80% or higher! 🎉";
        } else if (percentage >= 50) {
            motivationText = "You're doing well! Aim for 80% next time!";
        } 	else {
            motivationText = "Don't give up! Keep practicing!";
			}
			document.getElementById('examMotivation').textContent = motivationText;
		
            // Create the results HTML if questions exist in result
            examQuestions.forEach((question, index) => {
                let instruction = '';
                switch (question.type) {
                    case 'true_false':
                        instruction = `<p> <i class="fas fa-exclamation-circle"></i> Choose True or False.</p>`;
                        break;
                    case 'multiple_choice':
                        instruction = `<p> <i class="fas fa-check-circle"></i> Select the correct answer.</p>`;
                        break;
                    case 'fill_gaps':
                        instruction = `<p> <i class="fas fa-pencil-alt"></i> Fill in the blank.</p>`;
                        break;
                    case 'unscramble':
                        instruction = `<p> <i class="fas fa-random"></i> Unscramble the word.</p>`;
                        break;
                    case 'reading':
                        instruction = `<p> <i class="fas fa-book"></i> Read the passage and answer.</p>`;
                        break;
                    case 'listening':
                        instruction = `<p> <i class="fas fa-headphones"></i> Listen to the audio and write the missing word.</p>`;
                        break;
                }

                let questionHtml = `<p>${index + 1}. ${question.text}</p>${instruction}`;

                // Display the user's selected answer and whether it was correct
                const userAnswer = answers[`q${index + 1}`];
                let isCorrect = userAnswer === question.correct;
                let resultClass = isCorrect ? 'correct' : 'incorrect';

                if (question.type === 'true_false') {
                    questionHtml += `
                        <input type="radio" name="q${index}" value="True" id="true${index}" ${userAnswer === 'True' ? 'checked' : ''}>
                        <label for="true${index}">True</label>
                        <input type="radio" name="q${index}" value="False" id="false${index}" ${userAnswer === 'False' ? 'checked' : ''}>
                        <label for="false${index}">False</label>
                    `;
                } else if (question.type === 'multiple_choice' && Array.isArray(question.options)) {
                    question.options.forEach(option => {
                        const optionId = `${option.replace(/\s+/g, '')}${index}`;
                        questionHtml += `<input type="radio" name="q${index}" value="${option}" id="${optionId}" ${userAnswer === option ? 'checked' : ''}>
                                          <label for="${optionId}">${option}</label>`;
                    });
                } else if (['fill_gaps', 'unscramble', 'reading', 'listening'].includes(question.type)) {
                    questionHtml += `<input type="text" name="q${index}" style="pointer-events: none;" autocomplete="off" spellcheck="false" value="${userAnswer || ''}">`;
                }

                // Add a result indicator for each question
                questionHtml += `<p class="${resultClass}">Your answer: ${userAnswer || 'No answer provided'} ${isCorrect ? '(Correct)' : '(Incorrect)'}</p>`;

                // Add the question HTML to the results container
                examResultsHtml.push(`<div class="exam-question exam-${question.type}">${questionHtml}</div>`);
            });

            // Ensure that the modal exists before updating its content
            const examResultsModal = document.getElementById('ExamResultsModal');
            if (examResultsModal) {
                document.getElementById('ExamResultsModal').style.display = 'flex';
                document.getElementById('examResultsContainer').innerHTML = examResultsHtml.join('');
            } else {
                console.error("Exam Results Modal not found.");
            }
        })
        .catch(error => {
            console.error('Error during exam submission:', error);
            showToastNotification('An error occurred. Please try again.');
            document.getElementById('loadingFinishExam').style.display = 'none'; // Hide loading animation in case of error
            document.getElementById('finishExam').disabled = false; // Re-enable the button
        });
    });
}

function toggleMistakes() {
    const resultsContainer = document.getElementById('examResultsContainer');
    const toggleText = document.getElementById('toggleText');
    const toggleIcon = document.getElementById('toggleIcon');
    
    // Проверяем текущее состояние
    const isVisible = resultsContainer.style.display === 'block';
    
    if (isVisible) {
        // Скрываем контейнер и меняем текст/иконку
        resultsContainer.style.display = 'none';
        toggleText.textContent = 'Do you want to see your mistakes?';
        toggleIcon.classList.remove('fa-chevron-up');
        toggleIcon.classList.add('fa-chevron-down');
    } else {
        // Показываем контейнер и меняем текст/иконку
        resultsContainer.style.display = 'block';
        toggleText.textContent = 'Hide mistakes';
        toggleIcon.classList.remove('fa-chevron-down');
        toggleIcon.classList.add('fa-chevron-up');
    }
}

// Получаем кнопку по ID
const finishButton = document.getElementById('finishExam');

// Функция для отключения кнопки
function disableFinishButton() {
    finishButton.setAttribute('disabled', 'true'); // Делаем кнопку отключённой
}

// Функция для включения кнопки
function enableFinishButton() {
    finishButton.removeAttribute('disabled');  // Убираем атрибут disabled
}

// Закрытие модального окна результатов
document.getElementById('closeExamResults').addEventListener('click', function() {
	disableFinishButton();
    document.getElementById('ExamResultsModal').style.display = 'none';
});

// Закрытие по кнопке "Done"
document.getElementById('ResultDone').addEventListener('click', function() {
    document.getElementById('ExamResultsModal').style.display = 'none';
	document.getElementById('examModal').style.display = 'none';
});


document.getElementById('closeExamModal').addEventListener('click', function() {
    document.getElementById('examModal').style.display = 'none';
});

socket.on('exam_started', function(data) {
    showToastNotification(data.message);
});