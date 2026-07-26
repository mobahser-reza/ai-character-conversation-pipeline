import subprocess
import uuid

from app.domain.interfaces.providers import AvatarProvider, AvatarResult
from app.infrastructure.providers.storage.factory import get_storage_provider


class LocalStubAvatarProvider(AvatarProvider):
    name = "local_stub"

    async def generate_clip(
        self, reference_image_url: str, audio_url: str, expression_tag: str | None
    ) -> AvatarResult:
        """Renders a placeholder color-card clip standing in for a real lip-synced avatar clip."""
        duration = 3.0
        tmp_path = f"/tmp/{uuid.uuid4()}.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=indigo:s=720x1280:d={duration}",
                "-vf",
                f"drawtext=text='{(expression_tag or 'avatar')[:40]}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2",
                tmp_path,
            ],
            check=True,
            capture_output=True,
        )
        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"avatar/{uuid.uuid4()}.mp4")
        return AvatarResult(video_url=url, duration_seconds=duration)
