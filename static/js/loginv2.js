document.addEventListener("DOMContentLoaded", () => {
  hideGlobalLoader();
  const loginContainer = document.querySelector(".login-container");
  const loginForm = document.getElementById("login-form");
  const accountSwitcher = document.getElementById("account-switcher");
  const manageToggle = document.querySelector(".login-header .close-btn");
  const closeAccount = document.getElementById("closeAccount");
  const accountList = document.getElementById("account-list");
  const addBtn = document.getElementById("add-account-btn");
  const manageAccountsBtn = document.getElementById("manage-accounts-btn");
  const manageModal = document.getElementById("manage-modal");
  const closeModal = document.getElementById("close-modal");
  const manageAccountList = document.getElementById("manage-account-list");
  const deleteAllBtn = document.getElementById("delete-all-btn");

  let accounts = JSON.parse(localStorage.getItem("savedAccounts") || "[]");

  function renderAccounts() {
    accountList.innerHTML = "";
    manageAccountList.innerHTML = "";
    accounts.forEach((acc, index) => {
      const div = document.createElement("div");
      div.className = "account-item";
      div.innerHTML = `
        <i class="fas fa-user fa-3d"></i>
        <span>${acc.username}<br><small>${acc.email}</small></span>
      `;
      div.addEventListener("click", () => {
        document.querySelector("input[name='username']").value = acc.email;
        document.querySelector("input[name='password']").value = acc.password || "";
        accountSwitcher.classList.remove("active");
        loginForm.dispatchEvent(new Event("submit"));
      });
      accountList.appendChild(div);

      const manageDiv = document.createElement("div");
      manageDiv.className = "account-item";
      manageDiv.innerHTML = `
        <span>${acc.username}</span>
        <button data-index="${index}"><i class="fas fa-trash fa-3d"></i></button>
      `;
      manageDiv.addEventListener("click", (e) => {
        if (e.target.tagName !== "BUTTON" && !e.target.classList.contains("fa-trash")) {
          document.querySelector("input[name='username']").value = acc.email;
          document.querySelector("input[name='password']").value = acc.password || "";
          accountSwitcher.classList.remove("active");
          loginForm.dispatchEvent(new Event("submit"));
        }
      });
      manageDiv.querySelector("button").addEventListener("click", () => {
        accounts.splice(index, 1);
        localStorage.setItem("savedAccounts", JSON.stringify(accounts));
        renderAccounts();
      });
      manageAccountList.appendChild(manageDiv);
    });
  }

  renderAccounts();

  manageToggle.addEventListener("click", () => {
    accountSwitcher.classList.add("active");
  });

  closeAccount.addEventListener("click", () => {
    accountSwitcher.classList.remove("active");
  });

  addBtn.addEventListener("click", () => {
    const username = prompt("Enter your username");
    const email = prompt("Enter your email");
    const password = prompt("Enter your password");
    if (username && email && password && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      accounts.push({ username, email, password });
      localStorage.setItem("savedAccounts", JSON.stringify(accounts));
      renderAccounts();
    } else if (username || email || password) {
      alert("Please provide a valid username, email, and password.");
    }
  });

  manageAccountsBtn.addEventListener("click", () => {
    manageModal.classList.remove("hidden");
    renderAccounts();
  });

  closeModal.addEventListener("click", () => {
    manageModal.classList.add("hidden");
  });

  deleteAllBtn.addEventListener("click", () => {
    accounts = [];
    localStorage.setItem("savedAccounts", JSON.stringify(accounts));
    renderAccounts();
    manageModal.classList.add("hidden");
  });

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showGlobalLoader();

    const username = loginForm.querySelector("input[name='username']").value.trim();
    const password = loginForm.querySelector("input[name='password']").value.trim();

    if (!username || !password) {
      hideGlobalLoader();
      showToastNotification("Please provide username and password.", "error");
      return;
    }

    // Store credentials in sessionStorage for reactivation
    sessionStorage.setItem("tempUsername", username);
    sessionStorage.setItem("tempPassword", password);

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (response.status === 200 && response.headers.get("content-length") === "0") {
        // Successful login, redirect to /chat
        let storedAccounts = JSON.parse(localStorage.getItem("savedAccounts") || "[]");
        const exists = storedAccounts.find(acc => acc.email === username && acc.password === password);
        if (!exists) {
          storedAccounts.push({ username, email: username, password });
          localStorage.setItem("savedAccounts", JSON.stringify(storedAccounts));
        }
        sessionStorage.setItem("username", username);
        sessionStorage.setItem("password", password);
        window.location.href = "/chat";
      } else {
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const banNotice = doc.querySelector(".ban-notice");

        hideGlobalLoader();

        if (banNotice) {
          // Replace the current page content with the new HTML containing the ban notice
          document.body.innerHTML = html;
          // Re-attach the reactivate event listener after replacing content
          const reactivateBtn = document.getElementById('reactivate-btn');
          if (reactivateBtn) {
            reactivateBtn.addEventListener('click', async () => {
              const username = reactivateBtn.getAttribute('data-username');
              if (!username) {
                showToastNotification("Username not found.", "error");
                return;
              }
              if (!document.getElementById('agree-terms').checked) {
                showToastNotification("Please agree to the Terms of Use.", "error");
                return;
              }

              try {
                const response = await fetch(`/banned-user-reactivate/${username}`, {
                  method: 'POST'
                });
                const data = await response.json();
                if (data.status === 'success') {
                  // Retrieve stored credentials and attempt login
                  const tempUsername = sessionStorage.getItem("tempUsername");
                  const tempPassword = sessionStorage.getItem("tempPassword");
                  if (tempUsername && tempPassword) {
                    const loginResponse = await fetch("/login", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ username: tempUsername, password: tempPassword })
                    });
                    if (loginResponse.status === 200 && loginResponse.headers.get("content-length") === "0") {
                      sessionStorage.removeItem("tempUsername");
                      sessionStorage.removeItem("tempPassword");
                      window.location.href = "/chat";
                    } else {
                      showToastNotification("Login failed after reactivation.", "error");
                      location.reload();
                    }
                  } else {
                    location.reload();
                  }
                } else {
                  showToastNotification(data.message, "error");
                }
              } catch (err) {
                showToastNotification("Reactivation failed. Please try again.", "error");
              }
            });
          }
        } else {
          const errorMatch = html.match(/<div class="error-message">(.*?)<\/div>/);
          if (errorMatch) {
            showToastNotification(errorMatch[1], "error");
          } else {
            showToastNotification("Login failed. Please try again.", "error");
          }
        }
      }
    } catch (err) {
      hideGlobalLoader();
      console.error("Login error:", err);
      showToastNotification("Login failed. Please check your connection.", "error");
    }
  });
});

const globalLottieLoader = document.getElementById("global-lottie-loader");
const globalLottieAnimation = document.getElementById("global-lottie-animation");

const loadingAnimation = lottie.loadAnimation({
  container: globalLottieAnimation,
  renderer: 'svg',
  loop: true,
  autoplay: false,
  path: 'static/animations/login.json'
});

function showGlobalLoader() {
  globalLottieLoader.style.display = "flex";
  loadingAnimation.play();
}

function hideGlobalLoader() {
  loadingAnimation.stop();
  globalLottieLoader.style.display = "none";
}

function showToastNotification(message, type = 'success', duration = 5000) {
  const icons = {
    success: 'fa-check',
    error: 'fa-exclamation-triangle',
    warning: 'fa-exclamation-circle',
    info: 'fa-info-circle'
  };

  const container = document.getElementById('toast-container');

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.style.setProperty('--hide-delay', `${(duration / 1000).toFixed(2)}s`);
  
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
  closeBtn.innerHTML = '×';
  closeBtn.onclick = () => toast.remove();

  toast.append(icon, msg, closeBtn);
  container.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('active'));

  setTimeout(() => toast.remove(), duration + 400);
}