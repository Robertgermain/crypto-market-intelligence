from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.decision import Decision

router = APIRouter(prefix="/api/v1/decisions", tags=["Decisions"])


@router.get("/")
def get_decisions(db: Session = Depends(get_db)):
    return (
        db.query(Decision)
        .order_by(Decision.created_at.desc())
        .limit(50)
        .all()
    )