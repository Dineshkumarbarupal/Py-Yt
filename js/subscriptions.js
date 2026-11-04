import { apiRequest } from "./api.js";

const list = document.querySelector("#subscription-list");
const count = document.querySelector("#subscription-count");
const status = document.querySelector("#subscription-status");

async function load() {
  try {
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
          const next = list.querySelectorAll(".channel-list-item").length;
          count.textContent = `${next} channels`;
        } catch (error) {
          status.textContent = error.message;
          button.disabled = false;
        }
      });
      item.append(avatar, info, button);
      list.append(item);
    }
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

load();
