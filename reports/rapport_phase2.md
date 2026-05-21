# Rapport Phase 2 — Études Statistiques
## Projet Mémoire Master GE — Système de Prévision de la Demande Client

**Notebook :** `notebooks/02_statistical_study.ipynb`  
**Auteur :** AdaMakchi  
**Date :** Mai 2026  
**Données sources :** `data/processed/dataset_ml_final.parquet` — 349 390 lignes × 24 colonnes  
**Livrable produit :** `data/processed/dataset_ml_enrichi.parquet` — 349 390 lignes × 38 colonnes

---

## 1. Contexte et Objectifs de la Phase 2

La Phase 1 (Data Engineering) a produit un dataset nettoyé de 349 390 commandes couvrant la période septembre 2020 – décembre 2025. La Phase 2 poursuit deux objectifs complémentaires :

1. **Comprendre la structure temporelle de la demande** : identifier les cycles saisonniers, les tendances de fond et les régularités calendaires afin d'anticiper les variations de volume.
2. **Quantifier l'influence des facteurs externes** : mesurer statistiquement l'impact de variables exogènes (jours fériés, météo, conjoncture industrielle, contexte sanitaire) sur la quantité demandée, puis sélectionner celles qui apporteront une valeur prédictive réelle au modèle d'IA en Phase 3.

La variable cible retenue est **`qte_demandee`** (quantité commandée par ligne de commande).

---

## 2. Étude A — Saisonnalité et Cyclicité

### 2.1 Décomposition de la série temporelle globale

La demande mensuelle totale a été construite en agrégeant toutes les quantités demandées par mois de commande (`date_cmd`). La série couvre **64 mois** (sept. 2020 – déc. 2025) avec une moyenne de **124 413 unités/mois** et un écart-type de 41 348.

Une **décomposition additive STL** (Seasonal-Trend decomposition using Loess) à période 12 mois a été appliquée via `statsmodels.tsa.seasonal.seasonal_decompose`. Cette méthode décompose la série en trois composantes indépendantes :

| Composante | Description | Résultat observé |
|---|---|---|
| **Tendance** | Évolution lissée à long terme | Haussière : **+13 130 unités** sur toute la période |
| **Saisonnalité** | Pattern annuel répété | Amplitude **89 725 unités** — pic en **mars** (mois 3), creux en **août** (mois 8) |
| **Résidus** | Bruit non expliqué | Chocs ponctuels non structurés |

**Interprétation :**
- La tendance haussière confirme une croissance progressive de l'activité commerciale de GE sur la période étudiée.
- L'amplitude saisonnière de près de 90 000 unités représente environ **72 % de la moyenne mensuelle**, ce qui rend la saisonnalité incontournable dans tout modèle de prévision.
- Le pic de mars s'explique par les clôtures budgétaires du 1er trimestre dans les secteurs industriels (commandes passées avant la fin de l'exercice ou pour l'ouverture du suivant). Le creux d'août correspond aux fermetures estivales industrielles en France.

*Figure produite :* `reports/decomposition_globale.png`

---

### 2.2 Décomposition par famille d'article

Le dataset contient **3 familles d'articles** (encodées 0, 1, 2). Leur contribution respective au volume total est très asymétrique :

| Famille (encodée) | Volume total | Nb de commandes | Part du volume |
|---|---|---|---|
| **0** | 7 119 204 unités | 338 517 | **96,3 %** |
| **1** | 562 156 unités | 3 669 | 7,6 % |
| **2** | 281 068 unités | 7 204 | 3,8 % |

La même décomposition STL a été appliquée à chacune des trois familles. La famille 0, dominante, porte l'essentiel de la structure saisonnière observée au niveau global. Les familles 1 et 2, plus petites, présentent davantage de bruit dans leurs séries en raison de la plus faible fréquence de commandes.

*Figure produite :* `reports/decomposition_par_famille.png`

---

### 2.3 Cycles budgétaires clients (fin de trimestre)

La demande moyenne par mois a été calculée sur l'ensemble de la période et comparée mois par mois. Les mois de fin de trimestre (mars, juin, septembre, décembre) ont été mis en évidence comme marqueurs des cycles budgétaires clients.

