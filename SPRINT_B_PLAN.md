# Sprint B — Plan d'exécution détaillé

> **Date :** 2026-05-29
> **Source :** [AMELIORATIONS.md](AMELIORATIONS.md) §8 Sprint B (items 9-15)
> **Branche :** `master` (commits directs validés par l'utilisateur)
> **Objectif :** consolider les acquis Sprint A et ajouter la **valeur jury** (DDMRP, backtest interactif, drift, tests, HITL opérationnel)
> **Durée cible :** 7-8 jours effectifs

---

## 0. Verrou identifié en amont — Dépendances Sprint A

**Prérequis pour démarrer Sprint B :**

| Livrable Sprint A | Utilisé par | Statut requis |
|---|---|---|
| `models/xgboost_optuna_v2.pkl` + features v2 (47 cols) | C1 (stacking), C5 (what-if) | **Indispensable** |
| `models/xgboost_residuel.pkl` (Sprint A C2) | C1 (stacking entry) | Souhaitable |
| `models/lgbm_quantile_p{10,50,90}.pkl` (Sprint A C3) | C5 (what-if intervalle) | **Indispensable** |
| `models/xgboost_segment_A.pkl` + `segment_abc` (Sprint A C7) | C2 (backtest segmenté) | Souhaitable |
| `data/processed/split_*_v3_features.parquet` | C1, C2, C5 | **Indispensable** |
| `reports/sprint_a_chantier1_metrics.json` | C8 (rapport consolidé) | Indispensable |

**Action préalable (Step 0, ~0.5 j) :**
- Vérifier la présence de tous les `.pkl` + `.json` ci-dessus
- Si LightGBM quantile manquant : reprendre Sprint A Chantier 3 d'abord
- Créer `dashboard/utils/stock_mock.py` : générateur de stock initial fictif par article (utilisé par DDMRP C3 et alerte rupture)
- Documenter l'environnement de retrain dans `requirements.txt` (pin des versions exactes)

**Livrable Step 0 :** checklist `SPRINT_B_PREFLIGHT.md` cochée + mock stock disponible.

---

## Ordre d'exécution proposé (avec dépendances)

```
Step 0  ──→  C6 (tests utils)  ─┐
            ─→  C3 (DDMRP)      │
            ─→  C4 (drift PSI)  ├──→  C8 (rapports + model card)
                                │
            ─→  C1 (stacking)  ─┤
                  ↓             │
                  C2 (backtest) ─┤
                  ↓             │
                  C5 (what-if) ─┤
                  ↓             │
                  C7 (retrain.py) ┘
```

| # | Chantier | Effort | Dépend de | Parallélisable |
|---|---|---|---|---|
| 0 | Pré-flight (vérif assets Sprint A + mock stock) | 0.5 j | — | — |
| 6 | Tests unitaires `dashboard/utils/` + CI minimaliste | 1.0 j | 0 | Oui (avec C3/C4) |
| 3 | Baseline **DDMRP** + comparaison IA vs DDMRP | 1.5 j | 0 | Oui |
| 4 | **Drift detection PSI** (dashboard) | 0.5 j | 0 | Oui |
| 1 | **CatBoost + stacking** (Ridge meta-learner) | 1.5 j | 0 | — |
| 2 | **Backtest interactif** semaine par semaine (page dashboard) | 1.5 j | 1 | — |
| 5 | **What-if simulation** (page Prévisions) | 1.0 j | 1 | — |
| 7 | Script `src/retrain.py` fonctionnel + UI bouton | 0.5 j | 1 | Oui (avec C5) |
| 8 | Mise à jour rapports + model card + AMELIORATIONS.md (statuts) | 0.5 j | tous | — |
| **Total** | | **8.0 j** | | |

> **Optimisation possible :** C3, C4, C6 sont parallélisables → Sprint B compressible à ~5-6 jours en travail séquentiel intense.

---

## Chantier 6 — Tests unitaires `dashboard/utils/`

**Notebook :** non — fichiers tests `dashboard/tests/test_*.py`.

**Périmètre :**

| Module ciblé | Tests à écrire | Couverture cible |
|---|---|---|
| `dashboard/utils/features.py` | `test_features_list_matches_model`, `test_no_silent_drop` | 90 % |
| `dashboard/utils/inference.py` (si existe) | `test_predict_qte_shape`, `test_predict_qte_non_negative`, `test_predict_qte_handles_unknown_couple` | 85 % |
| `dashboard/utils/confidence.py` | `test_confidence_branch_green`, `_orange`, `_red`, `_unknown` (4 branches §5.6 AMELIORATIONS) | 100 % |
| `dashboard/utils/data_loader.py` | `test_schemas_present`, `test_required_columns_not_null` | 80 % |

**Livrables :**
- `dashboard/tests/conftest.py` avec fixtures `tiny_split_train` (50 lignes échantillonnées), `xgb_dummy_model`
- `.github/workflows/ci.yml` : matrix Python 3.11/3.13, `ruff check . && pytest dashboard/tests`
- Badge build vert dans `README.md`

**Gain mémoire :** preuve de qualité industrielle, défense facile devant jury question « comment vous garantissez que ça marche ? »

---

## Chantier 3 — Baseline DDMRP + comparaison IA vs DDMRP

**Notebook :** `notebooks/09_baseline_ddmrp.ipynb`.

**Méthode (référence Ptak & Smith, 2016) :**

1. **Strategic Inventory Positioning** : top 100 articles (~80 % volume) sélectionnés via Pareto sur train
2. **Buffer Profiles & Levels** par article :
   - `ADU` (Average Daily Usage) = moyenne `qte_demandee/jour` sur 90 j glissants (train uniquement)
   - `LT` (Lead Time) = médiane `delai_demande_jours` du couple
   - `Variability` : coefficient de variation de la qte sur 90 j
   - **Red Zone** = `ADU × LT × variability_factor`
   - **Yellow Zone** = `ADU × LT`
   - **Green Zone** = `ADU × LT × order_cycle` (order_cycle = 7 j par défaut)
3. **Net Flow Position (NFP)** = `On-Hand + On-Order − Qualified Demand`
   - `On-Hand` : stock mock (généré par `stock_mock.py` Step 0)
   - `On-Order` : commandes en cours (mock = 0 pour simplifier)
   - `Qualified Demand` = commandes confirmées dans la fenêtre LT
4. **Décision de réappro** : si `NFP < Top of Yellow` → commander `Top of Green − NFP`
5. **Simuler 2025** semaine par semaine : DDMRP émet des commandes, on compare la quantité prédite vs la qte réelle
6. **Métriques DDMRP** :
   - MAE DDMRP vs MAE XGBoost v2
   - Taux de rupture évité (stock_dispo > 0 toujours)
   - Taux de sur-stock (stock_dispo / ADU > seuil)
   - Coût total = α × ruptures + β × sur-stock (mêmes α/β que Sprint A C4)

**Livrables :**
- `notebooks/09_baseline_ddmrp.ipynb` avec tableau comparatif **DDMRP vs IA vs hybride**
- `dashboard/utils/ddmrp.py` : fonctions `compute_buffers()`, `compute_nfp()`, `decide_replenishment()` réutilisables
- Section dédiée dans `reports/rapport_phase3_modelisation.md`

**Valeur mémoire :** ancre le projet dans la littérature opérationnelle, neutralise la critique « réinvention de la roue ». Réponse directe à AMELIORATIONS §6bis.1.

---

## Chantier 4 — Drift detection PSI

**Module :** `dashboard/utils/drift.py` + page `dashboard/pages/4_Drift.py`.

**Méthode (PSI = Population Stability Index) :**

```python
def psi(reference, current, bins=10):
    """PSI < 0.1 : pas de drift | 0.1-0.25 : drift modéré | > 0.25 : drift significatif"""
    bin_edges = np.quantile(reference, np.linspace(0, 1, bins + 1))
    ref_pct = np.histogram(reference, bin_edges)[0] / len(reference)
    cur_pct = np.histogram(current,   bin_edges)[0] / len(current)
    eps = 1e-6
    return np.sum((cur_pct - ref_pct) * np.log((cur_pct + eps) / (ref_pct + eps)))
```

**Features surveillées (top 6 par permutation importance Sprint A C1.8) :**
- `prix`, `code_article_freq`, `ipi_valeur`, `te_couple`, `qte_lag_1`, `nb_jours_depuis_derniere_cmd`

**Référence** : distribution train_v3. **Current** : upload CSV utilisateur ou test_v3 par défaut.

**UI dashboard :**
- Tableau coloré (vert/orange/rouge selon PSI)
- Bar chart PSI par feature
- Bandeau d'alerte : "3 features ont un drift > 0.25 — modèle potentiellement obsolète"

**Livrables :**
- `dashboard/utils/drift.py` (fonction `psi` + `compute_drift_report`)
- `dashboard/pages/4_Drift.py`
- Tests unitaires `test_psi_known_distributions` (Chantier 6)

---

## Chantier 1 — CatBoost + stacking

**Notebook :** `notebooks/10_catboost_stacking.ipynb`.

**Étape 1 — CatBoost solo :**
- Mêmes features v2 (47 cols) que XGBoost v2
- Optuna **150 essais** (CatBoost converge plus vite)
- Comparaison MAE/RMSE/R²/WAPE vs XGBoost v2

**Étape 2 — Stacking (Ridge meta-learner) :**
```
                    XGBoost-log v2  ─┐
                    XGBoost-Tweedie ─┤
                    LightGBM-log    ─┼──→  Ridge sur train_val_split  ──→  pred_test
                    CatBoost        ─┤
                    XGBoost résiduel┘
```

- Prédictions out-of-fold sur train via `cross_val_predict(TimeSeriesSplit(5))`
- Ridge avec `alpha` tuné par `RidgeCV`
- Métriques : gain MAE attendu +1 à +3 %

**Livrables :**
- `models/catboost_v2.pkl` + `models/catboost_v2_params.json`
- `models/stacking_ridge.pkl` + `models/stacking_components.json` (liste des modèles base)
- Comparaison tabulée des 6 modèles dans le notebook

**Gain attendu :** MAE 10.5 → 10.0 (selon résultats Sprint A v2)

---

## Chantier 2 — Backtest interactif semaine par semaine

**Page :** `dashboard/pages/5_Backtest.py`.

**UX cible (slider temporel + courbes) :**

1. **Slider semaine** : curseur de la semaine 1 (2025-01-06) à la semaine 51 (2025-12-22)
2. **Sélecteur modèle** : XGBoost v2 / Stacking / Baseline / DDMRP (multi-select)
3. **Courbe cumulée** : `qte_reelle_cumulee` vs `qte_predite_cumulee` jusqu'à la semaine sélectionnée
4. **Métriques rolling 4 semaines** : MAE, WAPE, taux de rupture, taux de sur-stock
5. **€ économisés / perdus cumulés** : `α × ruptures_evitees − β × surstock_genere`
6. **Tableau détaillé** : top 10 erreurs absolues de la semaine

**Données précalculées (au lancement du dashboard, mises en cache) :**
- DataFrame `backtest_2025.parquet` avec colonnes `(date_cmd, code_client, code_article, qte_reelle, pred_xgb_v2, pred_stacking, pred_baseline, pred_ddmrp)`
- Généré une fois en fin de Sprint A puis sauvegardé

**Livrables :**
- `dashboard/pages/5_Backtest.py`
- `data/processed/backtest_2025.parquet`
- Capture vidéo de démo (10 sec, slider en action) pour la slide soutenance

**Valeur jury :** **🟢🟢 très fort** — c'est LA preuve concrète "si on avait utilisé le modèle en 2025 voici ce qui se serait passé". Réponse directe à AMELIORATIONS §5.3.

---

## Chantier 5 — What-if simulation (page Prévisions)

**Page :** ajout dans `dashboard/pages/3_Previsions.py` (section "Simulation").

**UX :**
- Sélection d'une ligne du dataset test (autocomplétion par couple)
- Affichage des features actuelles + sliders/inputs pour :
  - `prix` (±50 %)
  - `delai_demande_jours` (0-30)
  - `ipi_valeur` (±10 %)
  - `est_periode_peak_liv_dem` (toggle)
  - `est_jour_ferie_liv_dem` (toggle)
- Re-prédiction live (XGBoost v2 + intervalle P10-P90 via quantile LGBM)
- Graphique : prédiction actuelle vs simulée + variation %

**Livrables :**
- Section "Simulation what-if" dans `3_Previsions.py`
- Helper `dashboard/utils/whatif.py` (`simulate_prediction(row, overrides) -> (pred, p10, p90)`)
- Tests unitaires (chantier 6)

**Valeur jury :** effet démonstratif fort, montre l'IA "manipulable". Réponse à AMELIORATIONS §5.3.

---

## Chantier 7 — Script `retrain.py` fonctionnel

**Fichier :** `src/retrain.py` (nouveau, à la racine du projet).

**Fonctionnement :**
```python
# python src/retrain.py [--quick | --full]
# --quick : Optuna 30 essais (CI / smoke test, ~5 min)
# --full  : Optuna 300 essais comme Sprint A (~1-2 h)
```

**Étapes du script :**
1. Charger `data/processed/split_*_v3_features.parquet`
2. Charger `models/xgboost_optuna_v2_params.json` pour hyperparams par défaut
3. Re-fit avec Optuna (nombre d'essais selon flag)
4. Évaluer sur test
5. Comparer avec rapport précédent (`reports/sprint_a_chantier1_metrics.json`)
6. Sauvegarder modèle horodaté : `models/xgboost_optuna_v2_{YYYYMMDD_HHMM}.pkl`
7. Mettre à jour `models/xgboost_optuna_v2.pkl` (symlink ou copie du dernier)
8. Logger dans `logs/retrain_{YYYYMMDD_HHMM}.log`

**Intégration dashboard :**
- Page `2_IA.py` : bouton "Re-entraîner (rapide)" → `subprocess.Popen(['python', 'src/retrain.py', '--quick'])`
- Streaming du log en live via `st.empty().code()`

**Livrables :**
- `src/retrain.py`
- Mise à jour `dashboard/pages/2_IA.py` (bouton fonctionnel)
- README section "Re-entrainement"

---

## Chantier 8 — Rapports + Model card consolidés

**Fichiers à mettre à jour ou créer :**

1. **`reports/rapport_phase3_modelisation.md`** — ajouter :
   - Section Sprint B (CatBoost, stacking, DDMRP comparison)
   - Tableau récapitulatif tous modèles : v1 / v2 / Tweedie / LGBM / CatBoost / Stacking / DDMRP
   - Discussion : pourquoi stacking si gain marginal ?

2. **`reports/rapport_phase4_dashboard.md`** — ajouter :
   - Screenshots des nouvelles pages (Backtest, Drift, What-if)
   - Décisions UX justifiées
   - Parcours utilisateur "planificateur" en 3 étapes

3. **`docs/MODEL_CARD.md`** (créé Sprint A C8, à enrichir) :
   - Ajouter colonne "DDMRP comparison" dans métriques par segment
   - Section "Limites éthiques" enrichie avec données du backtest (où le modèle perd vs DDMRP ?)

4. **`AMELIORATIONS.md`** — mettre à jour les statuts §8 :
   - Items 9-15 cochés ✅
   - Section "Sprint C — Perspectives" reste à décrire

5. **`SPRINT_B_PLAN.md`** — ajouter section "Résultats réels" en fin de fichier après chaque chantier complété.

---

## Critères de succès par chantier

| Chantier | Critère de validation |
|---|---|
| 0 | Checklist pré-flight cochée ; mock stock présent |
| 6 | Couverture pytest ≥ 80 % sur `dashboard/utils/` ; CI verte |
| 3 | Tableau DDMRP vs IA publié ; au moins 1 métrique où DDMRP gagne (preuve d'analyse honnête) |
| 4 | PSI calculé sur 6 features ; page Drift accessible sans erreur |
| 1 | MAE stacking < min(MAE de chaque base) (sinon stacking abandonné, justifié dans notebook) |
| 2 | Backtest 51 semaines × 4 modèles précalculé ; slider fluide (< 200 ms refresh) |
| 5 | Simulation what-if : variation prix ±50 % change la prédiction de manière monotone |
| 7 | `python src/retrain.py --quick` se termine en < 10 min et produit un modèle évaluable |
| 8 | Rapports relus ; model card mise à jour ; AMELIORATIONS §8 items 9-15 cochés |

---

## Risques et mitigations

| Risque | Mitigation |
|---|---|
| CatBoost ne bat pas XGBoost v2 → stacking inutile | Garder XGBoost v2 comme modèle de production ; documenter pourquoi dans le rapport |
| Stacking overfit (gain val mais perte test) | TimeSeriesSplit strict pour les prédictions OOF ; tester sur 2 sous-périodes 2025 H1 vs H2 |
| Backtest 51 semaines × 4 modèles = précompute long (~1 h) | Calculer une seule fois en fin de Sprint A et stocker en parquet ; pas de recalcul à l'usage |
| DDMRP avec stock mock = artefact non défendable | Préciser dans le rapport : "stock mock = hypothèse de travail, méthode reste valide si stocks réels disponibles" |
| Drift PSI confond drift réel et bruit échantillon | Vérifier sur 2 splits train/train (même distribution) que PSI < 0.1 ; sinon recalibrer les bins |
| `subprocess.Popen` du retrain bloque l'UI Streamlit | Logger dans fichier + tail dans `st.empty()` via thread séparé ; OU lancer en arrière-plan avec PID stocké en session_state |
| Tests CI cassent sur GitHub Actions à cause de dépendances lourdes (XGBoost / CatBoost) | Mock les modèles dans `conftest.py` ; tests d'inférence avec `xgb_dummy_model` fixture (~50 lignes) |
| Page What-if : ré-encoder l'input utilisateur (catégorielles) est complexe | Limiter la simulation aux **features numériques only** ; documenter cette limite |

---

## Métriques de fin de Sprint B (à reporter dans `reports/sprint_b_summary.json`)

| Catégorie | Métrique cible |
|---|---|
| Modèle | MAE stacking < MAE XGBoost v2 OU décision documentée |
| Industrialisation | CI verte ; couverture tests > 80 % ; bouton retrain fonctionnel |
| Dashboard | 3 nouvelles pages opérationnelles (Backtest, Drift, What-if) |
| Mémoire | Section DDMRP comparison écrite + section éthique enrichie |
| Reproductibilité | `requirements.txt` pinné ; `python src/retrain.py --quick` E2E fonctionnel |

---

## Prochaines étapes immédiates

1. ✅ Valider ce plan avec l'utilisateur
2. ⏭ Attendre fin de Sprint A (notebook 04 en background) — vérifier que tous les livrables Sprint A sont sortis
3. ⏭ Décider quels chantiers Sprint A optionnels (résiduel, ABC, Prophet) sont des **prérequis bloquants** vs **améliorations bonus** pour Sprint B
4. ⏭ Lancer **Step 0** : pré-flight check + mock stock generator
5. ⏭ Enchaîner C6 (tests) en parallèle de C3 (DDMRP) — premiers gains rapides

---

*Document de travail Sprint B. À mettre à jour après chaque chantier complété (statut + résultats réels).*
