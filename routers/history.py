"""
Routers for history endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db, User
from schemas import (
    HistoryListResponse,
    SaveHistoryRequest,
    HistoryEntryResponse,
    MessageResponse,
)
from services import HistoryService
from auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("", response_model=HistoryListResponse)
async def get_user_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's history of explained concepts.

    Returns paginated list of user's saved concept explanations.
    """
    entries, total = HistoryService.get_user_history(
        db, current_user.id.value, limit, offset
    )

    return HistoryListResponse(
        entries=[HistoryEntryResponse.model_validate(entry) for entry in entries],
        total=total,
    )


@router.post("", response_model=HistoryEntryResponse)
async def save_history_entry(
    history_data: SaveHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save a concept explanation to user's history.

    Allows authenticated users to save explanations for future reference.
    """
    try:
        entry = HistoryService.save_history_entry(
            db, current_user.id.value, history_data
        )
        return HistoryEntryResponse.model_validate(entry)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save history entry: {str(e)}",
        )


@router.delete("/{entry_id}", response_model=MessageResponse)
async def delete_history_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a history entry.

    Removes a specific history entry from the user's saved explanations.
    """
    success = HistoryService.delete_history_entry(db, entry_id, current_user.id.value)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="History entry not found"
        )

    return MessageResponse(message="History entry deleted successfully")
