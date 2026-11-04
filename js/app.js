import { apiRequest } from "./api.js";

const form = document.querySelector("#search-form");
const input = document.querySelector("#search-query");
const feed = document.querySelector(".feed-section");
const toastRegion = document.querySelector("#toast-region");

function toast(message) {
  if (!toastRegion) return;
  const element = document.createElement("div");
  element.className = "toast";
  element.textContent = message;
  toastRegion.append(element);
  window.setTimeout(() => element.remove(), 3200);
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;
  try {
    const result = await apiRequest(`/discovery/search?q=${encodeURIComponent(query)}`);
    const heading = feed?.querySelector("h2");
    if (heading) heading.textContent = `Search results for “${query}”`;
    const empty = feed?.querySelector(".empty-state p");
    if (empty) empty.textContent = result.items?.length ? "" : "No videos matched this search. Try another phrase or upload the first video.";
  } catch (error) {
    toast(error.message);
  }
});

document.querySelectorAll("[data-category]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-category]").forEach((item) => item.classList.remove("selected"));
    button.classList.add("selected");
    toast(`Showing the ${button.dataset.category} feed when content is available.`);
  });
});

document.querySelector("#menu-toggle")?.addEventListener("click", () => {
  document.querySelector("#sidebar")?.classList.toggle("open");
});

document.querySelector("#theme-toggle")?.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  localStorage.setItem("pyyt-theme", document.body.classList.contains("dark") ? "dark" : "light");
});
if (localStorage.getItem("pyyt-theme") === "dark") document.body.classList.add("dark");
