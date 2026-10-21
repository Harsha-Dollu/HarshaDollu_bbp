import numpy as np

from app.services.forecasting import HISTORY_MINUTES, HORIZON_MINUTES, evaluation, windows


def test_forecast_windows_have_expected_history_and_horizon_shapes():
    x, y = windows(np.arange(100, dtype=float), np.arange(100, dtype=float))
    assert x.shape == (30, HISTORY_MINUTES * 2)
    assert y.shape == (30, HORIZON_MINUTES)


def test_held_out_evaluation_compares_against_persistence_baseline():
    results = evaluation()
    assert "held-out chronological test" in results["split"]
    assert results["ridge_mae"] >= 0 and results["persistence_mae"] >= 0
