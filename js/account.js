import { apiRequest } from "./api.js";

const avatar = document.querySelector(".top-actions .avatar");
if (avatar) {
  try {
    const user = await apiRequest("/auth/me");
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
  } catch {
    avatar.href = "/login";
    avatar.textContent = "Sign in";
    avatar.classList.remove("avatar");
    avatar.classList.add("sign-in-link");
    avatar.setAttribute("aria-label", "Sign in");
  }
}
