const STORAGE_KEY = "pyyt_watch_queue";
const dialog = document.querySelector("#queue-dialog");
const itemsContainer = document.querySelector("#queue-items");
const countLabel = document.querySelector("#queue-count");
const status = document.querySelector("#queue-status");
const openButton = document.querySelector("#queue-open");

function readQueue() {
  try {
    const value = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value)
      ? value.filter((item) => item && typeof item.id === "string" && typeof item.title === "string")
      : [];
  } catch {
    return [];
  }
}

function writeQueue(items) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    render();
    window.dispatchEvent(new CustomEvent("pyyt:queue-updated", { detail: { count: items.length } }));
    return true;
  } catch {
    if (status) status.textContent = "Browser session storage is unavailable; the queue cannot be saved.";
    return false;
  }
}

function render() {
  const items = readQueue();
  if (countLabel) countLabel.textContent = String(items.length);
  if (!itemsContainer) return;
  itemsContainer.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Your queue is empty. Add videos from the feed or watch page.";
    itemsContainer.append(empty);
    return;
  }
  items.forEach((item, index) => {
    const row = document.createElement("article");
    row.className = "queue-item";
    const copy = document.createElement("div");
    copy.className = "queue-item-copy";
    const title = document.createElement("strong");
    title.textContent = item.title;
    const channel = document.createElement("small");
    channel.textContent = item.channel || "Creator";
    const order = document.createElement("span");
    order.className = "queue-order";
    order.textContent = String(index + 1);
    copy.append(order, title, channel);
    const actions = document.createElement("div");
    actions.className = "queue-item-actions";
    const play = document.createElement("button");
    play.type = "button";
    play.className = "secondary-button";
    play.textContent = "Play";
    play.addEventListener("click", () => {
      const remaining = readQueue().filter((entry) => entry.id !== item.id);
      writeQueue(remaining);
      window.location.assign(`/watch/${encodeURIComponent(item.id)}`);
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "queue-remove";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Remove ${item.title} from queue`);
    remove.addEventListener("click", () => {
      writeQueue(readQueue().filter((entry) => entry.id !== item.id));
    });
    actions.append(play, remove);
    row.append(copy, actions);
    itemsContainer.append(row);
  });
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-queue-add]");
  if (!button) return;
  const id = button.dataset.queueId;
  const title = button.dataset.queueTitle;
  if (!id || !title) return;
  const items = readQueue();
  if (items.some((item) => item.id === id)) {
    status.textContent = "This video is already in the queue.";
    dialog?.showModal();
    return;
  }
  items.push({
    id,
    title,
    channel: button.dataset.queueChannel || "Creator",
  });
  if (writeQueue(items)) {
    status.textContent = "Added to queue.";
    button.textContent = "Added";
    button.disabled = true;
  }
});

openButton?.addEventListener("click", () => {
  status.textContent = "";
  render();
  dialog?.showModal();
});
document.querySelector("#queue-close")?.addEventListener("click", () => dialog?.close());
document.querySelector("#queue-clear")?.addEventListener("click", () => {
  writeQueue([]);
  status.textContent = "Queue cleared.";
});
window.addEventListener("pyyt:queue-updated", render);
render();
