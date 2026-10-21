from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ControlCommand, Prediction, Reading
from ..schemas import CommandRequest, IngestRequest
from ..services.control import current_process_time, ingest, submit_command
from ..services.forecasting import create_forecast, evaluation
from ..simulator import controller_tick, simulator

router = APIRouter(tags=["control"])


@router.post("/ingest")
def post_ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    try: return {"stored": ingest(db, payload.readings)}
    except ValueError as error: raise HTTPException(422, str(error))


@router.post("/command")
def post_command(payload: CommandRequest, db: Session = Depends(get_db)):
    command = submit_command(db, payload)
    if command.rejection_reason:
        raise HTTPException(422, detail={"message": command.rejection_reason, "command_id": command.id})
    return {"id": command.id, "status": command.status, "apply_at_time_h": command.apply_at_time_h}


@router.get("/api/control/state")
def control_state(db: Session = Depends(get_db)):
    return {"current_process_time_h": current_process_time(db), "readings": db.query(Reading).order_by(Reading.process_time_h).all(), "predictions": db.query(Prediction).order_by(Prediction.id.desc()).limit(10).all()[::-1], "commands": db.query(ControlCommand).order_by(ControlCommand.id.desc()).limit(100).all()[::-1]}


@router.get("/api/forecast/evaluation")
def forecast_evaluation():
    return evaluation()


@router.post("/api/forecast")
def forecast(db: Session = Depends(get_db)):
    try: return {"predictions": create_forecast(db)}
    except ValueError as error: raise HTTPException(422, str(error))


@router.post("/api/simulator/start")
def start_simulator():
    simulator.start()
    return {"running": simulator.running, "speed_process_minutes_per_second": simulator.speed}


@router.post("/api/simulator/reset")
def reset_simulator(db: Session = Depends(get_db)):
    if not simulator.reset():
        raise HTTPException(409, "Stop or finish the active replay before resetting it.")
    db.execute(delete(Prediction))
    db.execute(delete(ControlCommand))
    db.execute(delete(Reading))
    db.commit()
    return {"reset": True, "message": "Simulation telemetry cleared; schedules are unchanged."}


@router.post("/api/controller/tick")
def run_controller(db: Session = Depends(get_db)):
    command = controller_tick(db)
    return {"command_id": command.id if command else None}
