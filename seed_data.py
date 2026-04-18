"""
seed_data.py — наполнение таблицы locations начальными данными.

Запуск:
    python seed_data.py

Скрипт идемпотентен: если в таблице уже есть записи — ничего не делает.
Геометрия строится прямо в SQL через ST_SetSRID(ST_MakePoint(lon, lat), 4326),
чтобы не тащить зависимость на Shapely и избежать ручного WKB-кодирования.
"""

import asyncio
import sys
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Настраиваем PYTHONPATH-совместимый импорт (запуск из корня проекта)
from app.core.database import AsyncSessionLocal
from app.models.models import Location, LocationCategory


# ---------------------------------------------------------------------------
# Данные локаций
# ---------------------------------------------------------------------------
@dataclass
class LocationSeed:
    name: str
    description: str
    category: LocationCategory
    latitude: float
    longitude: float
    image_url: str | None = None


SEED_LOCATIONS: list[LocationSeed] = [
    LocationSeed(
        name="Саймалуу-Таш (Saimaluu Tash)",
        description=(
            "The largest collection of petroglyphs in Central Asia, located in the Fergana Range. "
            "It contains over 10,000 stones dating from the Bronze Age to the Middle Ages. "
            "A sacred high-mountain sanctuary where ancestors communicated with the heavens."
        ),
        category=LocationCategory.petroglyph,
        latitude=41.1831,
        longitude=73.8169,
        image_url="https://rockartcentralasia.com/wp-content/uploads/2021/08/saimaluu-tash-top.jpg",
    ),
    LocationSeed(
        name="Чолпон-Ата (Cholpon-Ata)",
        description=(
            "Open-air museum on the shore of Issyk-Kul. Key images include snow leopards, "
            "stags, and hunting scenes. Reflects the Scytho-Sakan animal style and nomadic cosmology."
        ),
        category=LocationCategory.petroglyph,
        latitude=42.6633,
        longitude=77.0683,
        image_url="https://rockartcentralasia.com/wp-content/uploads/2021/08/cholpon-ata-1.jpg",
    ),
    LocationSeed(
        name="Мазар Манжылы-Ата (Manjyly-Ata)",
        description=(
            "The Valley of Sacred Springs on the southern shore of Issyk-Kul. "
            "A place of healing and spiritual pilgrimage for centuries, where the Earth's breath is felt."
        ),
        category=LocationCategory.mazar,
        latitude=42.1764,
        longitude=76.2625,
        image_url="https://rockartcentralasia.com/wp-content/uploads/2021/08/manjyly-ata.jpg",
    ),
    LocationSeed(
        name="Арал (Aral) - Talas",
        description=(
            "Petroglyphs located in the Talas valley. Notable for depictions of chariots "
            "and complex geometric symbols of the ancient nomadic tribes."
        ),
        category=LocationCategory.petroglyph,
        latitude=42.5186,
        longitude=72.2314,
        image_url="https://rockartcentralasia.com/wp-content/uploads/2021/08/aral-talas.jpg",
    ),
    LocationSeed(
        name="Ак-Чункур (Ak-Chunkur)",
        description=(
            "A high-altitude cave with unique red ochre paintings. One of the few "
            "Paleolithic sites in the region, representing the dawn of human artistic expression."
        ),
        category=LocationCategory.petroglyph,
        latitude=42.1643,
        longitude=78.8924,
        image_url="https://rockartcentralasia.com/wp-content/uploads/2021/08/ak-chunkur.jpg",
    ),
]


# ---------------------------------------------------------------------------
# Вспомогательная функция — строит WKB-совместимое выражение через PostGIS
# ---------------------------------------------------------------------------
def make_point_expr(longitude: float, latitude: float):
    """
    Возвращает SQLAlchemy-выражение:
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)

    GeoAlchemy2 принимает это как значение geom-колонки.
    """
    return func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)


# ---------------------------------------------------------------------------
# Основная логика
# ---------------------------------------------------------------------------
async def seed_locations(session: AsyncSession) -> None:
    # Idempotency-check: считаем строки в таблице
    count_result = await session.execute(select(func.count()).select_from(Location))
    existing_count: int = count_result.scalar_one()

    if existing_count > 0:
        print(
            f"[seed] Таблица 'locations' уже содержит {existing_count} записей. "
            "Пропускаем вставку."
        )
        return

    print(f"[seed] Таблица пустая. Вставляем {len(SEED_LOCATIONS)} локаций...")

    for item in SEED_LOCATIONS:
        location = Location(
            name=item.name,
            description=item.description,
            category=item.category,
            # Геометрия через PostGIS-функции — работает на уровне SQL
            geom=make_point_expr(item.longitude, item.latitude),
            image_url=item.image_url,
        )
        session.add(location)

    await session.flush()   # Получаем id без закрытия транзакции
    await session.commit()

    # Читаем вставленные записи для подтверждения
    result = await session.execute(
        select(Location.id, Location.name, Location.category)
        .order_by(Location.id)
    )
    rows = result.all()

    print("\n[seed] Успешно вставлено:")
    print(f"  {'ID':<5} {'Категория':<15} {'Название'}")
    print("  " + "-" * 55)
    for row in rows:
        print(f"  {row.id:<5} {row.category.value:<15} {row.name}")


async def main() -> None:
    print("[seed] Подключение к БД...")
    try:
        async with AsyncSessionLocal() as session:
            await seed_locations(session)
    except Exception as exc:
        print(f"\n[seed] ОШИБКА: {exc}", file=sys.stderr)
        print(
            "\nПодсказка: убедитесь, что:\n"
            "  1. Docker-контейнер запущен:  docker compose up -d\n"
            "  2. Миграции применены:        alembic upgrade head\n"
            "  3. .env файл заполнен верно",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n[seed] Готово ✓")


if __name__ == "__main__":
    asyncio.run(main())
