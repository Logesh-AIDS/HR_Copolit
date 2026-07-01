# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.common.database import Base

# In-memory SQLite for unit and integration testing
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_redis():
    class MockRedisClient:
        def __init__(self):
            self.store = {}
        def get(self, key):
            return self.store.get(key)
        def set(self, key, value, ex=None):
            self.store[key] = value
            return True
        def delete(self, key):
            if key in self.store:
                del self.store[key]
                return True
            return False
        def exists(self, key):
            return key in self.store
        def incr(self, key):
            val = int(self.store.get(key, 0)) + 1
            self.store[key] = str(val)
            return val
        def expire(self, key, seconds):
            return True
        def ping(self):
            return True
            
    return MockRedisClient()
