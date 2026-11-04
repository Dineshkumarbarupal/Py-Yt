import { apiRequest } from "./api.js";

const form = document.querySelector("#search-form");
const input = document.querySelector("#search-query");
const feed = document.querySelector(".feed-section");
const toastRegion = document.querySelector("#toast-region");
let activeCategory = "All";

function toast(message) {
  if (!toastRegion) return;
  const element = document.createElement("div");
  element.className = "toast";
  element.textContent = message;
  toastRegion.append(element);
  window.setTimeout(() => element.remove(), 3200);
}

function renderVideos(items, emptyMessage = "No videos found.") {
  const oldGrid = feed?.querySelector(".video-grid");
  if (oldGrid) oldGrid.remove();
  const oldEmpty = feed?.querySelector(".empty-state");
  if (oldEmpty) oldEmpty.remove();
  if (!items?.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const icon = document.createElement("div");
    icon.className = "empty-icon";
    icon.textContent = "▶";
    const title = document.createElement("h2");
    title.textContent = "No videos found";
    const description = document.createElement("p");
    description.textContent = emptyMessage;
    empty.append(icon, title, description);
    feed?.append(empty);
    return;
  }
  const grid = document.createElement("div");
  grid.className = "video-grid";
  for (const video of items) {
    const card = document.createElement("article");
    card.className = "video-card";
    const thumbLink = document.createElement("a");
    thumbLink.className = "video-thumb";
    thumbLink.href = `/watch/${encodeURIComponent(video.id)}`;
    if (video.thumbnail_url) {
      const image = document.createElement("img");
      image.src = video.thumbnail_url;
      image.alt = "";
      image.loading = "lazy";
      thumbLink.append(image);
    } else {
      const placeholder = document.createElement("span");
      placeholder.className = "thumb-placeholder";
      placeholder.textContent = "▶";
      thumbLink.append(placeholder);
    }
    const meta = document.createElement("div");
    meta.className = "video-meta";
    const avatar = document.createElement("div");
    avatar.className = "channel-avatar";
    avatar.textContent = (video.channel_name || "P").slice(0, 1).toUpperCase();
    const copy = document.createElement("div");
    copy.className = "video-copy";
    const title = document.createElement("a");
    title.className = "video-title";
    title.href = thumbLink.href;
    title.textContent = video.title;
    const channel = document.createElement("div");
    channel.className = "muted";
    channel.textContent = video.channel_name || "Creator";
    const category = document.createElement("div");
    category.className = "muted";
    category.textContent = video.category || "";
    copy.append(title, channel, category);
    meta.append(avatar, copy);
    card.append(thumbLink, meta);
    grid.append(card);
  }
  feed?.append(grid);
}

async function loadFeed(category = "All") {
  activeCategory = category;
  const heading = feed?.querySelector("h2");
  if (heading) heading.textContent = category === "All" ? "Latest videos" : category;
  const result = await apiRequest(`/discovery/feed?category=${encodeURIComponent(category)}`);
  renderVideos(result.items, "No published videos are available in this category yet.");
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;
  try {
    const result = await apiRequest(`/discovery/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(activeCategory)}`);
    const heading = feed?.querySelector("h2");
    if (heading) heading.textContent = `Search results for “${query}”`;
    renderVideos(result.items, "No videos matched this search. Try another phrase or category.");
  } catch (error) {
    toast(error.message);
  }
});

document.querySelectorAll("[data-category]").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll("[data-category]").forEach((item) => item.classList.remove("selected"));
    button.classList.add("selected");
    input.value = "";
    try {
      await loadFeed(button.dataset.category);
    } catch (error) {
      toast(error.message);
    }
  });
});

document.querySelector("#menu-toggle")?.addEventListener("click", () => {
  document.querySelector("#sidebar")?.classList.toggle("open");
});

document.querySelector("#theme-toggle")?.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  localStorage.setItem("pyyt-theme", document.body.classList.contains("dark") ? "dark" : "light");
});
if (localStorage.getItem("pyyt-theme") === "dark") document.body.classList.add("dark");
