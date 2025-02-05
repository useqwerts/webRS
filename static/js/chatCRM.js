        const socket = io(); // Подключаемся к серверу через Socket.IO
        const releaseUpdateButton = document.getElementById('releaseUpdateButton');
        const currentVersionElement = document.getElementById('currentVersion');
        const modal = document.getElementById('updateModal');
        const modalVersionElement = document.getElementById('modalVersion');
        const closeModalButton = document.getElementById('closeModalButton');

const navItems = document.querySelectorAll('.nav-item'); // Все элементы навигации
const contentSections = document.querySelectorAll('.content-section'); // Все секции контента

// Получаем элементы для спиннера и iframe
const chatSpinner = document.getElementById('chatSpinner');
const chatIframe = document.getElementById('chatIframe');

const addCoinsButton = document.getElementById('addCoinsButton');
const getBalanceButton = document.getElementById('getBalanceButton');
const usernameInput = document.getElementById('username');
const coinsInput = document.getElementById('coins');
const balanceUsernameInput = document.getElementById('balanceUsername');
const coinsMessage = document.getElementById('coinsMessage');
const balanceMessage = document.getElementById('balanceMessage');
const currentBalanceElement = document.getElementById('currentBalance');

// Обработка нажатия кнопки "Add Coins"
addCoinsButton.addEventListener('click', () => {
    const username = usernameInput.value.trim();
    const coins = parseInt(coinsInput.value);

    if (username && coins > 0) {
        // Отправляем запрос на сервер через Socket.IO
        socket.emit('add_coins', { username, coins });

        // Анимация на кнопке
        addCoinsButton.classList.add('clicked');

        // Скрыть сообщение баланса и показать сообщение об успешном добавлении
        balanceMessage.style.display = 'none';
        coinsMessage.style.display = 'inline-block';

        // Сброс поля ввода
        usernameInput.value = '';
        coinsInput.value = '';
    } else {
        alert("Please enter a valid username and coin amount.");
    }
});

// Обработка нажатия кнопки "Get Balance"
getBalanceButton.addEventListener('click', () => {
    const username = balanceUsernameInput.value.trim();

    if (username) {
        // Отправляем запрос на сервер через Socket.IO
        socket.emit('get_balance', username);

        // Скрываем сообщение об успешном добавлении и показываем сообщение о балансе
        coinsMessage.style.display = 'none';
        balanceMessage.style.display = 'inline-block';
    } else {
        alert("Please enter a valid username.");
    }
});

socket.on('coins_added', (data) => {
    if (data.success) {
        coinsMessage.textContent = `Coins added successfully to ${data.username}!`;

        // После успешного добавления монет обновляем баланс пользователя
        currentBalanceElement.textContent = data.coins;
        balanceMessage.style.display = 'inline-block';
    } else {
        coinsMessage.textContent = `Error: ${data.message}`;
    }
});

// Обработка ответа от сервера для получения баланса
socket.on('balance', (data) => {
    if (data.success) {
        balanceMessage.style.display = 'inline-block';
        currentBalanceElement.textContent = data.coins;
    } else {
        alert('User not found.');
    }
});


navItems.forEach(item => {
    item.addEventListener('click', () => {
        // Снимаем "active" с предыдущей активной кнопки
        document.querySelector('.nav-item.active').classList.remove('active');
        item.classList.add('active');

        // Убираем активные классы у всех секций
        contentSections.forEach(section => {
            section.classList.remove('active');
        });

        // Показываем целевую секцию с эффектами
        const targetSection = document.getElementById(item.dataset.section);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // Если выбрана секция Chat, загружаем iframe и показываем спиннер
        if (item.dataset.section === "chat") {
            chatSpinner.style.display = 'inline-block'; // Показываем спиннер
            chatIframe.style.display = 'none'; // Скрываем iframe

            // Загружаем страницу /chat в iframe с задержкой
            chatIframe.src = "/chat";

            // Создаем искусственную задержку для загрузки /chat
            setTimeout(function() {
                // Когда время задержки прошло, скрываем спиннер и показываем iframe
                chatSpinner.style.display = 'none'; // Скрываем спиннер
                chatIframe.style.display = 'block'; // Показываем iframe
            }, 0700); // Задержка в 1 секунду (1000 миллисекунд)
        }
		if (item.dataset.section === "ban") {
            // Скрываем все сообщения
            coinsMessage.style.display = 'none';
            balanceMessage.style.display = 'none';
            banMessage.style.display = 'none';
        }
    });
});

const banUsernameInput = document.getElementById('banUsername');
const banButton = document.getElementById('banButton');
const banMessage = document.getElementById('banMessage');

