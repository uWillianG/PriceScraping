from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from shopping_assistant.db.database import initialize_database
from shopping_assistant.dashboard.routes import router


initialize_database(settings.database_path)

app = FastAPI(title=settings.app_name)
app.mount(
    "/static",
    StaticFiles(directory="shopping_assistant/dashboard/static"),
    name="static",
)
app.include_router(router)
