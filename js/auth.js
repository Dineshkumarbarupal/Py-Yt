import { apiRequest } from "./api.js";

const form = document.querySelector("#login-form") || document.querySelector("#signup-form");
const message = document.querySelector("#auth-message");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form).entries());
  const endpoint = form.id === "login-form" ? "/auth/login" : "/auth/register";
  const submit = form.querySelector("button[type=submit]");
  submit.disabled = true;
  message.textContent = "Please wait…";
  try {
    await apiRequest(endpoint, { method: "POST", body: JSON.stringify(values) });
    window.location.assign("/");
  } catch (error) {
    message.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});
