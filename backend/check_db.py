"""Read-only database check. Run it from the backend folder: python check_db.py

It connects, runs two SELECT queries, and prints whether the connection works
and which tables exist. It does not change anything and prints no credentials.
"""

from sqlalchemy import text

from peerora.database import get_engine


def main() -> None:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = (
                connection.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' ORDER BY table_name"
                    )
                )
                .scalars()
                .all()
            )
    except Exception as error:
        # Only the type of the error is printed, because error texts can
        # contain connection details.
        print("Database connection: FAILED")
        print("Error type:", type(error).__name__)
        return

    print("Database connection: OK")
    print("Tables in schema 'public':", ", ".join(tables) if tables else "(none)")
    print("'tutors' table exists:", "tutors" in tables)


if __name__ == "__main__":
    main()