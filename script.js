const loginForm = document.getElementById("loginForm");
const message = document.getElementById("message");
const dashboard = document.getElementById("dashboard");

const users = {
  admin: "admin123",
  member1: "member123",
  member2: "member123"
};

let notices = JSON.parse(localStorage.getItem("notices") || "[]");

function showHistory() {
  const history = document.getElementById("history");
  history.innerHTML = "";

  notices.forEach((item) => {
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

loginForm.addEventListener("submit", function (event) {
  event.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  if (users[username] && users[username] === password) {
    message.textContent = "Login successful!";
    loginForm.hidden = true;
    dashboard.hidden = false;
    showHistory();
  } else {
    message.textContent = "Wrong username or password.";
  }
});

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
  loginForm.hidden = false;
  message.textContent = "You have logged out.";
});
