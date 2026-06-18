-- ============================================================================
-- SENTRY memory store - canonical schema
-- Works unchanged on SQLite (local dev) and Postgres/Supabase (deployed).
-- This file is the schema of record; src/models.py is its SQLAlchemy mirror.
-- ============================================================================

CREATE TABLE events (
    -- identity ---------------------------------------------------------------
    id              INTEGER PRIMARY KEY AUTOINCREMENT,  -- internal row id
    source_id       TEXT,                                -- original CSV `id`
                                                           -- for historical rows;
                                                           -- NULL for live-logged events

    -- what kind of event this is ----------------------------------------------
    event_type      TEXT NOT NULL,        -- 'planned' | 'unplanned'
    event_cause     TEXT NOT NULL,        -- e.g. 'vehicle_breakdown', 'public_event'
    status          TEXT NOT NULL,        -- 'active' | 'resolved' | 'closed'
    source          TEXT NOT NULL,        -- 'historical' | 'live'
                                           -- 'historical' = seeded from the 8173-row
                                           -- CSV at setup time.
                                           -- 'live' = written through the API during
                                           -- the running demo. This is the column
                                           -- that proves "the system learns from
                                           -- what just happened" - it's the only
                                           -- structural difference between a seed
                                           -- row and a row your own demo created.

    -- where ---------------------------------------------------------------
    police_station  TEXT NOT NULL,        -- jurisdiction; the primary key half of
                                           -- the confidence lookup
    corridor        TEXT,                 -- nullable: 20 historical rows have no
                                           -- corridor recorded
    zone            TEXT,                 -- nullable: only ~42% of rows have this
    junction        TEXT,                 -- nullable: only ~31% of rows have this
    address         TEXT,
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,

    -- severity / handling ----------------------------------------------------
    priority               TEXT,          -- 'High' | 'Low'; nullable, 2 historical
                                           -- rows have neither
    requires_road_closure  BOOLEAN NOT NULL DEFAULT 0,

    -- free text ---------------------------------------------------------------
    description     TEXT,                 -- nullable: ~17% of historical rows
                                           -- have no description

    -- timing ---------------------------------------------------------------
    start_datetime    TEXT NOT NULL,       -- ISO 8601 string
    end_datetime      TEXT,               -- nullable
    closed_datetime   TEXT,               -- nullable: populated on <40% of rows
    resolved_datetime TEXT,               -- nullable: populated on <1% of rows
    duration_minutes  REAL,               -- computed at write time, see below;
                                           -- NULL when no reliable end timestamp
                                           -- exists yet (e.g. event still active)

    -- bookkeeping ---------------------------------------------------------------
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- This index is the whole point of the confidence feature: every read
-- (similar-event lookup) and every confidence calculation filters on this
-- exact pair, so it needs to be fast even as live writes accumulate during
-- the demo.
CREATE INDEX idx_events_station_cause ON events (police_station, event_cause);

-- Secondary index for the corridor-narrowed version of the same lookup.
CREATE INDEX idx_events_corridor_cause ON events (corridor, event_cause);

-- ============================================================================
-- How duration_minutes gets set (logic lives in src/memory_store.py, not SQL):
--   - on seed: end_datetime - start_datetime, only when end_datetime exists
--     AND is after start_datetime (3 historical rows have end before start -
--     those are data entry errors, left as NULL rather than a negative number)
--   - on a live write: NULL until the event is marked resolved/closed, at
--     which point it gets backfilled - this is the literal "outcome" that
--     becomes tomorrow's retrievable precedent
-- ============================================================================

-- ============================================================================
-- Confidence tiers (computed live via COUNT(*), not stored - see
-- src/confidence.py for why a materialized count table was deliberately
-- skipped). Thresholds are based on the real distribution across all 509
-- observed (police_station, event_cause) pairs in the historical data:
--   count == 0        -> "no_precedent"  (409 of 918 possible pairs - the
--                                          majority case is actually NO prior
--                                          example, not a rare edge case)
--   1  <= count <= 3   -> "thin"          (~41% of observed pairs)
--   4  <= count <= 15  -> "moderate"
--   count >= 16        -> "strong"        (e.g. Yelahanka + vehicle_breakdown
--                                          has 251 prior records)
-- ============================================================================