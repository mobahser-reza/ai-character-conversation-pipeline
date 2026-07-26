import uuid

from app.domain.interfaces.providers import TTSProvider, TTSResult
from app.infrastructure.providers.storage.factory import get_storage_provider


class LocalStubTTSProvider(TTSProvider):
    name = "local_stub"

    async def synthesize(self, text: str, voice_id: str, language: str) -> TTSResult:
        """Generates a silent placeholder wav so the pipeline runs end-to-end with zero external keys."""
        import wave

        duration = max(1.0, len(text.split()) * 0.4)
        tmp_path = f"/tmp/{uuid.uuid4()}.wav"
        framerate = 16000
        n_frames = int(duration * framerate)
        with wave.open(tmp_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(framerate)
            wav_file.writeframes(b"\x00\x00" * n_frames)

        storage = get_storage_provider()
        url = await storage.save(tmp_path, f"tts/{uuid.uuid4()}.wav")
        words = text.split()
        step = duration / max(1, len(words))
        timestamps = [
            {"word": w, "start": round(i * step, 2), "end": round((i + 1) * step, 2)}
            for i, w in enumerate(words)
        ]
        return TTSResult(audio_url=url, duration_seconds=duration, word_timestamps=timestamps)
