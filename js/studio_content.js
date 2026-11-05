import { apiRequest } from "./api.js";

const list = document.querySelector("#studio-content-list");
const status = document.querySelector("#studio-content-status");
const categories = ["General", "Music", "Gaming", "Technology", "Learning", "Live", "Comedy", "Sports", "News", "Entertainment"];

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

function render(items) {
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const title = document.createElement("h2");
    title.textContent = "You haven't uploaded a video yet";
    const link = document.createElement("a");
    link.href = "/studio/upload";
    link.className = "primary-button";
    link.textContent = "Upload a video";
    empty.append(title, link);
    list.append(empty);
    return;
  }
  for (const video of items) {
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
    meta.textContent = `${video.status} · ${video.video_format === "short" ? "Shorts" : "Standard"} · ${Number(video.view_count || 0).toLocaleString()} views`;
    info.append(title, meta);

    const category = selectControl("studio-category", categories, video.category || "General");
    const format = selectControl("studio-format", ["standard", "short"], video.video_format || "standard");
    const visibility = selectControl("studio-visibility", ["public", "unlisted", "private"], video.visibility);

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
        meta.textContent = `${video.status} · ${format.value === "short" ? "Shorts" : "Standard"} · ${Number(video.view_count || 0).toLocaleString()} views`;
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
        card.remove();
        status.textContent = "Video deleted.";
      } catch (error) {
        status.textContent = error.message;
        remove.disabled = false;
      }
    });
    actions.append(save, remove);
    card.append(info, category, format, visibility, actions);
    list.append(card);
  }
}

async function load() {
  try {
    const data = await apiRequest("/studio/videos");
    render(data.items || []);
  } catch (error) {
    status.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  }
}
load();
