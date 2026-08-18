import uuid
from typing import List
from typing import Optional
from collections.abc import Generator
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Text, Uuid, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import create_engine
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass

class Document(Base):
   __tablename__ = "documents"

   #change to uuid object if shift to postgresql
   id : Mapped[str] = mapped_column(String, primary_key=True, default=lambda:str(uuid.uuid4()))
   file_name : Mapped[str] = mapped_column(String, nullable=False)
   content_type : Mapped[str] = mapped_column(String, nullable=False)
   file_size_bytes : Mapped[int] = mapped_column(Integer, nullable=False)
   extracted_text : Mapped[str] = mapped_column(Text, nullable=False)
   uploaded_at : Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())



    
engine = create_engine("sqlite:///./documents.db", echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
         db.close()

def all_documents(db:Session) -> list[Document]:
    return db.execute(select(Document)).scalars().all()