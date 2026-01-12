from sqlmodel import create_engine

from intentbid.app.core.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    echo=settings.env == "dev",
    connect_args=connect_args,
)
