import os
import tempfile
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / "bbp_schedule_tests.sqlite"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

import pytest
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine


@pytest.fixture()
def db() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
