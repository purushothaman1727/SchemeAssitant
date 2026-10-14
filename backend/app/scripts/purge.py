"""Delete expired stored data. Run daily (cron / `docker compose run --rm backend python -m app.scripts.purge`)."""
from app.core.database import SessionLocal
from app.services.retention import purge_expired


def main() -> None:
    import app.models  # noqa: F401

    db = SessionLocal()
    try:
        print(purge_expired(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
