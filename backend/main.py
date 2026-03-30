"""Baseball Models — FastAPI backend entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import auth_backend, fastapi_users
from backend.db import create_tables
from backend.routes import leagues, valuate
from backend.schemas import UserCreate, UserRead, UserUpdate


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Baseball Models API",
    version="0.1.0",
    description=(
        "SGP/MSP valuation engine for rotisserie fantasy baseball. "
        "Wraps the existing Python model pipeline behind authenticated REST endpoints."
    ),
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# ALLOWED_ORIGINS env var is comma-separated; defaults to local Next.js dev server.
# On Render, set to your Vercel production URL (e.g. https://your-app.vercel.app).

_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth routes (fastapi-users) ───────────────────────────────────────────────

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# ── App routes ────────────────────────────────────────────────────────────────

app.include_router(leagues.router)
app.include_router(valuate.router)


# ── Health check ──────────────────────────────────────────────────────────────


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}
