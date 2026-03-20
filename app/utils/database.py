from sqlalchemy import create_engine, text
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
    _ensure_product_analytics_columns()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Called during startup
def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_product_analytics_columns()


def _ensure_product_analytics_columns():
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        table_info = connection.execute(text("PRAGMA table_info(products)")).fetchall()
        existing_columns = {row[1] for row in table_info}

        if "category" not in existing_columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR"))

        if "quantity" not in existing_columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN quantity INTEGER DEFAULT 1"))

        connection.execute(
            text("UPDATE products SET category = 'General' WHERE category IS NULL OR TRIM(category) = ''")
        )
        connection.execute(
            text("UPDATE products SET quantity = 1 WHERE quantity IS NULL OR quantity < 1")
        )