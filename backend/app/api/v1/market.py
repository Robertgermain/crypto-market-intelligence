from fastapi import APIRouter, Depends, status, HTTPException
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
# GET: Market Prices
# --------------------------------------------------
@router.get(
    "/prices",
    status_code=status.HTTP_200_OK,
)
def get_prices(db: Session = Depends(get_db)):
    """
    Retrieve all market prices
    """
    try:
        prices = db.query(MarketPrice).all()

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
            "count": len(prices)
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
# GET: Market Signals
# --------------------------------------------------
@router.get(
    "/signals",
    status_code=status.HTTP_200_OK,
)
def get_signals(db: Session = Depends(get_db)):
    """
    Retrieve all market signals
    """
    try:
        signals = db.query(MarketSignal).all()

        return {
            "status": "success",
            "message": "Market signals retrieved successfully",
            "data": [
                {
                    "id": s.id,
                    "asset_id": s.asset_id,
                    "signal_type": s.signal_type,
                    "strength": float(s.strength),
                    "metadata": s.meta_data,  # IMPORTANT: matches your DB fix
                    "detected_at": s.detected_at,
                }
                for s in signals
            ],
            "count": len(signals)
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