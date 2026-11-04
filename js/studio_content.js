import { apiRequest } from "./api.js";

const list = document.querySelector("#studio-content-list");
const status = document.querySelector("#studio-content-status");

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
    const title = document.createElement("strong");
    title.textContent = video.title;
    const meta = document.createElement("p");
    meta.className = "muted";
    meta.textContent = `${video.status} · ${video.category} · ${Number(video.view_count || 0).toLocaleString()} views`;
    info.append(title, meta);

    const visibility = document.createElement("select");
    visibility.className = "studio-visibility";
    for (const value of ["public", "unlisted", "private"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value[0].toUpperCase() + value.slice(1);
      visibility.append(option);
    }
    visibility.value = video.visibility;

    const save = document.createElement("button");
    save.className = "secondary-button";
    save.textContent = "Save";
    save.addEventListener("click", async () => {
      save.disabled = true;
      try {
        await apiRequest(`/videos/${encodeURIComponent(video.id)}`, {
          method: "PATCH",
          body: JSON.stringify({ visibility: visibility.value }),
        });
        status.textContent = "Video visibility updated.";
      } catch (error) {
        status.textContent = error.message;
      } finally {
        save.disabled = false;
      }
    });
    card.append(info, visibility, save);
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