banButton.addEventListener('click', () => {
    const username = banUsernameInput.value.trim();

    if (username) {
        socket.emit('ban_user', username);
        banUsernameInput.value = ''; // Очищаем поле ввода
        coinsMessage.style.display = 'none';
        balanceMessage.style.display = 'none';
        banMessage.style.display = 'block';
    } else {
        alert("Please enter a username to ban.");
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const sliderContainer = document.getElementById('startExamSliderContainer');
    const sliderHandle = document.getElementById('startExamSliderHandle');
    const sliderText = document.querySelector('.slider-text');
	const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'none';  // Показываем индикатор
    if (!sliderContainer || !sliderHandle || !sliderText) {
        console.error("Slider elements not found! Check your HTML IDs.");
        return;
    }

    let isDragging = false;
    let sliderStartPositionX;
    let handleStartPositionX;

    // Когда начинается перетаскивание
    sliderHandle.addEventListener('mousedown', function(e) {
        isDragging = true;
        sliderStartPositionX = sliderContainer.getBoundingClientRect().left;
        handleStartPositionX = e.clientX - sliderHandle.offsetLeft;
        sliderHandle.style.transitionDuration = '0s'; // Отключаем анимацию во время перетаскивания
        sliderText.classList.add('hidden'); // Скрываем текст при перетаскивании
    });

    // Когда происходит перетаскивание
    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;

        let mouseX = e.clientX - sliderStartPositionX;
        let newHandlePosition = mouseX - handleStartPositionX;

        let minPos = 5;
        let maxPos = sliderContainer.offsetWidth - sliderHandle.offsetWidth - 5;

        if (newHandlePosition < minPos) newHandlePosition = minPos;
        if (newHandlePosition > maxPos) newHandlePosition = maxPos;

        sliderHandle.style.left = newHandlePosition + 'px';
    });

    // Когда отпускаем мышку
    document.addEventListener('mouseup', function(e) {
        if (!isDragging) return;
        isDragging = false;
        sliderHandle.style.transitionDuration = '0.4s'; // Включаем анимацию после завершения перетаскивания
        sliderText.classList.remove('hidden'); // Показать текст снова

        const slideThreshold = sliderContainer.offsetWidth - sliderHandle.offsetWidth - 20;

        if (sliderHandle.offsetLeft >= slideThreshold) {
            sliderContainer.classList.add('active');
            sliderHandle.classList.add('active');

            fetch('/api/start-exam', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                setTimeout(() => {
                    resetSlider();
                }, 1500);
            })
            .catch(error => {
                console.error('Error:', error);
                resetSlider();
            });
        } else {
            resetSlider();
        }
    });

    // Функция сброса слайдера
    function resetSlider() {
        sliderHandle.style.left = '5px';
        sliderContainer.classList.remove('active');
        sliderHandle.classList.remove('active');
        sliderText.classList.remove('hidden');
    }
});


const timeline = document.getElementById('timeline');

// Функция для добавления версии в временную шкалу
function addVersionToTimeline(version, date, description, isActive = false) {
    const timelineItem = document.createElement('div');
    timelineItem.classList.add('timeline-item');

    if (isActive) {
        timelineItem.classList.add('active');
    }

    // Добавление элементов в временной шкале
    const versionTitle = document.createElement('div');
    versionTitle.classList.add('version-title');
    versionTitle.textContent = version;

    const versionDate = document.createElement('div');
    versionDate.classList.add('version-date');
    versionDate.textContent = date;

    const versionDesc = document.createElement('div');
    versionDesc.classList.add('version-desc');
    versionDesc.textContent = description;

    // Составляем элемент временной шкалы
    timelineItem.appendChild(versionTitle);
    timelineItem.appendChild(versionDate);
    timelineItem.appendChild(versionDesc);

    // Делаем старые элементы неактивными
    const items = timeline.querySelectorAll('.timeline-item');
    items.forEach(item => {
        item.classList.remove('active');
        item.classList.add('inactive');
    });

    // Добавляем новый элемент с анимацией
    timelineItem.style.opacity = '0';
    timeline.appendChild(timelineItem);

    setTimeout(() => {
        timelineItem.style.opacity = '1';
        timelineItem.style.transform = 'translateY(0)';
    }, 100);
}

// Обработка нажатия кнопки "Release Update"
releaseUpdateButton.addEventListener('click', () => {
    fetch('/release-update', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentVersionElement.textContent = data.version;
                console.log(`Update released: ${data.version}`);

                // Добавляем новую версию в временную шкалу
                addVersionToTimeline(
                    data.version,
                    new Date().toLocaleDateString(),
                    data.description || 'No additional information',
                    true
                );
            }
        })
        .catch(err => console.error('Error releasing update:', err));
});

