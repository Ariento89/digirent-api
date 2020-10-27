from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from digirent.core.config import DATABASE_URL, SQLALCHEMY_LOG


def load_spatialite(dbapi_conn, connection_record):
    """Load spatialite extension, for geoalchemy with sqlite"""
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension("/usr/lib/x86_64-linux-gnu/mod_spatialite.so")
    dbapi_conn.execute("SELECT InitSpatialMetaData();")


if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}, echo=SQLALCHEMY_LOG
    )
    listen(engine, "connect", load_spatialite)
else:
    engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_LOG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
