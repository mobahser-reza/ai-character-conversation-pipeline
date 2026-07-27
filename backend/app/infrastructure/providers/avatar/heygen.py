import asyncio
import uuid

import httpx

from app.domain.interfaces.providers import AvatarProvider, AvatarResult
from app.infrastructure.providers.api_key_lookup import get_decrypted_key
from app.infrastructure.providers.storage.factory import get_storage_provider
from app.infrastructure.providers.storage.paths import new_tmp_path

_BASE_URL = "https://api.heygen.com"
_POLL_INTERVAL_SECONDS = 5
_POLL_TIMEOUT_SECONDS = 600


class HeyGenAvatarProvider(AvatarProvider):
    """Real HeyGen adapter (v3 Videos API): uploads the reference image as a talking
    photo to get an avatar_id, submits a video job with a pre-rendered audio track,
    then polls until HeyGen finishes lip-sync rendering."""

    name = "heygen"

    async def generate_clip(
        self, reference_image_url: str, audio_url: str, expression_tag: str | None
    ) -> AvatarResult:
        api_key = await get_decrypted_key("heygen")
        headers = {"X-Api-Key": api_key}
        content_type = "image/png" if reference_image_url.lower().endswith(".png") else "image/jpeg"

        async with httpx.AsyncClient(timeout=60) as client:
            image_bytes = (await client.get(reference_image_url)).content
            upload_response = await client.post(
                "https://upload.heygen.com/v1/talking_photo",
                headers={**headers, "Content-Type": content_type},
                content=image_bytes,
            )
            upload_response.raise_for_status()
            avatar_id = upload_response.json()["data"]["talking_photo_id"]

            submit_response = await client.post(
                f"{_BASE_URL}/v3/videos",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "audio_url": audio_url,
                    "aspect_ratio": "9:16",
                },
            )
            submit_response.raise_for_status()
            video_id = submit_response.json()["data"]["video_id"]

            elapsed = 0
            video_url = None
            while elapsed < _POLL_TIMEOUT_SECONDS:
                status_response = await client.get(
                    f"{_BASE_URL}/v3/videos/{video_id}",
                    headers=headers,
                )
                status_response.raise_for_status()
                data = status_response.json()["data"]
                if data["status"] == "completed":
                    video_url = data["video_url"]
                    break
                if data["status"] == "failed":
                    raise RuntimeError(f"HeyGen render failed: {data.get('error')}")
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                elapsed += _POLL_INTERVAL_SECONDS

            if video_url is None:
                raise TimeoutError(f"HeyGen render for video_id={video_id} timed out")

            download = await client.get(video_url)
            download.raise_for_status()

        tmp_path = new_tmp_path(".mp4")
        with open(tmp_path, "wb") as f:
            f.write(download.content)

        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"avatar/{uuid.uuid4()}.mp4")
        return AvatarResult(video_url=url, duration_seconds=0.0)
