// Получаем элементы, уже существующие в коде
const form = document.querySelector('.login-form');
const body = document.body;
const forgotPasswordLink = document.getElementById('forgot-password-link');
const modal = document.getElementById('forgot-password-modal');
const closeModalButton = document.getElementById('close-modal');
const recoveryUsernameInput = document.getElementById('recovery-username');
const recoverBtn = document.getElementById('recover-btn');
const usernameInput = document.getElementById('username');
const errorContainer = document.querySelector('.error-container'); // Контейнер для ошибок
const avatarImage = document.getElementById('user-avatar');
const avatarContainer = document.querySelector('.avatar-container');

// --- Логика получения аватара при вводе username ---
usernameInput.addEventListener('input', async () => {
    const username = usernameInput.value.trim();
    if (username.length === 0) {
        avatarContainer.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/get_avatar/${username}`);
        const data = await response.json();

        if (data.avatar_url) {
            avatarContainer.style.display = 'flex';
            avatarImage.style.display = 'block';
            avatarImage.src = data.avatar_url;
            errorContainer.style.backgroundColor = '#28a745';
        } else {
            avatarContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching avatar:', error);
        avatarContainer.style.display = 'none';
    }
});


const loginButtonText = document.querySelector('.login-button .text-skeleton');

form.addEventListener('submit', (e) => {
    e.preventDefault();

    // При необходимости можно добавить дополнительный визуальный эффект или отключить кнопку
    loginButtonText.style.pointerEvents = 'none';
	 loginButtonText.classList.add('text-loading');
    
    // Сохраняем данные в localStorage и sessionStorage
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    localStorage.setItem('username', username);
    localStorage.setItem('password', password);

    setTimeout(() => {
        sessionStorage.setItem('username', username);
        form.submit();
        console.log("User logged in:", sessionStorage.getItem('username'));
    }, 0);
});


// --- Логика модального окна "Forgot Password" ---
forgotPasswordLink.addEventListener('click', () => {
    modal.style.display = 'flex';
});

closeModalButton.addEventListener('click', () => {
    modal.style.display = 'none';
});

recoverBtn.addEventListener('click', () => {
    const recoveryUsername = recoveryUsernameInput.value;
    const storedUsername = localStorage.getItem('username');

    if (recoveryUsername === storedUsername) {
        const storedPassword = localStorage.getItem('password');
        recoveryResult.innerHTML = `Your username: ${storedUsername} <br> Your password: ${storedPassword}`;
        recoveryResult.style.color = '#28a745';
    } else {
        recoveryResult.innerHTML = 'Username not found!';
        recoveryResult.style.color = '#dc3545';
    }
});

// --- Новая логика для проверки localStorage и отображения модального окна "Remember Me" ---
window.addEventListener('load', () => {
    const storedUsername = localStorage.getItem('username');
    const storedPassword = localStorage.getItem('password');
    
    // Если найдены сохранённые данные, показываем модальное окно
    if (storedUsername && storedPassword) {
        const rememberModal = document.getElementById('remember-modal');
        const rememberUsername = document.getElementById('remember-username');
        rememberUsername.textContent = storedUsername;
        rememberModal.style.display = 'flex';
    }
});

// Обработчик для кнопки "Continue"
document.getElementById('continue-btn').addEventListener('click', () => {
    const storedUsername = localStorage.getItem('username');
    const storedPassword = localStorage.getItem('password');
    
    // Автоматически заполняем форму и инициируем вход
    usernameInput.value = storedUsername;
    document.getElementById('password').value = storedPassword;
    sessionStorage.setItem('username', storedUsername);

    // Можно добавить задержку или анимацию, как в основном обработчике формы
    setTimeout(() => {
        form.submit();
    }, 0);

    // Скрываем модальное окно
    document.getElementById('remember-modal').style.display = 'none';
});

// Обработчик для кнопки "Cancel Account"
document.getElementById('cancel-btn').addEventListener('click', () => {
    // Удаляем сохранённые данные из localStorage
    localStorage.removeItem('username');
    localStorage.removeItem('password');
    
    // Скрываем модальное окно
    document.getElementById('remember-modal').style.display = 'none';
});
