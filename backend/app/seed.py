from datetime import date

from sqlalchemy.orm import Session

from .models import Batch, Equipment, OperationStatus, OperationType, UnitOperation


def seed_database(db: Session) -> None:
    if db.query(Equipment).count():
        return
    equipment = {name: Equipment(name=name) for name in ("1.5L", "15L", "20L", "75L", "1500L")}
    db.add_all(equipment.values())
    alpha = Batch(name="Alpha antibody", start_date=date(2026, 10, 1), end_date=date(2026, 10, 18))
    beta = Batch(name="Beta enzyme", start_date=date(2026, 10, 2), end_date=date(2026, 10, 15))
    gamma = Batch(name="Gamma vaccine", start_date=date(2026, 10, 8), end_date=date(2026, 10, 25))
    db.add_all([alpha, beta, gamma])
    db.flush()
    db.add_all([
        UnitOperation(name="Alpha seed", type=OperationType.seed, status=OperationStatus.confirmed, start_date=date(2026, 10, 1), end_date=date(2026, 10, 4), batch=alpha, equipment=equipment["1.5L"], color="#2563eb"),
        UnitOperation(name="Alpha bioreactor", type=OperationType.bioreactor, status=OperationStatus.confirmed, start_date=date(2026, 10, 3), end_date=date(2026, 10, 9), batch=alpha, equipment=equipment["15L"], color="#2563eb"),
        UnitOperation(name="Alpha TFF", type=OperationType.tff, status=OperationStatus.draft, start_date=date(2026, 10, 9), end_date=date(2026, 10, 11), batch=alpha, equipment=equipment["20L"], color="#2563eb"),
        UnitOperation(name="Beta seed", type=OperationType.seed, status=OperationStatus.confirmed, start_date=date(2026, 10, 3), end_date=date(2026, 10, 7), batch=beta, equipment=equipment["1.5L"], color="#16a34a"),
        UnitOperation(name="Beta bioreactor", type=OperationType.bioreactor, status=OperationStatus.draft, start_date=date(2026, 10, 7), end_date=date(2026, 10, 12), batch=beta, equipment=equipment["75L"], color="#16a34a"),
        UnitOperation(name="Gamma seed", type=OperationType.seed, status=OperationStatus.confirmed, start_date=date(2026, 10, 8), end_date=date(2026, 10, 10), batch=gamma, equipment=equipment["20L"], color="#9333ea"),
        UnitOperation(name="Gamma bioreactor", type=OperationType.bioreactor, status=OperationStatus.draft, start_date=date(2026, 10, 10), end_date=date(2026, 10, 18), batch=gamma, equipment=equipment["1500L"], color="#9333ea"),
    ])
    db.commit()
