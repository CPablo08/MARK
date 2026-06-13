"""Skills API — camera frame upload for the Cam skill."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from mark_core.auth import get_current_user
from mark_core.models import User
from mark_skills.cam import get_latest_frame, store_frame

router = APIRouter()


class DetectionItem(BaseModel):
    class_name: str = Field(alias="class")
    score: float = 0.0
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None

    model_config = {"populate_by_name": True}


class CamFrameBody(BaseModel):
    image_base64: str
    width: int = 0
    height: int = 0
    detections: list[dict] = []


class CamFrameStatus(BaseModel):
    has_frame: bool
    updated_at: str | None = None
    detection_count: int = 0


@router.post("/cam/frame")
async def post_cam_frame(
    body: CamFrameBody,
    user: User = Depends(get_current_user),
):
    b64 = body.image_base64
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[-1]
    store_frame(
        str(user.id),
        image_base64=b64,
        detections=body.detections,
        width=body.width,
        height=body.height,
    )
    return {"ok": True}


@router.get("/cam/status", response_model=CamFrameStatus)
async def cam_status(user: User = Depends(get_current_user)):
    frame = get_latest_frame(str(user.id))
    if not frame:
        return CamFrameStatus(has_frame=False)
    return CamFrameStatus(
        has_frame=True,
        updated_at=frame.get("updated_at"),
        detection_count=len(frame.get("detections", [])),
    )
