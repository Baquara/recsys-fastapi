from fastapi import FastAPI
from app.config import settings
from app.database import Base, engine
from app.routers import items, users, events, recommendations, admin

# Create DB tables that don't exist yet (e.g. events)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
    openapi_tags=settings.tags_metadata,
    contact={"name": "RecSys API"},
    license_info={"name": "MIT"},
)

app.include_router(items.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(recommendations.router)
app.include_router(admin.router)
