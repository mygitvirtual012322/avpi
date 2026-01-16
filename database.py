
import os
import json
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Get DB URL from env or use local sqlite
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Local SQLite
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'admin_data', 'ipva.db')}"
elif DATABASE_URL.startswith("postgres://"):
    # Fix for SQLAlchemy expecting postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()

class Config(Base):
    __tablename__ = "configs"
    key = Column(String(50), primary_key=True, index=True)
    value = Column(Text, nullable=False) # JSON encoded value

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db_config(key, default=None):
    session = SessionLocal()
    try:
        config = session.query(Config).filter(Config.key == key).first()
        if config:
            return json.loads(config.value)
        return default
    except Exception as e:
        print(f"DB Error getting config {key}: {e}")
        return default
    finally:
        session.close()

def set_db_config(key, value):
    session = SessionLocal()
    try:
        config = session.query(Config).filter(Config.key == key).first()
        if not config:
            config = Config(key=key, value=json.dumps(value))
            session.add(config)
        else:
            config.value = json.dumps(value)
        session.commit()
        return True
    except Exception as e:
        print(f"DB Error setting config {key}: {e}")
        session.rollback()
        return False
    finally:
        session.close()
