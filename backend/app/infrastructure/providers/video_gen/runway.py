import asyncio
import uuid

import httpx

from app.domain.interfaces.providers import VideoGenProvider, BackgroundResult
from app.infrastructure.providers.api_key_lookup import get_decrypted_key
from app.infrastructure.providers.storage.factory import get_storage_provider
from app.infrastructure.providers.storage.paths import new_tmp_path

_BASE_URL = "https://api.runwayml.com/v1"
_POLL_INTERVAL_SECONDS = 5
_POLL_TIMEOUT_SECONDS = 600

_ASPECT_TO_RATIO = {"9:16": "768:1344", "1:1": "1024:1024", "16:9": "1344:768"}


class RunwayVideoGenProvider(VideoGenProvider):
    """Real Runway adapter (Gen-3/4 text-to-video). Verify endpoint/model names against
    current Runway API docs before relying on this in production."""

    name = "runway"

    async def generate_background(
        self, prompt: str, camera_notes: str, duration_seconds: float, aspect_ratio: str
    ) -> BackgroundResult:
        api_key = await get_decrypted_key("runway")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        full_prompt = f"{prompt}. Camera: {camera_notes}" if camera_notes else prompt

        async with httpx.AsyncClient(timeout=60) as client:
            submit_response = await client.post(
                f"{_BASE_URL}/text_to_video",
                headers=headers,
                json={
                    "promptText": full_prompt,
                    "ratio": _ASPECT_TO_RATIO.get(aspect_ratio, "768:1344"),
                    "duration": min(10, max(4, round(duration_seconds))),
                },
            )
            submit_response.raise_for_status()
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
