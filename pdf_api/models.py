from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import String, Boolean, Integer, JSON
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    documents: Mapped["Document"] = relationship("Document", cascade="all, delete")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(1024), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    hash: Mapped[str] = mapped_column(String(256), nullable=False)
    public: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    chunks: Mapped[str] = mapped_column(JSON())
    content_size: Mapped[int] = mapped_column(Integer())
