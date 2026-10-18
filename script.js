 
const API_URL = "https://wireless-notice-api.onrender.com";

const loginForm = document.getElementById("loginForm");
const message = document.getElementById("message");
const dashboard = document.getElementById("dashboard");
const authSection = document.getElementById("authSection");
const formTitle = document.getElementById("formTitle");
const loginBtn = document.getElementById("loginBtn");
const toggleForm = document.getElementById("toggleForm");

let isRegisterMode = false;
let currentUser = "";

let notices = JSON.parse(localStorage.getItem("notices") || "[]");

toggleForm.addEventListener("click", function () {
  isRegisterMode = !isRegisterMode;

  formTitle.textContent = isRegisterMode ? "Create Account" : "Login";
  loginBtn.textContent = isRegisterMode ? "Sign Up" : "Login";
  toggleForm.textContent = isRegisterMode
    ? "Already have an account? Login"
    : "Create Account / Sign Up";

  message.textContent = "";
  loginForm.reset();
});

loginForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  message.textContent = isRegisterMode
    ? "Creating account..."
    : "Logging in...";

  loginBtn.disabled = true;

  try {
    const response = await fetch(
      API_URL + (isRegisterMode ? "/register" : "/login"),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      message.textContent = data.message || "Request failed.";
      return;
    }

    if (isRegisterMode) {
      message.textContent = "Account created! You can now log in.";
      isRegisterMode = false;
      formTitle.textContent = "Login";
      loginBtn.textContent = "Login";
      toggleForm.textContent = "Create Account / Sign Up";
      loginForm.reset();
      return;
    }

    currentUser = username;
    document.getElementById("currentUser").textContent = currentUser;

    authSection.hidden = true;
    dashboard.hidden = false;
    message.textContent = "";
    showHistory();
  } catch (error) {
    message.textContent =
      "Could not connect to the server. Please try again.";
  } finally {
    loginBtn.disabled = false;
  }
});

function showHistory() {
  const history = document.getElementById("history");
  history.innerHTML = "";

  notices.forEach(function (item) {
    const li = document.createElement("li");
    li.textContent = item;
    history.appendChild(li);
  });
}

function saveNotice(text) {
  notices.unshift(new Date().toLocaleString() + " — " + text);
  localStorage.setItem("notices", JSON.stringify(notices));
  document.getElementById("boardNotice").textContent = text;
  showHistory();
}

document.getElementById("sendBtn").addEventListener("click", function () {
  const text = document.getElementById("noticeText").value.trim();

  if (!text) {
    alert("Please enter a notice.");
    return;
  }

  saveNotice(text);
  document.getElementById("noticeText").value = "";
});

document.getElementById("scheduleBtn").addEventListener("click", function () {
  const text = document.getElementById("noticeText").value.trim();
  const date = document.getElementById("scheduleDate").value;
  const time = document.getElementById("scheduleTime").value;

  if (!text || !date || !time) {
    alert("Enter notice, date and time.");
    return;
  }

  const scheduledTime = new Date(date + "T" + time).getTime();

  if (scheduledTime <= Date.now()) {
    alert("Please choose a future date and time.");
    return;
  }

  const timer = scheduledTime - Date.now();

  alert("Notice scheduled! Keep this page open until the scheduled time.");

  setTimeout(function () {
    saveNotice("Scheduled: " + text);
  }, timer);
});

document.getElementById("logoutBtn").addEventListener("click", function () {
  dashboard.hidden = true;
  authSection.hidden = false;
  loginForm.reset();
  message.textContent = "You have logged out.";
  currentUser = "";
});
