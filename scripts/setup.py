import subprocess
import sys

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models.models import Location, LocationCategory


def run_cmd(command: list[str]) -> None:
    print(f'[setup] Running: {" ".join(command)}')
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise RuntimeError(f'Command failed: {" ".join(command)}')


SEED_LOCATIONS = [
    ('Saimaluu-Tash', 'Ancient alpine petroglyph sanctuary with over ten thousand rock carvings.', 'petroglyph', 41.1833, 73.8167),
    ('Burana Tower', '11th-century minaret complex of Balasagun on the Silk Road.', 'historical', 42.7467, 75.2500),
    ('Manjyly-Ata', 'Sacred valley of healing springs and pilgrimage paths near Issyk-Kul.', 'mazar', 42.1764, 76.2625),
    ('Cholpon-Ata Petroglyphs', 'Open-air stone archive of Scythian and Turkic symbols.', 'petroglyph', 42.6633, 77.0683),
    ('Tash-Rabat', 'Stone caravanserai in At-Bashy valley linked to trade and legends.', 'historical', 40.8247, 75.2975),
    ('Shah-Fazil Mausoleum', 'Karakhanid-era sacred complex in Jalal-Abad region.', 'mazar', 41.5007, 72.9762),
    ('Sulaiman-Too', 'UNESCO sacred mountain with shrines and cave worship heritage.', 'mazar', 40.5283, 72.8010),
    ('Uzgen Minaret', 'Medieval tower and mausoleums from the Karakhanid period.', 'historical', 40.7699, 73.3003),
    ('Rukh Ordo', 'Cultural-spiritual center preserving multi-faith memory of the region.', 'historical', 42.6485, 77.0945),
    ('San-Tash', 'Legendary memorial field tied to Manas-era warrior storytelling.', 'historical', 42.1906, 79.1628),
]


async def seed_locations() -> None:
    from sqlalchemy import text

    async with AsyncSessionLocal() as session:
        count = await session.execute(select(func.count()).select_from(Location))
        if count.scalar_one() >= 10:
            print('[setup] Locations already seeded, skipping.')
            return

        for name, desc, cat, lat, lon in SEED_LOCATIONS:
            location = Location(
                name=name,
                description=desc,
                category=LocationCategory(cat),
                geom=text(f'ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)'),
            )
            session.add(location)

        await session.commit()
        print('[setup] Seed completed with heritage locations.')


def main() -> None:
    run_cmd([sys.executable, '-m', 'alembic', 'upgrade', 'head'])

    import asyncio

    asyncio.run(seed_locations())


if __name__ == '__main__':
    main()
