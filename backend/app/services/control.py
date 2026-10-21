from sqlalchemy.orm import Session

from ..models import CommandStatus, ControlCommand, Reading
from ..schemas import CommandRequest, ReadingInput

SIGNAL_UNITS = {"DO": "%", "pH": "-", "temp": "degC", "feed_rate": "mL/h"}
FEED_MIN, FEED_MAX = 0.0, 30.0


def current_process_time(db: Session) -> float:
    latest = db.query(Reading).order_by(Reading.process_time_h.desc()).first()
    return latest.process_time_h if latest else 0.0


def ingest(db: Session, readings: list[ReadingInput]) -> int:
    for reading in readings:
        expected = SIGNAL_UNITS.get(reading.signal_name)
        if expected != reading.unit:
            raise ValueError(f"{reading.signal_name} must use unit {expected!r}.")
    db.add_all([Reading(process_time_h=r.time_h, signal_name=r.signal_name, value=r.value, unit=r.unit) for r in readings])
    db.commit()
    return len(readings)


def submit_command(db: Session, command: CommandRequest) -> ControlCommand:
    now = current_process_time(db)
    reason = None
    if command.setpoint_name != "feed_rate": reason = "Only feed_rate commands are supported."
    elif command.unit != "mL/h": reason = "feed_rate commands must use mL/h."
    elif not FEED_MIN <= command.value <= FEED_MAX: reason = "feed_rate must be between 0.0 and 30.0 mL/h."
    elif command.apply_at_time_h < now: reason = f"apply_at_time_h cannot be earlier than current process time {now:.4f}."
    elif db.query(ControlCommand).filter(ControlCommand.setpoint_name == command.setpoint_name, ControlCommand.status == CommandStatus.accepted, ControlCommand.apply_at_time_h > now).first(): reason = "A feed_rate command is already pending."
    record = ControlCommand(**command.model_dump(), status=CommandStatus.rejected if reason else CommandStatus.accepted, rejection_reason=reason)
    db.add(record); db.commit(); db.refresh(record)
    return record
