import { apiRequest } from "./api.js";

const list = document.querySelector("#playlist-list");
const dialog = document.querySelector("#create-playlist-dialog");
const form = document.querySelector("#create-playlist-form");
const status = document.querySelector("#playlist-page-status");
const formStatus = document.querySelector("#create-playlist-status");

function render(items) {
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const title = document.createElement("h2");
    title.textContent = "Create your first playlist";
    const copy = document.createElement("p");
    copy.textContent = "Collect videos into lists for learning, music, workouts or anything you like.";
    empty.append(title, copy);
    list.append(empty);
    return;
  }
  for (const playlist of items) {
    const card = document.createElement("a");
    card.className = "playlist-tile";
    card.href = `/playlist/${encodeURIComponent(playlist.id)}`;
    const icon = document.createElement("span");
    icon.className = "playlist-tile-icon";
    icon.textContent = "▤";
    const title = document.createElement("strong");
    title.textContent = playlist.title;
    const description = document.createElement("p");
    description.className = "muted";
    description.textContent = playlist.description || playlist.visibility;
    card.append(icon, title, description);
    list.append(card);
  }
}

async function load() {
  try {
    const result = await apiRequest("/playlists/mine");
    render(result.items || []);
  } catch (error) {
    status.textContent = error.message;
    list.replaceChildren();
    const link = document.createElement("a");
    link.href = "/login";
    link.className = "primary-button";
    link.textContent = "Sign in to manage playlists";
    list.append(link);
  }
}

document.querySelector("#new-playlist-button")?.addEventListener("click", () => dialog.showModal());
document.querySelector("#close-create-playlist")?.addEventListener("click", () => dialog.close());
document.querySelector("#cancel-create-playlist")?.addEventListener("click", () => dialog.close());

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form).entries());
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  formStatus.textContent = "Creating…";
  try {
    await apiRequest("/playlists", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    dialog.close();
    await load();
  } catch (error) {
    formStatus.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});

load();
