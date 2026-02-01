from sqlalchemy import create_engine

def create_db_engine(url: str):
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
