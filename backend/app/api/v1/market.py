from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.deps import get_db
from app.services.market_data_service import ingest_market_data
from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal

router = APIRouter()


# --------------------------------------------------
# POST: Ingest Market Data
# --------------------------------------------------
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

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Invalid data or external API issue",
                "error": str(e)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Unexpected server error",
                "error": str(e)
            }
        )


# --------------------------------------------------
# GET: Market Prices (WITH PAGINATION + FILTERS)
# --------------------------------------------------
@router.get(
    "/prices",
    status_code=status.HTTP_200_OK,
)
def get_prices(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    asset_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Retrieve market prices with pagination and filtering
    """
    try:
        query = db.query(MarketPrice)

        # -----------------------------
        # Filtering
        # -----------------------------
        if asset_id:
            query = query.filter(MarketPrice.asset_id == asset_id)

        if start_date:
            query = query.filter(MarketPrice.observed_at >= start_date)

        if end_date:
            query = query.filter(MarketPrice.observed_at <= end_date)

        # -----------------------------
        # Total count BEFORE pagination
        # -----------------------------
        total = query.count()

        # -----------------------------
        # Pagination + Sorting
        # -----------------------------
        prices = (
            query
            .order_by(MarketPrice.observed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "status": "success",
            "message": "Market prices retrieved successfully",
            "data": [
                {
                    "id": p.id,
                    "asset_id": p.asset_id,
                    "price_usd": float(p.price_usd),
                    "observed_at": p.observed_at,
                }
                for p in prices
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "returned": len(prices),
            }
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Database error occurred while fetching prices",
                "error": str(e)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Unexpected server error",
                "error": str(e)
            }
        )


# --------------------------------------------------
# GET: Market Signals (WITH PAGINATION + FILTERS)
# --------------------------------------------------
@router.get(
    "/signals",
    status_code=status.HTTP_200_OK,
)
def get_signals(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    asset_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Retrieve market signals with pagination and filtering
    """
    try:
        query = db.query(MarketSignal)

        # -----------------------------
        # Filtering
        # -----------------------------
        if asset_id:
            query = query.filter(MarketSignal.asset_id == asset_id)

        if start_date:
            query = query.filter(MarketSignal.detected_at >= start_date)

        if end_date:
            query = query.filter(MarketSignal.detected_at <= end_date)

        # -----------------------------
        # Total count
        # -----------------------------
        total = query.count()

        # -----------------------------
        # Pagination + Sorting
        # -----------------------------
        signals = (
            query
            .order_by(MarketSignal.detected_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "status": "success",
            "message": "Market signals retrieved successfully",
            "data": [
                {
                    "id": s.id,
                    "asset_id": s.asset_id,
                    "signal_type": s.signal_type,
                    "strength": float(s.strength),
                    "metadata": s.meta_data,
                    "detected_at": s.detected_at,
                }
                for s in signals
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "returned": len(signals),
            }
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Database error occurred while fetching signals",
                "error": str(e)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Unexpected server error",
                "error": str(e)
            }
        )