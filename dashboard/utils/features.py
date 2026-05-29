"""Constantes de features partagées — sans dépendances lourdes (pas de torch/xgboost).

Source de vérité : doit rester strictement identique au notebook
`notebooks/03_model_training.ipynb` (cellules 4 et 26).
"""
from __future__ import annotations

FEATURES: list[str] = [
    "prix",
    "delai_demande_jours",
    "code_client_freq",
    "code_article_freq",
    "est_jour_ferie_cmd",
    "est_jour_ferie_liv_dem",
    "pluie_mm_liv_dem",
    "vent_max_kmh_liv_dem",
    "temp_min_liv_dem",
    "ipi_valeur",
    "annee_cmd",
    "mois_cmd",
    "trimestre_cmd",
    "semaine_cmd",
    "jour_semaine_cmd",
    "est_fin_mois_cmd",
    "jour_semaine_liv_dem",
    "statut_enc",
    "devise_enc",
    "pays_enc",
    "famille_activite_client_enc",
    "famille_activite_article_enc",
    "segment_enc",
    "type_activite_enc",
    "est_weekend_liv_dem",
    "est_vacances_scolaires_liv_dem",
    "est_periode_peak_liv_dem",
    "est_periode_covid",
]

TARGET_QTE = "qte_demandee"

FEATURES_V2: list[str] = FEATURES + [
    "qte_lag_1",
    "qte_lag_7",
    "qte_lag_30",
    "qte_roll_mean_7",
    "qte_roll_mean_30",
    "qte_roll_mean_90",
    "qte_roll_std_30",
    "qte_roll_mean_30_client",
    "qte_roll_std_30_client",
    "qte_roll_mean_30_article",
    "qte_roll_std_30_article",
    "nb_cmd_30j_couple",
    "nb_jours_depuis_derniere_cmd",
    "prix_lag_1",
    "prix_delta_pct",
    "cumul_qte_annee",
    "te_couple",
    "te_client",
    "te_article",
]

FEATURES_LSTM: list[str] = [
    "mois_cmd",
    "trimestre_cmd",
    "qte_demandee",
    "prix",
    "delai_demande_jours",
    "est_periode_peak_liv_dem",
    "est_periode_covid",
    "ipi_valeur",
]

SEQ_LEN = 6
