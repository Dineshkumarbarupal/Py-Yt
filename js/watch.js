import { apiRequest } from "./api.js";

const page = document.querySelector(".watch-layout");
const videoId = page?.dataset.videoId;
const player = document.querySelector("#pyyt-player");
const playerStatus = document.querySelector("#player-status");
const commentForm = document.querySelector("#comment-form");
const commentStatus = document.querySelector("#comment-status");
const commentsList = document.querySelector("#comments-list");
const commentSort = document.querySelector("#comment-sort");
const playlistDialog = document.querySelector("#playlist-dialog");
const playlistForm = document.querySelector("#playlist-form");
const playlistSelect = document.querySelector("#playlist-select");
const playlistStatus = document.querySelector("#playlist-status");
const reportDialog = document.querySelector("#report-dialog");
const reportForm = document.querySelector("#report-form");
const reportStatus = document.querySelector("#report-status");
let reportTarget = { type: "video", id: videoId };
let lastSavedSecond = -1;
let viewRecorded = false;
let chapterTimeUpdateHandler = null;


const upNextList = document.querySelector("#up-next-list");
const autoplayToggle = document.querySelector("#autoplay-toggle");
let nextVideos = [];

async function loadUpNext() {
  if (!upNextList) return;
  try {
    const result = await apiRequest("/discovery/feed?category=All&limit=12");
    nextVideos = (result.items || []).filter((item) => item.id !== videoId).slice(0, 8);
    upNextList.replaceChildren();
    if (!nextVideos.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "No more videos are available yet.";
      upNextList.append(empty);
      return;
    }
    for (const item of nextVideos) {
      const card = document.createElement("a");
      card.className = "up-next-card";
      card.href = `/watch/${encodeURIComponent(item.id)}`;
      if (item.thumbnail_url) {
        const image = document.createElement("img");
        image.src = item.thumbnail_url;
        image.alt = "";
        image.loading = "lazy";
        card.append(image);
      } else {
        const placeholder = document.createElement("span");
        placeholder.className = "up-next-placeholder";
        placeholder.textContent = "▶";
        card.append(placeholder);
      }
      const copy = document.createElement("span");
      copy.className = "up-next-copy";
      const title = document.createElement("strong");
      title.textContent = item.title;
      const channel = document.createElement("small");
      channel.textContent = item.channel_name || "Creator";
      copy.append(title, channel);
      card.append(copy);
      upNextList.append(card);
    }
  } catch (error) {
    upNextList.textContent = error.message;
  }
}

