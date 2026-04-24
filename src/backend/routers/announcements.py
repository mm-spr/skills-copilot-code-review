"""
Announcement endpoints for the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Announcement request payload."""

    title: str
    message: str
    expires_at: datetime
    start_date: Optional[datetime] = None


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a MongoDB announcement document into a JSON-safe payload."""
    return {
        "id": document["_id"],
        "title": document["title"],
        "message": document["message"],
        "start_date": document.get("start_date").isoformat() if document.get("start_date") else None,
        "expires_at": document["expires_at"].isoformat(),
        "created_at": document.get("created_at").isoformat() if document.get("created_at") else None,
        "updated_at": document.get("updated_at").isoformat() if document.get("updated_at") else None,
        "is_active": _is_active(document)
    }


def _require_signed_in_user(teacher_username: Optional[str]) -> Dict[str, Any]:
    """Require a signed-in teacher account for announcement management."""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _normalize_datetime(value: datetime) -> datetime:
    """Store all datetimes in UTC for predictable filtering."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_active(document: Dict[str, Any]) -> bool:
    """Check whether an announcement is currently visible."""
    now = datetime.now(timezone.utc)
    start_date = document.get("start_date")
    expires_at = document.get("expires_at")

    if start_date and _normalize_datetime(start_date) > now:
        return False

    return _normalize_datetime(expires_at) >= now


def _validate_payload(payload: AnnouncementPayload) -> Dict[str, Any]:
    """Validate and normalize announcement input."""
    title = payload.title.strip()
    message = payload.message.strip()
    expires_at = _normalize_datetime(payload.expires_at)
    start_date = _normalize_datetime(payload.start_date) if payload.start_date else None

    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    if start_date and start_date >= expires_at:
        raise HTTPException(status_code=400, detail="Start date must be before expiration date")

    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Expiration date must be in the future")

    return {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expires_at": expires_at
    }


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get the announcements that should currently be visible to everyone."""
    now = datetime.now(timezone.utc)
    query = {
        "$and": [
            {"expires_at": {"$gte": now}},
            {
                "$or": [
                    {"start_date": None},
                    {"start_date": {"$exists": False}},
                    {"start_date": {"$lte": now}}
                ]
            }
        ]
    }

    announcements = announcements_collection.find(query).sort([
        ("start_date", 1),
        ("expires_at", 1),
        ("created_at", -1)
    ])
    return [_serialize_announcement(document) for document in announcements]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements for the management dialog."""
    _require_signed_in_user(teacher_username)
    announcements = announcements_collection.find({}).sort([("created_at", -1)])
    return [_serialize_announcement(document) for document in announcements]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement."""
    _require_signed_in_user(teacher_username)
    normalized_payload = _validate_payload(payload)
    now = datetime.now(timezone.utc)

    announcement = {
        "_id": str(uuid4()),
        **normalized_payload,
        "created_at": now,
        "updated_at": now
    }
    announcements_collection.insert_one(announcement)
    return _serialize_announcement(announcement)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement."""
    _require_signed_in_user(teacher_username)
    normalized_payload = _validate_payload(payload)

    result = announcements_collection.update_one(
        {"_id": announcement_id},
        {"$set": {**normalized_payload, "updated_at": datetime.now(timezone.utc)}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    document = announcements_collection.find_one({"_id": announcement_id})
    return _serialize_announcement(document)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an announcement."""
    _require_signed_in_user(teacher_username)
    result = announcements_collection.delete_one({"_id": announcement_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}