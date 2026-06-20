"""

SQLAlchemy mirror of schema.sql. Keep these two files in sync by hand -

schema.sql is the document you'd show a judge or teammate; this is what

the code actually runs against. Works unchanged against SQLite (dev) and

Postgres/Supabase (deployed) because nothing here is dialect-specific.

"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index

from sqlalchemy.orm import declarative_base

from datetime import datetime


Base = declarative_base()


class Event(Base):

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_id = Column(String, nullable=True)

    event_type = Column(String, nullable=False)

    event_cause = Column(String, nullable=False)

    status = Column(String, nullable=False)

    source = Column(String, nullable=False)

    police_station = Column(String, nullable=False)

    corridor = Column(String, nullable=True)

    zone = Column(String, nullable=True)

    junction = Column(String, nullable=True)

    address = Column(String, nullable=True)

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)

    priority = Column(String, nullable=True)

    requires_road_closure = Column(Boolean, nullable=False, default=False)

    description = Column(Text, nullable=True)

    start_datetime = Column(DateTime, nullable=False)

    end_datetime = Column(DateTime, nullable=True)

    closed_datetime = Column(DateTime, nullable=True)

    resolved_datetime = Column(DateTime, nullable=True)

    duration_minutes = Column(Float, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    spike_ratio = Column(Float, nullable=True)

    spike_label = Column(String, nullable=True)

    is_hotspot = Column(Boolean, nullable=True)

    hotspot_tier = Column(String, nullable=True)

    route_to = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_events_station_cause", "police_station", "event_cause"),
        Index("idx_events_corridor_cause", "corridor", "event_cause"),
    )

    def to_dict(self):

        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
