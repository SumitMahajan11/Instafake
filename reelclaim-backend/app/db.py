import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict

from sqlalchemy import create_engine, Column, String, Text, Float, DateTime, JSON, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger("reelclaim.db")

Base = declarative_base()

class AuditRecord(Base):
    __tablename__ = "audits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    caption = Column(Text, nullable=False)
    promoted_site = Column(Text, nullable=True)
    override_url = Column(Text, nullable=True)
    claims = Column(JSON, nullable=True)
    crawl_status = Column(String(50), nullable=True)
    verdicts = Column(JSON, nullable=True)
    trust_score = Column(Float, nullable=True)
    coverage_status = Column(String(50), nullable=True)
    summary_label = Column(Text, nullable=True)
    status = Column(String(50), default="completed")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    rate_limit_per_hour = Column(Integer, default=10, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


engine = None
SessionLocal = None
_db_initialized = False

def init_db() -> bool:
    """
    Initializes database engine and sessionmaker if DATABASE_URL is provided in environment.
    If DATABASE_URL is unset, degrades gracefully to 'persistence disabled' and logs a warning.
    """
    global engine, SessionLocal, _db_initialized
    database_url = os.getenv("DATABASE_URL")
    if not database_url or not database_url.strip():
        logger.warning("DATABASE_URL environment variable is unset. Audit persistence is disabled.")
        return False

    db_url = database_url.strip()
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    try:
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True if not db_url.startswith("sqlite") else False)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _db_initialized = True
        logger.info("Database initialized successfully.")
        return True
    except Exception as e:
        logger.warning(f"Database initialization failed ({e}). Audit persistence is disabled.")
        _db_initialized = False
        return False

def get_db_session() -> Optional[Session]:
    if not _db_initialized or SessionLocal is None:
        return None
    try:
        return SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        return None

def save_audit_record(
    caption: str,
    promoted_site: Optional[str],
    override_url: Optional[str],
    claims: List[Any],
    crawl_status: Optional[str],
    check_result: Optional[Any]
) -> Optional[str]:
    """
    Persists a completed audit run result into the database.
    Returns the audit record ID, or None if database is uninitialized or write fails.
    """
    session = get_db_session()
    if not session:
        return None

    try:
        audit_id = str(uuid.uuid4())

        # Convert claim Pydantic objects or dicts to JSON-serializable list
        claims_data = []
        if claims:
            for c in claims:
                if hasattr(c, "model_dump"):
                    claims_data.append(c.model_dump())
                elif hasattr(c, "dict"):
                    claims_data.append(c.dict())
                elif isinstance(c, dict):
                    claims_data.append(c)

        verdicts_data = None
        trust_score = None
        coverage_status = None
        summary_label = None

        if check_result:
            trust_score = getattr(check_result, "trust_score", None)
            coverage_status = getattr(check_result, "coverage_status", None)
            summary_label = getattr(check_result, "summary_label", None)
            verdicts = getattr(check_result, "verdicts", [])
            if verdicts:
                verdicts_data = []
                for v in verdicts:
                    if hasattr(v, "model_dump"):
                        verdicts_data.append(v.model_dump())
                    elif hasattr(v, "dict"):
                        verdicts_data.append(v.dict())
                    elif isinstance(v, dict):
                        verdicts_data.append(v)

        record = AuditRecord(
            id=audit_id,
            created_at=datetime.now(timezone.utc),
            caption=caption,
            promoted_site=promoted_site,
            override_url=override_url,
            claims=claims_data,
            crawl_status=crawl_status,
            verdicts=verdicts_data,
            trust_score=trust_score,
            coverage_status=coverage_status,
            summary_label=summary_label,
            status="completed"
        )
        session.add(record)
        session.commit()
        session.close()
        return audit_id
    except Exception as e:
        logger.error(f"Failed to persist audit record: {e}")
        if session:
            session.rollback()
            session.close()
        return None

def get_audit_record_by_id(audit_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches an audit record by ID.
    Returns record dictionary or None if not found or DB disabled.
    """
    session = get_db_session()
    if not session:
        return None

    try:
        record = session.query(AuditRecord).filter(AuditRecord.id == audit_id).first()
        if not record:
            session.close()
            return None

        data = {
            "id": record.id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "caption": record.caption,
            "promoted_site": record.promoted_site,
            "override_url": record.override_url,
            "claims": record.claims or [],
            "crawl_status": record.crawl_status,
            "trust_score": record.trust_score,
            "coverage_status": record.coverage_status,
            "summary_label": record.summary_label,
            "verdicts": record.verdicts or [],
            "status": record.status
        }
        session.close()
        return data
    except Exception as e:
        logger.error(f"Failed to fetch audit by ID {audit_id}: {e}")
        if session:
            session.close()
        return None

def list_recent_audit_records(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    Lists recent audit records paginated, ordered by creation date descending.
    """
    session = get_db_session()
    if not session:
        return {"total": 0, "limit": limit, "offset": offset, "audits": [], "persistence": "disabled"}

    try:
        total = session.query(AuditRecord).count()
        records = (
            session.query(AuditRecord)
            .order_by(AuditRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for record in records:
            items.append({
                "id": record.id,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "caption": record.caption,
                "promoted_site": record.promoted_site,
                "crawl_status": record.crawl_status,
                "trust_score": record.trust_score,
                "coverage_status": record.coverage_status,
                "summary_label": record.summary_label,
                "total_claims": len(record.claims or []),
                "status": record.status
            })
        session.close()
        return {"total": total, "limit": limit, "offset": offset, "audits": items}
    except Exception as e:
        logger.error(f"Failed to list audit records: {e}")
        if session:
            session.close()
        return {"total": 0, "limit": limit, "offset": offset, "audits": [], "error": str(e)}

def save_api_key_record(key_hash: str, name: str, rate_limit_per_hour: int = 10) -> Optional[str]:
    """
    Saves an API key hash record into the database.
    Returns key ID or None if DB disabled or save fails.
    """
    session = get_db_session()
    if not session:
        return None

    try:
        key_id = str(uuid.uuid4())
        record = ApiKey(
            id=key_id,
            key_hash=key_hash,
            name=name,
            rate_limit_per_hour=rate_limit_per_hour,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        session.add(record)
        session.commit()
        session.close()
        return key_id
    except Exception as e:
        logger.error(f"Failed to save API key record: {e}")
        if session:
            session.rollback()
            session.close()
        return None

def get_api_key_by_hash(key_hash: str) -> Optional[Dict[str, Any]]:
    """
    Looks up an API key record by its SHA-256 hash.
    Returns dictionary or None if not found or DB disabled.
    """
    session = get_db_session()
    if not session:
        return None

    try:
        record = session.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True).first()
        if not record:
            session.close()
            return None

        data = {
            "id": record.id,
            "key_hash": record.key_hash,
            "name": record.name,
            "rate_limit_per_hour": record.rate_limit_per_hour,
            "is_active": record.is_active,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
        session.close()
        return data
    except Exception as e:
        logger.error(f"Failed to lookup API key: {e}")
        if session:
            session.close()
        return None