// Получение текущей версии при подключении
socket.on('currentVersion', (data) => {
    currentVersionElement.textContent = data.version;

    // Очищаем временную шкалу и добавляем все версии
    timeline.innerHTML = '';
    data.versions.forEach(({ version, date, description }) => {
        addVersionToTimeline(
            version,
            date || new Date().toLocaleDateString(),
            description || 'No additional information',
            version === data.version
        );
    });
});

document.querySelector(".nav-item[data-section='create-exam']").addEventListener('click', function() {
    document.getElementById('create-exam-modal').style.display = 'block';
});

document.getElementById('add-question').addEventListener('click', function () {
    const examForm = document.getElementById('exam-form');
    const questionTypeElement = document.getElementById('question-type');
    const questionType = questionTypeElement.value;

    // Создаем блок вопроса
    let questionBlock = document.createElement('div');
    questionBlock.classList.add('question-block');

    questionBlock.innerHTML = `
        <input type='hidden' class='question-type' value='${questionType}'>
        <input type='text' class='question-text' placeholder='Enter question text'>
    `;

    if (questionType === 'multiple_choice') {
        questionBlock.innerHTML += `
            <input type='text' class='option' placeholder='Option 1'>
            <input type='text' class='option' placeholder='Option 2'>
            <input type='text' class='option' placeholder='Option 3'>
            <select class='correct-answer'>
                <option value='' disabled selected>Select correct answer</option>
            </select>
        `;
    } else {
        questionBlock.innerHTML += `<input type='text' class='correct-answer' placeholder='Correct Answer'>`;
    }

    // Добавляем кнопку удаления вопроса
    let deleteButton = document.createElement('button');
    deleteButton.innerText = 'Remove';
    deleteButton.classList.add('remove-question');
    deleteButton.addEventListener('click', function () {
        questionBlock.remove();
    });

    questionBlock.appendChild(deleteButton);
    examForm.appendChild(questionBlock);

    // Если это multiple_choice, обновляем select
    if (questionType === 'multiple_choice') {
        updateCorrectAnswerSelect(questionBlock);
    }
});

// Функция для обновления select с правильными ответами
function updateCorrectAnswerSelect(questionBlock) {
    const optionsInputs = questionBlock.querySelectorAll('.option');
    const correctAnswerSelect = questionBlock.querySelector('.correct-answer');

    correctAnswerSelect.innerHTML = `<option value='' disabled selected>Select correct answer</option>`;

    optionsInputs.forEach(input => {
        input.addEventListener('input', function () {
            correctAnswerSelect.innerHTML = `<option value='' disabled selected>Select correct answer</option>`;
            optionsInputs.forEach(opt => {
                if (opt.value.trim() !== '') {
                    let optionElement = document.createElement('option');
                    optionElement.value = opt.value;
                    optionElement.innerText = opt.value;
                    correctAnswerSelect.appendChild(optionElement);
                }
            });
        });
    });
}

// Сохранение экзамена
document.getElementById('save-exam').addEventListener('click', function () {
    const questions = [];
    let questionId = 1;

    document.querySelectorAll('.question-block').forEach(block => {
        const questionType = block.querySelector('.question-type').value;
        const questionText = block.querySelector('.question-text').value;
        let correctAnswer = block.querySelector('.correct-answer').value;

        let question = {
            id: questionId++,
            text: questionText,
            correct: correctAnswer,
            type: questionType
        };

        if (questionType === 'multiple_choice') {
            let options = Array.from(block.querySelectorAll('.option')).map(opt => opt.value).filter(opt => opt.trim() !== '');
            question.options = options;
        }

        questions.push(question);
    });

    fetch('/create_exam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questions })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Exam successfully created!');
            document.getElementById('create-exam-modal').style.display = 'none';
        }
    });
});

// Clear the exam creation form
function clearExamForm() {
    document.getElementById('exam-form').innerHTML = '';
    document.getElementById('question-type').value = 'multiple_choice'; // Reset to default
}

