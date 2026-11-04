import { apiRequest } from "./api.js";

const page = document.querySelector(".watch-layout");
const videoId = page?.dataset.videoId;
const player = document.querySelector("#pyyt-player");
const status = document.querySelector("#player-status");
let lastSavedSecond = -1;

async function initializePlayer() {
  if (!videoId || !player) return;
  try {
    const result = await apiRequest(`/videos/${encodeURIComponent(videoId)}/playback`);
    player.src = result.playback_url;
    status.textContent = "";
    await apiRequest(`/videos/${encodeURIComponent(videoId)}/view`, { method: "POST" }).catch(() => null);
  } catch (error) {
    status.textContent = error.message;
  }
}

player?.addEventListener("timeupdate", async () => {
  const second = Math.floor(player.currentTime);
  if (second - lastSavedSecond < 15) return;
  lastSavedSecond = second;
  await apiRequest(`/engagement/videos/${encodeURIComponent(videoId)}/history`, {
    method: "POST",
    body: JSON.stringify({ progress_seconds: second }),
  }).catch(() => null);
});

document.querySelector("#like-button")?.addEventListener("click", async () => {
  try {
    await apiRequest(`/engagement/videos/${encodeURIComponent(videoId)}/reaction`, {
      method: "PUT",
      body: JSON.stringify({ reaction: "like" }),
    });
    toast("Video liked.");
  } catch (error) { toast(error.message); }
});

document.querySelector("#save-button")?.addEventListener("click", () => {
  toast("Create a playlist in your library before saving videos.");
});

function toast(message) {
  let region = document.querySelector("#toast-region");
  if (!region) {
    region = document.createElement("div");
    region.id = "toast-region";
    region.className = "toast-region";
    document.body.append(region);
  }
  const item = document.createElement("div");
  item.className = "toast";
  item.textContent = message;
  region.append(item);
  window.setTimeout(() => item.remove(), 3000);
}

initializePlayer();
