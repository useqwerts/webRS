// Получаем элементы, уже существующие в коде
const form = document.querySelector('.login-form');
const body = document.body;
const forgotPasswordLink = document.getElementById('forgot-password-link');
const modal = document.getElementById('forgot-password-modal');
const closeModalButton = document.getElementById('close-modal');
const recoveryUsernameInput = document.getElementById('recovery-username');
const recoverBtn = document.getElementById('recover-btn');
const usernameInput = document.getElementById('username');
const errorContainer = document.querySelector('.error-container');
const errorMessage = document.getElementById('error-message');
const avatarImage = document.getElementById('user-avatar');
const avatarContainer = document.querySelector('.avatar-container');

// Новые элементы для Terms and Conditions
const termsCheckbox = document.getElementById('terms');
const termsLink = document.getElementById('terms-link');
const termsModal = document.getElementById('terms-modal');
const acceptTermsBtn = document.getElementById('accept-terms-btn');
const declineTermsBtn = document.getElementById('decline-terms-btn');

let debounceTimer;

// Логика для проверки localStorage и отображения модального окна "Remember Me"
window.addEventListener('load', () => {
    const storedUsername = localStorage.getItem('username');
    const storedPassword = localStorage.getItem('password');
    
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
    
    usernameInput.value = storedUsername;
    document.getElementById('password').value = storedPassword;
    sessionStorage.setItem('username', storedUsername);

    setTimeout(() => {
        form.submit();
    }, 0);

    document.getElementById('remember-modal').style.display = 'none';
});

// Обработчик для кнопки "Cancel Account"
document.getElementById('cancel-btn').addEventListener('click', () => {
    localStorage.removeItem('username');
    localStorage.removeItem('password');
    document.getElementById('remember-modal').style.display = 'none';
});

usernameInput.addEventListener('input', () => {
    const username = usernameInput.value.trim();
    
    if (username.length === 0) {
        avatarContainer.style.display = 'none';
        const fallback = avatarContainer.querySelector('.avatar-image.fallback');
        if (fallback) fallback.remove();
        return;
    }
    
    clearTimeout(debounceTimer);
    
    debounceTimer = setTimeout(async () => {
        try {
            const response = await fetch(`/get_avatar/${username}`);
            const data = await response.json();

            if (data.avatar_url) {
                avatarContainer.style.display = 'flex';
                avatarImage.style.display = 'block';
                avatarImage.src = data.avatar_url;
                const fallback = avatarContainer.querySelector('.avatar-image.fallback');
                if (fallback) fallback.remove();
                errorContainer.style.backgroundColor = '#28a745';
            } else {
                avatarImage.style.display = 'none';
                avatarContainer.style.display = 'flex';
                let fallback = avatarContainer.querySelector('.avatar-image.fallback');
                if (!fallback) {
                    fallback = document.createElement('div');
                    fallback.className = 'avatar-image fallback';
                    fallback.style.display = 'flex';
                    fallback.style.alignItems = 'center';
                    fallback.style.justifyContent = 'center';
                    fallback.style.fontSize = '24px';
                    fallback.style.fontWeight = 'bold';
                    fallback.style.color = '#fff';
                    fallback.style.backgroundColor = '#6a11cb';
                    fallback.style.width = '48px';
                    fallback.style.height = '48px';
                    fallback.style.borderRadius = '50%';
                    avatarContainer.appendChild(fallback);
                }
                fallback.textContent = username[0].toUpperCase();
            }
        } catch (error) {
            console.error('Error fetching avatar:', error);
            avatarImage.style.display = 'none';
            avatarContainer.style.display = 'flex';
            let fallback = avatarContainer.querySelector('.avatar-image.fallback');
            if (!fallback) {
                fallback = document.createElement('div');
                fallback.className = 'avatar-image fallback';
                fallback.style.display = 'flex';
                fallback.style.alignItems = 'center';
                fallback.style.justifyContent = 'center';
                fallback.style.fontSize = '24px';
                fallback.style.fontWeight = 'bold';
                fallback.style.color = '#fff';
                fallback.style.backgroundColor = '#6a11cb';
                fallback.style.width = '48px';
                fallback.style.height = '48px';
                fallback.style.borderRadius = '50%';
                avatarContainer.appendChild(fallback);
            }
            fallback.textContent = username[0].toUpperCase();
        }
    }, 700);
});

const container = document.getElementById('login-button');

// Показываем модальное окно Terms and Conditions при клике на ссылку
termsLink.addEventListener('click', (e) => {
    e.preventDefault();
    termsModal.style.display = 'block';
});

// Принимаем Terms and Conditions
acceptTermsBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    
    if (!username) {
        errorContainer.style.display = 'block';
        errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle error-icon"></i> Please enter a username before accepting the Terms and Conditions.';
        termsModal.style.display = 'none';
        return;
    }

    try {
        const response = await fetch('/accept_terms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username }),
        });

        const data = await response.json();

        if (data.success) {
            termsCheckbox.checked = true;
            termsModal.style.display = 'none';
        } else {
            errorContainer.style.display = 'block';
            errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle error-icon"></i> Error accepting Terms and Conditions. Please try again.';
            termsModal.style.display = 'none';
        }
    } catch (error) {
        console.error('Error accepting terms:', error);
        errorContainer.style.display = 'block';
        errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle error-icon"></i> Error accepting Terms and Conditions. Please try again.';
        termsModal.style.display = 'none';
    }
});

// Отклоняем Terms and Conditions
declineTermsBtn.addEventListener('click', () => {
    termsCheckbox.checked = false;
    termsModal.style.display = 'none';
});

// Проверяем Terms and Conditions перед отправкой формы
container.addEventListener('click', async (e) => {
    e.preventDefault();

    const username = usernameInput.value.trim();

    if (!termsCheckbox.checked) {
        errorContainer.style.display = 'block';
        errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle error-icon"></i> You must accept the Terms and Conditions to proceed.';
        return;
    }

    container.classList.add('active');

    const password = document.getElementById('password').value;
    localStorage.setItem('username', username);
    localStorage.setItem('password', password);
    sessionStorage.setItem('username', username);
    sessionStorage.setItem('password', password);

    form.submit();
});

container.addEventListener('animationend', () => {
    container.classList.remove('active');
});

closeModalButton.addEventListener('click', () => {
    modal.style.display = 'none';
});


// --- Логика для проверки localStorage и отображения модального окна "Remember Me" ---
window.addEventListener('load', () => {
    const storedUsername = localStorage.getItem('username');
    const storedPassword = localStorage.getItem('password');
    
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
    
    usernameInput.value = storedUsername;
    document.getElementById('password').value = storedPassword;
    sessionStorage.setItem('username', storedUsername);

    setTimeout(() => {
        form.submit();
    }, 0);

    document.getElementById('remember-modal').style.display = 'none';
});

// Обработчик для кнопки "Cancel Account"
document.getElementById('cancel-btn').addEventListener('click', () => {
    localStorage.removeItem('username');
    localStorage.removeItem('password');
    document.getElementById('remember-modal').style.display = 'none';
});
