import base64
import logging
from typing import AsyncIterator

logger = logging.getLogger("mark.voice.tts")

# British male JARVIS tone (ElevenLabs "Daniel")
DEFAULT_JARVIS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"


async def stream_tts(text: str) -> AsyncIterator[str]:
    """Stream TTS audio chunks as base64 (masculine JARVIS-style voice)."""
    settings = __import__("mark_core.config", fromlist=["get_settings"]).get_settings()

    if not settings.elevenlabs_api_key:
        yield ""
        return

    voice_id = settings.elevenlabs_voice_id or DEFAULT_JARVIS_VOICE_ID
    model_id = settings.elevenlabs_model_id or "eleven_turbo_v2_5"

    try:
        from elevenlabs import AsyncElevenLabs, VoiceSettings

        client = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)
        speed = max(0.7, min(1.25, settings.elevenlabs_speed))
        voice_settings = VoiceSettings(
            stability=settings.elevenlabs_stability,
            similarity_boost=settings.elevenlabs_similarity_boost,
            style=settings.elevenlabs_style,
            speed=speed,
            use_speaker_boost=True,
        )
        raw = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text[:2000],
            model_id=model_id,
            voice_settings=voice_settings,
            output_format="mp3_44100_128",
        )
        if hasattr(raw, "__await__"):
            raw = await raw
        if hasattr(raw, "__aiter__"):
            async for chunk in raw:
                if chunk:
                    yield base64.b64encode(chunk).decode()
        else:
            data = raw if isinstance(raw, bytes) else b""
            if not data:
                logger.warning("ElevenLabs TTS returned no audio bytes")
                yield ""
                return
            chunk_size = 4096
            for i in range(0, len(data), chunk_size):
                yield base64.b64encode(data[i : i + chunk_size]).decode()
    except Exception as e:
        logger.warning("ElevenLabs TTS failed: %s", e)
        yield ""


async def synthesize_tts_bytes(text: str) -> bytes:
    """Single MP3 payload for HTTP playback (avoids broken joined base64 chunks)."""
    chunks: list[bytes] = []
    async for b64 in stream_tts(text):
        if b64:
            try:
                chunks.append(base64.b64decode(b64, validate=True))
            except Exception:
                chunks.append(base64.b64decode(b64))
    return b"".join(chunks)
