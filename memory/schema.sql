
CREATE TABLE events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,  
    source_id       TEXT,           

    event_type      TEXT NOT NULL,        
    event_cause     TEXT NOT NULL,        
    status          TEXT NOT NULL,        
    source          TEXT NOT NULL,        

    police_station  TEXT NOT NULL,        
    corridor        TEXT,                 
    zone            TEXT,                 
    junction        TEXT,                 
    address         TEXT,
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,

    priority               TEXT,          
    requires_road_closure  BOOLEAN NOT NULL DEFAULT 0,
    description     TEXT,                 
    start_datetime    TEXT NOT NULL,       
    end_datetime      TEXT,               
    closed_datetime   TEXT,              
    resolved_datetime TEXT,               
    duration_minutes  REAL,               

    is_scenario     BOOLEAN NOT NULL DEFAULT 0,
    explanation     TEXT,
    manpower_tier   TEXT,

    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_station_cause ON events (police_station, event_cause);
CREATE INDEX idx_events_corridor_cause ON events (corridor, event_cause);