document.querySelector(".nav-item[data-section='exam-results']").addEventListener('click', function() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsContainer = document.getElementById('examResultsContainer');
    loadingIndicator.style.display = 'block';  // Показываем индикатор
    resultsContainer.style.display = 'none';
    
    fetch('/api/get_exam_results', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        const resultsContainer = document.getElementById('examResultsContainer');
        resultsContainer.innerHTML = ''; // Clear previous results

        // Iterate through the user results (e.g. sdsda, etc.)
        for (let username in data) {
            if (data.hasOwnProperty(username)) {
                const result = data[username]; // Get results for each user

                const resultElement = document.createElement('div');
                resultElement.classList.add('exam-result');
                resultElement.innerHTML = `
    <div class="exam-result-summary">
        <p><strong>Username:</strong> ${username}</p>
        <p><strong>Correct Answers:</strong> ${result.correct}</p>
        <p><strong>Incorrect Answers:</strong> ${result.incorrect}</p>
        <p><strong>Skipped Answers:</strong> ${result.skipped}</p>
        <p><strong>Total Questions:</strong> ${result.total_questions}</p>
        <p><strong>Correct Percentage:</strong> ${result.correct_percentage}%</p>
        <p><strong>Rewarded:</strong> ${result.rewarded ? 'Yes' : 'No'}</p>
        <p><strong>Coins:</strong> ${result.coins}</p>
        <button class="toggle-details"><span class="icon">⬇️</span> Show Details</button>
        <div class="details" style="display: none;">
            <h3>Details of Results:</h3>
        </div>
    </div>
    <hr/>
`;

                // Add the detailed results for each question
                result.results.forEach((questionResult, index) => {
                    let questionHtml = `<p><strong>Question:</strong> ${questionResult.question}</p>`;

                    const userAnswer = questionResult.user_answer;
                    const correctAnswer = questionResult.correct_answer;
                    const isCorrect = questionResult.is_correct;
                    let resultClass = isCorrect ? 'correct' : 'incorrect';

                    if (questionResult.question_type === 'true_false') {
                        questionHtml += `
                            <input type="radio" name="q${index}" value="True" id="true${index}" ${userAnswer === 'True' ? 'checked' : ''}>
                            <label for="true${index}">True</label>
                            <input type="radio" name="q${index}" value="False" id="false${index}" ${userAnswer === 'False' ? 'checked' : ''}>
                            <label for="false${index}">False</label>
                        `;
                    } else if (questionResult.question_type === 'multiple_choice' && Array.isArray(questionResult.options)) {
                        // For multiple choice, show the selected answer as an input
                        questionHtml += `
                            <input type="text" value="${userAnswer || ''}" style="pointer-events: none;" readonly/>
                        `;
                    } else if (['fill_gaps', 'unscramble', 'reading', 'listening'].includes(questionResult.question_type)) {
                        questionHtml += `
                            <input type="text" name="q${index}" style="pointer-events: none;" autocomplete="off" spellcheck="false" value="${userAnswer || ''}">
                        `;
                    }

                    // Add a result indicator for each question
                    questionHtml += `
                        <p class="${resultClass}">Your answer: ${userAnswer || 'No answer provided'} ${isCorrect ? '(Correct)' : '(Incorrect)'}</p>
                        <p><strong>Correct Answer:</strong> ${correctAnswer}</p>
                    `;

                    // Add the question HTML to the results container
                    resultElement.querySelector('.details').innerHTML += `
                        <div class="question-result">
                            ${questionHtml}
                        </div>
                    `;
                });

                // Add toggle functionality for details
                resultElement.querySelector('.toggle-details').addEventListener('click', function() {
                    const details = resultElement.querySelector('.details');
                    const button = resultElement.querySelector('.toggle-details');
                    const icon = button.querySelector('.icon');
                    if (details.style.display === 'none') {
                        details.style.display = 'block';
                        button.textContent = 'Hide Details';
                    } else {
                        details.style.display = 'none';
                        button.textContent = 'Show Details';
                    }
                });

                // Append the user result to the container
                resultsContainer.appendChild(resultElement);
            }
        }

        // If no results, show a message
        if (resultsContainer.innerHTML === '') {
            resultsContainer.innerHTML = '<p>No results available.</p>';
        }
        loadingIndicator.style.display = 'none';
        resultsContainer.style.display = 'block';
    })
    .catch(error => console.error('Error fetching exam results:', error));
});




// Обработчик для добавления события клика на каждый элемент навигации
document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener('click', function() {
        // Убираем активный класс у всех элементов
        document.querySelectorAll(".nav-item").forEach(navItem => navItem.classList.remove('active'));
        
        // Добавляем активный класс к выбранному элементу
        item.classList.add('active');

        // Сохраняем выбранную секцию в localStorage
        localStorage.setItem('selectedSection', item.getAttribute('data-section'));
    });
});

// При загрузке страницы восстанавливаем выбранную секцию и симулируем клик
window.addEventListener('load', () => {
    const savedSection = localStorage.getItem('selectedSection');
    
    if (savedSection) {
        // Находим элемент по data-section и делаем его активным
        const activeNavItem = document.querySelector(`.nav-item[data-section='${savedSection}']`);
        if (activeNavItem) {
            // Симулируем клик по восстановленному элементу
            activeNavItem.classList.add('active'); // добавляем активный класс вручную
            activeNavItem.click(); // искусственный клик
        }
    }
});

