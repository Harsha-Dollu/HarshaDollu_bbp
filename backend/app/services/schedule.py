from collections.abc import Iterable

from sqlalchemy.orm import Session, joinedload

from ..models import UnitOperation, UnitOperationDependency
from ..schemas import Violation

TYPE_ORDER = {"Seed": 0, "Bioreactor": 1, "TFF": 2, "Spray": 3, "Sum": 4}


def operations_with_relations(db: Session) -> list[UnitOperation]:
    return list(db.query(UnitOperation).options(joinedload(UnitOperation.batch), joinedload(UnitOperation.equipment)).all())


def find_violations(operations: Iterable[UnitOperation], dependencies: Iterable[UnitOperationDependency]) -> list[Violation]:
    ops = list(operations)
    violations: list[Violation] = []
    emitted: set[tuple[str, tuple[int, ...]]] = set()

    def add(rule: str, op_ids: list[int], message: str) -> None:
        key = (rule, tuple(sorted(op_ids)))
        if key not in emitted:
            emitted.add(key)
            violations.append(Violation(rule=rule, operation_ids=op_ids, message=message))

    for op in ops:
        if op.start_date < op.batch.start_date or op.end_date > op.batch.end_date:
            add("batch_dates", [op.id], f"{op.name} lies outside batch {op.batch.name}'s dates.")

    for index, first in enumerate(ops):
        for second in ops[index + 1 :]:
            if first.equipment_id == second.equipment_id and max(first.start_date, second.start_date) < min(first.end_date, second.end_date):
                add("equipment_overlap", [first.id, second.id], f"{first.name} and {second.name} double-book {first.equipment.name}.")
            if first.batch_id == second.batch_id:
                earlier, later = (first, second) if TYPE_ORDER[first.type.value] < TYPE_ORDER[second.type.value] else (second, first)
                if TYPE_ORDER[earlier.type.value] != TYPE_ORDER[later.type.value] and later.start_date < earlier.end_date:
                    add("sequence", [earlier.id, later.id], f"{later.name} ({later.type.value}) starts before earlier operation {earlier.name} ({earlier.type.value}) ends.")

    by_id = {op.id: op for op in ops}
    for dependency in dependencies:
        source, target = by_id.get(dependency.from_unitop_id), by_id.get(dependency.to_unitop_id)
        if source and target and target.start_date < source.end_date:
            add("dependency", [source.id, target.id], f"{target.name} starts before dependency {source.name} ends.")
    return violations


def current_violations(db: Session) -> list[Violation]:
    return find_violations(operations_with_relations(db), db.query(UnitOperationDependency).all())
