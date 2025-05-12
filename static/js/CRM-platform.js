const socket = io();

document.addEventListener('DOMContentLoaded', () => {
	
let remainingTime = null;
let lastFetchTime = 0;
const FETCH_INTERVAL = 10000;
let timerInterval = null;
let stopFetching = false; // Флаг для остановки запросов после 400

    // Initial fetch
    fetchLeaderboard();

function updateTimer() {
  const currentTime = Date.now();

  // Если получен код 400 ранее, не отправляем запрос
  if (stopFetching) {
    if (remainingTime !== null) {
      remainingTime = Math.max(0, remainingTime - 1);
      updateDisplay(remainingTime);
    }
    return;
  }

  if (remainingTime === null || currentTime - lastFetchTime >= FETCH_INTERVAL) {
    fetch('/get_remaining_time')
      .then(res => {
        if (!res.ok) {
          if (res.status === 400) {
            stopFetching = true; // Устанавливаем флаг при 400
          }
          throw new Error(`HTTP error! Status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        if (data.remaining_time !== undefined) {
          remainingTime = data.remaining_time;
          lastFetchTime = currentTime;
          updateDisplay(remainingTime);
        }
      })
      .catch(error => {
        console.error('Error fetching time:', error);
      });
  } else {
    if (remainingTime !== null) {
      remainingTime = Math.max(0, remainingTime - 1);
      updateDisplay(remainingTime);
    }
  }

  function updateDisplay(time) {
    const minutesEl = document.getElementById('timer-minutes');
    const secondsEl = document.getElementById('timer-seconds');
    const startBtn = document.querySelector('.start-btn');

    if (minutesEl && secondsEl && startBtn) {
      const currentTime = formatTime(time); // returns "MM : SS"
      const [newMin, newSec] = currentTime.split(' : ');

      if (minutesEl.textContent !== newMin) {
        animateTextChange(minutesEl, newMin);
      }
      if (secondsEl.textContent !== newSec) {
        animateTextChange(secondsEl, newSec);
      }

      // Управление кнопкой: отключена, пока time > 0
      startBtn.disabled = time > 0;

      if (time <= 0) {
        clearInterval(timerInterval);
      }
    }
  }
}

  // Запуск таймера
  timerInterval = setInterval(updateTimer, 1000);
});

socket.on('update-results', function() {
loadExamResults();
});
  
async function loadExamResults() {
  const container = document.getElementById("results-table-container");

  // Показываем скелетон-загрузку
  container.innerHTML = `
    <div class="skeleton-table">
      ${Array.from({ length: 5 }).map(() => `
        <div class="skeleton-row">
          <div class="skeleton skeleton-avatar"></div>
          <div class="skeleton skeleton-name"></div>
          <div class="skeleton skeleton-score"></div>
          <div class="skeleton skeleton-bar"></div>
        </div>
      `).join('')}
    </div>
  `;

  try {
    // Получаем имя пользователя из результатов
    const response = await fetch('/api/get_exam_results');
    if (!response.ok) {
      container.innerHTML = `<p style="color:white;">Failed to load results.</p>`;
      return;
    }

    const results = await response.json();
    container.innerHTML = ""; // Очищаем скелетон

    if (!results || Object.keys(results).length === 0) {
      container.innerHTML = `
        <div class="no-exams">
          <i class="fas fa-exclamation-triangle"></i>
          No one has passed the exam yet
        </div>
      `;
      return;
    }

    showToastNotification('Exam results loaded successfully!', 'success');

    // Отображаем результаты
    for (const [username, userData] of Object.entries(results)) {
      const userRow = document.createElement("div");
      userRow.className = "user-result-row";

      const avatarRes = await fetch(`/get_avatar/${username}`);
      const avatarData = await avatarRes.json();
      const avatarUrl = avatarData.avatar_url;

      const percentage = userData.correct_percentage.toFixed(0);

      const avatarHTML = avatarUrl
        ? `<img src="${avatarUrl}" class="avatar-img" alt="avatar" />`
        : `<div class="avatar-placeholder">${username.charAt(0).toUpperCase()}</div>`;

      userRow.innerHTML = `
        <div class="result-left">
          ${avatarHTML}
          <div class="user-info">
            <div class="user-name">${username}</div>
            <div class="user-score">${userData.correct} / ${userData.total_questions}</div>
          </div>
        </div>
        <div class="result-right">
          <div class="progress-wrapper">
            <div class="progress-container">
              <div class="progress-bar" style="width: ${percentage}%;"></div>
            </div>
            <span class="progress-label">Score ${percentage}%</span>
          </div>
        </div>
      `;

      // Добавляем обработчик клика с передачей имени пользователя
      userRow.addEventListener("click", () => {
        openUserDetailedReview(username, userData);
      });

      container.appendChild(userRow);
    }

  } catch (error) {
    console.error("Error loading exam results:", error);
    container.innerHTML = `<p style="color:white;">An error occurred while loading results.</p>`;
  }
}

async function openUserDetailedReview(username, userData) {
  // Удаляем существующее модальное окно, если есть
  document.querySelector('.detailed-questions-review')?.remove();

  // Создаем модальное окно
  const modal = document.createElement('div');
  modal.className = 'detailed-questions-review';

  // Создаем контейнер для Lottie-анимации
  const loadingContainer = document.createElement('div');
  loadingContainer.id = 'loading-animation';
  loadingContainer.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 200px; height: 200px;';
  modal.appendChild(loadingContainer);

  // Добавляем модальное окно в DOM сразу, чтобы показать анимацию
  document.body.appendChild(modal);

  // Инициализируем Lottie-анимацию с рандомным выбором файла
  let animation;
  try {
    if (typeof lottie === 'undefined') {
      throw new Error('Lottie-web is not loaded');
    }
    // Массив с путями к анимациям
    const animationPaths = [
      '/static/animations/loading-questions.json',
      '/static/animations/loading-questions-alt.json'
    ];
    // Случайный выбор пути
    const randomPath = animationPaths[Math.floor(Math.random() * animationPaths.length)];
    
    animation = lottie.loadAnimation({
      container: loadingContainer,
      renderer: 'svg',
      loop: true,
      autoplay: true,
      path: randomPath
    });
  } catch (error) {
    console.error('Failed to initialize Lottie animation:', error);
    // Продолжаем без анимации, если Lottie не загружен
    loadingContainer.innerHTML = '<p style="color:white;">Loading...</p>';
  }

  let headerHtml = `
    <div class="detailed-questions-reviewHeader">
      <span class="back-btn" onclick="detailedQuestionReviewClose(this.closest('.detailed-questions-review'))">
        <i class="fas fa-arrow-left"></i> Back
      </span>
      <h2><i class="fas fa-user"></i> Review: ${username}</h2>
    </div>
  `;

  let questionsHtml = '<div class="questions-container">';

  try {
    // Запрос результатов пользователя
    const resultsRes = await fetch(`/api/get_exam_results?username=${username}`);
    const resultsData = await resultsRes.json();

    // Запрос структуры вопросов
    const questionsRes = await fetch(`/get_exam_questions_result`);
    const questionsData = await questionsRes.json();

    // Удаляем анимацию после успешной загрузки данных
    if (animation) {
      animation.destroy();
    }
    loadingContainer.remove();

    if (resultsData.error) {
      questionsHtml = `<p style="color:white;">${resultsData.error}</p>`;
    } else {
      window.examResultsData = resultsData[username]?.results || [];

      // Создаем карту вопросов для быстрого доступа по id
      const questionMap = {};
      questionsData.questions.forEach(parentQuestion => {
        if (parentQuestion.subquestions) {
          parentQuestion.subquestions.forEach(subq => {
            questionMap[subq.id] = { ...subq, parent: parentQuestion };
          });
        } else {
          questionMap[parentQuestion.id] = { ...parentQuestion, parent: parentQuestion };
        }
      });

      // Группируем результаты по родительским вопросам
      const parentQuestions = {};
      for (const result of window.examResultsData) {
        const { question, user_answer, correct_answer, is_correct, question_type, question_id, parent_question_id, text } = result;
        const questionDetails = questionMap[question_id] || {};
        const parentId = parent_question_id || questionDetails?.parent?.id || question_id;

        if (!parentQuestions[parentId]) {
          parentQuestions[parentId] = {
            type: questionDetails?.parent?.type || question_type,
            text: questionDetails?.parent?.text || text || '',
            subquestions: [],
          };
        }
        parentQuestions[parentId].subquestions.push({
          ...result,
          options: questionDetails.options || [],
          text: questionDetails.text || question,
        });
      }

      // Рендерим каждую родительскую группу
      for (const parentId in parentQuestions) {
        const parent = parentQuestions[parentId];

        // Добавляем Type для каждого родительского вопроса
        questionsHtml += parent.type ? `<div class="type-label">Type: ${parent.type}</div>` : '';

        // Добавляем пассаж для reading
        if (parent.type === 'reading' && parent.text) {
          questionsHtml += `<div class="passage-text">${parent.text}</div>`;
        }

        // Добавляем инструкцию (кроме reading)
        if (parent.text && parent.type !== 'reading') {
          questionsHtml += `<div class="instruction">${parent.text}</div>`;
        }

        if (parent.type === 'box-choose') {
          let combinedText = '<div class="box-choose-questions">';
          parent.subquestions.forEach((subq, index) => {
            const userAnswer = subq.user_answer || '';
            const isCorrect = userAnswer.trim().toLowerCase() === subq.correct_answer.trim().toLowerCase();
            const questionNumber = index + 1;
            const displayText = subq.text.replace('____', `<span class="box-choose-blank ${isCorrect ? 'correct' : 'incorrect'}">${userAnswer || '____'}</span>`);
            combinedText += `
              <div class="box-choose-subquestion">
                <span class="main-question-number">${questionNumber}</span>
                <span class="subquestion-text">${displayText}</span>
              </div>
            `;
          });
          combinedText += '</div>';

          questionsHtml += `
            <div class="question-item">
              <div class="question-text">${combinedText}</div>
            </div>
          `;
        } else {
          parent.subquestions.forEach((subq, index) => {
            const userAnswer = subq.user_answer || '';
            const isCorrect = userAnswer.trim().toLowerCase() === subq.correct_answer.trim().toLowerCase();
            const questionNumber = index + 1;

            questionsHtml += `
              <div class="question-item">
                <div class="question-header">
                  <span class="main-question-number">${questionNumber}</span>
                  <div class="question-text">${subq.text}</div>
                </div>
                ${renderAnswerInput(subq, userAnswer, isCorrect)}
              </div>
            `;
          });
        }
      }
    }
  } catch (error) {
    // Удаляем анимацию при ошибке
    if (animation) {
      animation.destroy();
    }
    loadingContainer.remove();
    console.error("Error loading exam results or questions:", error);
    questionsHtml = `<p style="color:white;">An error occurred while loading results.</p>`;
  }

  // Обновляем содержимое модального окна
  questionsHtml += '</div>';
  modal.innerHTML = headerHtml + questionsHtml;
}

function renderAnswerInput(result, userAnswer, isCorrect) {
  const { question_type, question_id, correct_answer, options } = result;
  const correctnessTag = isCorrect ? 'detailed-question-correct' : 'detailed-question-incorrect';

  if (question_type === 'true_false') {
    return `
      <div class="options">
        <input type="radio" id="true-option-${question_id}" ${userAnswer === 'True' ? 'checked' : ''} disabled class="${userAnswer === 'True' ? correctnessTag : ''}">
        <label for="true-option-${question_id}" class="${correct_answer === 'True' ? 'detailed-question-correct' : userAnswer === 'True' && !isCorrect ? 'detailed-question-incorrect' : ''}">True ${correct_answer === 'True' ? '<i class="fas fa-check correct-icon"></i>' : userAnswer === 'True' && !isCorrect ? '<i class="fas fa-times incorrect-icon"></i>' : ''}</label>
        <input type="radio" id="false-option-${question_id}" ${userAnswer === 'False' ? 'checked' : ''} disabled class="${userAnswer === 'False' ? correctnessTag : ''}">
        <label for="false-option-${question_id}" class="${correct_answer === 'False' ? 'detailed-question-correct' : userAnswer === 'False' && !isCorrect ? 'detailed-question-incorrect' : ''}">False ${correct_answer === 'False' ? '<i class="fas fa-check correct-icon"></i>' : userAnswer === 'False' && !isCorrect ? '<i class="fas fa-times incorrect-icon"></i>' : ''}</label>
      </div>
    `;
  } else if (question_type === 'multiple_choice' && Array.isArray(options)) {
    return `
      <div class="options">
        ${options.map((option, index) => {
          const isUserAnswer = userAnswer === option;
          const isCorrectAnswer = correct_answer === option;
          const optionClass = isUserAnswer
            ? isCorrect
              ? 'detailed-question-correct'
              : 'detailed-question-incorrect'
            : isCorrectAnswer
            ? 'detailed-question-correct'
            : '';
          const icon = isUserAnswer
            ? isCorrect
              ? '<i class="fas fa-check correct-icon"></i>'
              : '<i class="fas fa-times incorrect-icon"></i>'
            : isCorrectAnswer
            ? '<i class="fas fa-check correct-icon"></i>'
            : '';
          return `
            <div class="option-item">
              <input type="radio" id="option-${question_id}-${index}" ${isUserAnswer ? 'checked' : ''} disabled class="${optionClass}">
              <label for="option-${question_id}-${index}" class="${optionClass}">${option} ${icon}</label>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } else if (question_type === 'unscramble') {
    const userLetters = userAnswer ? userAnswer.split('') : [];
    let lettersHtml = '<div class="unscramble-letters-review">';
    userLetters.forEach(letter => {
      lettersHtml += `<span class="unscramble-letter ${correctnessTag}">${letter}</span>`;
    });
    lettersHtml += '</div>';

    return `
      <div class="answer-container">
        ${lettersHtml}
      </div>
    `;
  } else if (question_type === 'box-choose') {
    return '';
  } else if (['fill_gaps', 'reading', 'listening', 'question'].includes(question_type)) {
    return `
      <div style="display: flex; align-items: center;">
        <input class="filled-answer ${correctnessTag}" type="text" disabled value="${userAnswer}">
        ${isCorrect ? '<i class="fas fa-check correct-icon"></i>' : '<i class="fas fa-times incorrect-icon"></i>'}
        ${!isCorrect ? `<div class="correct-answer">Correct: ${correct_answer}</div>` : ''}
      </div>
    `;
  }

  return '';
}

function detailedQuestionReviewClose(modal) {
  modal.classList.add('closing');
  modal.addEventListener('animationend', () => {
    modal.remove();
  }, { once: true });
}

function showSection(element, id) {
  // Сброс активного класса у всех пунктов
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  element.classList.add('active');

  // Переключение видимой секции
  document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));

  const target = document.getElementById(id);
  target.classList.add('active', 'fade-in');

  // Удалить класс анимации после её завершения
  target.addEventListener('animationend', () => {
    target.classList.remove('fade-in');
  }, { once: true });
}

	  let timerInterval;

  function formatTime(seconds) {
    const min = String(Math.floor(seconds / 60)).padStart(2, '0');
    const sec = String(Math.floor(seconds % 60)).padStart(2, '0');
    return `${min} : ${sec}`;
  }

let remainingTime = null;
let lastFetchTime = 0;
const FETCH_INTERVAL = 10000; // Синхронизация с сервером каждые 10 секунд

function updateTimer() {
  const currentTime = Date.now();

  // Если время не получено или пора синхронизировать
  if (remainingTime === null || currentTime - lastFetchTime >= FETCH_INTERVAL) {
    fetch('/get_remaining_time')
      .then(res => res.json())
      .then(data => {
        if (data.remaining_time !== undefined) {
          remainingTime = data.remaining_time; // Обновляем локальное время
          lastFetchTime = currentTime; // Запоминаем время запроса
          updateDisplay(remainingTime);
        }
      });
  } else {
    // Локально уменьшаем время и обновляем интерфейс
    if (remainingTime !== null) {
      remainingTime = Math.max(0, remainingTime - 1);
      updateDisplay(remainingTime);
    }
  }

  function updateDisplay(time) {
    const minutesEl = document.getElementById('timer-minutes');
    const secondsEl = document.getElementById('timer-seconds');
	const startBtn = document.querySelector('.start-btn');

    const currentTime = formatTime(time); // returns "MM : SS"
    const [newMin, newSec] = currentTime.split(' : ');

    if (minutesEl.textContent !== newMin) {
      animateTextChange(minutesEl, newMin);
    }
    if (secondsEl.textContent !== newSec) {
      animateTextChange(secondsEl, newSec);
    }
	
	startBtn.disabled = time > 0;

    if (time <= 0) {
      clearInterval(timerInterval);
    }
  }
}

function animateTextChange(element, newValue) {
  element.textContent = newValue;
  
  // Reset animation
  element.classList.remove('timer-number-animate');
  void element.offsetWidth; // Force reflow
  element.classList.add('timer-number-animate');
}


function startExam() {
  loadAudioExamQuestions();
  fetch('/api/start-exam', {
    method: 'POST'
  })
  .then(res => {
    if (!res.ok) {
      throw new Error('Failed to start exam');
    }
    return res.json();
  })
  .then(() => {
    updateTimer(); // instantly show
    timerInterval = setInterval(updateTimer, 1000);
    showToastNotification('Exam started successfully!', 'success');
  })
  .catch(error => {
    console.error('Start exam error:', error);
    showToastNotification('Failed to start exam. Please try again.', 'error');
  });
}

  
async function loadAudioExamQuestions() {
  const container = document.getElementById("exam-audio-files");
  const loadBtn = document.querySelector(".load-audio-btn");

  // Скрываем кнопку "Load files" перед началом загрузки
  if (loadBtn) loadBtn.style.display = "none";

  // Показываем скелетоны
  container.innerHTML = `
    <div class="skeleton-table">
      ${Array.from({ length: 3 }).map(() => `
        <div class="skeleton-row custom-audio-player skeleton">
          <div class="skeleton custom-play-btn"></div>
          <div class="skeleton custom-audio-waves skeleton"></div>
          <div class="skeleton custom-time-display"></div>
        </div>
      `).join('')}
    </div>
  `;

  try {
    const response = await fetch('/get_exam_questions');
    if (!response.ok) {
      throw new Error("Failed to fetch exam questions.");
    }

    const data = await response.json();
    const questions = data.questions || [];

    const audioQuestions = questions.filter(q => q.audio || q.audio_Exam);
    if (audioQuestions.length === 0) {
      container.innerHTML = `
        <div class="no-exams">
          <i class="fas fa-volume-mute"></i>
          No audio questions available
        </div>
      `;
      return;
    }

    container.innerHTML = ""; // Удалить скелетоны

    // Добавляем аудио вопросы
    for (const question of audioQuestions) {
      const audioUrl = question.audio_Exam || question.audio;
      const card = document.createElement("div");
      card.className = "exam-audio-players";

      card.innerHTML = `
        <div class="custom-audio-player">
          <button class="custom-play-btn"><i class="fas fa-play"></i></button>
          <div class="custom-audio-waves"><div class="progress"></div></div>
          <div class="custom-time-display">0:00</div>
        </div>
        <audio src="${audioUrl}" preload="metadata" style="display: none;"></audio>
      `;

      setupCustomPlayer(card);
      container.appendChild(card);
    }

  } catch (error) {
    console.error("Error loading audio questions:", error);
    container.innerHTML = `
      <div class="no-exams">
        <i class="fas fa-exclamation-triangle"></i>
        Failed to load audio questions
      </div>
    `;
    if (loadBtn) loadBtn.style.display = "inline-block";
  }
}




function setupCustomPlayer(card) {
  const audio = card.querySelector("audio");
  const playBtn = card.querySelector(".custom-play-btn");
  const waves = card.querySelector(".custom-audio-waves");
  const progress = card.querySelector(".progress");
  const timeDisplay = card.querySelector(".custom-time-display");
  const icon = playBtn.querySelector("i");

  playBtn.addEventListener("click", () => {
    if (audio.paused) {
      document.querySelectorAll("audio").forEach(a => a.pause()); // Pause other players
      audio.play();
    } else {
      audio.pause();
    }
  });

  audio.addEventListener("play", () => {
    icon.className = "fas fa-pause";
  });

  audio.addEventListener("pause", () => {
    icon.className = "fas fa-play";
  });

  audio.addEventListener("timeupdate", () => {
    const percentage = (audio.currentTime / audio.duration) * 100;
    progress.style.width = `${percentage}%`;
    const mins = Math.floor(audio.currentTime / 60);
    const secs = Math.floor(audio.currentTime % 60).toString().padStart(2, "0");
    timeDisplay.textContent = `${mins}:${secs}`;
  });

  waves.addEventListener("click", e => {
    const rect = waves.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const ratio = x / waves.clientWidth;
    audio.currentTime = ratio * audio.duration;
  });
}

function showToastNotification(message, type = 'success', duration = 5000) {
    const icons = {
      success: 'fa-check',
      error:   'fa-exclamation-triangle',
      warning: 'fa-exclamation-circle',
      info:    'fa-info-circle'
    };

    const container = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.style.setProperty('--hide-delay', `${(duration/1000).toFixed(2)}s`);
	
	if (type === 'error') {
    const audio = new Audio('static/music/error.wav');
    audio.play().catch(err => {
    console.warn('Failed to play error sound:', err);
    });
    }

    const icon = document.createElement('div');
    icon.className = 'toast-icon';
    icon.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i>`;

    const msg = document.createElement('div');
    msg.className = 'toast-message';
    msg.innerHTML = message;

    const closeBtn = document.createElement('div');
    closeBtn.className = 'toast-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = () => toast.remove();

    toast.append(icon, msg, closeBtn);
    container.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('active'));

    setTimeout(() => toast.remove(), duration + 400);
}

    const itemsPerPage = 4;
    let currentPage = 1;
    let leaderboardData = [];
    let currentUsername = null;
    let isLoading = false;

    // Show skeleton loading
    function showSkeletonLoading() {
      const tbody = document.getElementById('leaderboard-body');
      tbody.innerHTML = `
        <tr>
          <td class="tdProgress">
            <div class="avatar-container">
              <div class="sceletion-loading-avatar"></div>
              <div class="sceletion-loading-text"></div>
            </div>
          </td>
          <td class="tdProgress"><div class="sceletion-loading-circle"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-button"></div></td>
        </tr>
        <tr>
          <td class="tdProgress">
            <div class="avatar-container">
              <div class="sceletion-loading-avatar"></div>
              <div class="sceletion-loading-text"></div>
            </div>
          </td>
          <td class="tdProgress"><div class="sceletion-loading-circle"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-button"></div></td>
        </tr>
		<tr>
          <td class="tdProgress">
            <div class="avatar-container">
              <div class="sceletion-loading-avatar"></div>
              <div class="sceletion-loading-text"></div>
            </div>
          </td>
          <td class="tdProgress"><div class="sceletion-loading-circle"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-button"></div></td>
        </tr>
		<tr>
          <td class="tdProgress">
            <div class="avatar-container">
              <div class="sceletion-loading-avatar"></div>
              <div class="sceletion-loading-text"></div>
            </div>
          </td>
          <td class="tdProgress"><div class="sceletion-loading-circle"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-text"></div></td>
          <td class="tdProgress"><div class="sceletion-loading-button"></div></td>
        </tr>
      `;
    }

    // Fetch leaderboard data
    async function fetchLeaderboard() {
      if (isLoading) return;
      isLoading = true;
      showSkeletonLoading(); // Show skeleton while fetching

      try {
        const response = await fetch('/api/get-leaderboard');
        const data = await response.json();
        if (response.ok) {
          leaderboardData = Object.entries(data).map(([username, info]) => ({
            username,
            ...info
          }));
          await renderTable();
        } else {
          console.error('Error fetching leaderboard:', data.error);
        }
      } catch (error) {
        console.error('Fetch error:', error);
      } finally {
        isLoading = false;
      }
    }

    // Fetch avatar for a student
    async function fetchAvatar(username) {
      try {
        const response = await fetch(`/get_avatar/${username}`);
        const data = await response.json();
        return data.avatar_url || null; // Return null if no avatar
      } catch (error) {
        console.error('Error fetching avatar:', error);
        return null;
      }
    }

    // Render the table with pagination
    async function renderTable() {
      const tbody = document.getElementById('leaderboard-body');
      tbody.innerHTML = '';

      const start = (currentPage - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      const paginatedData = leaderboardData.slice(start, end);

      for (const student of paginatedData) {
        const avatarUrl = await fetchAvatar(student.username);
        const row = document.createElement('tr');
        const avatarDisplay = avatarUrl
          ? `<img src="${avatarUrl}" alt="${student.username} avatar" class="avatar">`
          : `<div class="avatar-placeholder">${student.username.charAt(0).toUpperCase()}</div>`;
        const progressClass = student.progress < 60 ? 'progress-circle low' : 'progress-circle';
        row.innerHTML = `
          <td class="tdProgress">
            <div class="avatar-container">
              ${avatarDisplay}
              ${student.username}
            </div>
          </td>
          <td class="tdProgress"><span class="${progressClass}">${student.progress}</span></td>
          <td class="tdProgress">${student.start_date}</td>
          <td class="tdProgress">${student.study_days}</td>
          <td class="tdProgress">
            <button class="edit-button" onclick="openModal('${student.username}')">
              <i class="fas fa-pen"></i> Edit
            </button>
          </td>
        `;
        tbody.appendChild(row);
      }

      // Update pagination info
      const totalEntries = leaderboardData.length;
      document.getElementById('total-entries').textContent = totalEntries;
      document.getElementById('page-info').textContent = `${start + 1} to ${Math.min(end, totalEntries)}`;

      // Update pagination buttons
      document.getElementById('prev-page').disabled = currentPage === 1;
      document.getElementById('next-page').disabled = end >= totalEntries;
    }

    // Open modal for editing progress
    function openModal(username) {
      currentUsername = username;
      document.getElementById('edit-modal').style.display = 'flex';
      document.getElementById('progress-increment').value = '';
    }

    // Close modal
    function closeModal() {
      document.getElementById('edit-modal').style.display = 'none';
      currentUsername = null;
    }

    // Save updated progress
    async function saveProgress() {
      const increment = document.getElementById('progress-increment').value;
      if (!increment || isNaN(increment)) {
		showToastNotification(`<b>Failed to update progress</b> <span style="color:red;">Please enter a valid number for progress increment.</span>`,'error');
        return;
      }

      try {
        const response = await fetch('/api/update-student-progress-exam', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: currentUsername, progress: parseFloat(increment) })
        });
        const result = await response.json();

        if (response.ok) {
          closeModal();
          showSkeletonLoading(); // Show skeleton while fetching updated data
          fetchLeaderboard(); // Refresh table
		  showToastNotification('Progress updated successfully!', 'success');
        } else {
		  showToastNotification(`<b>Failed to update progress</b> <span style="color:red;">${result.error || 'Unknown error'}</span>`,'error');
        }
      } catch (error) {
        console.error('Update error:', error);
        showToastNotification(`<b>Failed to update progress</b> <span style="color:red;">${error || 'Unknown error'}</span>`,'error');
      }
    }

    // Pagination controls
    document.getElementById('prev-page').addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        fetchLeaderboard();
      }
    });

    document.getElementById('next-page').addEventListener('click', () => {
      if ((currentPage * itemsPerPage) < leaderboardData.length) {
        currentPage++;
        fetchLeaderboard();
      }
    });
	
  const socketBan = io();
  const itemsPerPageBan = 5;
  let currentPageBan = 1;
  let banSessions = [];
  let currentBanUsername = null;
  let isLoadingBan = false;

  // Show skeleton loading for ban users
  function showBanSkeletonLoading() {
    const tbody = document.getElementById('ban-users-body');
    tbody.innerHTML = `
      <tr>
        <td class="tdBan">
          <div class="avatar-container-ban">
            <div class="sceletion-loading-avatar-ban"></div>
            <div class="sceletion-loading-text-ban"></div>
          </div>
        </td>
        <td class="tdBan"><div class="sceletion-loading-text-ban"></div></td>
        <td class="tdBan"><div class="sceletion-loading-text-ban"></div></td>
        <td class="tdBan"><div class="sceletion-loading-text-ban"></div></td>
        <td class="tdBan"><div class="sceletion-loading-button-ban"></div></td>
      </tr>
      <tr>
        <td class="tdBan">
          <div class="avatar-container-ban">
            <div class="sceletion-loading-avatar-ban"></div>
            <div class="sceletion-loading-text-ban"></div>
          </div>
        </td>
        <td class="tdBan"><div class="sceletion-loading-text-ban"></div></td>
        <td class="tdBan"><div class="sceletion-loading-text-ban"></div></td>
        <td class="tdBan"><div class="sceletion-loading-text-ban"></div></td>
        <td class="tdBan"><div class="sceletion-loading-button-ban"></div></td>
      </tr>
    `;
  }

  // Fetch active sessions for ban users from API endpoint
  async function fetchBanSessions() {
    if (isLoadingBan) return;
    isLoadingBan = true;
    showBanSkeletonLoading(); // Show skeleton while fetching

    try {
      const response = await fetch('/api/sessions/');
      const data = await response.json();
      if (response.ok) {
        // Group sessions by username and take the latest session for each user
        const sessionsByUserBan = {};
        data.sessions.forEach(session => {
          const usernameBan = session.username;
          if (!sessionsByUserBan[usernameBan]) {
            sessionsByUserBan[usernameBan] = session;
          }
        });

        banSessions = Object.entries(sessionsByUserBan).map(([usernameBan, session]) => ({
          username: usernameBan,
          session: {
            "Device-Type": session.deviceType,
            "OS": session.os,
            "Platform": session.platform
          }
        }));

        await renderBanTable();
      } else {
        console.error('Error fetching ban sessions:', data.error);
      }
    } catch (error) {
      console.error('Fetch error for ban sessions:', error);
    } finally {
      isLoadingBan = false;
    }
  }

  // Fetch avatar for a user in ban users section
  async function fetchBanAvatar(username) {
    try {
      const response = await fetch(`/get_avatar/${username}`);
      const data = await response.json();
      return data.avatar_url || null; // Return null if no avatar
    } catch (error) {
      console.error('Error fetching ban avatar:', error);
      return null;
    }
  }

  // Render the table with pagination for ban users
  async function renderBanTable() {
    const tbody = document.getElementById('ban-users-body');
    tbody.innerHTML = '';

    const startBan = (currentPageBan - 1) * itemsPerPageBan;
    const endBan = startBan + itemsPerPageBan;
    const paginatedDataBan = banSessions.slice(startBan, endBan);

    for (const user of paginatedDataBan) {
      const avatarUrlBan = await fetchBanAvatar(user.username);
      const row = document.createElement('tr');
      const avatarDisplayBan = avatarUrlBan
        ? `<img src="${avatarUrlBan}" alt="${user.username} avatar" class="avatar-ban">`
        : `<div class="avatar-placeholder-ban">${user.username.charAt(0).toUpperCase()}</div>`;
      row.innerHTML = `
        <td class="tdBan">
          <div class="avatar-container-ban">
            ${avatarDisplayBan}
            ${user.username}
          </div>
        </td>
        <td class="tdBan">${user.session["Device-Type"] || "Unknown"}</td>
        <td class="tdBan">${user.session["OS"] || "Unknown"}</td>
        <td class="tdBan">${user.session["Platform"] || "Unknown"}</td>
        <td class="tdBan">
          <button class="ban-button" onclick="openBanModal('${user.username}')">
            <i class="fas fa-ban"></i> Ban
          </button>
        </td>
      `;
      tbody.appendChild(row);
    }

    // Update pagination info
    const totalEntriesBan = banSessions.length;
    document.getElementById('total-entries').textContent = totalEntriesBan;
    document.getElementById('page-info').textContent = `${startBan + 1} to ${Math.min(endBan, totalEntriesBan)}`;

    // Update pagination buttons
    document.getElementById('prev-page').disabled = currentPageBan === 1;
    document.getElementById('next-page').disabled = endBan >= totalEntriesBan;
  }

  // Open modal for banning user
  function openBanModal(username) {
    currentBanUsername = username;
    document.getElementById('ban-modal').style.display = 'flex';
    document.getElementById('ban-duration').value = '';
  }

  // Close modal for banning user
  function closeBanModal() {
    document.getElementById('ban-modal').style.display = 'none';
    currentBanUsername = null;
  }

  // Ban user
  function executeBanUser() {
    const durationBan = document.getElementById('ban-duration').value;
    if (!durationBan || isNaN(durationBan) || durationBan <= 0) {
      alert('Please enter a valid duration in minutes.');
      return;
    }

    // Emit socket event for temporary ban
    socketBan.emit("tempBanUser", { username: currentBanUsername, duration: parseInt(durationBan) });

    // Close modal and refresh table
    closeBanModal();
    showBanSkeletonLoading();
    fetchBanSessions();
  }
  
  function executeUnblockUser() {
  if (!currentBanUsername) {
    alert('No user selected for unblocking.');
    return;
  }

  // Эмитим событие разблокировки на сервер
  socketBan.emit("unblockUser", { username: currentBanUsername });

  // Закрываем модальное окно
  closeBanModal();
  showBanSkeletonLoading();
  fetchBanSessions();
}

  // Pagination controls
  document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPageBan > 1) {
      currentPageBan--;
      fetchBanSessions();
    }
  });

  document.getElementById('next-page').addEventListener('click', () => {
    if ((currentPageBan * itemsPerPageBan) < banSessions.length) {
      currentPageBan++;
      fetchBanSessions();
    }
  });

  // Initial fetch
  fetchBanSessions();
 
async function generateTeams() {
            try {
                // Fetch users from Flask API
                const response = await fetch('/api/users');
                const userData = await response.json();

                // Extract only the names (keys) from the object
                const users = Object.keys(userData);

                // Shuffle users array
                for (let i = users.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [users[i], users[j]] = [users[j], users[i]];
                }

                // Split into two teams
                const half = Math.ceil(users.length / 2);
                const team1 = users.slice(0, half);
                const team2 = users.slice(half);

                // Update DOM with animated list items
                const team1List = document.getElementById('team1-list');
                const team2List = document.getElementById('team2-list');
                team1List.innerHTML = '';
                team2List.innerHTML = '';

                team1.forEach((user, index) => {
                    const li = document.createElement('li');
                    li.textContent = user;
                    li.style.animationDelay = `${index * 0.2}s`;
                    team1List.appendChild(li);
                });

                team2.forEach((user, index) => {
                    const li = document.createElement('li');
                    li.textContent = user;
                    li.style.animationDelay = `${index * 0.2}s`;
                    team2List.appendChild(li);
                });
            } catch (error) {
                console.error('Error fetching users:', error);
                const team1List = document.getElementById('team1-list');
                const team2List = document.getElementById('team2-list');
                team1List.innerHTML = '<li>Error loading teams</li>';
                team2List.innerHTML = '<li>Error loading teams</li>';
            }
        }

        // Define custom element for random-teams-button
        class RandomTeamsButton extends HTMLElement {
            connectedCallback() {
                this.style.display = 'inline-block';
            }
        }
        customElements.define('random-teams-button', RandomTeamsButton);