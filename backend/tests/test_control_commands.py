from app.schemas import CommandRequest, ReadingInput
from app.services.control import ingest, submit_command


def test_command_bounds_units_time_and_pending_conflicts_are_persisted(db):
    ingest(db, [ReadingInput(time_h=4.0, signal_name="DO", value=50, unit="%")])
    bad_unit = submit_command(db, CommandRequest(setpoint_name="feed_rate", value=5, unit="L/h", apply_at_time_h=4.1))
    too_high = submit_command(db, CommandRequest(setpoint_name="feed_rate", value=31, unit="mL/h", apply_at_time_h=4.1))
    past = submit_command(db, CommandRequest(setpoint_name="feed_rate", value=5, unit="mL/h", apply_at_time_h=3.9))
    accepted = submit_command(db, CommandRequest(setpoint_name="feed_rate", value=5, unit="mL/h", apply_at_time_h=4.1))
    pending = submit_command(db, CommandRequest(setpoint_name="feed_rate", value=6, unit="mL/h", apply_at_time_h=4.2))
    assert bad_unit.rejection_reason and too_high.rejection_reason and past.rejection_reason
    assert accepted.rejection_reason is None
    assert pending.rejection_reason == "A feed_rate command is already pending."


def test_ingest_rejects_signal_with_wrong_unit(db):
    try:
        ingest(db, [ReadingInput(time_h=1, signal_name="DO", value=50, unit="mL/h")])
    except ValueError as error:
        assert "must use unit" in str(error)
    else:
        raise AssertionError("Expected bad ingest unit to be rejected")
