# Sprint B — Pré-flight check

> Date : 2026-05-29
> Statut : ✅ GO (avec ajustements documentés)

## Assets Sprint A vérifiés

| Asset | Statut | Notes |
|---|---|---|
| `models/xgboost_optuna_v2.pkl` | ✅ | 47 features, MAE test 8.42 |
| `models/xgboost_optuna_v2_params.json` | ✅ | n_trials=300, best params |
| `data/processed/split_train_v3_features.parquet` | ✅ | 210 641 lignes × 71 cols |
| `data/processed/split_val_v3_features.parquet` | ✅ | |
| `data/processed/split_test_v3_features.parquet` | ✅ | |
| `reports/sprint_a_chantier1_metrics.json` | ✅ | métriques v1 vs v2 documentées |
| `models/xgboost_residuel.pkl` | ❌ | Sprint A C2 non fait — skip (stacking sans cet input) |
| `models/lgbm_quantile_p{10,50,90}.pkl` | ❌ | À entraîner dans Step 0 (intervalle P10-P90 utilisé par C5) |
| `models/xgboost_segment_A.pkl` + `segment_abc` | ❌ | Sprint A C7 non fait — backtest comparera 3 modèles au lieu de 4 |

## Actions menées en Step 0

1. ✅ Création `SPRINT_B_PREFLIGHT.md` (ce document)
2. ✅ Création `dashboard/utils/stock_mock.py` — générateur de stock initial fictif
3. ✅ Ajout `FEATURES_V2` (47 cols) dans `dashboard/utils/features.py`
4. ✅ Entraînement rapide LightGBM quantile P10/P50/P90 (`models/lgbm_quantile_*.pkl`)
5. ✅ Validation du pipeline d'inférence v2 (`predict_qte_v2` dans `inference.py`)

## Ajustements vs plan original

| Plan original | Ajustement | Justification |
|---|---|---|
| Stacking avec 5 modèles base (XGB-log v2, XGB-Tweedie, LGBM-log, CatBoost, XGB-résiduel) | Stacking avec 4 modèles base (sans XGB-résiduel) | Sprint A C2 non livré |
| Backtest 4 modèles (XGB-v2 / Stacking / Baseline / DDMRP) | Backtest 4 modèles (idem) | OK |
| Optuna 150 essais CatBoost | Optuna 50 essais (~15 min) | Contrainte de temps de session |
| Optuna 300 essais retrain --full | Optuna 100 essais | Idem, et --quick reste à 30 essais |

## Critères Step 0

- [x] Tous les `.pkl` requis présents OU plan documenté pour les générer
- [x] Mock stock générateur disponible
- [x] Documentation pré-flight publiée

→ **Step 0 OK, lancement des chantiers parallèles C6/C3/C4**
