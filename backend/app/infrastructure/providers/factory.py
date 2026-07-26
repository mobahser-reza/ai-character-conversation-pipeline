from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.providers import (
    AvatarProvider,
    SubtitleProvider,
    TTSProvider,
    VideoGenProvider,
)
from app.infrastructure.db.models import Capability, ProviderConfig

_TTS_REGISTRY: dict[str, type[TTSProvider]] = {}
_AVATAR_REGISTRY: dict[str, type[AvatarProvider]] = {}
_VIDEO_GEN_REGISTRY: dict[str, type[VideoGenProvider]] = {}
_SUBTITLE_REGISTRY: dict[str, type[SubtitleProvider]] = {}


def _load_registries() -> None:
    if _TTS_REGISTRY:
        return

    from app.infrastructure.providers.tts.local_stub import LocalStubTTSProvider
    from app.infrastructure.providers.avatar.local_stub import LocalStubAvatarProvider
    from app.infrastructure.providers.video_gen.local_stub import LocalStubVideoGenProvider
    from app.infrastructure.providers.subtitles.local_stub import LocalStubSubtitleProvider

    _TTS_REGISTRY["local_stub"] = LocalStubTTSProvider
    _AVATAR_REGISTRY["local_stub"] = LocalStubAvatarProvider
    _VIDEO_GEN_REGISTRY["local_stub"] = LocalStubVideoGenProvider
    _SUBTITLE_REGISTRY["local_stub"] = LocalStubSubtitleProvider

    try:
        from app.infrastructure.providers.tts.elevenlabs import ElevenLabsTTSProvider

        _TTS_REGISTRY["elevenlabs"] = ElevenLabsTTSProvider
    except ImportError:
        pass

    try:
        from app.infrastructure.providers.avatar.heygen import HeyGenAvatarProvider

        _AVATAR_REGISTRY["heygen"] = HeyGenAvatarProvider
    except ImportError:
        pass

    try:
        from app.infrastructure.providers.video_gen.runway import RunwayVideoGenProvider

        _VIDEO_GEN_REGISTRY["runway"] = RunwayVideoGenProvider
    except ImportError:
        pass


_REGISTRIES = {
    Capability.tts: lambda: _TTS_REGISTRY,
    Capability.avatar: lambda: _AVATAR_REGISTRY,
    Capability.video_gen: lambda: _VIDEO_GEN_REGISTRY,
    Capability.subtitles: lambda: _SUBTITLE_REGISTRY,
}


class ProviderFactory:
    """Resolves the active provider implementation for a capability.

    Adding a new provider = new adapter file + one line in _load_registries().
    No other code changes required (Open/Closed principle).
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        _load_registries()

    async def get(self, capability: Capability):
        result = await self.db.execute(
            select(ProviderConfig).where(
                ProviderConfig.capability == capability, ProviderConfig.is_default.is_(True)
            )
        )
        config = result.scalar_one_or_none()
        provider_name = config.provider_name if config else "local_stub"

        registry = _REGISTRIES[capability]()
        provider_cls = registry.get(provider_name)
        if provider_cls is None:
            provider_cls = registry["local_stub"]
        return provider_cls()
