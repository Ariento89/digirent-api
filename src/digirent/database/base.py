from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from digirent.core.config import DATABASE_URL, IS_PRODUCTION

echo = not IS_PRODUCTION


def load_spatialite(dbapi_conn, connection_record):
    """Load spatialite extension, for geoalchemy with sqlite"""
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension("/usr/lib/x86_64-linux-gnu/mod_spatialite.so")
    dbapi_conn.execute("SELECT InitSpatialMetaData(1);")


if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}, echo=echo
    )
    listen(engine, "connect", load_spatialite)
else:
    engine = create_engine(DATABASE_URL, echo=echo)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
