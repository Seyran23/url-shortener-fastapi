import time
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.constants import HEALTH_PREFIX
from app.db.session import engine

router = APIRouter(prefix=HEALTH_PREFIX, tags=["health"])

START_TIME = time.monotonic()


@router.get("")
async def health_check() -> JSONResponse:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    payload = {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "uptime_seconds": round(time.monotonic() - START_TIME, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(
        status_code=200 if db_status == "ok" else 503, 
        content=payload
    )
