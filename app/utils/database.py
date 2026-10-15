from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

database_url = DATABASE_URL
is_sqlite = database_url.startswith("sqlite")

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if is_sqlite else {}
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
    _ensure_product_analytics_columns()
    _ensure_scan_result_user_column()


def _ensure_product_analytics_columns():
    if "products" not in inspect(engine).get_table_names():
        return
    if not database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        table_info = connection.execute(text("PRAGMA table_info(products)")).fetchall()
        existing_columns = {row[1] for row in table_info}

        if "category" not in existing_columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR"))

        if "quantity" not in existing_columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN quantity INTEGER DEFAULT 1"))

        if "alert_sent" not in existing_columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN alert_sent BOOLEAN DEFAULT 0"))

        connection.execute(
            text("UPDATE products SET category = 'General' WHERE category IS NULL OR TRIM(category) = ''")
        )
        connection.execute(
            text("UPDATE products SET quantity = 1 WHERE quantity IS NULL OR quantity < 1")
        )
        connection.execute(
            text("UPDATE products SET alert_sent = 0 WHERE alert_sent IS NULL")
        )


def _ensure_scan_result_user_column():
    if "scan_results" not in inspect(engine).get_table_names():
        return

    columns = {column["name"] for column in inspect(engine).get_columns("scan_results")}
    if "user_id" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE scan_results ADD COLUMN user_id INTEGER"))