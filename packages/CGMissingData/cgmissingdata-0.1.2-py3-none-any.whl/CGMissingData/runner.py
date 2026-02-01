from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, List, Dict

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

DEFAULT_TARGET_COL = "LBORRES"
DEFAULT_FEATURE_COLS = ("TimeSeries", "TimeDifferenceMinutes", "USUBJID")

def mean_absolute_percentage_error(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    mask = y_true != 0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

def _mask_df(df: pd.DataFrame, rng: np.random.Generator, rate: float) -> pd.DataFrame:
    arr = df.to_numpy(dtype=float)
    mask = rng.random(arr.shape) < rate
    arr[mask] = np.nan
    return pd.DataFrame(arr, columns=df.columns, index=df.index)

@dataclass(frozen=True)
class BenchmarkConfig:
    test_size: float = 0.20
    random_state: int = 42
    imputer_random_state: int = 42
    rf_n_estimators: int = 200
    knn_k: int = 5

def run_missingness_benchmark(
    data_path: str,
    target_col: str = DEFAULT_TARGET_COL,
    feature_cols: Sequence[str] = DEFAULT_FEATURE_COLS,
    mask_rates: Sequence[float] = (0.05, 0.10, 0.20, 0.30, 0.40),
    config: BenchmarkConfig = BenchmarkConfig(),
) -> pd.DataFrame:
    """
    Load CSV -> split train/val -> mask FEATURES -> MICE impute -> train RF + KNN -> return MAPE + R2.
    """
    df = pd.read_csv(data_path)

    needed = [target_col] + list(feature_cols)
    missing_cols = [c for c in needed if c not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV missing required columns: {missing_cols}")

    # baseline complete-case for required columns
    df = df[needed].dropna().copy()

    X = df[list(feature_cols)].reset_index(drop=True)
    y = df[target_col].reset_index(drop=True)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=config.test_size, random_state=config.random_state
    )

    rows: List[Dict[str, object]] = []
    for rate in mask_rates:
        rng = np.random.default_rng(100 + int(rate * 100))

        # mask FEATURES independently in train/val
        X_train_masked = _mask_df(X_train, rng, rate)
        X_val_masked   = _mask_df(X_val,   rng, rate)

        # MICE: fit on train only (avoid leakage)
        imputer = IterativeImputer(random_state=config.imputer_random_state)
        X_train_imp = imputer.fit_transform(X_train_masked)
        X_val_imp   = imputer.transform(X_val_masked)

        # Random Forest
        rf = RandomForestRegressor(
            n_estimators=config.rf_n_estimators,
            n_jobs=-1,
            random_state=config.random_state,
        )
        rf.fit(X_train_imp, y_train)
        rf_pred = rf.predict(X_val_imp)

        # KNN 
        scaler = StandardScaler()
        Xtr_sc = scaler.fit_transform(X_train_imp)
        Xva_sc = scaler.transform(X_val_imp)

        knn = KNeighborsRegressor(n_neighbors=config.knn_k)
        knn.fit(Xtr_sc, y_train)
        knn_pred = knn.predict(Xva_sc)

        y_val_np = y_val.to_numpy(dtype=float)
        for name, pred in [("Random Forest", rf_pred), ("KNN", knn_pred)]:
            rows.append({
                "MaskRate": f"{int(rate*100)}%",
                "Model": name,
                "MAPE": mean_absolute_percentage_error(y_val_np, pred),
                "R2": float(r2_score(y_val_np, pred)),
            })

    return pd.DataFrame(rows).sort_values(["MaskRate", "MAPE", "Model"]).reset_index(drop=True)
