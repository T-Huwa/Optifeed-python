from sqlmodel import SQLModel, Session, create_engine
from contextlib import asynccontextmanager

DATABASE_URL = "sqlite:///database.db"  # Change this to PostgreSQL/MySQL if needed

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
