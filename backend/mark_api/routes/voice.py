from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from mark_core.auth import get_current_user
from mark_core.events import publish_ws
from mark_core.models import User
from mark_voice.stt import transcribe_audio
from mark_voice.tts import synthesize_tts_bytes

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceChunk(BaseModel):
    audio: str
    format: str = "webm"


class SpeakBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.post("/transcribe")
async def transcribe(body: VoiceChunk, user: User = Depends(get_current_user)):
    text, final = await transcribe_audio(body.audio, body.format)
    await publish_ws(
        str(user.id),
        "voice.transcript",
        {"text": text, "final": final},
    )
    return {"text": text, "final": final}


@router.post("/speak")
async def speak(body: SpeakBody, user: User = Depends(get_current_user)):
    """Return full TTS audio in HTTP body (UI plays once — no duplicate WS stream)."""
    import base64

    audio_bytes = await synthesize_tts_bytes(body.text)
    audio = base64.b64encode(audio_bytes).decode("ascii") if audio_bytes else ""
    if audio:
        await publish_ws(
            str(user.id),
            "voice.audio",
            {"chunk": "", "format": "mp3", "done": True},
        )
    if not audio:
        from mark_core.config import get_settings

        settings = get_settings()
        if not settings.elevenlabs_api_key:
            return {
                "ok": False,
                "audio": "",
                "format": "mp3",
                "error": "ELEVENLABS_API_KEY is not configured",
            }
        return {"ok": False, "audio": "", "format": "mp3", "error": "TTS generation failed"}
    return {"ok": True, "audio": audio, "format": "mp3"}
