from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func, DateTime
from models.incident import AlertState
from enum import StrEnum
from datetime import datetime

class Status(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
   

class Base(DeclarativeBase):
    pass


class IncidentORM(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    fingerprint: Mapped[str] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(default=AlertState.FIRING)
    title: Mapped[str]
    severity: Mapped[str]
    service: Mapped[str]    
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    times_seen: Mapped[int] = mapped_column(default=1)
    progress_status: Mapped[str] = mapped_column(default=Status.OPEN)