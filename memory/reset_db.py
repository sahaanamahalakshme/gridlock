"""Utility to reset and recreate the database schema."""

import sys

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from memory.db import engine, init_db

from sqlalchemy import text


def reset():

    print("[1/3] Connecting to database...")

    with engine.connect() as conn:

        print("[2/3] Dropping events table if it exists...")

        conn.execute(text("DROP TABLE IF EXISTS events"))

        conn.commit()

        print("      Done.")

    print("[3/3] Recreating events table with correct schema...")

    init_db()

    print("      Done.")

    print()

    print("Table reset complete. Run seed_historical.py next.")


if __name__ == "__main__":

    reset()
