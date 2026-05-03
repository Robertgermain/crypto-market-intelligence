from typing import Optional
from datetime import datetime, timezone, timedelta
import json

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from app.deps import get_db
from app.services.market_data_service import ingest_market_data
from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal
from app.models.asset import Asset
from app.schemas.market import PricesResponse, SignalsResponse

from app.core.redis import redis_conn, task_queue
from app.workers.tasks import run_full_pipeline

router = APIRouter()


# --------------------------------------------------
# POST: Ingest Market Data
# --------------------------------------------------
@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_data(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        result = ingest_market_data(db, limit=limit)

        return {
            "status": "success",
            "message": "Market data ingested successfully",
            "data": {"inserted": len(result)},
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Database error", "error": str(e)},
        )


# --------------------------------------------------
# GET: Market Prices (AUTO-REFRESH + SAFE CACHE)
# --------------------------------------------------
@router.get("/prices", response_model=PricesResponse)
def get_prices(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    asset_id: Optional[int] = None,
):
    try:
        # =========================================================
        # STEP 1: CHECK STALENESS
        # =========================================================
        latest_price = (
            db.query(MarketPrice)
            .order_by(MarketPrice.observed_at.desc())
            .first()
        )

        is_stale = False

        if latest_price:
            age = datetime.now(timezone.utc) - latest_price.observed_at
            print(f"[DEBUG] Latest price age: {age}")

            if age > timedelta(seconds=60):
                is_stale = True

        # =========================================================
        # STEP 2: PREVENT QUEUE SPAM (LOCK)
        # =========================================================
        refresh_lock_key = "market:refresh:lock"

        if is_stale:
            # Only enqueue if no active refresh job
            if not redis_conn.get(refresh_lock_key):
                print("[AUTO-REFRESH] Queueing pipeline")

                task_queue.enqueue(run_full_pipeline)

                # Lock for 30 seconds
                redis_conn.setex(refresh_lock_key, 30, "1")
            else:
                print("[AUTO-REFRESH] Skipped (already running)")

        # =========================================================
        # STEP 3: REDIS CACHE (SKIP IF STALE)
        # =========================================================
        cache_key = f"prices:{limit}:{offset}:{asset_id or 'all'}"

        if not is_stale:
            cached = redis_conn.get(cache_key)

            if cached:
                print("[REDIS] Returning cached prices")

                try:
                    return json.loads(cached.decode("utf-8"))
                except Exception:
                    print("[WARN] Cache decode failed")

        else:
            # Bust stale cache immediately
            redis_conn.delete(cache_key)

        # =========================================================
        # STEP 4: QUERY DB (LATEST PER ASSET)
        # =========================================================
        subquery = (
            db.query(
                MarketPrice.asset_id,
                func.max(MarketPrice.observed_at).label("latest_time"),
            )
            .group_by(MarketPrice.asset_id)
            .subquery()
        )

        query = (
            db.query(MarketPrice, Asset)
            .join(
                subquery,
                (MarketPrice.asset_id == subquery.c.asset_id)
                & (MarketPrice.observed_at == subquery.c.latest_time),
            )
            .join(Asset, Asset.id == MarketPrice.asset_id)
        )

        if asset_id:
            query = query.filter(MarketPrice.asset_id == asset_id)

        total = query.count()

        prices = (
            query.order_by(Asset.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # =========================================================
        # STEP 5: BUILD RESPONSE
        # =========================================================
        response = {
            "status": "success",
            "message": "Market prices retrieved successfully",
            "data": [
                {
                    "id": p.id,
                    "asset_id": p.asset_id,
                    "symbol": a.symbol,
                    "price_usd": float(p.price_usd),
                    "observed_at": p.observed_at.isoformat(),
                }
                for p, a in prices
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "returned": len(prices),
            },
        }

        # =========================================================
        # STEP 6: CACHE RESPONSE (SHORT TTL)
        # =========================================================
        redis_conn.setex(cache_key, 15, json.dumps(response))

        return response

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Database error while fetching prices",
                "error": str(e),
            },
        )


# --------------------------------------------------
# GET: Market Signals
# --------------------------------------------------
@router.get("/signals", response_model=SignalsResponse)
def get_signals(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    asset_id: Optional[int] = None,
):
    try:
        query = db.query(MarketSignal)

        if asset_id:
            query = query.filter(MarketSignal.asset_id == asset_id)

        total = query.count()

        signals = (
            query.order_by(MarketSignal.detected_at.desc())
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
                    "metadata": s.signal_metadata,
                    "detected_at": s.detected_at,
                }
                for s in signals
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "returned": len(signals),
            },
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Database error while fetching signals",
                "error": str(e),
            },
        )