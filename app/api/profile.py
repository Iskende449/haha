from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import Location, User, UserProgress
from app.schemas.auth import UserResponse
from app.schemas.profile_schemas import ProfileResponse, ProfileStats, ProfileUnlockedLegend

router = APIRouter(prefix='/profile', tags=['profile'])


@router.get('', response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    result = await db.execute(
        select(UserProgress, Location)
        .join(Location, Location.id == UserProgress.location_id)
        .where(UserProgress.user_id == current_user.id)
        .order_by(UserProgress.unlocked_at.desc())
    )

    unlocked_legends = [
        ProfileUnlockedLegend(
            location_id=location.id,
            location_name=location.name,
            category=location.category.value,
            image_url=location.image_url,
            legend_quest=progress.legend_quest,
            unlocked_at=progress.unlocked_at,
        )
        for progress, location in result.all()
    ]

    return ProfileResponse(
        user=UserResponse.model_validate(current_user),
        stats=ProfileStats(
            experience_points=current_user.experience_points,
            unlocked_legends=len(unlocked_legends),
        ),
        unlocked_legends=unlocked_legends,
    )
