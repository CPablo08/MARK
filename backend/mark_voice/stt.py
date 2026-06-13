import base64
import io
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger("mark.voice.stt")


async def transcribe_audio(audio_b64: str, audio_format: str = "webm") -> tuple[str, bool]:
    """Transcribe audio. Returns (text, is_final)."""
    settings = __import__("mark_core.config", fromlist=["get_settings"]).get_settings()
    audio_bytes = base64.b64decode(audio_b64)
    if len(audio_bytes) < 100:
        return "", False

    suffix = f".{audio_format}" if audio_format else ".webm"
    if suffix not in (".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mpeg", ".mpga"):
        suffix = ".webm"

    if settings.whisper_backend == "openai":
        if not settings.openai_api_key:
            logger.warning("WHISPER_BACKEND=openai requires OPENAI_API_KEY")
            return "", False
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        try:
            buf = io.BytesIO(audio_bytes)
            buf.name = f"audio{suffix}"
            resp = await client.audio.transcriptions.create(
                model="whisper-1",
                file=buf,
                response_format="text",
            )
            text = resp if isinstance(resp, str) else getattr(resp, "text", str(resp))
            return (text or "").strip(), True
        except Exception as e:
            logger.warning("OpenAI Whisper STT failed: %s", e)
            return "", False

    # Local whisper (requires `pip install openai-whisper` and ffmpeg on PATH)
    path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_bytes)
            path = f.name
        import whisper

        model = whisper.load_model(settings.whisper_model)
        result = model.transcribe(path)
        text = (result.get("text") or "").strip()
        return text, True
    except Exception as e:
        logger.warning("Local Whisper STT failed: %s", e)
        return "", False
    finally:
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
