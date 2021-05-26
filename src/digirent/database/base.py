from functools import wraps
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from digirent.core.config import DATABASE_URL, SQLALCHEMY_LOG


def load_spatialite(dbapi_conn, connection_record):
    """Load spatialite extension, for geoalchemy with sqlite"""
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension("/usr/lib/x86_64-linux-gnu/mod_spatialite.so")
    dbapi_conn.execute("SELECT InitSpatialMetaData();")


if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=SQLALCHEMY_LOG,
    )
    listen(engine, "connect", load_spatialite)
else:
    engine = create_engine(
        DATABASE_URL, echo=SQLALCHEMY_LOG, pool_size=20, max_overflow=10
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

__session = scoped_session(SessionLocal)


@contextmanager
def session_scope(bind=None):
    """
    Provide a transactional scope around a series of operations.
    Ensures that the session is commited and closed.
    Exceptions raised within the 'with' block using this contextmanager
    should be handled in the with block itself.
    They will not be caught by the 'except' here.
    """
    try:
        if bind:
            yield __session(bind=bind)
        else:
            yield __session()
        __session.commit()
    except Exception:
        # Only the exceptions raised by session.commit above are caught here
        __session.rollback()
        raise
    finally:
        __session.remove()


def with_db_session(func):
    """
    Wraps the function in a transaction, any errors thrown in the function
    are intercepted so the tx can be rolled back.
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        with session_scope() as session:
            try:
                result = func(*args, **kwargs, session=session)
                session.commit()
                return result
            except Exception as exception:
                print("\n\n\n\n\n from wrapped with db session")
                print(exception)
                print("\n\n\n\n\n")
                session.rollback()
                raise

    return wrapped
