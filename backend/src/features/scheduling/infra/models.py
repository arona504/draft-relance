"""SQLAlchemy models for the scheduling feature."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.db import Base
from ..domain.value_objects import AppointmentStatus, SlotMode, SlotStatus


class Calendar(Base):
    __tablename__ = "calendars"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    practitioner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    slots: Mapped[list["Slot"]] = relationship(back_populates="calendar", cascade="all, delete-orphan")


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (
        UniqueConstraint("calendar_id", "starts_at", name="uq_slot_calendar_starts"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    calendar_id: Mapped[str] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    mode: Mapped[SlotMode] = mapped_column(Enum(SlotMode, name="slot_mode"), nullable=False)
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus, name="slot_status"), nullable=False, index=True)

    calendar: Mapped["Calendar"] = relationship(back_populates="slots")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="slot", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.BOOKED,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[SlotMode] = mapped_column(Enum(SlotMode, name="appointment_mode"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    slot: Mapped["Slot"] = relationship(back_populates="appointments")