player?.addEventListener("ended", () => {
  if (!autoplayToggle?.checked) return;
  let queue = [];
  try {
    queue = JSON.parse(sessionStorage.getItem("pyyt_watch_queue") || "[]");
  } catch {
    queue = [];
  }
  queue = Array.isArray(queue) ? queue.filter((item) => item && item.id && item.id !== videoId) : [];
  if (queue.length) {
    const nextQueued = queue[0];
    sessionStorage.setItem("pyyt_watch_queue", JSON.stringify(queue.slice(1)));
    window.location.assign(`/watch/${encodeURIComponent(nextQueued.id)}`);
    return;
  }
  if (nextVideos.length) {
    window.location.assign(`/watch/${encodeURIComponent(nextVideos[0].id)}`);
  }
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


function linkifyDescriptionTimestamps() {
  const description = document.querySelector("#video-description");
  if (!description) return;
  const source = description.textContent || "";
  const pattern = /\b(?:(\d{1,2}):)?([0-5]?\d):([0-5]\d)\b/g;
  let cursor = 0;
  let match;
  const fragment = document.createDocumentFragment();

  while ((match = pattern.exec(source)) !== null) {
    if (match.index > cursor) {
      fragment.append(document.createTextNode(source.slice(cursor, match.index)));
    }
    const hours = match[1] ? Number(match[1]) : 0;
    const minutes = Number(match[2]);
    const seconds = Number(match[3]);
    const totalSeconds = hours * 3600 + minutes * 60 + seconds;
    const link = document.createElement("a");
    link.href = `#t=${totalSeconds}`;
    link.className = "description-timestamp";
    link.textContent = match[0];
    link.setAttribute("aria-label", `Seek to ${match[0]}`);
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const seek = () => {
        player.currentTime = totalSeconds;
        player.play().catch(() => null);
      };
      if (player.readyState >= 1) seek();
      else player.addEventListener("loadedmetadata", seek, { once: true });
    });
    fragment.append(link);
    cursor = match.index + match[0].length;
  }

  if (cursor < source.length) fragment.append(document.createTextNode(source.slice(cursor)));
  description.replaceChildren(fragment);
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

const likeButton = document.querySelector("#like-button");
const dislikeButton = document.querySelector("#dislike-button");

function compactCount(value) {
  return Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(Number(value || 0));
}

async function loadReactionSummary() {
  const data = await apiRequest(`/engagement/videos/${encodeURIComponent(videoId)}/reaction`);
  likeButton.textContent = `♡ Like ${compactCount(data.likes)}`;
  dislikeButton.textContent = `⊘ Dislike ${compactCount(data.dislikes)}`;
  likeButton.setAttribute("aria-pressed", String(data.current_reaction === "like"));
  dislikeButton.setAttribute("aria-pressed", String(data.current_reaction === "dislike"));
}

async function setReaction(reaction) {
  const active = (reaction === "like" ? likeButton : dislikeButton)?.getAttribute("aria-pressed") === "true";
  try {
    if (active) {
      await apiRequest(`/engagement/videos/${encodeURIComponent(videoId)}/reaction`, { method: "DELETE" });
    } else {
      await apiRequest(`/engagement/videos/${encodeURIComponent(videoId)}/reaction`, {
        method: "PUT",
        body: JSON.stringify({ reaction }),
      });
    }
    await loadReactionSummary();
  } catch (error) {
    toast(error.message);
  }
}

likeButton?.addEventListener("click", () => setReaction("like"));
dislikeButton?.addEventListener("click", () => setReaction("dislike"));
loadReactionSummary().catch(() => null);

async function loadComments() {
  if (!commentsList) return;
  try {
    const result = await apiRequest(`/comments/video/${encodeURIComponent(videoId)}?sort=${encodeURIComponent(commentSort?.value || "newest")}`);
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
      article.id = `comment-${comment.id}`;
      const header = document.createElement("div");
      header.className = "comment-header";
      const author = document.createElement("strong");
      author.textContent = comment.display_name || "Py-Yt user";
      const replyButton = document.createElement("button");
      replyButton.type = "button";
      replyButton.className = "comment-reply-button";
      replyButton.textContent = "Reply";
      const reportButton = document.createElement("button");
      reportButton.type = "button";
      reportButton.className = "comment-reply-button";
      reportButton.textContent = "Report";
      reportButton.addEventListener("click", () => openReportDialog("comment", comment.id));
      header.append(author, replyButton, reportButton);

      const body = document.createElement("p");
      body.className = "comment-body";
      body.textContent = comment.body;
      article.append(header, body);

      if (comment.can_manage) {
        const ownerActions = document.createElement("div");
        ownerActions.className = "comment-owner-actions";
        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.className = "comment-reply-button";
        editButton.textContent = "Edit";
        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "comment-reply-button";
        deleteButton.textContent = "Delete";

        const editForm = document.createElement("form");
        editForm.className = "comment-edit-form hidden";
        const editInput = document.createElement("textarea");
        editInput.name = "body";
        editInput.rows = 3;
        editInput.maxLength = 5000;
        editInput.required = true;
        editInput.value = comment.body;
        const editActions = document.createElement("div");
        editActions.className = "comment-edit-actions";
        const saveEdit = document.createElement("button");
        saveEdit.type = "submit";
        saveEdit.className = "secondary-button";
        saveEdit.textContent = "Save";
        const cancelEdit = document.createElement("button");
        cancelEdit.type = "button";
        cancelEdit.className = "secondary-button";
        cancelEdit.textContent = "Cancel";
        const editStatus = document.createElement("span");
        editStatus.className = "muted";
        editStatus.setAttribute("role", "status");
        editActions.append(saveEdit, cancelEdit);
        editForm.append(editInput, editActions, editStatus);

        editButton.addEventListener("click", () => {
          editForm.classList.toggle("hidden");
          editInput.focus();
        });
        cancelEdit.addEventListener("click", () => {
          editInput.value = comment.body;
          editForm.classList.add("hidden");
          editStatus.textContent = "";
        });
        editForm.addEventListener("submit", async (event) => {
          event.preventDefault();
          const nextBody = editInput.value.trim();
          if (!nextBody) return;
          saveEdit.disabled = true;
          editStatus.textContent = "Saving…";
          try {
            await apiRequest(`/comments/${encodeURIComponent(comment.id)}`, {
              method: "PATCH",
              body: JSON.stringify({ body: nextBody }),
            });
            await loadComments();
          } catch (error) {
            editStatus.textContent = error.message;
          } finally {
            saveEdit.disabled = false;
          }
        });
        deleteButton.addEventListener("click", async () => {
          if (!window.confirm("Delete your comment?")) return;
          deleteButton.disabled = true;
          try {
            await apiRequest(`/comments/${encodeURIComponent(comment.id)}`, { method: "DELETE" });
            await loadComments();
          } catch (error) {
            toast(error.message);
            deleteButton.disabled = false;
          }
        });
        ownerActions.append(editButton, deleteButton);
        article.append(ownerActions, editForm);
      }

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

commentSort?.addEventListener("change", loadComments);

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


function openReportDialog(type, id) {
  reportTarget = { type, id };
  reportStatus.textContent = "";
  document.querySelector("#report-target-label").textContent =
    type === "video" ? "Report this video to the moderation team." : "Report this comment to the moderation team.";
  reportDialog?.showModal();
}

document.querySelector("#report-video-button")?.addEventListener("click", () => openReportDialog("video", videoId));
document.querySelector("#close-report-dialog")?.addEventListener("click", () => reportDialog?.close());
document.querySelector("#cancel-report")?.addEventListener("click", () => reportDialog?.close());

reportForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(reportForm).entries());
  const submit = reportForm.querySelector('button[type="submit"]');
  submit.disabled = true;
  reportStatus.textContent = "Submitting report…";
  try {
    const result = await apiRequest("/reports", {
      method: "POST",
      body: JSON.stringify({
        target_type: reportTarget.type,
        target_id: reportTarget.id,
        reason: values.reason,
        details: values.details,
      }),
    });
    reportStatus.textContent = result.status === "already_reported"
      ? "You have already reported this content."
      : "Report submitted. Thank you for helping keep Py-Yt safe.";
    if (result.status !== "already_reported") {
      reportForm.reset();
      window.setTimeout(() => reportDialog?.close(), 1100);
    }
  } catch (error) {
    reportStatus.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) {
      const link = document.createElement("a");
      link.href = "/login";
      link.textContent = "Sign in";
      reportStatus.append(" ", link, " to report content.");
    }
  } finally {
    submit.disabled = false;
  }
});