**Observation :** une sur-demande notable est visible en fin de trimestre, cohérente avec le comportement typique des acheteurs industriels qui consomment leur budget avant clôture comptable. Ce signal renforce la pertinence d'inclure `trimestre_cmd` et `est_fin_mois_cmd` comme features dans le modèle.

*Figure produite :* `reports/cycles_budgetaires.png`

---

### 2.4 Cycles météo (saisonniers)

La demande moyenne par saison (Hiver / Printemps / Été / Automne) a été calculée. Le creux estival (Été, juillet-août) se détache nettement, confirmant l'effet des arrêts industriels et des congés annuels sur la chaîne de commande.

*Figure produite :* `reports/cycles_meteo.png`

---

## 3. Étude B — Corrélations Exogènes

L'objectif de cette étude est de construire et d'évaluer 12 variables exogènes susceptibles d'expliquer les variations de la demande, puis de ne retenir que celles ayant une valeur prédictive réelle.

### 3.1 Construction des variables exogènes

#### B.1.1 — Variables jours fériés (library `holidays`)

Quatre indicateurs calendaires ont été créés ligne par ligne sur l'ensemble du dataset :

| Variable | Description | Valeur moyenne |
|---|---|---|
| `est_jour_ferie_cmd` | La date de commande est-elle un jour férié ? (0/1) | 0,284 (28,4 % des lignes) |
| `est_jour_ferie_liv_dem` | La date de livraison demandée est-elle un jour férié ? | 0,286 |
| `nb_jours_feries_dans_delai` | Nb de jours fériés ouvrés dans l'intervalle cmd→livraison | 0,34 (max : 11) |
| `nb_weekends_dans_delai` | Nb de jours de week-end dans le même intervalle | 2,12 (max : 114) |

Les jours fériés ont été calculés avec le calendrier officiel français (`holidays.France()`). Le comptage dans l'intervalle utilise `pandas.date_range` avec `freq='B'` (jours ouvrés) pour les fériés et la règle `weekday >= 5` pour les week-ends.

#### B.1.2 — Variables météo (API Open-Meteo — proxy Paris)

Les données météo quotidiennes de Paris (48.85°N, 2.35°E) ont été récupérées via l'API Open-Meteo Archive pour la période 2020-2025, puis agrégées en mensuel :

| Variable | Agrégation | Description |
|---|---|---|
| `pluie_mm_liv_dem` | Somme mensuelle | Précipitations cumulées (mm) au mois de livraison |
| `vent_max_kmh_liv_dem` | Maximum mensuel | Vitesse maximale de vent (km/h) au mois de livraison |
| `temp_min_liv_dem` | Minimum mensuel | Température minimale (°C) au mois de livraison |

**Proxy Paris :** 89 % des commandes GE ont pour destination la France ; Paris est utilisé comme proxy représentatif. Aucun NaN n'a été généré après la jointure (couverture 2020-2025 complète).

#### B.1.3 — Indice de Production Industrielle France (IPI — INSEE)

La série IPI (Industrie Manufacturière, base 100 = 2015, référence INSEE n°010537309) a été jointurée sur le mois de commande. En l'absence du fichier CSV téléchargeable manuellement depuis l'INSEE, des valeurs de référence approximatives ont été encodées en dur dans le notebook à titre de proxy — elles devront être remplacées par les valeurs officielles pour la version finale du mémoire.

| Statistique | Valeur |
|---|---|
| Moyenne | 99,7 |
| Écart-type | 2,9 |
| Min (choc COVID avr. 2020) | 65,0 |
| Max | 105,0 |

#### B.1.4 — Taux de change (EUR/USD/CNY)

Le dataset contient trois devises : EUR (99,7 % des lignes), USD (0,3 %) et CNY (< 0,01 %). Les taux de change annuels moyens EUR → devise ont été appliqués selon l'année de commande :

| Devise | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| EUR | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| USD | 1,141 | 1,183 | 1,053 | 1,081 | 1,082 | 1,073 |
| CNY | 7,874 | 7,628 | 7,079 | 7,653 | 7,818 | 7,750 |

#### B.1.5 — Variables contextuelles

