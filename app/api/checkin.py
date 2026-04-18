from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Location, User, UserProgress
from app.schemas.route_schemas import CheckinRequest, CheckinResponse
from app.services.ai_service import ai_service

router = APIRouter(prefix='/checkin', tags=['checkin'])


@router.post('', response_model=CheckinResponse)
async def checkin(
    body: CheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckinResponse:
    location_result = await db.execute(select(Location).where(Location.id == body.location_id))
    location = location_result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Location not found')

    user_geog = func.ST_GeogFromText(f'SRID=4326;POINT({body.user_lon} {body.user_lat})')
    within_result = await db.execute(
        select(func.ST_DWithin(func.ST_Geography(Location.geom), user_geog, settings.CHECKIN_RADIUS_METERS)).where(
            Location.id == body.location_id
        )
    )

    if not bool(within_result.scalar_one()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Check-in allowed only within {settings.CHECKIN_RADIUS_METERS} meters',
        )

    existing_result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.location_id == body.location_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return CheckinResponse(
            status='success',
            message='Location already checked in. Ancestors remember your visit.',
            experience_points=current_user.experience_points,
            legend_quest=existing.legend_quest,
        )

    # Generate or retrieve quest first
    legend_quest, expected_answer = await ai_service.generate_legend_quest_with_answer(
        location.name,
        location.description,
    )

    # If no answer provided, return the quest to the user
    if not body.legend_answer:
        return CheckinResponse(
            status='pending_quest',
            message='To unlock the secrets of this place, you must solve the Legend Quest.',
            experience_points=current_user.experience_points,
            legend_quest=legend_quest,
        )

    normalized_answer = (body.legend_answer or '').strip().lower()
    # Check if answer contains the key word (fuzzy match simpler for demo)
    if expected_answer not in normalized_answer and normalized_answer not in expected_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'The spirits say this is not the right word. Listen to the legend again: {legend_quest}',
        )

    progress = UserProgress(
        user_id=current_user.id,
        location_id=location.id,
        legend_quest=legend_quest,
    )

    current_user.experience_points += settings.CHECKIN_XP_REWARD
    db.add(progress)
    await db.commit()
    await db.refresh(current_user)

    return CheckinResponse(
        status='success',
        message='Success! You have unlocked a new petroglyph achievement in your profile.',
        experience_points=current_user.experience_points,
        legend_quest=legend_quest,
    )
