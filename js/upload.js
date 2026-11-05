import { apiRequest } from "./api.js";

const form = document.querySelector("#upload-form");
const status = document.querySelector("#upload-status");
const button = document.querySelector("#upload-submit");
const thumbnailInput = document.querySelector("#thumbnail-file");
const THUMBNAIL_TYPES = ["image/jpeg", "image/png", "image/webp"];
const THUMBNAIL_MAX_BYTES = 5 * 1024 * 1024;

async function uploadThumbnail(videoId, file) {
  if (!THUMBNAIL_TYPES.includes(file.type)) {
    throw new Error("Thumbnail must be a JPEG, PNG or WebP image.");
  }
  if (file.size <= 0 || file.size > THUMBNAIL_MAX_BYTES) {
    throw new Error("Thumbnail must be larger than zero and no bigger than 5 MB.");
  }
  const presign = await apiRequest(`/uploads/${encodeURIComponent(videoId)}/thumbnail/presign`, {
    method: "POST",
    body: JSON.stringify({
      content_type: file.type,
      file_size_bytes: file.size,
    }),
  });
  const response = await fetch(presign.upload_url, {
    method: presign.method || "PUT",
    headers: presign.headers || { "Content-Type": file.type },
    body: file,
  });
  if (!response.ok) {
    throw new Error("Media storage rejected the thumbnail upload.");
  }
  return apiRequest(`/uploads/${encodeURIComponent(videoId)}/thumbnail/complete`, {
    method: "POST",
  });
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.querySelector("#video-file")?.files?.[0];
  if (!file) {
    status.textContent = "Choose a video file first.";
    return;
  }
  const thumbnailFile = thumbnailInput?.files?.[0] || null;
  const values = Object.fromEntries(new FormData(form).entries());
  button.disabled = true;
  let thumbnailWarning = "";
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

    if (thumbnailFile) {
      status.textContent = "Uploading and verifying custom thumbnail…";
      try {
        await uploadThumbnail(presign.video_id, thumbnailFile);
      } catch (error) {
        thumbnailWarning = error.message;
      }
    }

    status.textContent = "Publishing video…";
    await apiRequest(`/videos/${encodeURIComponent(presign.video_id)}/publish`, {
      method: "POST",
      body: JSON.stringify({ visibility: values.visibility }),
    });
    status.textContent = thumbnailWarning
      ? `Video published. Thumbnail was not applied: ${thumbnailWarning}`
      : "Video published successfully.";
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
