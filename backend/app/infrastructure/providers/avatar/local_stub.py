import subprocess
import uuid

import httpx

from app.domain.interfaces.providers import AvatarProvider, AvatarResult
from app.infrastructure.providers.storage.factory import get_storage_provider

_ASPECT_TO_SIZE = {"9:16": "720x1280", "1:1": "1080x1080", "16:9": "1280x720"}


class LocalStubAvatarProvider(AvatarProvider):
    name = "local_stub"

    async def generate_clip(
        self, reference_image_url: str, audio_url: str, expression_tag: str | None, aspect_ratio: str
    ) -> AvatarResult:
        """Renders a placeholder color-card clip with the real TTS audio muxed in, standing in
        for a real lip-synced avatar clip (which would bake the same audio into its output)."""
        audio_path = f"/tmp/{uuid.uuid4()}.mp3"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(audio_url)
            response.raise_for_status()
        with open(audio_path, "wb") as f:
            f.write(response.content)

        tmp_path = f"/tmp/{uuid.uuid4()}.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=indigo:s={_ASPECT_TO_SIZE.get(aspect_ratio, '720x1280')}",
                "-i",
                audio_path,
                "-vf",
                f"drawtext=text='{(expression_tag or 'avatar')[:40]}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2",
                "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1",
                "-c:a", "aac",
                "-shortest",
                tmp_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"avatar/{uuid.uuid4()}.mp4")
        return AvatarResult(video_url=url, duration_seconds=0.0)
