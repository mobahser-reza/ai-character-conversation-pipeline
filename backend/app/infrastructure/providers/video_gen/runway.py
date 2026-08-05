import asyncio
import uuid

import httpx

from app.domain.interfaces.providers import VideoGenProvider, BackgroundResult
from app.infrastructure.providers.api_key_lookup import get_decrypted_key
from app.infrastructure.providers.storage.factory import get_storage_provider
from app.infrastructure.providers.storage.paths import new_tmp_path

_BASE_URL = "https://api.dev.runwayml.com/v1"
_API_VERSION = "2024-11-06"
_POLL_INTERVAL_SECONDS = 5
_POLL_TIMEOUT_SECONDS = 600

# veo3 only accepts these four ratios (no square option) and a fixed 8s duration.
_ASPECT_TO_RATIO = {"9:16": "720:1280", "1:1": "720:1280", "16:9": "1280:720"}


class RunwayVideoGenProvider(VideoGenProvider):
    """Real Runway adapter using the veo3 model via the public v1 API
    (api.dev.runwayml.com, not api.runwayml.com - that hostname 401s)."""

    name = "runway"

    async def generate_background(
        self, prompt: str, camera_notes: str, duration_seconds: float, aspect_ratio: str
    ) -> BackgroundResult:
        api_key = await get_decrypted_key("runway")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": _API_VERSION,
        }
        full_prompt = f"{prompt}. Camera: {camera_notes}" if camera_notes else prompt

        async with httpx.AsyncClient(timeout=60) as client:
            submit_response = await client.post(
                f"{_BASE_URL}/text_to_video",
                headers=headers,
                json={
                    "promptText": full_prompt,
                    "ratio": _ASPECT_TO_RATIO.get(aspect_ratio, "720:1280"),
                    "duration": 8,
                    "model": "veo3.1",
                },
            )
            if submit_response.status_code >= 400:
                raise RuntimeError(
                    f"Runway submit failed ({submit_response.status_code}): {submit_response.text}"
                )
            task_id = submit_response.json()["id"]

            elapsed = 0
            output_url = None
            while elapsed < _POLL_TIMEOUT_SECONDS:
                status_response = await client.get(f"{_BASE_URL}/tasks/{task_id}", headers=headers)
                status_response.raise_for_status()
                data = status_response.json()
                if data["status"] == "SUCCEEDED":
                    output_url = data["output"][0]
                    break
                if data["status"] == "FAILED":
                    raise RuntimeError(f"Runway generation failed: {data.get('failure')}")
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                elapsed += _POLL_INTERVAL_SECONDS

            if output_url is None:
                raise TimeoutError(f"Runway generation for task_id={task_id} timed out")

            download = await client.get(output_url)
            download.raise_for_status()

        tmp_path = new_tmp_path(".mp4")
        with open(tmp_path, "wb") as f:
            f.write(download.content)

        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"background/{uuid.uuid4()}.mp4")
        return BackgroundResult(video_url=url, duration_seconds=duration_seconds)
