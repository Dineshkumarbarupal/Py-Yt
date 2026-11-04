import { apiRequest } from "./api.js";

const id = document.querySelector("main")?.dataset.playlistId;
const list = document.querySelector("#playlist-video-list");
const status = document.querySelector("#playlist-detail-status");

async function load() {
  try {
    const playlist = await apiRequest(`/playlists/${encodeURIComponent(id)}`);
    document.querySelector("#playlist-title").textContent = playlist.title;
    document.querySelector("#playlist-description").textContent = playlist.description || "";
    if (!playlist.items?.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "This playlist has no visible videos yet.";
      list.append(empty);
      return;
    }
    for (const video of playlist.items) {
      const card = document.createElement("article");
      card.className = "video-card";
      const link = document.createElement("a");
      link.className = "video-title";
      link.href = `/watch/${encodeURIComponent(video.video_id)}`;
      link.textContent = video.title;
      card.append(link);
      list.append(card);
    }
  } catch (error) {
    status.textContent = error.message;
  }
}
load();
