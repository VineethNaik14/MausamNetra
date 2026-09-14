"""Re-exports the DB session dependency for convenient importing in routes."""
from app.db.database import get_db_session

__all__ = ["get_db_session"]
