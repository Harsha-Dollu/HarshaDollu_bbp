from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Batch, Equipment, UnitOperation
from ..schemas import ScheduleResponse, UnitOperationRead, UnitOperationWrite
from ..services.schedule import current_violations, operations_with_relations

router = APIRouter(prefix="/api", tags=["schedule"])


def violation_error(violations):
    raise HTTPException(status_code=422, detail={"message": "Schedule change rejected.", "violations": [v.model_dump() for v in violations]})


def validate_candidate(db: Session, candidate: UnitOperation) -> None:
    relevant = [v for v in current_violations(db) if candidate.id in v.operation_ids]
    if relevant:
        violation_error(relevant)


def assign_values(operation: UnitOperation, payload: UnitOperationWrite) -> None:
    for key, value in payload.model_dump().items():
        setattr(operation, key, value)


@router.get("/schedule", response_model=ScheduleResponse)
def get_schedule(start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db)):
    query = db.query(UnitOperation)
    if start_date:
        query = query.filter(UnitOperation.end_date > start_date)
    if end_date:
        query = query.filter(UnitOperation.start_date < end_date)
    operations = list(query.all())
    return ScheduleResponse(equipment=db.query(Equipment).order_by(Equipment.id).all(), batches=db.query(Batch).order_by(Batch.id).all(), operations=operations, violations=current_violations(db))


@router.post("/unit_operations", response_model=UnitOperationRead, status_code=status.HTTP_201_CREATED)
def create_operation(payload: UnitOperationWrite, db: Session = Depends(get_db)):
    if not db.get(Batch, payload.batch_id) or not db.get(Equipment, payload.equipment_id):
        raise HTTPException(404, "Batch or equipment was not found.")
    operation = UnitOperation(**payload.model_dump())
    db.add(operation)
    db.flush()
    validate_candidate(db, operation)
    db.commit()
    db.refresh(operation)
    return operation


@router.put("/unit_operations/{op_id}", response_model=UnitOperationRead)
def update_operation(op_id: int, payload: UnitOperationWrite, db: Session = Depends(get_db)):
    operation = db.get(UnitOperation, op_id)
    if not operation:
        raise HTTPException(404, "Unit operation was not found.")
    if operation.status.value == "completed":
        raise HTTPException(409, "Completed unit operations cannot be moved or edited.")
    if not db.get(Batch, payload.batch_id) or not db.get(Equipment, payload.equipment_id):
        raise HTTPException(404, "Batch or equipment was not found.")
    assign_values(operation, payload)
    db.flush()
    validate_candidate(db, operation)
    db.commit()
    db.refresh(operation)
    return operation


@router.delete("/unit_operations/{op_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(op_id: int, db: Session = Depends(get_db)):
    operation = db.get(UnitOperation, op_id)
    if not operation:
        raise HTTPException(404, "Unit operation was not found.")
    if operation.status.value == "completed":
        raise HTTPException(409, "Completed unit operations cannot be deleted.")
    db.delete(operation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
