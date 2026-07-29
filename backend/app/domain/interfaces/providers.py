from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio_url: str
    duration_seconds: float
    word_timestamps: list[dict]


class TTSProvider(ABC):
    name: str

    @abstractmethod
    async def synthesize(
        self, text: str, voice_id: str, language: str
    ) -> TTSResult:
        ...


@dataclass
class AvatarResult:
    video_url: str
    duration_seconds: float


class AvatarProvider(ABC):
    name: str

    @abstractmethod
    async def generate_clip(
        self,
        reference_image_url: str,
        audio_url: str,
        expression_tag: str | None,
        aspect_ratio: str,
    ) -> AvatarResult:
        ...


@dataclass
class BackgroundResult:
    video_url: str
    duration_seconds: float


class VideoGenProvider(ABC):
    name: str

    @abstractmethod
    async def generate_background(
        self,
        prompt: str,
        camera_notes: str,
        duration_seconds: float,
        aspect_ratio: str,
    ) -> BackgroundResult:
        ...


@dataclass
class SubtitleResult:
    srt_url: str


class SubtitleProvider(ABC):
    name: str

    @abstractmethod
    async def generate(
        self, lines: list[dict], language: str
    ) -> SubtitleResult:
        ...


class StorageProvider(ABC):
    name: str

    @abstractmethod
    async def save(self, local_path: str, key: str) -> str:
        """Persists a local file and returns a publicly resolvable URL."""

    @abstractmethod
    async def resolve(self, key: str) -> str:
        ...
