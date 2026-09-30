"""
Standalone seed script. Run with: python scripts/seed.py
Requires DATABASE_URL in env (sync postgresql:// URL).
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.base import Base
from app.models.asset import Asset
from app.models.price_history import PriceHistory


ATHLETES = [
    ("LeBron James", 150.0),
    ("Stephen Curry", 120.0),
    ("Kevin Durant", 110.0),
    ("Giannis Antetokounmpo", 140.0),
    ("Luka Doncic", 100.0),
    ("Mike Trout", 85.0),
    ("Shohei Ohtani", 130.0),
    ("Patrick Mahomes", 95.0),
    ("Ja Morant", 75.0),
    ("Nikola Jokic", 115.0),
]


async def seed():
    from app.core.config import get_settings
    settings = get_settings()
    url = settings.async_database_url

    engine = create_async_engine(url, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        result = await db.execute(select(Asset))
        existing = result.scalars().all()
        if existing:
            print(f"Database already has {len(existing)} assets. Skipping seed.")
            return

        for name, price in ATHLETES:
            asset = Asset(name=name, category="athlete", current_price=price)
            db.add(asset)
        await db.flush()

        result = await db.execute(select(Asset))
        for asset in result.scalars().all():
            ph = PriceHistory(asset_id=asset.id, price=asset.current_price)
            db.add(ph)
        await db.commit()
        print(f"Seeded {len(ATHLETES)} athlete assets.")


if __name__ == "__main__":
    asyncio.run(seed())
