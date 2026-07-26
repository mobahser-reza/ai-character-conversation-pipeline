import uuid

import httpx

from app.domain.interfaces.providers import TTSProvider, TTSResult
from app.infrastructure.providers.api_key_lookup import get_decrypted_key
from app.infrastructure.providers.storage.factory import get_storage_provider
from app.infrastructure.providers.storage.paths import new_tmp_path

_BASE_URL = "https://api.elevenlabs.io/v1"


class ElevenLabsTTSProvider(TTSProvider):
    """Real ElevenLabs TTS adapter. Supports English/Hindi natively via ElevenLabs'
    multilingual models; Hinglish is passed through as-is since ElevenLabs handles
    code-mixed text reasonably well without extra preprocessing."""

    name = "elevenlabs"

    async def synthesize(self, text: str, voice_id: str, language: str) -> TTSResult:
        api_key = await get_decrypted_key("elevenlabs")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{_BASE_URL}/text-to-speech/{voice_id}/with-timestamps",
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
            )
            response.raise_for_status()
            payload = response.json()

        import base64

        audio_bytes = base64.b64decode(payload["audio_base64"])
        tmp_path = new_tmp_path(".mp3")
        with open(tmp_path, "wb") as f:
            f.write(audio_bytes)

        alignment = payload.get("alignment", {})
        chars = alignment.get("characters", [])
        starts = alignment.get("character_start_times_seconds", [])
        ends = alignment.get("character_end_times_seconds", [])
        duration = ends[-1] if ends else max(1.0, len(text.split()) * 0.4)

        word_timestamps = _characters_to_word_timestamps(chars, starts, ends)

        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"tts/{uuid.uuid4()}.mp3")
        return TTSResult(audio_url=url, duration_seconds=duration, word_timestamps=word_timestamps)


def _characters_to_word_timestamps(
    chars: list[str], starts: list[float], ends: list[float]
) -> list[dict]:
    words: list[dict] = []
    current_word = ""
    word_start = None
    for i, ch in enumerate(chars):
        if ch == " ":
            if current_word:
                words.append({"word": current_word, "start": word_start, "end": ends[i - 1]})
                current_word = ""
                word_start = None
            continue
        if word_start is None:
            word_start = starts[i]
        current_word += ch
    if current_word and word_start is not None:
        words.append({"word": current_word, "start": word_start, "end": ends[-1]})
    return words
