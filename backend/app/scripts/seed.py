"""Load data/schemes.json into the database (idempotent). Overwrites scheme fields, rules and
sources for the ids in the file, so keep admin edits in the dataset file, or re-apply them."""
from app.core.database import SessionLocal


def main() -> None:
    import app.models  # noqa: F401
    from app.services.seed import seed_schemes

    db = SessionLocal()
    try:
        print(f"seeded {seed_schemes(db)} schemes")
    finally:
        db.close()


if __name__ == "__main__":
    main()
