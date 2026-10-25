 
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
let authToken = "";
let notices = [];

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

  message.textContent = isRegisterMode ? "Creating account..." : "Logging in...";
  loginBtn.disabled = true;

  try {
    const response = await fetch(
      API_URL + (isRegisterMode ? "/register" : "/login"),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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

    authToken = data.token;
    currentUser = data.username;

    if (!authToken || !currentUser) {
      message.textContent = "Login response incomplete. Please try again.";
      return;
    }

    document.getElementById("currentUser").textContent = currentUser;
    authSection.hidden = true;
    dashboard.hidden = false;
    message.textContent = "";

    await loadHistory();
  } catch (error) {
    message.textContent = "Could not connect to the server. Please try again.";
  } finally {
    loginBtn.disabled = false;
  }
});

async function loadHistory() {
  const response = await fetch(API_URL + "/notices", {
    headers: { "Authorization": "Bearer " + authToken }
  });

  const data = await response.json();

  if (response.status === 401) {
    logout("Session expired. Please log in again.");
    return;
  }

  if (!response.ok) {
    throw new Error(data.message || "Could not load notices.");
  }

  notices = data;
  showHistory();
}

function showHistory() {
  const history = document.getElementById("history");
  history.innerHTML = "";

  notices.forEach(function (item) {
    const li = document.createElement("li");
    const dateValue = item.scheduled_at || item.created_at;
    const dateText = dateValue ? new Date(dateValue).toLocaleString() : "";

    li.textContent =
      (item.scheduled_at ? "Scheduled: " : "") +
      dateText + " — " + item.notice;

    history.appendChild(li);
  });
}

async function saveNotice(text, scheduledAt = null) {
  const response = await fetch(API_URL + "/notices", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + authToken
    },
    body: JSON.stringify({
      notice: text,
      scheduled_at: scheduledAt
    })
  });

  const data = await response.json();

  if (response.status === 401) {
    logout("Session expired. Please log in again.");
    throw new Error("Please log in again.");
  }

  if (!response.ok) {
    throw new Error(data.message || "Could not save notice.");
  }

  await loadHistory();
  document.getElementById("boardNotice").textContent = text;
}

document.getElementById("sendBtn").addEventListener("click", async function () {
  const text = document.getElementById("noticeText").value.trim();

  if (!text) {
    alert("Please enter a notice.");
    return;
  }

  try {
    await saveNotice(text);
    document.getElementById("noticeText").value = "";
    alert("Notice saved to the database!");
  } catch (error) {
    alert(error.message);
  }
});

document.getElementById("scheduleBtn").addEventListener("click", async function () {
  const text = document.getElementById("noticeText").value.trim();
  const date = document.getElementById("scheduleDate").value;
  const time = document.getElementById("scheduleTime").value;

  if (!text || !date || !time) {
    alert("Enter notice, date and time.");
    return;
  }

  const scheduledDate = new Date(date + "T" + time);

  if (
    Number.isNaN(scheduledDate.getTime()) ||
    scheduledDate.getTime() <= Date.now()
  ) {
    alert("Please choose a future date and time.");
    return;
  }

  try {
    await saveNotice(text, scheduledDate.toISOString());
    document.getElementById("noticeText").value = "";
    alert(
      "Schedule saved to the database. Automatic delivery at the scheduled time is not enabled yet."
    );
  } catch (error) {
    alert(error.message);
  }
});

function logout(statusMessage = "You have logged out.") {
  dashboard.hidden = true;
  authSection.hidden = false;
  loginForm.reset();
  message.textContent = statusMessage;
  currentUser = "";
  authToken = "";
  notices = [];
}

document.getElementById("logoutBtn").addEventListener("click", function () {
  logout();
});