| Variable | Logique | Part des lignes = 1 |
|---|---|---|
| `est_vacances_scolaires_liv_dem` | Livraison pendant une période de vacances scolaires (toutes zones) | 30,9 % |
| `est_periode_peak_liv_dem` | Livraison en septembre, novembre ou décembre | 22,0 % |
| `est_periode_covid` | Commande passée pendant les trimestres perturbés (2021 T1-T2, 2022 T1) | 18,1 % |

---

### 3.2 Matrice de corrélation de Pearson

Les 12 variables exogènes ont été agrégées au niveau mensuel (72 mois) pour correspondre à la granularité temporelle de la demande. La corrélation de Pearson mesure la force et le sens de la relation linéaire entre chaque variable et `qte_demandee`.

**Seuil de significativité retenu :** |r| > 0,15

| Variable | r (Pearson) | Significatif ? |
|---|---|---|
| `nb_weekends_dans_delai` | **+0,545** | ★ OUI |
| `nb_jours_feries_dans_delai` | **+0,497** | ★ OUI |
| `ipi_valeur` | **−0,262** | ★ OUI |
| `est_jour_ferie_cmd` | **+0,198** | ★ OUI |
| `temp_min_liv_dem` | **−0,156** | ★ OUI |
| `vent_max_kmh_liv_dem` | +0,149 | Non |
| `taux_change_devise` | −0,106 | Non |
| `est_vacances_scolaires_liv_dem` | −0,093 | Non |
| `est_periode_peak_liv_dem` | −0,080 | Non |
| `est_periode_covid` | −0,058 | Non |
| `pluie_mm_liv_dem` | +0,033 | Non |

**5 variables franchissent le seuil |r| > 0,15** et sont retenues pour le test de Granger.

*Figure produite :* `reports/matrice_correlation_pearson.png`

**Interprétation des corrélations significatives :**
- **`nb_weekends_dans_delai` (r = +0,545) :** Plus il y a de week-ends dans le délai de livraison, plus la quantité demandée est élevée. Cet effet reflète probablement une anticipation des clients qui commandent davantage lorsque le délai effectif de livraison est allongé par les week-ends.
- **`nb_jours_feries_dans_delai` (r = +0,497) :** Même logique que les week-ends — les jours fériés allongent le délai réel et poussent à commander des quantités plus importantes pour compenser.
- **`ipi_valeur` (r = −0,262) :** Corrélation négative avec l'indice de production industrielle. Lorsque l'industrie tourne fort (IPI élevé), les stocks de produits GE sont plus sollicités en interne et la demande sur le marché diminue, ou inversement, les livraisons s'accélèrent en contexte de faible production (rattrapage). Ce signal contre-intuitif mérite d'être vérifié avec l'IPI officiel INSEE.
- **`est_jour_ferie_cmd` (r = +0,198) :** Les commandes passées un jour férié sont associées à des quantités plus élevées, possiblement des commandes d'urgence ou de rattrapage.
- **`temp_min_liv_dem` (r = −0,156) :** Les températures hivernales basses (mois froids) sont associées à une demande plus élevée, cohérent avec le pic saisonnier observé en mars.

---

### 3.3 Test de causalité de Granger

Le test de Granger vérifie si les **valeurs passées d'une variable X améliorent la prédiction de Y** au-delà de ce que les valeurs passées de Y permettent seules. Une p-value < 0,05 signifie que X apporte une information prédictive causale sur Y.

Le test a été appliqué aux 5 variables significatives en Pearson, avec des décalages de 1, 2 et 3 mois (`maxlag=3`).

| Variable | p-value lag=1 | p-value lag=2 | p-value lag=3 | Résultat |
|---|---|---|---|---|
| `nb_weekends_dans_delai` | **0,0000** | **0,0000** | 0,6015 | **Causalité Granger confirmée** |
| `nb_jours_feries_dans_delai` | **0,0000** | **0,0000** | 0,5532 | **Causalité Granger confirmée** |
| `ipi_valeur` | 0,9929 | 0,9989 | 0,1219 | Corrélation non causale |
| `est_jour_ferie_cmd` | 0,5085 | 0,5626 | 0,9212 | Corrélation non causale |
| `temp_min_liv_dem` | 0,2830 | 0,6085 | 0,5720 | Corrélation non causale |

**2 variables présentent une causalité de Granger significative aux lags 1 et 2 :**

