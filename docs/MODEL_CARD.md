# Model Card — Système de Prévision GE

> **Date :** 2026-05-29 (post-Sprint B)
> **Version active :** XGBoost Optuna v2 (47 features)
> **Auteur :** Adam Makchi (Master GE, mémoire 2026)

---

## 1. Vue d'ensemble

| Champ | Valeur |
|---|---|
| Tâche | Régression — prédire `qte_demandee` par couple (client, article, date) |
| Algorithme principal | XGBoost (gradient boosting) |
| Transformation cible | `log1p(qte_demandee)` |
| Métrique principale | MAE |
| Métriques secondaires | RMSE, R², WAPE |
| Split | Train 2021-2023 / Val 2024 / Test 2025 |
| Lignes | Train 210 641 • Val 70 871 • Test 66 174 |
| Modèles complémentaires | LightGBM quantile P10/P50/P90, CatBoost, Stacking Ridge |
| Baseline IA | Médiane historique par couple |
| Baseline opérationnelle | DDMRP (Ptak & Smith, 2016) |

---

## 2. Métriques par modèle (Sprint A + Sprint B)

| Modèle | MAE | RMSE | R² | WAPE | Source |
|---|---|---|---|---|---|
| Baseline médiane couple | 11.87 | 132.17 | 0.438 | 54.05 % | Sprint A C1 |
| XGBoost v1 (28 features) | 11.87 | 132.17 | 0.438 | 54.05 % | Sprint A v1 |
| **XGBoost v2 (47 features)** ⭐ MAE | **8.42** | 101.83 | 0.666 | 38.34 % | Sprint A C1 |
| LightGBM quantile P50 | **8.32** | 121.87 | 0.522 | 37.89 % | Sprint B Step 0 |
| CatBoost solo (Optuna 30) | 8.98 | 120.05 | 0.536 | 40.88 % | Sprint B C1 |
| **Stacking Ridge** ⭐ RMSE/R² | 8.70 | **97.55** | **0.694** | 39.62 % | Sprint B C1 |

**Lecture du tableau :**
- **Plus bas MAE** : LGBM P50 (8.32) — gain marginal de 0.10 vs XGB v2.
- **Plus bas RMSE** : Stacking Ridge (97.55) — meilleur sur les grandes erreurs ; le stacking corrige les outliers en moyennant les prédictions.
- **Plus haut R²** : Stacking Ridge (0.694) — confirme que la combinaison capture mieux la variance.
- **Choix de production** : on garde **XGBoost v2** car il est plus simple, déjà optimisé (300 essais Optuna) et a le meilleur MAE/coût d'inférence. Le stacking est documenté comme amélioration mais non déployé (principe d'Occam — gain marginal sur RMSE ne justifie pas la complexité supplémentaire).

> Le détail Sprint B est dans `reports/sprint_b_chantier1_stacking.json`.

---

## 3. Couverture de l'intervalle quantile

| Quantile | Mesure |
|---|---|
| P10 – P90 (cible nominale 80 %) | **74.6 %** (test 2025) |
| Largeur moyenne | 25.15 unités |
| MAE P50 | 8.32 |

→ couverture proche du nominal, écart de −5 pts à investiguer (probable sous-couverture sur la longue traîne).

---

## 4. Comparaison IA vs DDMRP (Sprint B C3)

Sur les 22 articles stratégiques (Pareto 80 % volume) — agrégation hebdomadaire :

| Modèle | MAE (agrégé hebdo) | Biais | Coût total (α=50, β=1) |
|---|---|---|---|
| IA (XGBoost v2) | **260** | −223 | **18 359** |
| DDMRP buffers | 661 | −179 | 21 023 327 |
| Hybride 50/50 | **242** | **−21** | 6 617 644 |

