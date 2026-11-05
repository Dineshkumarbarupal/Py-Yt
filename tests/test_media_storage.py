from io import BytesIO

import core.media_storage as media_storage


class FakeStorage:
    def __init__(self):
        self.calls = []

    def head_object(self, **kwargs):
        self.calls.append(("head", kwargs))
        return {"ContentLength": 128, "ContentType": "image/png"}

    def get_object(self, **kwargs):
        self.calls.append(("get", kwargs))
        return {"Body": BytesIO(bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + b"image-bytes")}

    def generate_presigned_url(self, operation, Params, ExpiresIn, HttpMethod):
        self.calls.append(("presign", {"operation": operation, "Params": Params, "ExpiresIn": ExpiresIn, "HttpMethod": HttpMethod}))
        return "https://storage.example.test/signed"

    def delete_object(self, **kwargs):
        self.calls.append(("delete", kwargs))


def test_thumbnail_inspection_reads_metadata_and_signature_from_thumbnail_bucket(monkeypatch):
    storage = FakeStorage()
    monkeypatch.setattr(media_storage, "client", lambda: storage)

    result = media_storage.inspect_uploaded_image("thumbnails/channel/video/cover", bucket_name="pyyt-thumbnails")

    assert result["ContentLength"] == 128
    assert result["ContentType"] == "image/png"
    assert result["Signature"].startswith(bytes([0x89, 0x50, 0x4E, 0x47]))
    assert storage.calls[0][1]["Bucket"] == "pyyt-thumbnails"
    assert storage.calls[1][1]["Bucket"] == "pyyt-thumbnails"
    assert storage.calls[1][1]["Range"] == "bytes=0-31"


def test_thumbnail_presign_and_delete_use_explicit_thumbnail_bucket(monkeypatch):
    storage = FakeStorage()
    monkeypatch.setattr(media_storage, "client", lambda: storage)

    url = media_storage.create_upload_url(
        "thumbnails/channel/video/cover",
        "image/png",
        bucket_name="pyyt-thumbnails",
    )
    media_storage.delete_object(
        "thumbnails/channel/video/cover",
        bucket_name="pyyt-thumbnails",
    )

    assert url == "https://storage.example.test/signed"
    presign = next(call for call in storage.calls if call[0] == "presign")
    assert presign[1]["Params"]["Bucket"] == "pyyt-thumbnails"
    deletion = next(call for call in storage.calls if call[0] == "delete")
    assert deletion[1]["Bucket"] == "pyyt-thumbnails"
