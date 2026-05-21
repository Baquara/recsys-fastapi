import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories import item_repository, user_repository, event_repository
from app.services import system_service
from app.schemas.recommendation import SystemInfo
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

_DB_PATH = os.path.abspath(
    settings.database_url.replace("sqlite:///", "").replace("./", "")
)


@router.delete(
    "/database",
    summary="Wipe all tables",
    description=(
        "Deletes **all rows** from every table (`items`, `users`, `events`). "
        "The table schema is preserved.\n\n"
        "> ⚠️ This action is **irreversible**. Use only in test/dev environments."
    ),
)
def clear_database(db: Session = Depends(get_db)):
    item_repository.clear(db)
    user_repository.clear(db)
    event_repository.clear(db)
    return {"detail": "All tables cleared successfully"}


@router.get(
    "/system",
    response_model=SystemInfo,
    summary="Server resource usage",
    description=(
        "Returns real-time server diagnostics:\n\n"
        "| Field | Description |\n"
        "|---|---|\n"
        "| `uptime` | How long the server has been running |\n"
        "| `total_ram_mb` | Total RAM in MB |\n"
        "| `available_ram_mb` | Available (free) RAM in MB |\n"
        "| `cpu_model` | CPU model name |\n"
        "| `cpu_clock_mhz` | CPU clock speed in MHz |\n"
        "| `database_size` | Size of the SQLite database file on disk |"
    ),
)
def system_info():
    return system_service.get_system_info(_DB_PATH)
