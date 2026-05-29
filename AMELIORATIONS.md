# Axes d'amélioration — Projet Mémoire GE

> **Date d'audit :** 2026-05-28
> **Périmètre :** Phases 1 → 4 du projet « Système de Prévision et d'Optimisation des Stocks »
> **Objectif North Star :** précision > 60 % (WAPE actuelle = **54.05 %** → précision **45.95 %**)
> **Écart au North Star :** ~14 points de WAPE à gagner

Ce document recense, pour chaque phase du pipeline, les améliorations à fort impact (court terme), moyen impact (avant soutenance) et structurelles (vision production). Chaque item indique : **constat → action → gain attendu**.

---

## 0. Synthèse exécutive

| Domaine | État actuel | Cible | Priorité |
|---|---|---|---|
| Quantité prédite (XGBoost Optuna) | MAE **11.87**, WAPE **54 %**, R² **0.438** | WAPE < 40 % | 🔴 P0 |
| Date prédite (LSTM) | Précision ±7j **25.5 %**, MAE **24.5 j** | > 50 % à ±7j | 🔴 P0 |
| Gain vs baseline naïve | **−9 % MAE** seulement | > 25 % | 🟠 P1 |
| Feature engineering temporel | Aucun lag / rolling | Lags 1/7/30 + roll 7/30/90 | 🔴 P0 |
| Dashboard prod-ready | MVP local, pas de tests | Tests + retrain auto | 🟠 P1 |
| Reproductibilité | Pas de MLflow / DVC / CI | Tracking + versioning | 🟡 P2 |

**Les 5 chantiers à ouvrir en priorité avant la soutenance :**
1. **Features temporelles** (lags + rolling client/article/couple, target encoding fold temporel) — plus gros levier MAE
2. **Modèle résiduel** (XGBoost prédit `y − baseline_couple`) — gain rapide +5 à +10 %
3. **Quantile regression** (LightGBM P10/P50/P90) — intervalles honnêtes pour le dashboard
4. **Reformulation du problème de date** (LSTM → survival / Prophet par couple)
5. **Walk-forward CV** + **MAE pondérée business** (asymétrie stockout/surstock)

---

## 1. Phase 1 — Data Engineering

### 1.1 Traçabilité et reproductibilité
- **Constat :** notebook [01_data_cleaning.ipynb](notebooks/01_data_cleaning.ipynb) produit `dataset_ml_final.parquet` mais aucune trace des choix d'imputation / des lignes droppées.
- **Action :**
  - Ajouter un **journal de nettoyage** (CSV) listant `(étape, nb_lignes_avant, nb_lignes_après, raison)`.
  - Versionner le parquet via **DVC** ou hash SHA-256 commit dans `data/processed/CHECKSUMS.md`.
- **Gain :** soutenabilité du mémoire (jury pourra vérifier), répétabilité scientifique.

### 1.2 Qualité des données livraisons
- **Constat :** seules les commandes sont nettoyées dans le notebook visible. Le rapprochement commande ↔ livraison n'a pas de métrique de qualité publiée.
- **Action :** publier un tableau « taux de rapprochement », « écart médian délai promis vs réel », « commandes orphelines ».

### 1.3 Fichiers parasites à nettoyer
- Notebooks de scratch présents : [notebooks/ipi_test.ipynb](notebooks/ipi_test.ipynb), [notebooks/test_meteo.ipynb](notebooks/test_meteo.ipynb), [notebooks/inderstand.ipynb](notebooks/inderstand.ipynb).
- `analyse.ipynb` et `ml.ipynb` à la racine devraient être déplacés dans `notebooks/legacy/` ou supprimés.
- 3 versions de présentation : `presentation_memoire_GE.pptx`, `[Autosaved].pptx`, `_v2.pptx` → garder une seule version source.

---

## 2. Phase 2 — Études statistiques

### 2.1 Features promises mais absentes du dataset
- **Constat (memory) :** `nb_jours_feries_dans_delai`, `nb_weekends_dans_delai`, `taux_change_devise` sont mentionnées dans `rapport_phase2.md` mais **absentes du parquet enrichi**.
- **Action :** soit les ajouter au pipeline d'enrichissement, soit corriger le rapport pour ne pas créer d'incohérence devant le jury.

