from sqlmodel import Session, SQLModel, create_engine

from config import settings

engine = create_engine(settings.database_url)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
