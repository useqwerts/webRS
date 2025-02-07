const form = document.querySelector('.login-form');
const loader = document.getElementById('loader');
const body = document.body;
const forgotPasswordLink = document.getElementById('forgot-password-link');
const modal = document.getElementById('forgot-password-modal');
const closeModalButton = document.getElementById('close-modal');
const recoveryUsernameInput = document.getElementById('recovery-username');
const recoverBtn = document.getElementById('recover-btn');
const recoveryResult = document.getElementById('recovery-result');
const usernameInput = document.getElementById('username');
const errorContainer = document.querySelector('.error-container'); // Контейнер для ошибок

// Вставляем этот код в файл login.js

// Получаем ссылку на изображение аватарки
const avatarImage = document.getElementById('user-avatar');
const avatarContainer = document.querySelector('.avatar-container');

// Следим за вводом username и получаем аватарку с сервера
usernameInput.addEventListener('input', async () => {
    const username = usernameInput.value.trim();
    if (username.length === 0) {
        avatarContainer.style.display = 'none'; // Скрыть аватарку, если поле пустое
        return;
    }

    try {
        const response = await fetch(`/get_avatar/${username}`);
        const data = await response.json();

        if (data.avatar_url) {
            avatarContainer.style.display = 'flex';  // Показываем аватар
            avatarImage.style.display = 'block';    // Делаем картинку видимой
            avatarImage.src = data.avatar_url;     // Устанавливаем URL аватара
            errorContainer.style.backgroundColor = '#28a745';  // Зеленый фон
        } else {
            avatarContainer.style.display = 'none';  // Если аватарки нет, скрываем контейнер
        }
    } catch (error) {
        console.error('Error fetching avatar:', error);
        avatarContainer.style.display = 'none'; // Ошибка - скрыть контейнер
    }
});


// 🔹 Отправка формы с анимацией
form.addEventListener('submit', (e) => {
    e.preventDefault();

    //loader.style.display = 'flex';
    body.style.filter = 'blur(1px)';

    const username = usernameInput.value;
    const password = document.getElementById('password').value;

    localStorage.setItem('username', username);
    localStorage.setItem('password', password);

    setTimeout(() => {
        sessionStorage.setItem('username', username);
        form.submit();
        console.log("User logged in:", sessionStorage.getItem('username'));
    }, 1000);
});

// 🔹 Forgot Password Modal Logic
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
