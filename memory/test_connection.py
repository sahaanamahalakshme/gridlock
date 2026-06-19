"""Simple script to test database connectivity."""

import sys
from memory.db import DATABASE_URL, engine, init_db
from sqlalchemy import text, inspect


def main():
    print(
        f"[1/3] DATABASE_URL points to: {(DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL)}"
    )
    if DATABASE_URL.startswith("sqlite"):
        print("      WARNING: this is still the local SQLite fallback.")
        print("      Check that memory/.env exists and DATABASE_URL is set,")
        print("      and that you're running this script from inside memory/.")
        sys.exit(1)
    print("      OK - using Postgres/Supabase.")
    print("[2/3] Testing raw connection (SELECT 1) ...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("      OK - connection and auth succeeded.")
    except Exception as e:
        print(f"      FAILED: {e}")
        print("      Common causes: wrong password, wrong port (use 6543 for the")
        print("      pooled connection, not 5432), or project paused in Supabase")
        print("      (free-tier projects pause after inactivity - open the Supabase")
        print("      dashboard once to wake it before running this again).")
        sys.exit(1)
    print("[3/3] Creating events table if missing, then verifying ...")
    init_db()
    inspector = inspect(engine)
    if "events" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("events")]
        print(f"      OK - 'events' table exists with {len(cols)} columns.")
    else:
        print("      FAILED: init_db() ran but 'events' table not found.")
        sys.exit(1)
    print("\nAll checks passed. Safe to run seed_historical.py next.")


if __name__ == "__main__":
    main()
