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

        // Снимаем active класс с текущей активной секции
        const currentActiveSection = document.querySelector('.content-section.active');
        if (currentActiveSection) {
            currentActiveSection.classList.remove('active');
        }

        const targetSection = document.getElementById(item.dataset.section);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        if (item.dataset.section === "chat") {
            chatSpinner.style.display = 'inline-block';
            chatIframe.style.display = 'none';

            chatIframe.src = "/chat";

            // Обработчик события onload для iframe
            chatIframe.onload = () => {
                chatSpinner.style.display = 'none';
                chatIframe.style.display = 'block';
                chatIframe.onload = null; // Отключаем обработчик, чтобы не сработал повторно
            };
        } else if (item.dataset.section === "ban") {
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

const updateProgressButton = document.getElementById('update-progress-button');
const studentNameInput = document.getElementById('student-name');
const progressInput = document.getElementById('progress-input');
const startDateInput = document.getElementById('start-date-input'); // Reference to start date input field

// Обработчик клика по кнопке обновления прогресса
updateProgressButton.addEventListener('click', () => {
    const username = studentNameInput.value.trim();
    const progress = parseInt(progressInput.value);
    const startDate = startDateInput.value; // Get the start date value from input field

    if (username && !isNaN(progress)) {
        const requestBody = { username, progress };
        
        // Если start_date не пустое, добавляем его в тело запроса
        if (startDate) {
            requestBody.start_date = startDate;
        }

        fetch('/api/update-student-progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody) // Отправляем только то, что есть
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Progress updated successfully!');
            } else {
                alert('Error updating progress');
            }
        })
        .catch(error => console.error('Error updating progress:', error));
    } else {
        alert('Please enter a valid username and progress');
    }
});

document.addEventListener("DOMContentLoaded", async function () {
    const studentSelect = document.getElementById("student-select");
    const tableBody = document.querySelector("#roadmap-table tbody");

    async function fetchStudents() {
        try {
            const response = await fetch("/api/get-student-names");
            const data = await response.json();

            studentSelect.innerHTML = '<option value="">🎓 Select Student</option>';
            data.students.forEach(student => {
                studentSelect.innerHTML += `<option value="${student}">${student}</option>`;
            });
        } catch (error) {
            console.error("Error loading students:", error);
        }
    }

    async function fetchStudentProgress(username) {
        try {
            const response = await fetch(`/api/get-student-progress?username=${username}`);
            const data = await response.json();
            return data[username] || null;
        } catch (error) {
            console.error("Error fetching progress:", error);
            return null;
        }
    }

    function calculateExamDate(startDate, studyDays, targetUnit) {
        let tempDate = new Date(startDate);
        const oddDays = [1, 3, 5];
        const evenDays = [2, 4, 6];
        const allowedDays = studyDays === "even" ? evenDays : oddDays;

        // Устанавливаем первый учебный день
        while (!allowedDays.includes(tempDate.getDay())) {
            tempDate.setDate(tempDate.getDate() + 1);
        }

        // Рассчитываем общее количество учебных дней до целевого юнита
        const [targetWeek, targetDay] = targetUnit.split('.').map(Number);
        const targetStudyDays = (targetWeek - 1) * 3 + targetDay;

        let studyDaysElapsed = 0;
        while (studyDaysElapsed < targetStudyDays) {
            if (allowedDays.includes(tempDate.getDay())) {
                studyDaysElapsed++;
            }
            tempDate.setDate(tempDate.getDate() + 1);
        }

        return tempDate.toISOString().split('T')[0];
    }

    function generateRoadmap(startDate, studyDays) {
        let units = [];
        let tempDate = new Date(startDate);
        const oddDays = [1, 3, 5];
        const evenDays = [2, 4, 6];
        const allowedDays = studyDays === "even" ? evenDays : oddDays;

        // Устанавливаем первый учебный день
        while (!allowedDays.includes(tempDate.getDay())) {
            tempDate.setDate(tempDate.getDate() + 1);
        }

        for (let week = 1; week <= 12; week++) {
            for (let day = 1; day <= 3; day++) {
                const unitName = `${week}.${day}`;
                const unitDate = new Date(tempDate);
                const formattedDate = unitDate.toISOString().split('T')[0];
                const isPast = unitDate < new Date() ? `<i class="fa-solid fa-check-circle completed"></i>` : "";

                units.push({ 
                    unit: unitName, 
                    lesson_date: formattedDate, 
                    status: isPast, 
                    week: week, 
                    progress: isPast ? "Completed" : "Pending" 
                });

                // Переход к следующему разрешённому дню
                do {
                    tempDate.setDate(tempDate.getDate() + 1);
                } while (!allowedDays.includes(tempDate.getDay()));
            }
        }

        return units;
    }

async function updateRoadmap(username) {
    const loader = document.getElementById("loader");
    const roadmapTable = document.getElementById("roadmap-table");
    const tableBody = roadmapTable.querySelector("tbody");

    // Показываем загрузку, скрываем таблицу
    loader.style.display = "block";
    roadmapTable.style.display = "none";

    tableBody.innerHTML = "";
    const studentData = await fetchStudentProgress(username);
    if (!studentData) {
        loader.style.display = "none";
        return;
    }

    const { start_date, study_days } = studentData;
    const roadmap = generateRoadmap(start_date, study_days);

    roadmap.forEach(entry => {
        const row = `<tr>
            <td><i class="fa-solid fa-book"></i> ${entry.unit}</td>
            <td><i class="fa-solid fa-calendar-days"></i> ${entry.lesson_date} ${entry.status}</td>
            <td>${entry.week}</td>
            <td>${entry.progress}</td>
        </tr>`;
        tableBody.innerHTML += row;
    });

    const midExamDate = calculateExamDate(start_date, study_days, "6.3");
    const finalExamDate = calculateExamDate(start_date, study_days, "12.3");

    tableBody.innerHTML += `
        <tr class="exam-row"><td colspan="4"><i class="fa-solid fa-pen"></i> Mid Exam: ${midExamDate}</td></tr>
        <tr class="exam-row"><td colspan="4"><i class="fa-solid fa-graduation-cap"></i> Final Exam: ${finalExamDate}</td></tr>
    `;

    // Скрываем загрузку, показываем таблицу
    loader.style.display = "none";
    roadmapTable.style.display = "table";
}


    studentSelect.addEventListener("change", function () {
        if (this.value) {
            updateRoadmap(this.value);
        }
    });

    fetchStudents();
});


