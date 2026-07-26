import uuid

from app.domain.interfaces.providers import SubtitleProvider, SubtitleResult
from app.infrastructure.providers.storage.factory import get_storage_provider


def _srt_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    h, rem = divmod(millis, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class LocalStubSubtitleProvider(SubtitleProvider):
    name = "local_stub"

    async def generate(self, lines: list[dict], language: str) -> SubtitleResult:
        entries = []
        for idx, line in enumerate(lines, start=1):
            entries.append(
                f"{idx}\n"
                f"{_srt_timestamp(line['start'])} --> {_srt_timestamp(line['end'])}\n"
                f"{line['text']}\n"
            )
        srt_content = "\n".join(entries)
        tmp_path = f"/tmp/{uuid.uuid4()}.srt"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"subtitles/{uuid.uuid4()}.srt")
        return SubtitleResult(srt_url=url)
