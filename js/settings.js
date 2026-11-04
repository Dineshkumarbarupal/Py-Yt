import { apiRequest } from "./api.js";

const profileForm = document.querySelector("#profile-form");
const passwordForm = document.querySelector("#password-form");
const profileStatus = document.querySelector("#profile-status");
const passwordStatus = document.querySelector("#password-status");
const sessionStatus = document.querySelector("#session-status");

async function loadProfile() {
  try {
    const user = await apiRequest("/auth/me");
    profileForm.elements.display_name.value = user.display_name || "";
    profileForm.elements.bio.value = user.bio || "";
    profileForm.elements.avatar_url.value = user.avatar_url || "";
  } catch (error) {
    profileStatus.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  }
}

profileForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(profileForm).entries());
  profileStatus.textContent = "Saving profile…";
  const button = profileForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    await apiRequest("/auth/me", { method: "PATCH", body: JSON.stringify(values) });
    profileStatus.textContent = "Profile saved.";
  } catch (error) {
    profileStatus.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

passwordForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(passwordForm).entries());
  if (values.new_password !== values.confirm_password) {
    passwordStatus.textContent = "New password and confirmation do not match.";
    return;
  }
  passwordStatus.textContent = "Updating password…";
  const button = passwordForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    await apiRequest("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: values.current_password,
        new_password: values.new_password,
      }),
    });
    passwordForm.reset();
    passwordStatus.textContent = "Password updated. Your current session is still active.";
  } catch (error) {
    passwordStatus.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#logout-button")?.addEventListener("click", async () => {
  const button = document.querySelector("#logout-button");
  button.disabled = true;
  try {
    await apiRequest("/auth/logout", { method: "POST" });
    window.location.assign("/login");
  } catch (error) {
    sessionStatus.textContent = error.message;
    button.disabled = false;
  }
});

loadProfile();
