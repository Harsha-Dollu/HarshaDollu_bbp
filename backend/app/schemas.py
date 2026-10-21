from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import OperationStatus, OperationType


class UnitOperationWrite(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: OperationType
    color: str = Field(default="#2563eb", max_length=20)
    status: OperationStatus = OperationStatus.draft
    start_date: date
    end_date: date
    batch_id: int
    equipment_id: int

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date (end dates are exclusive)")
        return self


class UnitOperationRead(UnitOperationWrite):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class BatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    start_date: date
    end_date: date


class Violation(BaseModel):
    rule: str
    operation_ids: list[int]
    message: str


class ScheduleResponse(BaseModel):
    equipment: list[EquipmentRead]
    batches: list[BatchRead]
    operations: list[UnitOperationRead]
    violations: list[Violation]


class ReadingInput(BaseModel):
    time_h: float = Field(ge=0)
    signal_name: str
    value: float
    unit: str


class IngestRequest(BaseModel):
    readings: list[ReadingInput] = Field(min_length=1)


class CommandRequest(BaseModel):
    setpoint_name: str
    value: float
    unit: str
    apply_at_time_h: float = Field(ge=0)
    source: str = "manual"
