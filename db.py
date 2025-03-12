from sqlmodel import SQLModel, Session, create_engine
from contextlib import asynccontextmanager

DATABASE_URL = "sqlitecloud://cymjknn2nz.g6.sqlite.cloud:8860/chinook.sqlite?apikey=yqhGDTzHlA9HjVhC6FOPdPBZLPIRsbUQddfnnv2NNRY"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
