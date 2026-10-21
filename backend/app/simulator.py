"""One-vessel replay. One wall-clock second equals one process-minute by default."""
import math
import threading
import time

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import CommandStatus, ControlCommand, Reading
from .schemas import CommandRequest, ReadingInput
from .services.control import ingest, submit_command
from .services.forecasting import create_forecast, load_signals, DATA_DIR


class ReplaySimulator:
    def __init__(self, speed: float = 1.0):
        signals = load_signals(DATA_DIR / "run_A.csv")
        self.do, self.feed, self.ph, self.temp = signals["DO"], signals["feed_rate"], signals["pH"], signals["temp"]
        self.speed, self.index, self.delta_do = speed, 0, 0.0
        self.running = False
        self._thread: threading.Thread | None = None

    def tick(self, db: Session) -> bool:
        if self.index >= len(self.do):
            self.running = False; return False
        process_time = self.index / 60
        command = db.query(ControlCommand).filter(ControlCommand.status == CommandStatus.accepted, ControlCommand.apply_at_time_h <= process_time).order_by(ControlCommand.apply_at_time_h.desc(), ControlCommand.id.desc()).first()
        applied_feed = command.value if command else float(self.feed[self.index])
        target_delta = -2.0 * (applied_feed - float(self.feed[self.index]))
        self.delta_do += (target_delta - self.delta_do) * (1 - math.exp(-1 / 5))
        baseline_do = float(self.do[self.index])
        ingest(db, [ReadingInput(time_h=process_time, signal_name="DO", value=max(0, min(100, baseline_do + self.delta_do)), unit="%"), ReadingInput(time_h=process_time, signal_name="feed_rate", value=applied_feed, unit="mL/h"), ReadingInput(time_h=process_time, signal_name="pH", value=float(self.ph[self.index]), unit="-"), ReadingInput(time_h=process_time, signal_name="temp", value=float(self.temp[self.index]), unit="degC")])
        self.index += 1
        # Five-minute cadence keeps the loop responsive without creating a prediction per second.
        if self.index >= 60 and self.index % 5 == 0:
            create_forecast(db)
            controller_tick(db)
        return True

    def start(self) -> None:
        if self.running: return
        self.running = True
        def loop():
            while self.running:
                with SessionLocal() as db:
                    if not self.tick(db): break
                time.sleep(1 / self.speed)
        self._thread = threading.Thread(target=loop, daemon=True); self._thread.start()

    def reset(self) -> bool:
        if self.running:
            return False
        self.index, self.delta_do = 0, 0.0
        return True


simulator = ReplaySimulator()


def controller_tick(db: Session):
    """Reactive policy: lower feed by 2 below 35% DO; raise by 1 above 60%, max every five minutes."""
    latest = db.query(Reading).filter(Reading.signal_name == "DO").order_by(Reading.process_time_h.desc()).first()
    if not latest: return None
    pending = db.query(ControlCommand).filter(ControlCommand.source == "controller", ControlCommand.status == CommandStatus.accepted, ControlCommand.apply_at_time_h > latest.process_time_h).first()
    if pending: return None
    last = db.query(ControlCommand).filter(ControlCommand.source == "controller", ControlCommand.status == CommandStatus.accepted).order_by(ControlCommand.apply_at_time_h.desc()).first()
    if last and latest.process_time_h - last.apply_at_time_h < 5 / 60: return None
    feed = db.query(Reading).filter(Reading.signal_name == "feed_rate", Reading.process_time_h == latest.process_time_h).first()
    if not feed: return None
    if latest.value < 35: value = max(0, feed.value - 2)
    elif latest.value > 60: value = min(30, feed.value + 1)
    else: return None
    return submit_command(db, CommandRequest(setpoint_name="feed_rate", value=value, unit="mL/h", apply_at_time_h=latest.process_time_h + 5 / 60, source="controller"))
