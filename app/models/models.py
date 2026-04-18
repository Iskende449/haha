import enum
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LocationCategory(str, enum.Enum):
    mazar = 'mazar'
    petroglyph = 'petroglyph'
    historical = 'historical'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    experience_points: Mapped[int] = mapped_column(Integer, default=0, server_default='0', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    progress: Mapped[list['UserProgress']] = relationship('UserProgress', back_populates='user', cascade='all, delete-orphan')


class Location(Base):
    __tablename__ = 'locations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[LocationCategory] = mapped_column(Enum(LocationCategory, name='location_category_enum'), nullable=False, index=True)
    geom: Mapped[object] = mapped_column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    progress: Mapped[list['UserProgress']] = relationship('UserProgress', back_populates='location', cascade='all, delete-orphan')


class UserProgress(Base):
    __tablename__ = 'user_progress'
    __table_args__ = (UniqueConstraint('user_id', 'location_id', name='uq_user_location_progress'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey('locations.id', ondelete='CASCADE'), nullable=False, index=True)
    legend_quest: Mapped[str | None] = mapped_column(Text, nullable=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped['User'] = relationship('User', back_populates='progress')
    location: Mapped['Location'] = relationship('Location', back_populates='progress')
