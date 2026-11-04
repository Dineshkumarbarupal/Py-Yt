import { apiRequest } from "./api.js";

const form = document.querySelector("#upload-form");
const status = document.querySelector("#upload-status");
const button = document.querySelector("#upload-submit");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.querySelector("#video-file")?.files?.[0];
  if (!file) {
    status.textContent = "Choose a video file first.";
    return;
  }
  const values = Object.fromEntries(new FormData(form).entries());
  button.disabled = true;
  try {
    status.textContent = "Preparing secure upload…";
    const presign = await apiRequest("/uploads/presign", {
      method: "POST",
      body: JSON.stringify({
        title: values.title,
        description: values.description,
        category: values.category,
        video_format: values.video_format,
        content_type: file.type,
        file_size_bytes: file.size,
      }),
    });
    status.textContent = "Uploading video directly to media storage…";
    const uploadResponse = await fetch(presign.upload_url, {
      method: presign.method || "PUT",
      headers: presign.headers || { "Content-Type": file.type },
      body: file,
    });
    if (!uploadResponse.ok) throw new Error("Media storage rejected the upload. Retry or check the storage configuration.");
    status.textContent = "Verifying uploaded video…";
    await apiRequest(`/uploads/${encodeURIComponent(presign.video_id)}/complete`, { method: "POST" });
    status.textContent = "Publishing video…";
    await apiRequest(`/videos/${encodeURIComponent(presign.video_id)}/publish`, {
      method: "POST",
      body: JSON.stringify({ visibility: values.visibility }),
    });
    status.textContent = "Video published successfully.";
    const link = document.createElement("a");
    link.href = `/watch/${encodeURIComponent(presign.video_id)}`;
    link.textContent = "Open your video";
    link.className = "primary-button";
    status.after(link);
    form.reset();
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
