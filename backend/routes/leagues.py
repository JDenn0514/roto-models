"""CRUD endpoints for per-user league configurations."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import current_active_user
from backend.db import get_db
from backend.models import LeagueConfig, User
from backend.schemas import LeagueConfigCreate, LeagueConfigRead, LeagueConfigUpdate

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("/", response_model=list[LeagueConfigRead])
async def list_league_configs(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LeagueConfig).where(LeagueConfig.user_id == user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=LeagueConfigRead, status_code=status.HTTP_201_CREATED)
async def create_league_config(
    body: LeagueConfigCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    config = LeagueConfig(**body.model_dump(), user_id=user.id)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/{config_id}", response_model=LeagueConfigRead)
async def get_league_config(
    config_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned(config_id, user, db)


@router.patch("/{config_id}", response_model=LeagueConfigRead)
async def update_league_config(
    config_id: uuid.UUID,
    body: LeagueConfigUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    config = await _get_owned(config_id, user, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_league_config(
    config_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    config = await _get_owned(config_id, user, db)
    await db.delete(config)
    await db.commit()


async def _get_owned(
    config_id: uuid.UUID, user: User, db: AsyncSession
) -> LeagueConfig:
    result = await db.execute(
        select(LeagueConfig).where(
            LeagueConfig.id == config_id,
            LeagueConfig.user_id == user.id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(status_code=404, detail="League config not found")
    return config
