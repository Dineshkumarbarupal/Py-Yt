import { apiRequest } from "./api.js";

const id = document.querySelector("main")?.dataset.playlistId;
const list = document.querySelector("#playlist-video-list");
const status = document.querySelector("#playlist-detail-status");
const title = document.querySelector("#playlist-title");
const description = document.querySelector("#playlist-description");
const controls = document.querySelector("#playlist-controls");

async function load() {
  try {
    const playlist = await apiRequest(`/playlists/${encodeURIComponent(id)}`);
    title.textContent = playlist.title;
    description.textContent = playlist.description || "";
    controls.replaceChildren();

    if (playlist.is_owner) {
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "secondary-button";
      edit.textContent = "Edit playlist";
      edit.addEventListener("click", async () => {
        const nextTitle = window.prompt("Playlist title", playlist.title);
        if (nextTitle === null) return;
        const nextDescription = window.prompt("Playlist description", playlist.description || "");
        if (nextDescription === null) return;
        const visibility = window.prompt("Visibility: private, unlisted or public", playlist.visibility || "private");
        if (visibility === null) return;
        if (!["private", "unlisted", "public"].includes(visibility)) {
          status.textContent = "Visibility must be private, unlisted or public.";
          return;
        }
        try {
          await apiRequest(`/playlists/${encodeURIComponent(id)}`, {
            method: "PATCH",
            body: JSON.stringify({ title: nextTitle, description: nextDescription, visibility }),
          });
          await load();
        } catch (error) {
          status.textContent = error.message;
        }
      });
      const removePlaylist = document.createElement("button");
      removePlaylist.type = "button";
      removePlaylist.className = "secondary-button danger-button";
      removePlaylist.textContent = "Delete playlist";
      removePlaylist.addEventListener("click", async () => {
        if (!window.confirm("Delete this playlist and its saved list?")) return;
        try {
          await apiRequest(`/playlists/${encodeURIComponent(id)}`, { method: "DELETE" });
          window.location.assign("/playlists");
        } catch (error) {
          status.textContent = error.message;
        }
      });
      controls.append(edit, removePlaylist);
    }

    list.replaceChildren();
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
      if (playlist.is_owner) {
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "secondary-button danger-button";
        remove.textContent = "Remove";
        remove.addEventListener("click", async () => {
          remove.disabled = true;
          try {
            await apiRequest(`/playlists/${encodeURIComponent(id)}/items/${encodeURIComponent(video.video_id)}`, { method: "DELETE" });
            await load();
          } catch (error) {
            status.textContent = error.message;
            remove.disabled = false;
          }
        });
        card.append(remove);
      }
      list.append(card);
    }
  } catch (error) {
    status.textContent = error.message;
  }
}
load();
