import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, SessionLocal
from app import hardware
from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.auth import router as auth_router
from app.auth import service as auth_service
from app.routers import items, users, events, recommendations, admin

logger = logging.getLogger(__name__)

# ── Hardware backend ───────────────────────────────────────────────────────────

hardware.configure(settings.hardware_backend)

# ── Security warnings ──────────────────────────────────────────────────────────

if settings.disable_security:
    logger.warning(
        "DISABLE_SECURITY=true — JWT authentication and rate limiting are OFF. "
        "This is a sandbox mode intended for local development only. "
        "Never deploy with this setting enabled."
    )
else:  # pragma: no cover
    if settings.secret_key == "CHANGE_THIS_IN_PRODUCTION":
        logger.critical(
            "SECRET_KEY is set to the insecure default value. "
            "Generate a strong secret and set the SECRET_KEY environment variable "
            "before deploying to any non-local environment."
        )
    if settings.first_superuser_password == "changeme":
        logger.warning(
            "FIRST_SUPERUSER_PASSWORD is set to the default 'changeme'. "
            "Change it via the FIRST_SUPERUSER_PASSWORD environment variable."
        )

# ── Database ───────────────────────────────────────────────────────────────────

Base.metadata.create_all(bind=engine)


def _seed_superuser() -> None:
    """Create the default admin account if it does not exist yet."""
    db = SessionLocal()
    try:
        if not auth_service.get_user(db, settings.first_superuser):
            auth_service.create_user(
                db, settings.first_superuser, settings.first_superuser_password
            )
            db.commit()
            logger.info("Created default superuser: %s", settings.first_superuser)
    finally:
        db.close()


_seed_superuser()

# ── App description (sandbox banner when security is off) ──────────────────────

_description = settings.app_description
if settings.disable_security:
    _description = (
        "> ⚠️ **SANDBOX MODE** — Authentication is disabled (`DISABLE_SECURITY=true`). "
        "All endpoints are open. **Do not use in production.**\n\n"
        + _description
    )

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=_description,
    openapi_tags=settings.tags_metadata,
    contact={"name": "RecSys API"},
    license_info={"name": "MIT"},
)

# ── Middleware (last added = outermost = first to receive requests) ─────────────

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(auth_router.router)
app.include_router(items.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(recommendations.router)
app.include_router(admin.router)
