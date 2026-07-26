import subprocess
import uuid

from app.domain.interfaces.providers import VideoGenProvider, BackgroundResult
from app.infrastructure.providers.storage.factory import get_storage_provider

_ASPECT_TO_SIZE = {"9:16": "720x1280", "1:1": "1080x1080", "16:9": "1280x720"}


class LocalStubVideoGenProvider(VideoGenProvider):
    name = "local_stub"

    async def generate_background(
        self, prompt: str, camera_notes: str, duration_seconds: float, aspect_ratio: str
    ) -> BackgroundResult:
        """Renders a placeholder gradient clip standing in for a generated background scene."""
        size = _ASPECT_TO_SIZE.get(aspect_ratio, "720x1280")
        tmp_path = f"/tmp/{uuid.uuid4()}.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=steelblue:s={size}:d={duration_seconds}",
                "-vf",
                f"drawtext=text='{prompt[:40]}':fontcolor=white:fontsize=28:x=(w-text_w)/2:y=40",
                tmp_path,
            ],
            check=True,
            capture_output=True,
        )
        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"background/{uuid.uuid4()}.mp4")
        return BackgroundResult(video_url=url, duration_seconds=duration_seconds)
