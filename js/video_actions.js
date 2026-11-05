import { apiRequest } from "./api.js";

function showToast(message) {
  let region = document.querySelector("#toast-region");
  if (!region) {
    region = document.createElement("div");
    region.id = "toast-region";
    region.className = "toast-region";
    region.setAttribute("aria-live", "polite");
    region.setAttribute("aria-atomic", "true");
    document.body.append(region);
  }

  const item = document.createElement("div");
  item.className = "toast";
  item.textContent = message;
  region.append(item);
  window.setTimeout(() => item.remove(), 3200);
}

document.addEventListener("click", async (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target?.closest("button[data-watch-later]");
  if (!button || button.disabled || button.dataset.saved === "true") return;

  const videoId = button.dataset.watchLater;
  if (!videoId) return;

  button.disabled = true;
  try {
    const result = await apiRequest(
      `/library/watch-later/${encodeURIComponent(videoId)}`,
      { method: "POST" },
    );
    button.dataset.saved = "true";
    button.textContent = "✓ Saved";
    button.setAttribute("aria-label", "Saved to Watch Later");
    showToast(
      result.status === "already_saved"
        ? "This video is already in Watch later."
        : "Saved to Watch later.",
    );
  } catch (error) {
    button.disabled = false;
    showToast(error.message);
  }
});
