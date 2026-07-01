# services/common/database.py
import logging
from typing import Generator, Type, TypeVar, Optional, List, Any
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from services.common.config import settings

logger = logging.getLogger(__name__)

# Base metadata ORM model class
Base = declarative_base()

# Configure SQLAlchemy creation parameters with connection pooling parameters
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("SQLAlchemy database connection pool established.")
except Exception as e:
    logger.critical(f"Failed to initialize SQLAlchemy engine pool: {e}")
    raise e


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency injection provider supplying transactional session boundaries.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rollback triggered due to exception: {e}")
        raise e
    finally:
        db.close()


T = TypeVar("T", bound=Base)

class SQLAlchemyRepository:
    """
    Base generic repository executing common ORM query patterns, ensuring SOLID principles.
    """
    def __init__(self, db: Session):
        self.db = db

    def add(self, model: Any) -> Any:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_by_id(self, model_class: Type[T], record_id: Any) -> Optional[T]:
        return self.db.query(model_class).filter(model_class.id == record_id).first()

    def list_all(self, model_class: Type[T], skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(model_class).offset(skip).limit(limit).all()

    def delete(self, model: Any) -> None:
        self.db.delete(model)
        self.db.commit()

    def commit(self) -> None:
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit transaction: {e}")
            raise e
