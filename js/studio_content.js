import { apiRequest } from "./api.js";

const list = document.querySelector("#studio-content-list");
const status = document.querySelector("#studio-content-status");
const countLabel = document.querySelector("#studio-content-count");
const searchInput = document.querySelector("#studio-search");
const statusFilter = document.querySelector("#studio-status-filter");
const visibilityFilter = document.querySelector("#studio-visibility-filter");
const formatFilter = document.querySelector("#studio-format-filter");
const searchButton = document.querySelector("#studio-search-button");
const loadMoreButton = document.querySelector("#studio-load-more");
const categories = ["General", "Music", "Gaming", "Technology", "Learning", "Live", "Comedy", "Sports", "News", "Entertainment"];
const pageSize = 30;
let currentItems = [];
let nextOffset = null;
let totalCount = 0;

function selectControl(className, values, current) {
  const select = document.createElement("select");
  select.className = className;
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value[0].toUpperCase() + value.slice(1);
    select.append(option);
  }
  select.value = current;
  return select;
}

function createVideoCard(video) {
  const card = document.createElement("article");
  card.className = "studio-content-row";
  const info = document.createElement("div");
  info.className = "studio-content-info";
  const title = document.createElement("input");
  title.className = "studio-title-input";
  title.type = "text";
  title.maxLength = 200;
  title.value = video.title;
  title.setAttribute("aria-label", "Video title");
  const meta = document.createElement("p");
  meta.className = "muted";

  const category = selectControl("studio-category", categories, video.category || "General");
  const format = selectControl("studio-format", ["standard", "short"], video.video_format || "standard");
  const visibility = selectControl("studio-visibility", ["public", "unlisted", "private"], video.visibility);
  const updateMeta = () => {
    meta.textContent = `${video.status} · ${format.value === "short" ? "Shorts" : "Standard"} · ${Number(video.view_count || 0).toLocaleString()} views`;
  };
  info.append(title, meta);
  updateMeta();

  const actions = document.createElement("div");
  actions.className = "studio-row-actions";
  const save = document.createElement("button");
  save.className = "secondary-button";
  save.textContent = "Save";
  save.addEventListener("click", async () => {
    if (!title.value.trim()) {
      status.textContent = "Video title cannot be empty.";
      return;
    }
    save.disabled = true;
    try {
      await apiRequest(`/videos/${encodeURIComponent(video.id)}`, {
        method: "PATCH",
        body: JSON.stringify({
          title: title.value.trim(),
          category: category.value,
          video_format: format.value,
          visibility: visibility.value,
        }),
      });
      video.title = title.value.trim();
      video.category = category.value;
      video.video_format = format.value;
      video.visibility = visibility.value;
      updateMeta();
      status.textContent = "Video details saved.";
    } catch (error) {
      status.textContent = error.message;
    } finally {
      save.disabled = false;
    }
  });

  const remove = document.createElement("button");
  remove.className = "secondary-button danger-button";
  remove.textContent = "Delete";
  remove.addEventListener("click", async () => {
    if (!window.confirm("Delete this video? The media object will also be removed from storage.")) return;
    remove.disabled = true;
    try {
      await apiRequest(`/videos/${encodeURIComponent(video.id)}`, { method: "DELETE" });
      currentItems = currentItems.filter((item) => item.id !== video.id);
      totalCount = Math.max(0, totalCount - 1);
      render();
      status.textContent = "Video deleted.";
    } catch (error) {
      status.textContent = error.message;
      remove.disabled = false;
    }
  });

  actions.append(save, remove);
  card.append(info, category, format, visibility, actions);
  return card;
}

function render() {
  list.replaceChildren();
  if (countLabel) countLabel.textContent = `${currentItems.length} of ${totalCount} videos`;
  if (!currentItems.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const title = document.createElement("h2");
    title.textContent = "No videos match these filters";
    const link = document.createElement("a");
    link.href = "/studio/upload";
    link.className = "primary-button";
    link.textContent = "Upload a video";
    empty.append(title, link);
    list.append(empty);
  } else {
    for (const video of currentItems) list.append(createVideoCard(video));
  }
  if (loadMoreButton) {
    loadMoreButton.classList.toggle("hidden", nextOffset === null);
    loadMoreButton.disabled = nextOffset === null;
  }
}

function buildQuery(offset) {
  const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
  const q = searchInput?.value.trim();
  if (q) params.set("q", q);
  if (statusFilter?.value) params.set("status", statusFilter.value);
  if (visibilityFilter?.value) params.set("visibility", visibilityFilter.value);
  if (formatFilter?.value) params.set("video_format", formatFilter.value);
  return params.toString();
}

async function load({ append = false } = {}) {
  status.textContent = "";
  if (!append) {
    currentItems = [];
    nextOffset = null;
    totalCount = 0;
    render();
  }
  const offset = append && nextOffset !== null ? nextOffset : 0;
  if (searchButton) searchButton.disabled = true;
  if (loadMoreButton) loadMoreButton.disabled = true;
  try {
    const data = await apiRequest(`/studio/videos?${buildQuery(offset)}`);
    currentItems = append ? currentItems.concat(data.items || []) : (data.items || []);
    totalCount = Number(data.total_count || 0);
    nextOffset = data.next_offset ?? null;
    render();
  } catch (error) {
    status.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  } finally {
    if (searchButton) searchButton.disabled = false;
    if (loadMoreButton && nextOffset !== null) loadMoreButton.disabled = false;
  }
}

searchButton?.addEventListener("click", () => load());
searchInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") load();
});
for (const filter of [statusFilter, visibilityFilter, formatFilter]) {
  filter?.addEventListener("change", () => load());
}
loadMoreButton?.addEventListener("click", () => load({ append: true }));
load();
