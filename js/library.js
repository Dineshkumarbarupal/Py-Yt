import { apiRequest } from "./api.js";

const page = document.querySelector(".library-page");
const libraryKey = page?.dataset.libraryKey;
const container = document.querySelector("#library-videos");
const status = document.querySelector("#library-status");
const count = document.querySelector("#library-count");
const clearButton = document.querySelector("#clear-library");

function render(items) {
  container.replaceChildren();
  count.textContent = `${items.length} videos`;
  if (!items.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const heading = document.createElement("h2");
    heading.textContent = "Nothing here yet";
    const message = document.createElement("p");
    message.textContent = "Videos you save or watch will appear in this library.";
    const link = document.createElement("a");
    link.href = "/";
    link.className = "primary-button";
    link.textContent = "Explore videos";
    empty.append(heading, message, link);
    container.append(empty);
    return;
  }
  if (clearButton) clearButton.classList.toggle("hidden", libraryKey !== "history" || items.length === 0);
  for (const video of items) {
    const card = document.createElement("article");
    card.className = "video-card";
    const thumb = document.createElement("a");
    thumb.className = "video-thumb";
    thumb.href = `/watch/${encodeURIComponent(video.id)}`;
    if (video.thumbnail_url) {
      const image = document.createElement("img");
      image.src = video.thumbnail_url;
      image.alt = "";
      image.loading = "lazy";
      thumb.append(image);
    } else {
      const placeholder = document.createElement("span");
      placeholder.className = "thumb-placeholder";
      placeholder.textContent = "▶";
      thumb.append(placeholder);
    }
    const title = document.createElement("a");
    title.className = "video-title";
    title.href = thumb.href;
    title.textContent = video.title;
    const channel = document.createElement("p");
    channel.className = "muted";
    channel.textContent = video.channel_name || "Creator";
    const meta = document.createElement("div");
    meta.className = "library-card-copy";
    meta.append(title, channel);
    if (Number.isInteger(video.progress_seconds)) {
      const progress = document.createElement("p");
      progress.className = "muted";
      progress.textContent = `Watched to ${Math.floor(video.progress_seconds / 60)} min`;
      meta.append(progress);
    }
    const actions = document.createElement("div");
    actions.className = "library-card-actions";
    if (libraryKey === "watch-later" || libraryKey === "liked" || libraryKey === "history") {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "secondary-button";
      remove.textContent = libraryKey === "watch-later" ? "Remove from Watch Later" : libraryKey === "liked" ? "Unlike" : "Remove from history";
      remove.addEventListener("click", async () => {
        remove.disabled = true;
        try {
          if (libraryKey === "watch-later") {
            await apiRequest("/library/watch-later/" + encodeURIComponent(video.id), { method: "DELETE" });
          } else if (libraryKey === "liked") {
            await apiRequest("/engagement/videos/" + encodeURIComponent(video.id) + "/reaction", { method: "DELETE" });
          } else {
            await apiRequest("/engagement/history/" + encodeURIComponent(video.id), { method: "DELETE" });
          }
          await load();
        } catch (error) {
          status.textContent = error.message;
          remove.disabled = false;
        }
      });
      actions.append(remove);
    }
    card.append(thumb, meta, actions);
    container.append(card);
  }
}

async function load() {
  if (!libraryKey || !container) return;
  try {
    const result = await apiRequest(`/library/${encodeURIComponent(libraryKey)}`);
    render(result.items || []);
  } catch (error) {
    container.replaceChildren();
    const link = document.createElement("a");
    link.href = "/login";
    link.textContent = "Sign in to view your library";
    link.className = "primary-button";
    status.textContent = error.message;
    container.append(link);
  }
}

load();

clearButton?.addEventListener("click", async () => {
  if (!window.confirm("Clear your entire watch history?")) return;
  clearButton.disabled = true;
  try {
    await apiRequest("/engagement/history", { method: "DELETE" });
    await load();
    status.textContent = "Watch history cleared.";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    clearButton.disabled = false;
  }
});
