import uuid
import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Float, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings
from app.domain.models import DatasetVersionCreate, ExperimentRunCreate, ModelVersionCreate

engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DatasetRecord(Base):
    __tablename__ = "mlops_datasets"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    version = Column(String)
    location = Column(String)
    schema_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExperimentRecord(Base):
    __tablename__ = "mlops_experiments"
    id = Column(String, primary_key=True, index=True)
    model_name = Column(String, index=True)
    hyperparameters = Column(JSON)
    metrics = Column(JSON)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ModelRecord(Base):
    __tablename__ = "mlops_models"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    version = Column(String)
    status = Column(String)  # Staged, Production, Deprecated
    artifact_uri = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PostgresRepository:
    def __init__(self, db_session):
        self.db = db_session

    def add_dataset(self, ds: DatasetVersionCreate):
        record = DatasetRecord(
            id=str(uuid.uuid4()),
            name=ds.name,
            version=ds.version,
            location=ds.location,
            schema_hash=ds.schema_hash
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_experiment(self, exp: ExperimentRunCreate):
        record = ExperimentRecord(
            id=str(uuid.uuid4()),
            model_name=exp.model_name,
            hyperparameters=exp.hyperparameters,
            metrics=exp.metrics,
            status=exp.status
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_model(self, mod: ModelVersionCreate):
        record = ModelRecord(
            id=str(uuid.uuid4()),
            name=mod.name,
            version=mod.version,
            status=mod.status,
            artifact_uri=mod.artifact_uri
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_models_by_name(self, name: str):
        return self.db.query(ModelRecord).filter(ModelRecord.name == name).all()

    def update_model_status(self, model_id: str, status: str):
        record = self.db.query(ModelRecord).filter(ModelRecord.id == model_id).first()
        if record:
            record.status = status
            self.db.commit()
            self.db.refresh(record)
        return record