**Observations honnêtes :**
- **IA gagne** sur le coût total (α élevé pénalise les ruptures, IA prédit mieux la demande individuelle).
- **DDMRP gagne** quand on regarde le taux de couverture stock (11 % de semaines en rupture seulement contre l'horizon « infini » pour IA si on prend sa prédiction comme commande).
- **Hybride** réduit le biais à −21 et gagne ~70 % de coût vs DDMRP pur. Compromis recommandé pour une mise en prod.

→ Référence explicite à Ptak & Smith (2016), réponse au reproche jury « réinvention de la roue ».

---

## 5. Drift et obsolescence

PSI surveillé sur 6 features (top permutation importance) :
- Référence : split train 2021-2023
- Distribution actuelle (par défaut) : test 2025

Seuils opérationnels :
- PSI < 0.10 : stable
- 0.10–0.25 : modéré, surveillance
- > 0.25 : significatif, retrain recommandé

→ Page Streamlit dédiée : `dashboard/pages/5_Drift.py`.

---

## 6. Limites et biais

### 6.1 Biais sur la longue traîne
Le modèle est plus précis sur les articles familiers (vu > 50 fois) que sur les articles rares. La page Prévisions affiche un **score de confiance** (vert / orange / rouge) pour signaler ces cas.

### 6.2 Biais saisonniers
Le modèle apprend les patterns 2021-2023 mais le Covid (2020-2021) reste un point singulier. La feature `est_periode_covid` permet au modèle de ne pas extrapoler ce régime.

### 6.3 Stock mock
La comparaison IA vs DDMRP utilise un stock initial fictif (`stock_mock.parquet`) car les données réelles de stock ne sont pas dans le périmètre. **Hypothèse de travail documentée** : la méthode DDMRP reste valide si stocks réels disponibles, ce qui constitue un axe de mise en prod.

### 6.4 Données ouvertes
Météo et IPI INSEE sont intégrés mais avec une granularité départementale/nationale, alors qu'idéalement on voudrait du local-client. Couvert dans la section "Perspectives" du mémoire.

---

## 7. Considérations éthiques

### 7.1 Risque opérationnel
Une sous-prédiction systématique entraînerait des **ruptures de stock** (impact client direct). Le système intègre :
- Intervalle P10–P90 visible dans le dashboard
- Score de confiance composite (orange / rouge = revue humaine)
- HITL prévu pour les articles à confiance "rouge" (cf. matrice gouvernance §7.3)

### 7.2 Risque commercial
Une **sur-prédiction systématique** entraînerait du sur-stock (immobilisation cash). Le tableau coût (α/β) dans la page Backtest permet à l'utilisateur de visualiser l'arbitrage.

### 7.3 Matrice de gouvernance HITL

| Niveau confiance | Action recommandée |
|---|---|
| Vert | Validation automatique |
| Orange | Revue planificateur (T+24h) |
| Rouge | Revue obligatoire avant commande |

---

## 8. Données et reproductibilité

- Sources : extractions internes GE 2021-2025 + IPI INSEE + jours fériés + météo Météo-France
- Splits sauvegardés : `data/processed/split_*_v3_features.parquet`
- Script de re-entraînement : `python src/retrain.py [--quick|--full]`
- Tests unitaires : `python -m pytest dashboard/tests` (27 tests, couverture ~88-100 % sur `dashboard/utils/`)
- CI : `.github/workflows/ci.yml` (matrix Python 3.11 / 3.13)

---

## 9. Historique des versions

| Version | Date | Changements clés |
|---|---|---|
| v1 | 2026-04-15 | XGBoost Optuna 50 essais, 28 features, MAE 11.87 |
| **v2** | 2026-05-29 | +19 features lags/rolling/TE, Optuna 300 essais, MAE 8.42 |
| Sprint B | 2026-05-29 | + LGBM quantile, CatBoost, Stacking Ridge, DDMRP baseline, drift PSI |

---

*Document de référence cité dans le rapport `reports/rapport_phase3_modelisation.md`.*