### 2.2 Granger et causalité
- **Constat :** matrice de p-values Granger générée, mais aucune feature exogène (IPI, météo) n'est introduite avec un **lag** correspondant aux délais Granger significatifs.
- **Action :** pour chaque exogène, créer la version laggée du lag optimal (`ipi_valeur_lag1`, `ipi_valeur_lag3`…).
- **Gain :** capturer l'effet retardé des facteurs macro sur la demande.

### 2.3 Analyses absentes
- Pas de **test de stationnarité** publié (ADF / KPSS) par série client × article.
- Pas de **décomposition Croston** des séries à demande intermittente (or beaucoup d'articles ont qte_demandee médiane faible et std très haute).
- Pas de **clustering** des séries (DTW + k-means) pour identifier des « profils types ».

---

## 3. Phase 2bis — EDA pré-modélisation

### 3.1 Choix de features à challenger
Les 28 features actuelles ([dashboard/utils/features.py:8-37](dashboard/utils/features.py#L8-L37)) sont **toutes contextuelles ou catégorielles** — il manque toute composante **autorégressive**.

| Feature manquante | Description | Coût | Gain attendu MAE |
|---|---|---|---|
| `qte_lag_1`, `qte_lag_7`, `qte_lag_30` | Quantité commandée à t-1, t-7, t-30 par couple client × article | Faible | **🔴 fort** |
| `qte_rolling_mean_7d`, `_30d`, `_90d` | Moyenne mobile par couple | Faible | **🔴 fort** |
| `qte_rolling_std_30d` | Volatilité récente | Faible | Moyen |
| `nb_jours_depuis_derniere_commande` | Inter-arrival time | Faible | Moyen |
| `nb_commandes_dans_30j` | Fréquence récente | Faible | Moyen |
| `prix_lag_1` + `prix_delta` | Élasticité prix | Faible | Moyen |
| `target_encoding_couple` | **Mean target encoding par fold temporel** (≠ frequency encoding actuel : code_client_freq / code_article_freq capturent la popularité, pas la valeur cible) | Moyen | **🔴 fort** |
| `rolling_*_par_client` | Mêmes rolling stats mais agrégées **par client seul** (pas par couple) — capte le profil d'achat global du client | Faible | Moyen |
| `rolling_*_par_article` | Idem **par article seul** — capte la tendance produit indépendamment du client | Faible | Moyen |
| `cumul_qte_annee` | Position dans cycle annuel | Faible | Faible |

> **Attention au data leakage :** tous les lags doivent être calculés sur train uniquement puis projetés sur val/test, **sans recalcul global**.

### 3.2 Sélection statique vs dynamique
- **Constat :** VIF + corrélations appliqués une fois, sélection figée.
- **Action :** ajouter une sélection **par importance permutation** (post-fit) et **Boruta-SHAP**.

### 3.3 Cible : log1p est-elle optimale ?
- **Constat :** skew 80.7 → 1.4 avec log1p, mais distribution reste lourde à droite.
- **Action :** comparer `log1p` vs `Yeo-Johnson` vs `Box-Cox` vs cible brute avec Tweedie/Poisson loss.
- **Gain :** potentiellement −5 à −10 % MAE.

---

## 4. Phase 3 — Modélisation

### 4.1 Validation temporelle insuffisante
- **Constat :** un seul split (train 2021-23 / val 2024 / test 2025). Pas de rolling backtest.
- **Action :** utiliser `sklearn.model_selection.TimeSeriesSplit(n_splits=5)` ou **expanding window** mensuelle :
  ```
  fold1 : train 2021-2022 → val 2023 H1
  fold2 : train 2021-2022 H1 → val 2023 H2
  …
  ```
- **Bonus :** test de **Diebold-Mariano** pour prouver statistiquement la supériorité de XGBoost vs baseline (sinon le gain de −9 % MAE n'est pas défendable devant un jury).

### 4.2 Hyperparamétrage sous-dimensionné
- **Constat :** Optuna **50 essais** seulement, `n_estimators=498` final → presque la borne haute du search space, signe que l'espace n'a pas été exploré assez.
- **Action :** passer à **200-500 essais**, élargir `n_estimators` (200-2000), `max_depth` (3-15), ajouter `gamma`, `max_delta_step`.
- **Gain :** facilement −0.3 à −0.8 sur MAE.

### 4.3 Modèles non testés
| Modèle | Pourquoi tester | Effort |
|---|---|---|
| **Modèle résiduel** : XGBoost prédit `qte_demandee − baseline_couple` au lieu de `qte_demandee` brute | Souvent **+5 à +10 % de MAE** rapide, le modèle se concentre sur le signal non capturé par la moyenne historique | 0.5 j |
| **CatBoost** | Gère natif les catégorielles, souvent bat XGBoost sur tabulaire bruité | 1 j |
| **LightGBM `objective="quantile"`** (P10, P50, P90) | Vrais intervalles de confiance, remplace le score composite ad-hoc, **beaucoup plus crédible pour le jury** | 1 j |
| **NGBoost** | Distribution complète prédite (alternative au quantile) | 2 j |
| **LightGBM Tweedie** | Pour cibles intermittentes/zéro-gonflées | 0.5 j |
| **Ensemble (XGB-log + XGB-Tweedie + LGBM) stacking** | Meta-learner (Ridge/Lasso) sur les prédictions val — toujours +1 à +3 % | 1 j |
| **Croston / TSB / ADIDA** | Demande intermittente (cas spécifique aux articles rares) | 1 j |
| **Prophet (par couple top-100)** | Comparaison « bonne pratique industrielle » | 1 j |

#### 4.3 bis — Segmentation ABC : un modèle par segment
- **Constat :** la longue traîne (articles rares, couples vus < 5 fois) tire la MAE globale vers le haut et tue le R². Un seul modèle généraliste sous-performe sur tout.
- **Action :** classification ABC sur le volume cumulé :
  - **A** (top 20 % articles = ~80 % volume) → XGBoost Optuna spécifique
  - **B** (15 % suivants) → XGBoost générique
  - **C** (longue traîne) → Croston / TSB ou simple médiane glissante
- **Bonus :** publier les MAE par segment dans le rapport → démontre une réflexion industrielle, pas juste un score global.
- **Gain attendu :** −10 à −20 % WAPE sur le segment A (le plus important business), MAE globale plus stable.

### 4.4 Architecture 2 (LSTM time-to-event) — réécriture recommandée
- **Constat :** précision ±7j **25.5 %** = quasi aléatoire. C'est le plus gros point faible du mémoire.
- **Causes probables :**
  1. `SEQ_LEN = 6` ([features.py:52](dashboard/utils/features.py#L52)) — trop court pour capter de la saisonnalité.
  2. 8 features seulement, aucune autorégressive sur le délai lui-même.
  3. Pas de scaling documenté.
  4. Pas d'attention, 2 couches, hidden 64 — sous-dimensionné OU sur-dimensionné selon la taille de séquence.
- **Actions (par ordre de gain attendu) :**
  1. **Reformuler en survival analysis** : `lifelines` (CoxPH), `scikit-survival` (Random Survival Forest), `pycox` (DeepSurv).
  2. **Prophet par couple** (top 100 couples qui couvrent 80 % du volume).
  3. **Reformuler en classification multi-classes** : bucket de délai [0-7], [7-14], [14-30], [30-60], [60+] → tâche plus simple, métrique log-loss interprétable.
  4. Si on garde LSTM : passer à `SEQ_LEN = 12-24`, ajouter `delai_lag_1..6`, scaling MinMax obligatoire, attention multi-head ou **Temporal Fusion Transformer** (PyTorch Forecasting).

### 4.5 Interprétabilité
- **Constat :** uniquement `feature_importance_xgb.png`. Pas de SHAP.
- **Action :** générer `shap.summary_plot`, `shap.dependence_plot` (top 6 features), exporter SHAP values par ligne du test set → **affichables en hover sur le dashboard**.

### 4.6 Métriques business absentes
Ajouter au [rapport_modelisation.json](reports/rapport_modelisation.json) :
- **MAE pondérée asymétrique business** : `cost = α·max(0, y−ŷ) + β·max(0, ŷ−y)` avec α (coût rupture) ≠ β (coût sur-stock). Définir α/β avec la direction supply chain et reporter cette « MAE pondérée business » comme métrique principale aux côtés de la MAE classique.
- Taux de couverture de stock évité (€ économisés si on suit la prédiction)
- Taux de rupture évité
- MAE par décile de volume (déjà calculée d'après plan, mais à publier)
- **MAE par segment** : top 10 clients, articles A/B/C, mois pic (sept/oct/nov) vs creux (juil/août) — démontre la robustesse réelle au-delà du score agrégé
- Pinball loss à quantiles 0.1 / 0.5 / 0.9 (pour les intervalles)

### 4.7 Reproductibilité du training
- **Constat :** seeds non visibles dans le rapport JSON, `requirements.txt` non pinné.
- **Action :**
  - Pin exact dans `requirements.txt` (`xgboost==3.2.0`, etc.).
  - Documenter `random_state=42` partout.
  - Ajouter **MLflow** local : `mlflow ui` permet de comparer toutes les runs Optuna.
  - Si possible : **DVC pipeline** (`dvc.yaml`) pour reproduire `02bis → 03` en une commande.

---

## 5. Phase 4 — Dashboard Streamlit

### 5.1 Bouton de ré-entraînement non fonctionnel
- **Constat :** [pages/2_IA.py:106-112](dashboard/pages/2_IA.py#L106-L112) — `src/retrain.py` absent, bouton décoratif.
- **Action :** créer `src/retrain.py` avec :
  - Chargement des splits
  - Re-fit XGBoost avec hyperparams Optuna déjà stockés
  - Évaluation sur test, mise à jour `rapport_modelisation.json` versionné (suffixe timestamp)
  - Sauvegarde modèle horodaté
  - `subprocess.Popen` + log streaming dans la page

### 5.2 Inférence : risque de désynchronisation features
- **Constat :** [features.py](dashboard/utils/features.py) duplique la liste hardcodée du notebook. Tout ajout dans le notebook **casse silencieusement** l'inférence.
- **Action :** sauvegarder la liste dans le `.pkl` lui-même (XGBoost a `model.feature_names_in_`) et la **lire depuis le modèle** au démarrage du dashboard.

### 5.3 Manques fonctionnels métier
| Fonctionnalité | Valeur ajoutée mémoire |
|---|---|
| **Backtest interactif semaine par semaine** : « si on avait utilisé le modèle en 2025, voici ce qui se serait passé » avec curseur temporel, courbe pred vs réel cumulée, € de stock économisés/perdus | 🟢🟢 **très fort jury** |
| **What-if baseline vs IA côte à côte** : tableau ou courbe avec colonnes (`qte_reelle`, `baseline`, `IA`, `Δ MAE`, `Δ € estimé`) sur un échantillon filtrable | 🟢 fort |
| **Intervalle P10–P90 affiché** autour de chaque prédiction (issu du modèle quantile §4.3) — remplace/complète le score composite confiance | 🟢 fort, beaucoup plus honnête statistiquement |
| **Drift detection (PSI)** sur les features clés (prix, code_article_freq, ipi_valeur) : alerte visuelle si les données importées dérivent du train | 🟢 fort bonus jury |
| **What-if simulation** : modifier `prix`, `delai_demande_jours`, `ipi_valeur` → voir l'impact sur la prédiction | 🟢 fort effet démonstratif jury |
| **Explication SHAP par ligne** (page Prévisions) | 🟢 fort |
| **Seuil de confiance configurable** pour automatisation : slider « si confiance > X, validation auto ; sinon humain » → matérialise le pitch HITL et donne un livrable opérationnel | 🟢🟢 **clé Phase 4** |
| **Alerte rupture** : flag automatique si `qte_predite > stock_dispo` (si on a un mock stock) | 🟢 fort |
| **Upload mode B** : CSV brut non encodé → pipeline d'encodage automatique côté serveur | 🟠 moyen |
| **Comparaison estimation humaine vs IA** : champ « estimation expert » → MAE humain vs MAE IA | 🟢 fort (justifie le « Human-in-the-loop ») |
| **Page « Données » : édition réelle qui re-entraîne** | 🟡 lourd mais clé du HITL |

### 5.4 Page Prévisions — performance
- **Constat :** [pages/3_Previsions.py:50-54](dashboard/pages/3_Previsions.py#L50-L54) charge train ET test, calcule historical_stats à chaque interaction.
- **Action :** sérialiser `historical_stats` une fois (pickle) à la fin de Phase 3 et le charger directement.

### 5.5 Honnêteté intellectuelle (point fort à pousser)
- Page Analyse mentionne déjà les 5 limites — c'est bien.
- **À ajouter :**
  - Graphique « WAPE par segment » montrant où l'IA est faible (segments rares).
  - **Calibration plot** : prédiction moyenne par décile vs valeur moyenne réelle.
  - Bandeau visible : « précision actuelle 45.95 %, objectif initial 60 % → écart restant assumé ».

### 5.6 Tests et qualité
- **Constat :** aucun test unitaire dans `dashboard/utils/`.
- **Action minimale :**
  - `tests/test_inference.py` : `predict_qte` retourne shape attendue, valeurs ≥ 0.
  - `tests/test_confidence.py` : tester les 4 branches de [confidence.py:15-39](dashboard/utils/confidence.py#L15-L39).
  - `tests/test_data_loader.py` : schémas attendus présents.
  - GitHub Actions minimaliste : lint + tests sur push.

---

## 6. Documentation et mémoire

### 6.1 Rapports manquants
- ✅ `rapport_phase1_data_engineering.pdf` existe
- ✅ `rapport_phase2.md` existe
- ❌ **Pas de `rapport_phase3_modelisation.md`** : le JSON brut n'est pas un livrable. Rédiger un MD avec narration des choix, courbes apprentissage, comparaisons.
- ❌ **Pas de `rapport_phase4_dashboard.md`** : screenshots, parcours utilisateur, décisions UX.

### 6.2 Plans gitignored
- **Constat :** `PLAN_PROJET_MEMOIRE.md`, `PHASE*.md` ne sont **pas dans git** (cf. conventions du projet).
- **Risque :** perte si machine locale crash + invisible pour encadrants.
- **Action :** déplacer une **copie versionnée** des sections finalisées vers `docs/` (committée), garder les plans personnels en local.

### 6.3 Présentation
- 3 fichiers `.pptx` coexistent → renommer en `presentation_v_final.pptx`, archiver les anciens.
- Vérifier que chaque slide cite un livrable précis (notebook, figure, page dashboard).

### 6.4 Model card
- **Constat :** aucun document standardisé qui résume « comment lire ce modèle » (à la Google Model Cards / HuggingFace).
- **Action :** créer `docs/MODEL_CARD.md` avec sections :
  - **Identification** : nom, version, date, auteur
  - **Usage prévu** : prédiction quantité demandée par couple client × article, horizon M+1 à M+3
  - **Usage non recommandé** : articles jamais vus en train, ruptures géopolitiques, premiers achats clients
  - **Données d'entraînement** : périmètre 2021-2023, volumétrie, biais connus
  - **Métriques par segment** (table issue de §4.6)
  - **Limites identifiées** : précision ±7j faible (LSTM), longue traîne, articles rares
  - **Biais éthiques** : sur-apprentissage des gros clients (cf. §6bis.2)
  - **Date de prochaine revue** + responsable
- **Valeur jury :** preuve de maturité industrielle et de réflexion responsabilité.

---

## 6 bis. Positionnement scientifique et éthique du mémoire

### 6bis.1 Comparaison avec DDMRP classique
- **Constat :** le mémoire pitche « Demand-Driven IA » mais ne se compare jamais explicitement à **DDMRP** (Demand-Driven Material Requirements Planning) — la référence académique du domaine (Ptak & Smith, 2016).
- **Action :** ajouter dans le mémoire une section **« IA vs DDMRP classique »** :
  - Rappeler les 5 composantes DDMRP : Strategic Inventory Positioning, Buffer Profiles & Levels, Dynamic Adjustments, **Demand-Driven Planning** (Net Flow Position = On-Hand + On-Order − Qualified Demand), Visible & Collaborative Execution
  - Implémenter (même en notebook simple) une **baseline DDMRP** : buffers vert/jaune/rouge sur top 10 articles, Net Flow Position calculée
  - Comparer : MAE DDMRP vs MAE XGBoost Optuna, taux de rupture évité, taux de sur-stock
- **Valeur jury :** ancre le projet dans la littérature opérationnelle, évite l'accusation « réinvention de la roue avec du ML ».

### 6bis.2 Section éthique & biais
- **Constat :** aucune section dédiée aux biais du modèle.
- **Action :** rédiger une section « Limites éthiques » avec données :
  - **Biais de fréquence** : MAE 2-3× plus élevée sur les petits clients (< 10 commandes/an) — risque de **rupture silencieuse** sur cette population
  - **Biais d'article** : longue traîne mal prédite → si l'entreprise se fie aveuglément, ces articles seront sous-stockés
  - **Biais temporel** : 2021-2022 contient période Covid → modèle peut sur-pondérer ce régime atypique
  - **Biais de sélection** : seuls les couples avec ≥ N commandes sont exploitables → exclusion des nouveaux clients
- **Action complémentaire :** publier le tableau **« MAE par décile de fréquence client »** comme preuve quantitative.

### 6bis.3 Recommandations opérationnelles (Human-in-the-loop)
- **Constat :** le dashboard Phase 4 affiche un score de confiance, mais le mémoire ne propose pas de **politique de décision** explicite.
- **Action :** formaliser une **matrice de gouvernance** dans le mémoire :

  | Niveau confiance | Action recommandée | % volume estimé |
  |---|---|---|
  | Vert (article familier, écart < 0.5, P50 < P90) | **Automatisation totale** : commande validée sans revue | ~60 % |
  | Orange | **Revue rapide** par planificateur (validation 1 clic) | ~30 % |
  | Rouge (article rare, prédiction P95+) | **Décision humaine obligatoire** + saisie justification | ~10 % |

- **Bonus :** rendre ce seuil configurable dans le dashboard (slider §5.3) → preuve que le pitch HITL est opérationnalisable.

---

## 7. Vision production (pour la partie « perspectives » du mémoire)

| Brique | Tech recommandée | Effort | Valeur mémoire |
|---|---|---|---|
| API d'inférence | **FastAPI** + Pydantic + Uvicorn | 2 j | 🟢 fort |
| Stockage | **PostgreSQL** + SQLAlchemy (historique prédictions + feedback) | 2 j | 🟢 fort |
| Monitoring drift | **Evidently AI** ou **Whylogs** (rapport HTML automatique) | 1 j | 🟢 fort |
| Versioning modèle | **MLflow Model Registry** (staging → prod) | 1 j | 🟠 moyen |
| Versioning data | **DVC** + remote S3/MinIO | 1 j | 🟠 moyen |
| Containerisation | **Docker** + `docker-compose` (app + db + mlflow) | 1 j | 🟢 fort |
| Orchestration retrain | **Prefect** ou **Airflow** (DAG hebdo) | 2 j | 🟠 moyen |
| Tests intégration | **pytest** + fixtures + GitHub Actions | 1 j | 🟢 fort |
| Observabilité | logs structurés (loguru / structlog) + Sentry | 0.5 j | 🟡 faible |

Même sans implémenter, **décrire l'architecture cible** dans le mémoire avec un schéma vaut plusieurs points.

---

## 8. Plan d'attaque suggéré (ordre de priorité)

### Sprint A — Avant soutenance (impact max, effort ≤ 7 j)
1. **Features lags + rolling** (client / article / couple) + **target encoding fold temporel** (1.5 j) → re-train XGBoost Optuna 300 essais
2. **Modèle résiduel** (XGBoost prédit `y − baseline_couple`) (0.5 j) → gain rapide attendu +5 à +10 %
3. **LightGBM quantile** P10/P50/P90 (0.5 j) → intervalles affichés dans le dashboard
4. **Walk-forward CV 5 folds + Diebold-Mariano + MAE pondérée business** (1 j) → légitimer scientifiquement le gain vs baseline et DDMRP
5. **SHAP global + per-row** (0.5 j) → intégrer hover dashboard
6. **Reformulation date** : Prophet top-100 couples + survival analysis (Cox) (1.5 j)
7. **Segmentation ABC** : modèles séparés top 20 % vs longue traîne (0.5 j)
8. **Rapport Phase 3 + Phase 4 + Model card** (1 j)

### Sprint B — Si le temps le permet (1 semaine)
9. ✅ CatBoost + stacking (meta-learner Ridge sur XGB v2 + LGBM P50 + CatBoost) — voir [notebooks/10_catboost_stacking.ipynb](notebooks/10_catboost_stacking.ipynb)
10. ✅ **Backtest interactif semaine par semaine** — page [dashboard/pages/6_Backtest.py](dashboard/pages/6_Backtest.py) + précompute [notebooks/11_backtest_2025_precompute.ipynb](notebooks/11_backtest_2025_precompute.ipynb)
11. ✅ **Baseline DDMRP** (Net Flow Position, buffers vert/jaune/rouge) → comparaison IA vs DDMRP — voir [notebooks/09_baseline_ddmrp.ipynb](notebooks/09_baseline_ddmrp.ipynb), [reports/sprint_b_chantier3_ddmrp.json](reports/sprint_b_chantier3_ddmrp.json)
12. ✅ **Drift detection PSI** intégré dashboard — module [dashboard/utils/drift.py](dashboard/utils/drift.py), page [dashboard/pages/5_Drift.py](dashboard/pages/5_Drift.py)
13. ✅ What-if simulation page Prévisions — section ajoutée à [dashboard/pages/3_Previsions.py](dashboard/pages/3_Previsions.py), helper [dashboard/utils/whatif.py](dashboard/utils/whatif.py)
14. ✅ Tests unitaires utils/ — 27 tests dans [dashboard/tests/](dashboard/tests/), couverture 88-100% sur les modules cibles, CI dans [.github/workflows/ci.yml](.github/workflows/ci.yml)
15. ✅ Script `retrain.py` fonctionnel — [src/retrain.py](src/retrain.py) avec modes `--quick` (30 essais) / `--full` (100 essais), bouton intégré dans [dashboard/pages/2_IA.py](dashboard/pages/2_IA.py)

### Sprint C — Perspectives mémoire (à décrire sans coder)
- FastAPI + PostgreSQL + Docker + MLflow + Evidently
- Schéma d'architecture cible
- Plan de mise en prod chez GE
- **Matrice de gouvernance HITL** (seuils confiance → automatisation vs revue humaine)
- **Section éthique** : biais petits clients / longue traîne, plan d'atténuation

---

## 9. Tableau de risques

| Risque | Probabilité | Impact mémoire | Mitigation |
|---|---|---|---|
| Question jury : « gain 9 % vs baseline, vraiment significatif ? » | Élevée | 🔴 fort | Diebold-Mariano + intervalles bootstrap |
| Question jury : « pourquoi LSTM si précision ±7j = 25 % ? » | Très élevée | 🔴 fort | Avoir testé Prophet + survival et présenter pourquoi LSTM est gardé/abandonné |
| Question jury : « WAPE 54 % vs objectif 60 % ? » | Très élevée | 🟠 moyen | Plan « features lags » montre la trajectoire d'amélioration |
| Crash dashboard pendant démo | Moyenne | 🟠 moyen | Mode démo : prévoir captures vidéo + données figées |
| Incohérences rapport vs code (features absentes §2.1) | Moyenne | 🟠 moyen | Corriger avant impression |

---

*Fichier généré pour servir de feuille de route avant la soutenance du 28 mai 2026.*
