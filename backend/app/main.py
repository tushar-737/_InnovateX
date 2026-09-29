"""FastAPI application — Kaushal Saathi backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import conversation, meta, recommend, session as session_router

settings = get_settings()

# create_all is idempotent — do it at import so the app works even if a host
# never fires lifespan events (e.g. bare TestClient without context manager).
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    description=(
        "Voice-first livelihood mapping & NSQF-aligned skilling recommendations "
        "for SC communities under PM-AJAY (MoSJE) — SIH 2026 prototype. "
        "All seed data is ILLUSTRATIVE; nothing here is an official integration."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(meta.router, prefix="/api", tags=["meta"])
app.include_router(session_router.router, prefix="/api", tags=["session"])
app.include_router(conversation.router, prefix="/api", tags=["conversation"])
app.include_router(recommend.router, prefix="/api", tags=["recommend"])
