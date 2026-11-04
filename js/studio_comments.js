import { apiRequest } from "./api.js";

const list = document.querySelector("#studio-comments-list");
const status = document.querySelector("#studio-comments-status");

async function load() {
  try {
    const data = await apiRequest("/studio/comments");
    list.replaceChildren();
    if (!data.items?.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "No comments on your videos yet.";
      list.append(empty);
      return;
    }
    for (const comment of data.items) {
      const card = document.createElement("article");
      card.className = "studio-comment-card";
      const heading = document.createElement("div");
      heading.className = "studio-comment-heading";
      const author = document.createElement("strong");
      author.textContent = comment.display_name;
      const video = document.createElement("a");
      video.href = `/watch/${encodeURIComponent(comment.video_id)}`;
      video.textContent = comment.video_title;
      const body = document.createElement("p");
      body.textContent = comment.body;
      const action = document.createElement("button");
      action.className = "secondary-button";
      action.textContent = comment.status === "hidden" ? "Restore" : "Hide";
      action.addEventListener("click", async () => {
        action.disabled = true;
        try {
          const next = comment.status === "hidden" ? "visible" : "hidden";
          await apiRequest(`/studio/comments/${encodeURIComponent(comment.id)}`, {
            method: "PATCH",
            body: JSON.stringify({ status: next }),
          });
          comment.status = next;
          action.textContent = next === "hidden" ? "Restore" : "Hide";
          status.textContent = "Comment status updated.";
        } catch (error) {
          status.textContent = error.message;
        } finally {
          action.disabled = false;
        }
      });
      heading.append(author, video);
      card.append(heading, body, action);
      list.append(card);
    }
  } catch (error) {
    status.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) window.location.assign("/login");
  }
}
load();
