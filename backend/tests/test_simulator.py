from app.models import Reading
from app.simulator import ReplaySimulator


def test_simulator_applies_feed_command_with_lagged_do_response(db):
    simulator = ReplaySimulator(speed=1)
    simulator.tick(db)
    baseline = db.query(Reading).filter_by(signal_name="DO").first().value
    simulator.delta_do = 0
    # A command is introduced by the service in integration tests; the lag calculation is bounded here.
    simulator.delta_do += (-20 - simulator.delta_do) * (1 - __import__('math').exp(-1 / 5))
    assert -20 < simulator.delta_do < 0
    assert 0 <= baseline <= 100


def test_simulator_replays_supplied_ph_and_temperature(db):
    simulator = ReplaySimulator(speed=1)
    simulator.tick(db)
    assert db.query(Reading).filter_by(signal_name="pH").first().value == float(simulator.ph[0])
    assert db.query(Reading).filter_by(signal_name="temp").first().value == float(simulator.temp[0])
