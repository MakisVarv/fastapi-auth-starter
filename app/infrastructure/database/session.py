from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
