from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ✅ Dependency for DB session (IMPORTANT)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Called during startup
def init_db():
    Base.metadata.create_all(bind=engine)