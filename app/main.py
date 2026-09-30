from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api import admin, analytics, assets, auth, execution_plans, ml, me as me_router, portfolio, strategies, trade
from app.core.config import get_settings
from app.db.session import async_session_maker
from app.models.asset import Asset
from app.models.price_history import PriceHistory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.seed_on_startup:
        async with async_session_maker() as db:
            result = await db.execute(select(Asset))
            assets_list = result.scalars().all()
            if not assets_list:
                from app.api.admin import ATHLETES
                for name, price in ATHLETES:
                    a = Asset(name=name, category="athlete", current_price=price)
                    db.add(a)
                await db.flush()
                result = await db.execute(select(Asset))
                for asset in result.scalars().all():
                    ph = PriceHistory(asset_id=asset.id, price=asset.current_price)
                    db.add(ph)
                await db.commit()
    yield


app = FastAPI(title="StarMarket API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(me_router.router)
api_router.include_router(assets.router)
api_router.include_router(portfolio.router)
api_router.include_router(trade.router)
api_router.include_router(admin.router)
api_router.include_router(analytics.router)
api_router.include_router(ml.router)
api_router.include_router(strategies.router)
api_router.include_router(execution_plans.router)
app.include_router(api_router)


# Serve the built frontend (frontend/dist) if it exists. Guarded so backend-only
# dev/tests never require a frontend build to be present.
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="spa-assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST.resolve()):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
