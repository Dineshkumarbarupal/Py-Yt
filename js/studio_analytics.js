import { apiRequest } from "./api.js";

const status = document.querySelector("#analytics-status");
async function load() {
  try {
    const data = await apiRequest("/studio/analytics");
    document.querySelector("#analytics-views").textContent = Number(data.total_views || 0).toLocaleString();
    document.querySelector("#analytics-videos").textContent = Number(data.published_videos || 0).toLocaleString();
    const list = document.querySelector("#analytics-top-videos");
    list.replaceChildren();
    if (!data.top_videos?.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "No published videos yet.";
      list.append(empty);
      return;
    }
    for (const video of data.top_videos) {
      const row = document.createElement("div");
      row.className = "analytics-video-row";
      const link = document.createElement("a");
      link.href = `/watch/${encodeURIComponent(video.id)}`;
      link.textContent = video.title;
      const views = document.createElement("strong");
      views.textContent = `${Number(video.view_count || 0).toLocaleString()} views`;
      row.append(link, views);
      list.append(row);
    }
  } catch (error) {
    status.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  }
}
load();
