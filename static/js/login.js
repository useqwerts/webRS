const form = document.querySelector('.login-form');
const loader = document.getElementById('loader');
const buttonText = document.getElementById('button-text');
const body = document.body;
const forgotPasswordLink = document.getElementById('forgot-password-link');
const modal = document.getElementById('forgot-password-modal');
const closeModalButton = document.getElementById('close-modal');
const recoveryUsernameInput = document.getElementById('recovery-username');
const recoverBtn = document.getElementById('recover-btn');
const recoveryResult = document.getElementById('recovery-result');

form.addEventListener('submit', (e) => {
    e.preventDefault();

    // Показать загрузочный спиннер и наложить эффект размытия
    loader.style.display = 'flex';
    body.style.filter = 'blur(1px)'; // Размытие фона

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Сохраняем username и пароль в localStorage
    localStorage.setItem('username', username);
    localStorage.setItem('password', password);

    // Имитируем задержку в 1 секунду для демонстрации процесса авторизации
    setTimeout(() => {
        sessionStorage.setItem('username', username);
        form.submit(); // Отправка формы
        console.log("User logged in:", sessionStorage.getItem('username'));
    }, 1000);
});

// Forgot Password Modal Logic
forgotPasswordLink.addEventListener('click', () => {
    modal.style.display = 'flex'; // Показываем модальное окно
});

closeModalButton.addEventListener('click', () => {
    modal.style.display = 'none'; // Закрыть модальное окно
});

recoverBtn.addEventListener('click', () => {
    const recoveryUsername = recoveryUsernameInput.value;
    const storedUsername = localStorage.getItem('username');

    if (recoveryUsername === storedUsername) {
        const storedPassword = localStorage.getItem('password');
        recoveryResult.innerHTML = `Your username: ${storedUsername} <br> Your password: ${storedPassword}`;
        recoveryResult.style.color = '#28a745'; // Green color for success
    } else {
        recoveryResult.innerHTML = 'Username not found!';
        recoveryResult.style.color = '#dc3545'; // Red color for error
    }
});
