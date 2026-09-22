"""
IP-SAKTI SAHAYAK
Database Engine / Session
==========================
Creates the SQLAlchemy engine + session factory and exposes a seed
routine that populates the initial authoritative source registry
(Section 4/5 of the spec) so the app has real rows to work with on
first run.
"""

import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from database.models import Base, Source

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables if they don't exist, then seed the source registry."""
    Base.metadata.create_all(bind=engine)
    _seed_sources()


@contextmanager
def get_session():
    """Context-managed session: `with get_session() as db: ...`"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# =====================================================
# SOURCE REGISTRY SEED
# =====================================================

SEED_SOURCES = [
    dict(source_name="IP India", base_url="https://ipindia.gov.in", jurisdiction="India",
         domain="General IP", authority="Controller General of Patents, Designs and Trade Marks",
         source_type="legislation", priority=1, update_frequency="weekly"),
    dict(source_name="India Code", base_url="https://www.indiacode.nic.in", jurisdiction="India",
         domain="General IP", authority="Legislative Department, Govt. of India",
         source_type="legislation", priority=1, update_frequency="monthly"),
    dict(source_name="Ministry of AYUSH", base_url="https://ayush.gov.in", jurisdiction="India",
         domain="Ayurveda", authority="Ministry of AYUSH", source_type="guidance",
         priority=1, update_frequency="weekly"),
    dict(source_name="National Biodiversity Authority", base_url="https://nbaindia.gov.in",
         jurisdiction="India", domain="Biodiversity", authority="National Biodiversity Authority",
         source_type="regulation", priority=1, update_frequency="weekly"),
    dict(source_name="TKDL", base_url="https://www.tkdl.res.in", jurisdiction="India",
         domain="Traditional Knowledge", authority="CSIR / TKDL",
         source_type="institutional", priority=2, update_frequency="monthly"),
    dict(source_name="WIPO", base_url="https://www.wipo.int", jurisdiction="International",
         domain="International IP", authority="World Intellectual Property Organization",
         source_type="treaty", priority=1, update_frequency="weekly"),
    dict(source_name="WIPO Lex", base_url="https://www.wipo.int/wipolex", jurisdiction="International",
         domain="International IP", authority="WIPO", source_type="legislation",
         priority=1, update_frequency="weekly"),
    dict(source_name="WTO (TRIPS)", base_url="https://www.wto.org", jurisdiction="International",
         domain="International IP", authority="World Trade Organization",
         source_type="treaty", priority=1, update_frequency="monthly"),
    dict(source_name="WHO", base_url="https://www.who.int", jurisdiction="International",
         domain="Regulatory", authority="World Health Organization", source_type="guidance",
         priority=2, update_frequency="monthly"),
]


def _seed_sources() -> None:
    with get_session() as db:
        existing = {s.source_name for s in db.query(Source).all()}
        added = 0
        for entry in SEED_SOURCES:
            if entry["source_name"] in existing:
                continue
            db.add(Source(last_checked=None, enabled=True, **entry))
            added += 1
        if added:
            logger.info("Seeded %d authoritative sources into the registry.", added)


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    with get_session() as db:
        count = db.query(Source).count()
        print(f"Sources in registry: {count}")
