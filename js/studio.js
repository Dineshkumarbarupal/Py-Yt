import { apiRequest } from "./api.js";

const status = document.querySelector("#studio-status");
const format = (value) => Number(value || 0).toLocaleString();

async function load() {
  try {
    const data = await apiRequest("/studio/overview");
    document.querySelector("#studio-channel-name").textContent = data.channel?.name || "Your creator dashboard";
    document.querySelector("#metric-views").textContent = format(data.total_views);
    document.querySelector("#metric-subscribers").textContent = format(data.subscribers);
    document.querySelector("#metric-videos").textContent = format(data.published_videos);
    document.querySelector("#metric-comments").textContent = format(data.visible_comments);
  } catch (error) {
    status.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  }
}
load();
