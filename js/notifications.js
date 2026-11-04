import { apiRequest } from "./api.js";

const list = document.querySelector("#notification-list");
const status = document.querySelector("#notification-status");
const count = document.querySelector("#notification-count");
const markAllButton = document.querySelector("#mark-all-read");

function render(items) {
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const title = document.createElement("h2");
    title.textContent = "You're all caught up";
    const copy = document.createElement("p");
    copy.textContent = "Updates from channels you follow and conversations on your videos will appear here.";
    empty.append(title, copy);
    list.append(empty);
    return;
  }
  for (const item of items) {
    const row = document.createElement("article");
    row.className = `notification-item${item.is_read ? "" : " unread"}`;
    const dot = document.createElement("span");
    dot.className = "notification-dot";
    const content = document.createElement("div");
    content.className = "notification-copy";
    const link = document.createElement("a");
    link.href = item.url;
    link.textContent = item.message;
    const time = document.createElement("time");
    time.className = "muted";
    time.textContent = item.created_at ? new Date(item.created_at).toLocaleString() : "";
    content.append(link, time);
    row.append(dot, content);
    if (!item.is_read) {
      const read = document.createElement("button");
      read.className = "secondary-button";
      read.textContent = "Mark read";
      read.addEventListener("click", async () => {
        read.disabled = true;
        try {
          await apiRequest(`/notifications/${encodeURIComponent(item.id)}/read`, { method: "POST" });
          item.is_read = true;
          row.classList.remove("unread");
          read.remove();
          await refreshCount();
        } catch (error) {
          status.textContent = error.message;
          read.disabled = false;
        }
      });
      row.append(read);
    }
    list.append(row);
  }
}

async function refreshCount() {
  const data = await apiRequest("/notifications?limit=1");
  count.textContent = data.unread_count ? `${data.unread_count} unread` : "No unread notifications";
}

async function load() {
  try {
    const data = await apiRequest("/notifications");
    render(data.items || []);
    count.textContent = data.unread_count ? `${data.unread_count} unread` : "No unread notifications";
    markAllButton.disabled = data.unread_count === 0;
  } catch (error) {
    status.textContent = error.message;
    list.replaceChildren();
    const link = document.createElement("a");
    link.href = "/login";
    link.className = "primary-button";
    link.textContent = "Sign in to view notifications";
    list.append(link);
  }
}

markAllButton?.addEventListener("click", async () => {
  markAllButton.disabled = true;
  try {
    await apiRequest("/notifications/read-all", { method: "POST" });
    await load();
  } catch (error) {
    status.textContent = error.message;
    markAllButton.disabled = false;
  }
});

load();
