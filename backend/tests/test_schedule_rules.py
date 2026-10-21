from datetime import date

from app.models import Batch, Equipment, OperationStatus, OperationType, UnitOperation, UnitOperationDependency
from app.services.schedule import find_violations


def make_operation(db, name, batch, equipment, kind, start, end, status=OperationStatus.draft):
    operation = UnitOperation(name=name, batch=batch, equipment=equipment, type=kind, status=status, start_date=start, end_date=end)
    db.add(operation)
    db.flush()
    return operation


def setup(db):
    first_equipment, second_equipment = Equipment(name="1.5L"), Equipment(name="15L")
    first_batch = Batch(name="Batch one", start_date=date(2026, 1, 1), end_date=date(2026, 1, 20))
    second_batch = Batch(name="Batch two", start_date=date(2026, 1, 1), end_date=date(2026, 1, 20))
    db.add_all([first_equipment, second_equipment, first_batch, second_batch])
    db.flush()
    return first_equipment, second_equipment, first_batch, second_batch


def rules(db):
    return find_violations(db.query(UnitOperation).all(), db.query(UnitOperationDependency).all())


def test_operation_must_stay_within_batch_dates(db):
    equipment, _, batch, _ = setup(db)
    outside = make_operation(db, "Outside", batch, equipment, OperationType.seed, date(2025, 12, 31), date(2026, 1, 2))
    violations = rules(db)
    assert [(v.rule, v.operation_ids) for v in violations] == [("batch_dates", [outside.id])]


def test_later_operation_type_waits_for_every_earlier_type(db):
    first_equipment, second_equipment, batch, _ = setup(db)
    seed = make_operation(db, "Seed", batch, first_equipment, OperationType.seed, date(2026, 1, 1), date(2026, 1, 5))
    reactor = make_operation(db, "Reactor", batch, second_equipment, OperationType.bioreactor, date(2026, 1, 4), date(2026, 1, 8))
    violation = next(v for v in rules(db) if v.rule == "sequence")
    assert set(violation.operation_ids) == {seed.id, reactor.id}
    assert "Reactor" in violation.message and "Seed" in violation.message


def test_equipment_overlap_and_exclusive_end_boundary(db):
    equipment, _, first_batch, second_batch = setup(db)
    first = make_operation(db, "First", first_batch, equipment, OperationType.seed, date(2026, 1, 1), date(2026, 1, 4))
    touching = make_operation(db, "Touching", second_batch, equipment, OperationType.seed, date(2026, 1, 4), date(2026, 1, 6))
    assert not [v for v in rules(db) if v.rule == "equipment_overlap"]
    overlapping = make_operation(db, "Overlapping", second_batch, equipment, OperationType.seed, date(2026, 1, 3), date(2026, 1, 6))
    overlaps = [v for v in rules(db) if v.rule == "equipment_overlap"]
    assert len(overlaps) == 2
    assert any(set(v.operation_ids) == {first.id, overlapping.id} for v in overlaps)
    assert any(set(v.operation_ids) == {touching.id, overlapping.id} for v in overlaps)


def test_explicit_dependency_is_enforced(db):
    first_equipment, second_equipment, batch, _ = setup(db)
    source = make_operation(db, "Source", batch, first_equipment, OperationType.seed, date(2026, 1, 1), date(2026, 1, 5))
    target = make_operation(db, "Target", batch, second_equipment, OperationType.seed, date(2026, 1, 4), date(2026, 1, 6))
    db.add(UnitOperationDependency(from_unitop_id=source.id, to_unitop_id=target.id))
    db.flush()
    violation = next(v for v in rules(db) if v.rule == "dependency")
    assert set(violation.operation_ids) == {source.id, target.id}


def test_each_pair_is_reported_once_per_rule(db):
    first_equipment, second_equipment, batch, _ = setup(db)
    seed = make_operation(db, "Seed", batch, first_equipment, OperationType.seed, date(2026, 1, 1), date(2026, 1, 5))
    reactor = make_operation(db, "Reactor", batch, second_equipment, OperationType.bioreactor, date(2026, 1, 4), date(2026, 1, 7))
    duplicate_links = [
        UnitOperationDependency(from_unitop_id=seed.id, to_unitop_id=reactor.id),
        UnitOperationDependency(from_unitop_id=seed.id, to_unitop_id=reactor.id),
    ]
    violations = find_violations([seed, reactor], duplicate_links)
    assert len([v for v in violations if v.rule == "sequence"]) == 1
    assert len([v for v in violations if v.rule == "dependency"]) == 1
