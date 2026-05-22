# Dashboard — Système de Prévision et d'Optimisation des Stocks GE

Prototype Streamlit "Human-in-the-loop" pour la Phase 4 du mémoire.

## Lancement local

```bash
# Depuis la racine du projet
pip install -r dashboard/requirements_dashboard.txt
streamlit run dashboard/app.py
```

Ouvre automatiquement http://localhost:8501.

## Pré-requis

- Modèles entraînés présents dans `models/` :
  - `xgboost_optuna_final.pkl` (modèle principal — quantité)
  - `lstm_time_to_event.pt` (date probable)
- Splits parquet dans `data/processed/` :
  - `split_train.parquet`, `split_val.parquet`, `split_test.parquet`
- Dataset enrichi : `data/processed/dataset_ml_enrichi.parquet`
- Rapport modélisation : `reports/rapport_modelisation.json`

## Structure

```
dashboard/
├── app.py              # Accueil + KPIs
├── pages/              # Pages Streamlit (multipage auto)
├── components/         # Widgets réutilisables
├── utils/              # Inference, encodage, confiance, data loader
├── assets/             # CSS / images
└── requirements_dashboard.txt
```

## Format d'upload attendu (page Données)

Le fichier doit contenir les 28 features encodées (suffixes `_freq`, `_enc`) et la colonne `qte_demandee`. Voir `utils/inference.py` pour la liste complète.

**Mode A — déjà encodé** (MVP) : utiliser un parquet/csv issu du pipeline Phase 2bis.
**Mode B — brut** : non supporté dans le MVP (cf. PHASE4_DASHBOARD.md §4.3).

## Liens

- Plan détaillé : `../PHASE4_DASHBOARD.md` (gitignored)
- Rapport modélisation : `../reports/rapport_modelisation.json`
