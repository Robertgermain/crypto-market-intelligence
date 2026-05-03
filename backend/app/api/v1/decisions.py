from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.deps import get_db
from app.models.decision import Decision
from app.models.asset import Asset
from app.schemas.decision import DecisionsResponse

router = APIRouter(prefix="/api/v1/decisions", tags=["Decisions"])


def clean_metadata(metadata: Optional[dict]) -> dict:
    """
    Remove legacy / null fields and ensure clean structure
    """
    if not metadata:
        return {}

    return {
        "signals": metadata.get("signals", []),
        "signal_count": metadata.get("signal_count", 0),
        "generated_at": metadata.get("generated_at"),
        "explanation": metadata.get("explanation"),
    }


@router.get(
    "/",
    response_model=DecisionsResponse,
    status_code=status.HTTP_200_OK,
)
def get_decisions(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    asset_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Retrieve decisions with pagination and filtering
    """
    try:
        query = (
            db.query(Decision, Asset)
            .join(Asset, Decision.asset_id == Asset.id)
        )

        # -----------------------------
        # Filtering
        # -----------------------------
        if asset_id:
            query = query.filter(Decision.asset_id == asset_id)

        if start_date:
            query = query.filter(Decision.created_at >= start_date)

        if end_date:
            query = query.filter(Decision.created_at <= end_date)

        # -----------------------------
        # Total count
        # -----------------------------
        total = query.count()

        # -----------------------------
        # Pagination + Sorting
        # -----------------------------
        decisions = (
            query
            .order_by(Decision.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # -----------------------------
        # Response formatting
        # -----------------------------
        data = []

        for d, a in decisions:
            cleaned_metadata = clean_metadata(d.decision_metadata)

            data.append({
                "id": d.id,
                "asset_id": d.asset_id,
                "symbol": a.symbol,
                "decision": d.decision,
                "confidence": d.confidence,
                "score": d.score,
                "metadata": cleaned_metadata,
                "created_at": d.created_at,
            })

        return {
            "status": "success",
            "message": "Decisions retrieved successfully",
            "data": data,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "returned": len(data),
            }
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Database error occurred while fetching decisions",
                "error": str(e),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Unexpected server error",
                "error": str(e),
            },
        )