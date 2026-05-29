"""Re-entrainement XGBoost v2 avec Optuna.

Usage :
    python src/retrain.py [--quick | --full]
    --quick : 30 essais  (~5 min)
    --full  : 100 essais (~30 min)

Sorties :
    models/xgboost_optuna_v2_{YYYYMMDD_HHMM}.pkl
    models/xgboost_optuna_v2.pkl (copie du dernier)
    logs/retrain_{YYYYMMDD_HHMM}.log
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.utils.features import FEATURES_V2, TARGET_QTE  # noqa: E402

DATA = ROOT / "data" / "processed"
MODELS = ROOT / "models"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
MODELS.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)


def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("retrain")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def load_data(logger):
    logger.info("Chargement des splits v3...")
    df_train = pd.read_parquet(DATA / "split_train_v3_features.parquet")
    df_val = pd.read_parquet(DATA / "split_val_v3_features.parquet")
    df_test = pd.read_parquet(DATA / "split_test_v3_features.parquet")
    logger.info(f"Train={df_train.shape} Val={df_val.shape} Test={df_test.shape}")
    return df_train, df_val, df_test


def evaluate(y_true, y_pred):
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
        "WAPE": float(np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))),
    }


def run(n_trials: int, mode: str, logger: logging.Logger) -> dict:
    df_train, df_val, df_test = load_data(logger)
    X_train = df_train[FEATURES_V2]
    X_val = df_val[FEATURES_V2]
    X_test = df_test[FEATURES_V2]
    y_train = np.log1p(df_train[TARGET_QTE].clip(lower=0))
    y_val = np.log1p(df_val[TARGET_QTE].clip(lower=0))
    y_test = df_test[TARGET_QTE].values

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 400, 1500),
            "max_depth": trial.suggest_int("max_depth", 4, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.15, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 1.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 1.0, log=True),
            "random_state": 42,
            "tree_method": "hist",
            "verbosity": 0,
        }
        m = xgb.XGBRegressor(**params)
        m.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        pred = np.clip(np.expm1(m.predict(X_val)), 0, None)
        return mean_absolute_error(np.expm1(y_val), pred)

    logger.info(f"Lancement Optuna mode={mode} n_trials={n_trials}")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    logger.info(f"Best MAE val = {study.best_value:.4f}")

    best_params = study.best_params
    best_model = xgb.XGBRegressor(**best_params, random_state=42, tree_method="hist", verbosity=0)
    best_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    pred_test = np.clip(np.expm1(best_model.predict(X_test)), 0, None)
    metrics = evaluate(y_test, pred_test)
    logger.info(f"Metrics test : {metrics}")

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    snap_path = MODELS / f"xgboost_optuna_v2_{ts}.pkl"
    joblib.dump(best_model, snap_path)
    shutil.copy(snap_path, MODELS / "xgboost_optuna_v2.pkl")
    logger.info(f"Modele sauvegarde : {snap_path}")

    prev_metrics = None
    prev_path = REPORTS / "sprint_a_chantier1_metrics.json"
    if prev_path.exists():
        prev = json.loads(prev_path.read_text(encoding="utf-8"))
        prev_metrics = prev.get("test_metrics_v2")
        if prev_metrics:
            for k in metrics:
                if k in prev_metrics:
                    delta = (metrics[k] - prev_metrics[k]) / max(abs(prev_metrics[k]), 1e-6) * 100
                    logger.info(f"{k}: {metrics[k]:.4f} (prev {prev_metrics[k]:.4f}, delta {delta:+.2f}%)")

    out = {
        "mode": mode,
        "n_trials": n_trials,
        "timestamp": ts,
        "best_val_mae": float(study.best_value),
        "best_params": best_params,
        "metrics_test": metrics,
        "prev_metrics_test": prev_metrics,
        "snapshot": snap_path.name,
    }
    json.dump(out, open(REPORTS / f"retrain_{ts}.json", "w", encoding="utf-8"), indent=2)
    logger.info("Termine.")
    return out


def main():
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--quick", action="store_true", help="30 essais Optuna (~5 min)")
    g.add_argument("--full", action="store_true", help="100 essais Optuna (~30 min)")
    args = parser.parse_args()

    mode = "quick" if args.quick or not args.full else "full"
    n_trials = 30 if mode == "quick" else 100

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    log_file = LOGS / f"retrain_{ts}.log"
    logger = setup_logger(log_file)
    logger.info(f"=== Re-entrainement mode={mode} ===")
    try:
        run(n_trials, mode, logger)
    except Exception as exc:
        logger.exception(f"ECHEC : {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
