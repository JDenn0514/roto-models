"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict

# ── Auth (fastapi-users) ──────────────────────────────────────────────────────


class UserRead(schemas.BaseUser[uuid.UUID]):
    created_at: datetime


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


# ── League configs ────────────────────────────────────────────────────────────

_DEFAULT_CATEGORIES = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]


class LeagueConfigCreate(BaseModel):
    name: str
    n_teams: int = 10
    hitter_slots: int = 15
    pitcher_slots: int = 11
    auction_budget: int = 360
    scoring_categories: list[str] = _DEFAULT_CATEGORIES


class LeagueConfigUpdate(BaseModel):
    name: Optional[str] = None
    n_teams: Optional[int] = None
    hitter_slots: Optional[int] = None
    pitcher_slots: Optional[int] = None
    auction_budget: Optional[int] = None
    scoring_categories: Optional[list[str]] = None


class LeagueConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    n_teams: int
    hitter_slots: int
    pitcher_slots: int
    auction_budget: int
    scoring_categories: list[str]
    created_at: datetime
    updated_at: datetime


# ── Valuations ────────────────────────────────────────────────────────────────


class ValuateRequest(BaseModel):
    projection_source: str = "atc"          # atc | thebatx | depthcharts
    season: int = 2026
    league_config_id: Optional[uuid.UUID] = None
    force_refresh: bool = False             # bypass FanGraphs 24h cache


class PlayerValuation(BaseModel):
    player_name: str
    team: Optional[str] = None
    pos_type: str                            # hitter | pitcher
    position: Optional[str] = None
    dollar_value: float
    par: float
    total_sgp: float
    # Volume stats
    PA: Optional[float] = None
    AB: Optional[float] = None
    IP: Optional[float] = None
    # Batting counting
    R: Optional[float] = None
    HR: Optional[float] = None
    RBI: Optional[float] = None
    SB: Optional[float] = None
    AVG: Optional[float] = None
    # Pitching
    W: Optional[float] = None
    SV: Optional[float] = None
    ERA: Optional[float] = None
    WHIP: Optional[float] = None
    SO: Optional[float] = None


class ValuateResponse(BaseModel):
    id: uuid.UUID
    projection_source: str
    season: int
    created_at: datetime
    players: list[PlayerValuation]


class SavedValuationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projection_source: str
    season: int
    created_at: datetime
    league_config_id: Optional[uuid.UUID] = None
    player_count: int
