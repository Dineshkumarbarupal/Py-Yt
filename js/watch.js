import { apiRequest } from "./api.js";

const page = document.querySelector(".watch-layout");
const videoId = page?.dataset.videoId;
const player = document.querySelector("#pyyt-player");
const playerStatus = document.querySelector("#player-status");
const commentForm = document.querySelector("#comment-form");
const commentStatus = document.querySelector("#comment-status");
const commentsList = document.querySelector("#comments-list");
const playlistDialog = document.querySelector("#playlist-dialog");
const playlistForm = document.querySelector("#playlist-form");
const playlistSelect = document.querySelector("#playlist-select");
const playlistStatus = document.querySelector("#playlist-status");
let lastSavedSecond = -1;
let viewRecorded = false;

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

async function initializePlayer() {
  if (!videoId || !player) return;
  try {
    const result = await apiRequest(`/videos/${encodeURIComponent(videoId)}/playback`);
    player.src = result.playback_url;
    playerStatus.textContent = "";
  } catch (error) {
    playerStatus.textContent = error.message;
  }
}

player?.addEventListener("play", async () => {
  if (viewRecorded) return;
  viewRecorded = true;
  await apiRequest(`/videos/${encodeURIComponent(videoId)}/view`, { method: "POST" }).catch(() => null);
});

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


document.querySelector("#dislike-button")?.addEventListener("click", async () => {
  try {
    await apiRequest(`/engagement/videos/${encodeURIComponent(videoId)}/reaction`, {
      method: "PUT",
      body: JSON.stringify({ reaction: "dislike" }),
    });
    toast("Feedback saved.");
  } catch (error) {
    toast(error.message);
  }
});

document.querySelector("#player-speed")?.addEventListener("change", (event) => {
  if (!player) return;
  player.playbackRate = Number(event.currentTarget.value);
});

const theaterButton = document.querySelector("#theater-toggle");
theaterButton?.addEventListener("click", () => {
  const enabled = page?.classList.toggle("theater-mode") ?? false;
  theaterButton.textContent = enabled ? "Exit theater mode" : "Theater mode";
  theaterButton.setAttribute("aria-pressed", String(enabled));
});

const pipButton = document.querySelector("#pip-toggle");
if (pipButton && (!document.pictureInPictureEnabled || !player?.requestPictureInPicture)) {
  pipButton.disabled = true;
  pipButton.title = "Picture-in-picture is not supported by this browser.";
}
pipButton?.addEventListener("click", async () => {
  try {
    if (document.pictureInPictureElement) {
      await document.exitPictureInPicture();
    } else if (player && document.pictureInPictureEnabled) {
      await player.requestPictureInPicture();
    }
  } catch {
    toast("Picture-in-picture could not be started.");
  }
});

document.querySelector("#share-button")?.addEventListener("click", async () => {
  const shareData = { title: document.title, url: window.location.href };
  try {
    if (navigator.share) {
      await navigator.share(shareData);
    } else if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(shareData.url);
      toast("Video link copied.");
    } else {
      toast("Copy this video URL from your browser address bar.");
    }
  } catch (error) {
    if (error.name !== "AbortError") toast("Could not share this video.");
  }
});

document.addEventListener("keydown", async (event) => {
  if (!player || event.ctrlKey || event.metaKey || event.altKey) return;
  if (playlistDialog?.open) return;
  const target = event.target;
  if (target instanceof HTMLElement && (
    target.isContentEditable ||
    ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(target.tagName)
  )) return;

  switch (event.key.toLowerCase()) {
    case " ":
      event.preventDefault();
      if (player.paused) await player.play().catch(() => null);
      else player.pause();
      break;
    case "arrowleft":
      event.preventDefault();
      player.currentTime = Math.max(0, player.currentTime - 5);
      break;
    case "arrowright":
      event.preventDefault();
      player.currentTime = Math.min(player.duration || Infinity, player.currentTime + 5);
      break;
    case "arrowup":
      event.preventDefault();
      player.volume = Math.min(1, player.volume + 0.05);
      break;
    case "arrowdown":
      event.preventDefault();
      player.volume = Math.max(0, player.volume - 0.05);
      break;
    case "m":
      player.muted = !player.muted;
      break;
    case "f":
      if (player.requestFullscreen) await player.requestFullscreen().catch(() => null);
      break;
    case "t":
      theaterButton?.click();
      break;
    case "0":
      player.currentTime = 0;
      break;
  }
});

