import { apiRequest } from "./api.js";

const list = document.querySelector("#report-list");
const status = document.querySelector("#moderation-status");
const filter = document.querySelector("#report-filter");

function render(items) {
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("section");
    empty.className = "empty-state";
    const title = document.createElement("h2");
    title.textContent = "No reports in this queue";
    const copy = document.createElement("p");
    copy.textContent = "New content reports will appear here.";
    empty.append(title, copy);
    list.append(empty);
    return;
  }
  for (const report of items) {
    const card = document.createElement("article");
    card.className = "report-card";
    const heading = document.createElement("div");
    heading.className = "report-heading";
    const title = document.createElement("strong");
    title.textContent = `${report.target_type} · ${report.reason.replaceAll("_", " ")}`;
    const badge = document.createElement("span");
    badge.className = "report-status";
    badge.textContent = report.status;
    heading.append(title, badge);
    const meta = document.createElement("p");
    meta.className = "muted";
    meta.textContent = `Reported by ${report.reporter} · ${new Date(report.created_at).toLocaleString()}`;
    const details = document.createElement("p");
    details.textContent = report.details || "No additional details.";
    const target = document.createElement("a");
    target.href = report.target_url || (report.target_type === "video" ? `/watch/${encodeURIComponent(report.target_id)}` : "#");
    target.textContent = report.target_type === "video" ? "Open video" : `Comment ID: ${report.target_id}`;
    card.append(heading, meta, details, target);
    if (["open", "reviewing"].includes(report.status)) {
      const actions = document.createElement("div");
      actions.className = "report-actions";
      const review = document.createElement("button");
      review.className = "secondary-button";
      review.textContent = "Mark reviewing";
      review.addEventListener("click", () => update(report, "reviewing"));
      const dismiss = document.createElement("button");
      dismiss.className = "secondary-button";
      dismiss.textContent = "Dismiss";
      dismiss.addEventListener("click", () => update(report, "dismissed"));
      const action = document.createElement("button");
      action.className = "secondary-button danger-button";
      action.textContent = "Take action";
      action.addEventListener("click", () => update(report, "actioned"));
      actions.append(review, dismiss, action);
      card.append(actions);
    }
    list.append(card);
  }
}

async function update(report, nextStatus) {
  const note = window.prompt("Resolution note (optional)", "") ?? "";
  try {
    await apiRequest(`/admin/reports/${encodeURIComponent(report.id)}`, {
      method: "PATCH",
      body: JSON.stringify({ status: nextStatus, resolution_note: note }),
    });
    await load();
  } catch (error) {
    status.textContent = error.message;
  }
}

async function load() {
  status.textContent = "";
  list.replaceChildren();
  try {
    const result = await apiRequest(`/admin/reports?status=${encodeURIComponent(filter.value)}`);
    render(result.items || []);
  } catch (error) {
    status.textContent = error.message;
    if (error.message.includes("Administrator access")) {
      list.textContent = "This page is restricted to administrators.";
    } else if (error.message.toLowerCase().includes("sign in")) {
      window.location.assign("/login");
    }
  }
}

filter.addEventListener("change", load);
document.querySelector("#refresh-reports")?.addEventListener("click", load);
load();
