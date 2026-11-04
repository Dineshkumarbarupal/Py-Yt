import { apiRequest } from "./api.js";

const page = document.querySelector(".channel-page");
const channelId = page?.dataset.channelId;
const button = document.querySelector("#subscribe-button");
const status = document.querySelector("#subscribe-status");
let subscribed = false;

async function initialize() {
  try {
    const result = await apiRequest("/subscriptions");
    subscribed = (result.items || []).some((item) => item.channel_id === channelId);
    updateButton();
  } catch {
    button.textContent = "Subscribe";
    subscribed = false;
  }
}

function updateButton() {
  button.textContent = subscribed ? "Subscribed · Unsubscribe" : "Subscribe";
  button.classList.toggle("subscribed-button", subscribed);
}

button?.addEventListener("click", async () => {
  button.disabled = true;
  status.textContent = "Updating subscription…";
  try {
    if (subscribed) {
      await apiRequest(`/subscriptions/${encodeURIComponent(channelId)}`, { method: "DELETE" });
      subscribed = false;
      status.textContent = "You unsubscribed from this channel.";
    } else {
      await apiRequest(`/subscriptions/${encodeURIComponent(channelId)}`, { method: "POST" });
      subscribed = true;
      status.textContent = "You are now subscribed.";
    }
    updateButton();
  } catch (error) {
    status.textContent = error.message;
    if (error.message.toLowerCase().includes("sign in")) {
      const link = document.createElement("a");
      link.href = "/login";
      link.textContent = "Sign in";
      status.append(" ", link, " to subscribe.");
    }
  } finally {
    button.disabled = false;
  }
});

initialize();
