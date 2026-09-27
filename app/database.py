from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# SQLite needs check_same_thread=False for multi-threaded FastAPI workers;
# Postgres handles connections natively.
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine_kwargs = {"connect_args": connect_args}
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
        }
    )

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def check_db_connection() -> bool:
    """Verifies active connectivity to the database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
