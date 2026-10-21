from functools import lru_cache
from pathlib import Path

import csv
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy.orm import Session

from ..models import Prediction, Reading

HISTORY_MINUTES, HORIZON_MINUTES = 60, 10
DATA_DIR = Path(__file__).resolve().parents[3] / "data_kit"


def load_signals(path: Path) -> dict[str, np.ndarray]:
    points: dict[float, dict[str, float]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle): points.setdefault(float(row["time_h"]), {})[row["signal_name"]] = float(row["value"])
    rows = [points[t] for t in sorted(points)]
    return {signal: np.array([row[signal] for row in rows]) for signal in ("DO", "feed_rate", "pH", "temp")}


def load_run(path: Path) -> tuple[np.ndarray, np.ndarray]:
    signals = load_signals(path)
    return signals["DO"], signals["feed_rate"]


def windows(do: np.ndarray, feed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y = [], []
    for index in range(HISTORY_MINUTES, len(do) - HORIZON_MINUTES):
        x.append(np.concatenate((do[index - HISTORY_MINUTES:index], feed[index - HISTORY_MINUTES:index])))
        y.append(do[index:index + HORIZON_MINUTES])
    return np.asarray(x), np.asarray(y)


@lru_cache(maxsize=1)
def trained_model():
    train_pairs = [load_run(DATA_DIR / name) for name in ("run_A.csv", "run_B.csv")]
    train_x, train_y = zip(*(windows(do, feed) for do, feed in train_pairs))
    model = Ridge(alpha=10.0).fit(np.vstack(train_x), np.vstack(train_y))
    return model


@lru_cache(maxsize=1)
def evaluation() -> dict[str, float | str]:
    do, feed = load_run(DATA_DIR / "run_C.csv")
    x, y = windows(do, feed)
    predicted = trained_model().predict(x)
    baseline = np.repeat(x[:, HISTORY_MINUTES - 1:HISTORY_MINUTES], HORIZON_MINUTES, axis=1)
    return {"split": "Train: runs A+B; held-out chronological test: run C. Windows never cross runs.", "ridge_mae": round(float(mean_absolute_error(y, predicted)), 3), "ridge_rmse": round(float(mean_squared_error(y, predicted) ** 0.5), 3), "persistence_mae": round(float(mean_absolute_error(y, baseline)), 3), "persistence_rmse": round(float(mean_squared_error(y, baseline) ** 0.5), 3)}


def create_forecast(db: Session) -> list[Prediction]:
    readings = db.query(Reading).filter(Reading.signal_name.in_(["DO", "feed_rate"])).order_by(Reading.process_time_h).all()
    by_time: dict[float, dict[str, float]] = {}
    for reading in readings: by_time.setdefault(reading.process_time_h, {})[reading.signal_name] = reading.value
    complete = [(time, item) for time, item in sorted(by_time.items()) if {"DO", "feed_rate"} <= item.keys()]
    if len(complete) < HISTORY_MINUTES: raise ValueError("At least 60 process-minutes of DO and feed_rate readings are required.")
    latest = complete[-HISTORY_MINUTES:]
    feature = np.array([[item["DO"] for _, item in latest] + [item["feed_rate"] for _, item in latest]])
    values = trained_model().predict(feature)[0]
    made_at = latest[-1][0]
    predictions = [Prediction(made_at_process_time_h=made_at, target_process_time_h=made_at + (i + 1) / 60, value=float(value), model_name="ridge_60m_10m") for i, value in enumerate(values)]
    db.add_all(predictions); db.commit()
    return predictions
