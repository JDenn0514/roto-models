"""SQLAlchemy ORM models: User, LeagueConfig, SavedValuation."""

import uuid
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base

# ── Users (managed by fastapi-users) ─────────────────────────────────────────


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    league_configs: Mapped[list["LeagueConfig"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    saved_valuations: Mapped[list["SavedValuation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ── League configs ────────────────────────────────────────────────────────────

_DEFAULT_CATEGORIES = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]


class LeagueConfig(Base):
    __tablename__ = "league_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        pg_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        pg_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # League structure (mirrors SGPConfig fields)
    n_teams: Mapped[int] = mapped_column(Integer, default=10)
    hitter_slots: Mapped[int] = mapped_column(Integer, default=15)
    pitcher_slots: Mapped[int] = mapped_column(Integer, default=11)
    auction_budget: Mapped[int] = mapped_column(Integer, default=360)
    scoring_categories: Mapped[list] = mapped_column(
        JSON, default=lambda: list(_DEFAULT_CATEGORIES)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="league_configs")
    saved_valuations: Mapped[list["SavedValuation"]] = relationship(
        back_populates="league_config"
    )


# ── Saved valuations ──────────────────────────────────────────────────────────


class SavedValuation(Base):
    __tablename__ = "saved_valuations"

    id: Mapped[uuid.UUID] = mapped_column(
        pg_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        pg_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    league_config_id: Mapped[uuid.UUID | None] = mapped_column(
        pg_UUID(as_uuid=True),
        ForeignKey("league_configs.id", ondelete="SET NULL"),
        nullable=True,
    )
    projection_source: Mapped[str] = mapped_column(String(50), nullable=False)
    season: Mapped[int] = mapped_column(Integer, default=2026)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Full player valuation records serialised as JSON array
    players: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship(back_populates="saved_valuations")
    league_config: Mapped["LeagueConfig | None"] = relationship(
        back_populates="saved_valuations"
    )