const chaptersSection = document.querySelector("#video-chapters");
const chaptersList = document.querySelector("#video-chapter-list");
const currentChapterLabel = document.querySelector("#current-chapter-label");

function formatChapterTime(value) {
  const seconds = Math.max(0, Number(value) || 0);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remaining = seconds % 60;
  const pad = (part) => String(part).padStart(2, "0");
  return hours ? `${pad(hours)}:${pad(minutes)}:${pad(remaining)}` : `${pad(minutes)}:${pad(remaining)}`;
}

async function loadChapters() {
  if (!chaptersList || !videoId) return;
  try {
    const result = await apiRequest("/videos/" + encodeURIComponent(videoId) + "/chapters");
    const items = result.items || [];
    chaptersList.replaceChildren();
    if (!items.length) {
      chaptersSection?.classList.add("hidden");
      return;
    }
    chaptersSection?.classList.remove("hidden");
    const chapterButtons = [];
    for (const chapter of items) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "video-chapter-button";
      button.dataset.startSeconds = String(chapter.start_seconds);
      const time = document.createElement("span");
      time.className = "video-chapter-time";
      time.textContent = formatChapterTime(chapter.start_seconds);
      const title = document.createElement("span");
      title.textContent = chapter.title;
      button.append(time, title);
      button.addEventListener("click", () => {
        const seek = () => {
          player.currentTime = chapter.start_seconds;
          player.play().catch(() => null);
        };
        if (player.readyState >= 1) seek();
        else player.addEventListener("loadedmetadata", seek, { once: true });
      });
      chaptersList.append(button);
      chapterButtons.push({ button, chapter });
    }

    const updateActiveChapter = () => {
      const currentTime = player.currentTime || 0;
      let activeIndex = -1;
      for (let index = 0; index < chapterButtons.length; index += 1) {
        if (chapterButtons[index].chapter.start_seconds <= currentTime) activeIndex = index;
        else break;
      }
      chapterButtons.forEach(({ button }, index) => {
        const active = index === activeIndex;
        button.classList.toggle("active", active);
        button.setAttribute("aria-current", active ? "time" : "false");
      });
      if (currentChapterLabel) {
        currentChapterLabel.textContent = activeIndex >= 0
          ? "Now playing: " + chapterButtons[activeIndex].chapter.title
          : "";
      }
    };
    if (player && chapterTimeUpdateHandler) {
      player.removeEventListener("timeupdate", chapterTimeUpdateHandler);
    }
    chapterTimeUpdateHandler = updateActiveChapter;
    player?.addEventListener("timeupdate", chapterTimeUpdateHandler);
    updateActiveChapter();
  } catch {
    chaptersSection?.classList.add("hidden");
  }
}

async function loadCaptionTracks() {
  if (!player || !videoId) return;
  try {
    const result = await apiRequest("/videos/" + encodeURIComponent(videoId) + "/captions");
    player.querySelectorAll('track[data-pyyt-caption="true"]').forEach((node) => node.remove());
    for (const caption of result.items || []) {
      const track = document.createElement("track");
      track.kind = "subtitles";
      track.label = caption.label;
      track.srclang = caption.language;
      track.src = caption.vtt_url;
      track.dataset.pyytCaption = "true";
      if (caption.is_default) track.setAttribute("default", "");
      player.append(track);
    }
  } catch {
    // Captions are optional; keep playback available if no tracks are published.
  }
}

linkifyDescriptionTimestamps();
initializePlayer();
loadComments();
loadUpNext();
loadCaptionTracks();
loadChapters();
