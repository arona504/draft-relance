"""SQLAlchemy models for the scheduling feature."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from ..domain.value_objects import AppointmentStatus, SlotMode, SlotStatus


class CalendarDB(Base):
    __tablename__ = "calendars"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    practitioner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    slots: Mapped[list["SlotDB"]] = relationship(back_populates="calendar", cascade="all, delete-orphan")


class SlotDB(Base):
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

    calendar: Mapped["CalendarDB"] = relationship(back_populates="slots")
    appointments: Mapped[list["AppointmentDB"]] = relationship(back_populates="slot", cascade="all, delete-orphan")


class AppointmentDB(Base):
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

    slot: Mapped["SlotDB"] = relationship(back_populates="appointments")


class PatientAccessGrantDB(Base):
    __tablename__ = "patient_access_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resource_tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    granted_tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    read_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