async function loadComments() {
  if (!commentsList) return;
  try {
    const result = await apiRequest(`/comments/video/${encodeURIComponent(videoId)}`);
    commentsList.replaceChildren();
    const items = result.items || [];
    if (!items.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "Be the first to comment.";
      commentsList.append(empty);
      return;
    }

    const children = new Map();
    const roots = [];
    for (const comment of items) {
      if (comment.parent_comment_id) {
        const siblings = children.get(comment.parent_comment_id) || [];
        siblings.push(comment);
        children.set(comment.parent_comment_id, siblings);
      } else {
        roots.push(comment);
      }
    }

    function createComment(comment, depth = 0) {
      const article = document.createElement("article");
      article.className = "comment-item";
      const header = document.createElement("div");
      header.className = "comment-header";
      const author = document.createElement("strong");
      author.textContent = comment.display_name || "Py-Yt user";
      const replyButton = document.createElement("button");
      replyButton.type = "button";
      replyButton.className = "comment-reply-button";
      replyButton.textContent = "Reply";
      header.append(author, replyButton);

      const body = document.createElement("p");
      body.textContent = comment.body;
      article.append(header, body);

      const replyContainer = document.createElement("div");
      replyContainer.className = "comment-replies";
      const replyForm = document.createElement("form");
      replyForm.className = "inline-reply-form hidden";
      const replyInput = document.createElement("textarea");
      replyInput.name = "body";
      replyInput.rows = 2;
      replyInput.maxLength = 5000;
      replyInput.placeholder = `Reply to ${comment.display_name || "this comment"}…`;
      replyInput.required = true;
      const submit = document.createElement("button");
      submit.type = "submit";
      submit.className = "secondary-button";
      submit.textContent = "Post reply";
      const replyStatus = document.createElement("span");
      replyStatus.className = "muted";
      replyStatus.setAttribute("role", "status");
      replyForm.append(replyInput, submit, replyStatus);
      replyButton.addEventListener("click", () => {
        replyForm.classList.toggle("hidden");
        if (!replyForm.classList.contains("hidden")) replyInput.focus();
      });
      replyForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const text = replyInput.value.trim();
        if (!text) return;
        submit.disabled = true;
        replyStatus.textContent = "Posting…";
        try {
          await apiRequest("/comments", {
            method: "POST",
            body: JSON.stringify({
              video_id: videoId,
              body: text,
              parent_comment_id: comment.id,
            }),
          });
          await loadComments();
        } catch (error) {
          replyStatus.textContent = error.message;
          if (error.message.toLowerCase().includes("sign in")) {
            const signIn = document.createElement("a");
            signIn.href = "/login";
            signIn.textContent = "Sign in";
            replyStatus.append(" ", signIn, " to reply.");
          }
        } finally {
          submit.disabled = false;
        }
      });
      replyContainer.append(replyForm);

      for (const child of children.get(comment.id) || []) {
        replyContainer.append(createComment(child, depth + 1));
      }
      if (depth < 4) article.append(replyContainer);
      return article;
    }

    for (const comment of roots) commentsList.append(createComment(comment));
  } catch (error) {
    commentsList.textContent = error.message;
  }
}

commentForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = new FormData(commentForm).get("body")?.toString().trim();
  if (!body) return;
  const submit = commentForm.querySelector("button[type=submit]");
  submit.disabled = true;
  commentStatus.textContent = "Posting…";
  try {
    await apiRequest("/comments", {
      method: "POST",
      body: JSON.stringify({ video_id: videoId, body }),
    });
    commentForm.reset();
    commentStatus.textContent = "Comment posted.";
    await loadComments();
  } catch (error) {
    commentStatus.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) {
      const link = document.createElement("a");
      link.href = "/login";
      link.textContent = "Sign in";
      commentStatus.append(" ", link, " to comment.");
    }
  } finally {
    submit.disabled = false;
  }
});

async function openPlaylistDialog() {
  if (!playlistDialog || !playlistSelect) return;
  playlistStatus.textContent = "";
  playlistSelect.replaceChildren();
  try {
    const result = await apiRequest("/playlists/mine");
    const playlists = result.items || [];
    for (const playlist of playlists) {
      const option = document.createElement("option");
      option.value = playlist.id;
      option.textContent = playlist.title;
      playlistSelect.append(option);
    }
    if (!playlists.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "No playlists yet — create one below";
      playlistSelect.append(option);
    }
    playlistDialog.showModal();
  } catch (error) {
    toast(error.message);
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  }
}


document.querySelector("#watch-later-button")?.addEventListener("click", async () => {
  try {
    const result = await apiRequest(`/library/watch-later/${encodeURIComponent(videoId)}`, { method: "POST" });
    toast(result.status === "already_saved" ? "This video is already in Watch later." : "Added to Watch later.");
  } catch (error) {
    toast(error.message);
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  }
});

document.querySelector("#save-button")?.addEventListener("click", openPlaylistDialog);
document.querySelector("#close-playlist-dialog")?.addEventListener("click", () => playlistDialog?.close());
document.querySelector("#cancel-playlist")?.addEventListener("click", () => playlistDialog?.close());

playlistForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const newTitle = document.querySelector("#new-playlist-title")?.value.trim();
  let playlistId = playlistSelect?.value;
  const submit = playlistForm.querySelector('button[type="submit"]');
  submit.disabled = true;
  playlistStatus.textContent = "Saving…";
  try {
    if (newTitle) {
      const created = await apiRequest("/playlists", {
        method: "POST",
        body: JSON.stringify({ title: newTitle, visibility: "private" }),
      });
      playlistId = created.id;
    }
    if (!playlistId) throw new Error("Choose a playlist or enter a new playlist name.");
    await apiRequest(`/playlists/${encodeURIComponent(playlistId)}/items`, {
      method: "POST",
      body: JSON.stringify({ video_id: videoId }),
    });
    playlistStatus.textContent = "Video saved to playlist.";
    window.setTimeout(() => playlistDialog?.close(), 700);
  } catch (error) {
    playlistStatus.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});

initializePlayer();
loadComments();
