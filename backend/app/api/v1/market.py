from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.deps import get_db
from app.services.market_data_service import ingest_market_data

router = APIRouter()


@router.post(
    "/ingest",
    status_code=status.HTTP_201_CREATED,
)
def ingest_data(db: Session = Depends(get_db)):
    """
    Trigger market data ingestion
    """
    try:
        result = ingest_market_data(db, ["bitcoin", "ethereum"])

        return {
            "status": "success",
            "message": "Market data ingested successfully",
            "data": {
                "inserted": len(result)
            }
        }

    # -------------------------------
    # Database Errors
    # -------------------------------
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Database error occurred",
                "error": str(e)
            }
        )

    # -------------------------------
    # External API / Logic Errors
    # -------------------------------
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Invalid data or external API issue",
                "error": str(e)
            }
        )

    # -------------------------------
    # Catch-All (Safety Net)
    # -------------------------------
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Unexpected server error",
                "error": str(e)
            }
        )