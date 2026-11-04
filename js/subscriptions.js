import { apiRequest } from "./api.js";

const list = document.querySelector("#subscription-list");
const feed = document.querySelector("#subscription-feed");
const count = document.querySelector("#subscription-count");
const status = document.querySelector("#subscription-status");

function renderVideoFeed(items) {
  feed.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "New public videos from channels you follow will appear here.";
    feed.append(empty);
    return;
  }
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
    card.append(thumb, title, channel);
    feed.append(card);
  }
}

async function loadChannels() {
  const result = await apiRequest("/subscriptions");
  const items = result.items || [];
  count.textContent = `${items.length} channels`;
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const title = document.createElement("h2");
    title.textContent = "No subscriptions yet";
    const copy = document.createElement("p");
    copy.textContent = "Visit a creator's channel and subscribe to see them here.";
    const link = document.createElement("a");
    link.href = "/";
    link.className = "primary-button";
    link.textContent = "Discover videos";
    empty.append(title, copy, link);
    list.append(empty);
    return;
  }
  for (const channel of items) {
    const item = document.createElement("article");
    item.className = "channel-list-item";
    const avatar = document.createElement("div");
    avatar.className = "channel-avatar";
    avatar.textContent = (channel.name || "P").slice(0, 1).toUpperCase();
    const info = document.createElement("div");
    const name = document.createElement("a");
    name.href = `/@${encodeURIComponent(channel.handle)}`;
    name.className = "channel-list-name";
    name.textContent = channel.name;
    const handle = document.createElement("p");
    handle.className = "muted";
    handle.textContent = `@${channel.handle}`;
    info.append(name, handle);
    const button = document.createElement("button");
    button.className = "secondary-button";
    button.textContent = "Unsubscribe";
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await apiRequest(`/subscriptions/${encodeURIComponent(channel.channel_id)}`, { method: "DELETE" });
        item.remove();
        count.textContent = `${list.querySelectorAll(".channel-list-item").length} channels`;
      } catch (error) {
        status.textContent = error.message;
        button.disabled = false;
      }
    });
    item.append(avatar, info, button);
    list.append(item);
  }
}

async function loadFeed() {
  const result = await apiRequest("/subscriptions/feed");
  renderVideoFeed(result.items || []);
}

document.querySelectorAll("[data-tab]").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll("[data-tab]").forEach((tab) => tab.classList.toggle("active", tab === button));
    const showFeed = button.dataset.tab === "feed";
    list.classList.toggle("hidden", showFeed);
    feed.classList.toggle("hidden", !showFeed);
    if (showFeed) {
      try {
        await loadFeed();
      } catch (error) {
        status.textContent = error.message;
      }
    }
  });
});

async function initialize() {
  try {
    await loadChannels();
  } catch (error) {
    status.textContent = error.message;
    list.replaceChildren();
    const link = document.createElement("a");
    link.href = "/login";
    link.className = "primary-button";
    link.textContent = "Sign in to see subscriptions";
    list.append(link);
  }
}
initialize();
