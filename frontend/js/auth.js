/* Design philosophy: authentication is a short, composed transition into a focused academic workspace; messages are direct and never theatrical. */
import { api, saveSession } from "./api.js";

const loginForm = document.querySelector("#login-form");
const registerForm = document.querySelector("#register-form");
const message = document.querySelector("#auth-message");
const tabs = document.querySelectorAll("[data-tab]");

function showMessage(text, kind = "error") {
  message.innerHTML = `<div class="alert alert-${kind}">${text}</div>`;
}
function redirect(user) {
  window.location.href =
    user.role === "teacher"
      ? "teacher_dashboard.html"
      : "student_dashboard.html";
}

tabs.forEach(tab =>
  tab.addEventListener("click", () => {
    tabs.forEach(item => item.classList.toggle("active", item === tab));
    const register = tab.dataset.tab === "register";
    loginForm.classList.toggle("hidden", register);
    registerForm.classList.toggle("hidden", !register);
    message.innerHTML = "";
  })
);

loginForm.addEventListener("submit", async event => {
  event.preventDefault();
  const button = loginForm.querySelector("button");
  button.disabled = true;
  button.textContent = "Opening…";
  try {
    const session = await api.login({
      email: document.querySelector("#login-email").value,
      password: document.querySelector("#login-password").value,
    });
    saveSession(session);
    redirect(session.user);
  } catch (error) {
    showMessage(error.message);
    button.disabled = false;
    button.innerHTML = "Open workspace <span>→</span>";
  }
});
registerForm.addEventListener("submit", async event => {
  event.preventDefault();
  const button = registerForm.querySelector("button");
  button.disabled = true;
  button.textContent = "Creating…";
  try {
    const session = await api.register({
      full_name: document.querySelector("#register-name").value,
      email: document.querySelector("#register-email").value,
      password: document.querySelector("#register-password").value,
      role: document.querySelector("#register-role").value,
    });
    showMessage("Account created successfully! Please sign in.", "success");
    registerForm.reset();

    const loginTab = document.querySelector('[data-tab="login"]');
    if (loginTab) {
      loginTab.click();
    }
  } catch (error) {
    showMessage(error.message);
    button.disabled = false;
    button.innerHTML = "Create account <span>→</span>";
  }
});
