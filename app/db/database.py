import json
import os
from datetime import date, datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, configure_mappers

load_dotenv()


def custom_json_serializer(obj):
    """Custom JSON serializer that handles dates and datetimes"""

    def default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        raise TypeError(
            f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, ensure_ascii=False, default=default)


engine = create_engine(
    os.getenv('DB_URI'),
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_use_lifo=True,
    connect_args={
        "options": "-c timezone=utc",
        "client_encoding": "utf8"
    },
    json_serializer=custom_json_serializer
)

Base = declarative_base()
# make_searchable(Base.metadata)
configure_mappers()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables(engine):
    configure_mappers()
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def drop_and_create_db(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
