from fastapi.testclient import TestClient

from app.main import app


def test_seeded_schedule_is_available_and_shows_demo_violations():
    with TestClient(app) as client:
        response = client.get("/api/schedule?start_date=2026-10-01&end_date=2026-10-20")
    assert response.status_code == 200
    body = response.json()
    assert len(body["equipment"]) == 5
    assert {v["rule"] for v in body["violations"]} >= {"sequence", "equipment_overlap"}


def test_invalid_write_is_rejected_with_readable_violation_details():
    with TestClient(app) as client:
        schedule = client.get("/api/schedule").json()
        alpha = next(batch for batch in schedule["batches"] if batch["name"] == "Alpha antibody")
        equipment = next(item for item in schedule["equipment"] if item["name"] == "1.5L")
        response = client.post("/api/unit_operations", json={
            "name": "Conflicting operation", "type": "Seed", "status": "draft", "color": "#000000",
            "start_date": "2026-10-02", "end_date": "2026-10-03", "batch_id": alpha["id"], "equipment_id": equipment["id"],
        })
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["violations"][0]["rule"] == "equipment_overlap"
    assert "Conflicting operation" in detail["violations"][0]["message"]


def test_completed_operation_cannot_be_updated_or_deleted():
    with TestClient(app) as client:
        schedule = client.get("/api/schedule").json()
        alpha = next(batch for batch in schedule["batches"] if batch["name"] == "Alpha antibody")
        equipment = next(item for item in schedule["equipment"] if item["name"] == "1.5L")
        payload = {
            "name": "Completed spray", "type": "Spray", "status": "completed", "color": "#000000",
            "start_date": "2026-10-11", "end_date": "2026-10-13", "batch_id": alpha["id"], "equipment_id": equipment["id"],
        }
        created = client.post("/api/unit_operations", json=payload)
        assert created.status_code == 201
        op_id = created.json()["id"]
        assert client.put(f"/api/unit_operations/{op_id}", json=payload).status_code == 409
        assert client.delete(f"/api/unit_operations/{op_id}").status_code == 409
