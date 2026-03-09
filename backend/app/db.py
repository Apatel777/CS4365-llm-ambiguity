from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings


settings = get_settings()
engine = create_engine(settings.database_url, future=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class ApiCache(Base):
    __tablename__ = "api_cache"

    key = Column(String(255), primary_key=True)
    source = Column(String(64), nullable=False)
    url = Column(Text, nullable=False)
    response_json = Column(JSON, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class TeamFeature(Base):
    __tablename__ = "team_features"

    feature_id = Column(String(255), primary_key=True)
    season = Column(Integer, nullable=False, index=True)
    team_id = Column(String(32), nullable=False, index=True)
    team_name = Column(String(128), nullable=False)
    conference = Column(String(32), nullable=False)
    region = Column(String(32), nullable=False)
    early_rank = Column(Float, nullable=False)
    projected_end_rank = Column(Float, nullable=False)
    actual_end_rank = Column(Float, nullable=False)
    trajectory_score = Column(Float, nullable=False)
    volatility_score = Column(Float, nullable=False)
    adj_em = Column(Float, nullable=False)
    adj_o = Column(Float, nullable=False)
    adj_d = Column(Float, nullable=False)
    rank_trajectory = Column(JSON, nullable=False)
    extra_data = Column("metadata", JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavedSchedule(Base):
    __tablename__ = "saved_schedules"

    schedule_id = Column(String(64), primary_key=True)
    season = Column(Integer, nullable=False)
    preset = Column(String(32), nullable=False)
    constraints = Column(JSON, nullable=False)
    summary = Column(JSON, nullable=False)
    games = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
