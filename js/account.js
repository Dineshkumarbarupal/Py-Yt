import { apiRequest } from "./api.js";

const avatar = document.querySelector(".top-actions .avatar");
const notificationLink = document.querySelector("#notification-link");
let user;

try {
  user = await apiRequest("/auth/me");
} catch {
  if (avatar) {
    avatar.href = "/login";
    avatar.textContent = "Sign in";
    avatar.classList.remove("avatar");
    avatar.classList.add("sign-in-link");
    avatar.setAttribute("aria-label", "Sign in");
  }
  if (notificationLink) notificationLink.href = "/login";
}

if (user) {
  if (avatar) {
    avatar.href = "/settings";
    avatar.classList.add("avatar-link");
    avatar.textContent = "";
    if (user.avatar_url) {
      const image = document.createElement("img");
      image.src = user.avatar_url;
      image.alt = "";
      avatar.append(image);
    } else {
      avatar.textContent = (user.display_name || user.email || "P").slice(0, 1).toUpperCase();
    }
    avatar.title = user.display_name || user.email;
    avatar.setAttribute("aria-label", "Account settings");
  }

  const adminLink = document.querySelector("#admin-link");
  if (adminLink && user.role === "admin") adminLink.classList.remove("hidden");

  if (notificationLink) {
    try {
      const result = await apiRequest("/notifications?limit=1");
      if (result.unread_count > 0) {
        const badge = document.createElement("span");
        badge.className = "notification-badge";
        badge.textContent = result.unread_count > 9 ? "9+" : String(result.unread_count);
        notificationLink.append(badge);
        notificationLink.setAttribute("aria-label", `${result.unread_count} unread notifications`);
      }
    } catch {
      // Notification availability must not change the authenticated account state.
    }
  }
}