1. **`nb_weekends_dans_delai`** : les valeurs passées de cette variable précèdent et prédisent les variations de la demande à court terme (1 à 2 mois).
2. **`nb_jours_feries_dans_delai`** : même conclusion — le nombre de jours fériés dans le délai de livraison est un prédicteur causal de la demande future.

**Note :** `ipi_valeur` et `est_jour_ferie_cmd` montrent une corrélation Pearson significative mais sans causalité Granger. Cela indique une **corrélation spurieuse ou contemporaine** (les deux variables bougent ensemble sur la même période, mais l'une n'anticipe pas l'autre). Elles sont néanmoins conservées dans le dataset enrichi, car elles peuvent apporter de la valeur en tant que features au même instant (non décalées) dans un modèle XGBoost.

*Figure produite :* `reports/granger_pvalues.png`

---

## 4. Synthèse des Résultats

### Variables retenues pour la Phase 3

| Variable | Pearson | Granger | Priorité Phase 3 |
|---|---|---|---|
| `nb_weekends_dans_delai` | ★ 0,545 | ★ p=0,000 | **Haute — feature causale** |
| `nb_jours_feries_dans_delai` | ★ 0,497 | ★ p=0,000 | **Haute — feature causale** |
| `ipi_valeur` | ★ −0,262 | — | **Moyenne — corrélation contemporaine** |
| `est_jour_ferie_cmd` | ★ 0,198 | — | **Moyenne — corrélation contemporaine** |
| `temp_min_liv_dem` | ★ −0,156 | — | **Moyenne — signal saisonnier** |
| Autres variables | Non sig. | — | Faible — à tester en ablation |

### Faits saillants

- La demande de GE présente une **saisonnalité marquée** (amplitude ≈ 90 000 unités/mois) avec un pic en mars et un creux en août.
- La **tendance de fond est haussière** (+13 130 unités sur 5 ans), validant la pertinence d'un modèle prédictif à horizon 12 mois.
- Les **cycles calendaires** (week-ends et jours fériés dans le délai de livraison) sont les facteurs exogènes les plus puissants, à la fois corrélés et causalement reliés à la demande.
- Les facteurs météo et macroéconomiques ont un impact plus limité et non causal à ce niveau de granularité.

---

## 5. Livrable Produit

Le dataset enrichi `data/processed/dataset_ml_enrichi.parquet` contient **349 390 lignes × 38 colonnes** (24 colonnes originales + 12 nouvelles features exogènes + 2 colonnes de dates reconstruites) sans aucune valeur manquante dans les nouvelles variables.

| Fichier | Description |
|---|---|
| `data/processed/dataset_ml_enrichi.parquet` | Dataset complet prêt pour la Phase 3 |
| `reports/decomposition_globale.png` | Décomposition STL série globale |
| `reports/decomposition_par_famille.png` | Décomposition STL par famille d'article |
| `reports/cycles_budgetaires.png` | Demande moyenne par mois (cycles fin de trimestre) |
| `reports/cycles_meteo.png` | Demande moyenne par saison |
| `reports/matrice_correlation_pearson.png` | Heatmap corrélations Pearson |
| `reports/granger_pvalues.png` | p-values test de Granger (lag=1) |

---

## 6. Recommandations pour la Phase 3

1. **Priorité aux features causales** : `nb_weekends_dans_delai` et `nb_jours_feries_dans_delai` doivent figurer en tête de liste dans les features XGBoost/LightGBM — leur causalité Granger aux lags 1-2 suggère qu'elles aident à prédire la demande future.
2. **Remplacer l'IPI hardcodé** : avant la soutenance, télécharger la série officielle INSEE (n°010537309) et la joindre au dataset pour garantir l'exactitude des valeurs.
3. **Split temporel strict** : conserver le split 2021-2023 (train) / 2024 (validation) / 2025 (test) défini en Phase 1 — ne jamais faire de split aléatoire sur des données temporelles.
4. **Ablation study** : tester la contribution marginale de chaque variable exogène via l'importance de features XGBoost pour confirmer ou invalider les variables à priorité faible.

---

*Rapport généré le 21 mai 2026 — Phase 2 terminée, Phase 3 à démarrer.*
