import { apiRequest } from "./api.js";

const feed = document.querySelector("#shorts-feed");
const status = document.querySelector("#shorts-status");
let observer;

function makeShort(item) {
  const card = document.createElement("article");
  card.className = "short-card";
  const frame = document.createElement("div");
  frame.className = "short-frame";

  const video = document.createElement("video");
  video.className = "short-video";
  video.playsInline = true;
  video.muted = true;
  video.loop = true;
  video.preload = "none";
  video.setAttribute("aria-label", item.title);
  let viewRecorded = false;
  let lastProgressSaved = -1;

  video.addEventListener("play", () => {
    if (viewRecorded) return;
    viewRecorded = true;
    apiRequest("/videos/" + encodeURIComponent(item.id) + "/view", { method: "POST" }).catch(() => null);
  });
  video.addEventListener("timeupdate", () => {
    const second = Math.floor(video.currentTime);
    if (second - lastProgressSaved < 15) return;
    lastProgressSaved = second;
    apiRequest("/engagement/videos/" + encodeURIComponent(item.id) + "/history", {
      method: "POST",
      body: JSON.stringify({ progress_seconds: second }),
    }).catch(() => null);
  });

  const overlay = document.createElement("div");
  overlay.className = "short-overlay";
  const details = document.createElement("div");
  details.className = "short-details";
  const title = document.createElement("strong");
  title.textContent = item.title;
  const channel = document.createElement("a");
  channel.href = `/@${encodeURIComponent(item.channel_handle)}`;
  channel.textContent = `@${item.channel_handle}`;
  details.append(title, channel);

  const actions = document.createElement("div");
  actions.className = "short-actions";
  const like = document.createElement("button");
  like.type = "button";
  like.className = "short-action";
  like.textContent = "♡";
  like.setAttribute("aria-label", "Like Short");
  like.addEventListener("click", async () => {
    try {
      await apiRequest(`/engagement/videos/${encodeURIComponent(item.id)}/reaction`, {
        method: "PUT",
        body: JSON.stringify({ reaction: "like" }),
      });
      like.textContent = "♥";
    } catch (error) {
      status.textContent = error.message;
    }
  });

  const share = document.createElement("button");
  share.type = "button";
  share.className = "short-action";
  share.textContent = "↗";
  share.setAttribute("aria-label", "Share Short");
  share.addEventListener("click", async () => {
    const data = { title: item.title, url: `${window.location.origin}/watch/${encodeURIComponent(item.id)}` };
    try {
      if (navigator.share) await navigator.share(data);
      else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(data.url);
        status.textContent = "Short link copied.";
      } else status.textContent = data.url;
    } catch (error) {
      if (error.name !== "AbortError") status.textContent = "Could not share this Short.";
    }
  });

  const queue = document.createElement("button");
  queue.type = "button";
  queue.className = "short-action";
  queue.textContent = "+";
  queue.setAttribute("aria-label", "Add Short to queue");
  queue.dataset.queueAdd = "";
  queue.dataset.queueId = item.id;
  queue.dataset.queueTitle = item.title;
  queue.dataset.queueChannel = item.channel_name || "Creator";

  const later = document.createElement("button");
  later.type = "button";
  later.className = "short-action";
  later.textContent = "◷";
  later.setAttribute("aria-label", "Save Short to Watch Later");
  later.addEventListener("click", async () => {
    try {
      const result = await apiRequest(`/library/watch-later/${encodeURIComponent(item.id)}`, { method: "POST" });
      status.textContent = result.status === "already_saved" ? "Already in Watch later." : "Saved to Watch later.";
    } catch (error) {
      status.textContent = error.message;
    }
  });

  const watch = document.createElement("a");
  watch.className = "short-action";
  watch.href = `/watch/${encodeURIComponent(item.id)}`;
  watch.textContent = "▶";
  watch.setAttribute("aria-label", "Open watch page");
  actions.append(like, share, queue, later, watch);
  overlay.append(details, actions);
  frame.append(video, overlay);

  video.addEventListener("click", () => {
    if (video.paused) video.play().catch(() => null);
    else video.pause();
  });

  card.append(frame);
  card.dataset.videoId = item.id;
  return { card, video };
}

async function loadShorts() {
  try {
    const data = await apiRequest("/discovery/shorts?limit=20");
    feed.replaceChildren();
    if (!data.items?.length) {
      const empty = document.createElement("section");
      empty.className = "empty-state";
      const icon = document.createElement("div");
      icon.className = "empty-icon";
      icon.textContent = "▣";
      const title = document.createElement("h2");
      title.textContent = "No Shorts yet";
      const copy = document.createElement("p");
      copy.textContent = "Creators can choose Shorts format when uploading a vertical video.";
      const link = document.createElement("a");
      link.href = "/studio/upload";
      link.className = "primary-button";
      link.textContent = "Create a Short";
      empty.append(icon, title, copy, link);
      feed.append(empty);
      return;
    }

    const cards = data.items.map(makeShort);
    for (const entry of cards) feed.append(entry.card);

    observer?.disconnect();
    observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        const video = entry.target;
        if (entry.isIntersecting && entry.intersectionRatio >= 0.65) {
          for (const other of feed.querySelectorAll("video")) {
            if (other !== video) other.pause();
          }
          if (!video.src) {
            const item = data.items.find((candidate) => candidate.id === video.closest(".short-card")?.dataset.videoId);
            if (item) {
              apiRequest(`/videos/${encodeURIComponent(item.id)}/playback`)
                .then((result) => {
                  video.src = result.playback_url;
                  return video.play();
                })
                .catch((error) => { status.textContent = error.message; });
            }
          } else {
            video.play().catch(() => null);
          }
        } else {
          video.pause();
        }
      }
    }, { threshold: [0, 0.65, 0.9] });

    for (const entry of cards) observer.observe(entry.video);
  } catch (error) {
    status.textContent = error.message;
    feed.replaceChildren();
    const link = document.createElement("a");
    link.href = "/login";
    link.className = "primary-button";
    link.textContent = "Sign in to continue";
    feed.append(link);
  }
}

loadShorts();
