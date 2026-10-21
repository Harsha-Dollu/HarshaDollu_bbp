import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class OperationType(str, enum.Enum):
    seed = "Seed"
    bioreactor = "Bioreactor"
    tff = "TFF"
    spray = "Spray"
    sum = "Sum"


class OperationStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    completed = "completed"


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    operations: Mapped[list["UnitOperation"]] = relationship(back_populates="equipment")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    operations: Mapped[list["UnitOperation"]] = relationship(back_populates="batch")


class UnitOperation(Base):
    __tablename__ = "unit_operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#2563eb")
    status: Mapped[OperationStatus] = mapped_column(Enum(OperationStatus), nullable=False, default=OperationStatus.draft)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), nullable=False)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    batch: Mapped[Batch] = relationship(back_populates="operations")
    equipment: Mapped[Equipment] = relationship(back_populates="operations")


class UnitOperationDependency(Base):
    __tablename__ = "unit_operation_dependencies"
    __table_args__ = (UniqueConstraint("from_unitop_id", "to_unitop_id", name="uq_dependency_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    from_unitop_id: Mapped[int] = mapped_column(ForeignKey("unit_operations.id"), nullable=False)
    to_unitop_id: Mapped[int] = mapped_column(ForeignKey("unit_operations.id"), nullable=False)


class Reading(Base):
    __tablename__ = "readings"
    id: Mapped[int] = mapped_column(primary_key=True)
    process_time_h: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    signal_name: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(12), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    made_at_process_time_h: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    target_process_time_h: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    signal_name: Mapped[str] = mapped_column(String(30), default="DO", nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CommandStatus(str, enum.Enum):
    accepted = "accepted"
    rejected = "rejected"


class ControlCommand(Base):
    __tablename__ = "control_commands"
    id: Mapped[int] = mapped_column(primary_key=True)
    setpoint_name: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(12), nullable=False)
    apply_at_time_h: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[CommandStatus] = mapped_column(Enum(CommandStatus), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
