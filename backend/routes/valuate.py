"""POST /valuate — run the projection → SGP → dollar value pipeline.

The heavy lifting (pandas / scipy) is synchronous; we offload it to a thread
pool with anyio.to_thread.run_sync so the async event loop stays unblocked.
"""

import uuid
from typing import Any

import anyio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import current_active_user
from backend.db import get_db
from backend.models import LeagueConfig, SavedValuation, User
from backend.schemas import SavedValuationRead, ValuateRequest, ValuateResponse

router = APIRouter(prefix="/valuate", tags=["valuate"])

VALID_SOURCES = {"atc", "thebatx", "depthcharts"}


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/", response_model=ValuateResponse)
async def valuate(
    body: ValuateRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if body.projection_source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"projection_source must be one of {sorted(VALID_SOURCES)}",
        )

    # Resolve optional league config overrides
    sgp_overrides: dict[str, Any] = {}
    if body.league_config_id is not None:
        result = await db.execute(
            select(LeagueConfig).where(
                LeagueConfig.id == body.league_config_id,
                LeagueConfig.user_id == user.id,
            )
        )
        league_cfg = result.scalar_one_or_none()
        if league_cfg is None:
            raise HTTPException(status_code=404, detail="League config not found")
        sgp_overrides = {
            "n_teams": league_cfg.n_teams,
            "hitter_slots": league_cfg.hitter_slots,
            "pitcher_slots": league_cfg.pitcher_slots,
            "auction_budget_per_team": league_cfg.auction_budget,
        }

    # Run synchronous pipeline in threadpool
    players_data: list[dict] = await anyio.to_thread.run_sync(
        lambda: _run_pipeline(
            body.projection_source,
            body.season,
            sgp_overrides,
            body.force_refresh,
        )
    )

    # Persist
    valuation = SavedValuation(
        user_id=user.id,
        league_config_id=body.league_config_id,
        projection_source=body.projection_source,
        season=body.season,
        players=players_data,
    )
    db.add(valuation)
    await db.commit()
    await db.refresh(valuation)

    return ValuateResponse(
        id=valuation.id,
        projection_source=valuation.projection_source,
        season=valuation.season,
        created_at=valuation.created_at,
        players=players_data,
    )


@router.get("/", response_model=list[SavedValuationRead])
async def list_valuations(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedValuation)
        .where(SavedValuation.user_id == user.id)
        .order_by(SavedValuation.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        SavedValuationRead(
            id=r.id,
            projection_source=r.projection_source,
            season=r.season,
            created_at=r.created_at,
            league_config_id=r.league_config_id,
            player_count=len(r.players) if r.players else 0,
        )
        for r in rows
    ]


@router.get("/{valuation_id}", response_model=ValuateResponse)
async def get_valuation(
    valuation_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedValuation).where(
            SavedValuation.id == valuation_id,
            SavedValuation.user_id == user.id,
        )
    )
    valuation = result.scalar_one_or_none()
    if valuation is None:
        raise HTTPException(status_code=404, detail="Valuation not found")

    return ValuateResponse(
        id=valuation.id,
        projection_source=valuation.projection_source,
        season=valuation.season,
        created_at=valuation.created_at,
        players=valuation.players,
    )


# ── Synchronous pipeline (runs in threadpool) ─────────────────────────────────


def _run_pipeline(
    source: str,
    season: int,
    sgp_overrides: dict[str, Any],
    force_refresh: bool,
) -> list[dict]:
    """Fetch → transform → valuate. Returns serialisable list of player dicts."""
    import numpy as np

    from projections.fetch import fetch_projections
    from projections.transform import build_player_projections, fill_minor_leaguers
    from projections.valuate import compute_projected_values
    from sgp.config import SGPConfig

    config = SGPConfig.composite(**sgp_overrides) if sgp_overrides else SGPConfig.composite()

    MIN_PA = 25
    MIN_IP = 5

    # Map source name to FanGraphs system key
    _system_map = {
        "atc": "atc",
        "thebatx": "thebatx",
        "depthcharts": "fangraphsdc",
    }
    fg_system = _system_map[source]

    bat_raw = fetch_projections(fg_system, "bat", season=season, force_refresh=force_refresh)
    pit_raw = fetch_projections(fg_system, "pit", season=season, force_refresh=force_refresh)

    projections_df = build_player_projections(
        bat_raw, pit_raw, fg_system, min_pa=MIN_PA, min_ip=MIN_IP
    )

    # Fill minor leaguers from Depth Charts for ATC/THE BAT X
    if source != "depthcharts":
        dc_bat = fetch_projections("fangraphsdc", "bat", season=season, force_refresh=force_refresh)
        dc_pit = fetch_projections("fangraphsdc", "pit", season=season, force_refresh=force_refresh)
        if not dc_bat.empty and not dc_pit.empty:
            projections_df = fill_minor_leaguers(
                projections_df, dc_bat, dc_pit, min_pa=MIN_PA, min_ip=MIN_IP
            )

    valued_df = compute_projected_values(projections_df, config=config)

    # Serialise — keep only schema-relevant columns, replace NaN → None
    _COLS = [
        "player_name", "team", "pos_type", "position",
        "dollar_value", "par", "total_sgp",
        "PA", "AB", "IP",
        "R", "HR", "RBI", "SB", "AVG",
        "W", "SV", "ERA", "WHIP", "SO",
    ]
    available = [c for c in _COLS if c in valued_df.columns]
    records = (
        valued_df[available]
        .replace({np.nan: None})
        .to_dict(orient="records")
    )
    return records
