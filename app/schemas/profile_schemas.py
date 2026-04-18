from datetime import datetime

from pydantic import BaseModel

from app.schemas.auth import UserResponse


class ProfileUnlockedLegend(BaseModel):
    location_id: int
    location_name: str
    category: str
    image_url: str | None = None
    legend_quest: str | None = None
    unlocked_at: datetime


class ProfileStats(BaseModel):
    experience_points: int
    unlocked_legends: int


class ProfileResponse(BaseModel):
    user: UserResponse
    stats: ProfileStats
    unlocked_legends: list[ProfileUnlockedLegend]
