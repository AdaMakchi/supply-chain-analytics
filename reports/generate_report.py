# -*- coding: utf-8 -*-
"""
Génération du rapport PDF - Phase 1 : Data Engineering
Projet mémoire : Système de prévision des livraisons client 2021-2025
Auteur : Ada Makchi
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

# ---------------------------------------------------------------------------
# Constantes visuelles
# ---------------------------------------------------------------------------
NAVY    = (15,  40,  80)
BLUE    = (30,  80, 160)
LIGHT_B = (220, 232, 248)
GRAY_BG = (245, 247, 250)
GRAY_LN = (200, 205, 215)
WHITE   = (255, 255, 255)
BLACK   = (30,  30,  30)
GREEN   = (34, 139,  34)
ORANGE  = (200,  90,  20)
RED_D   = (180,  30,  30)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH   = os.path.join(BASE_DIR, "reports", "rapport_phase1_data_engineering.pdf")

# ---------------------------------------------------------------------------
# Classe PDF personnalisée
# ---------------------------------------------------------------------------
class ReportPDF(FPDF):

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=22)
        self._page_label = ""

    # ---- EN-TÊTE ----------------------------------------------------------
    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 10, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        self.set_xy(0, 1.5)
        self.cell(210, 7,
                  "Phase 1 - Data Engineering  |  Prévision des livraisons client 2021-2025",
                  align="C")
        self.set_text_color(*BLACK)
        self.ln(6)

    # ---- PIED DE PAGE -----------------------------------------------------
    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_fill_color(*NAVY)
        self.rect(0, self.get_y(), 210, 14, "F")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*WHITE)
        self.set_x(20)
        self.cell(0, 14, f"Page {self.page_no() - 1}", align="L", new_x=XPos.LMARGIN)
        self.set_x(0)
        self.cell(190, 14, "Ada Makchi - Mémoire Master - Avril 2026", align="R")
        self.set_text_color(*BLACK)

    # ---- UTILITAIRES ------------------------------------------------------
    def section_title(self, num, title):
        self.ln(5)
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 9, f"  {num}. {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_text_color(*BLACK)
        self.ln(3)

    def sub_title(self, title):
        self.ln(3)
        self.set_fill_color(*LIGHT_B)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 7, f"  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_text_color(*BLACK)
        self.ln(2)

    def body_text(self, txt, indent=0):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BLACK)
        self.set_x(self.l_margin + indent)
        self.multi_cell(0, 5.5, txt)
        self.ln(1)

    def bullet(self, items, indent=4):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BLACK)
        for item in items:
            self.set_x(self.l_margin + indent)
            self.cell(5, 5.5, "-", new_x=XPos.RIGHT)
            self.multi_cell(0, 5.5, item)

    def info_box(self, label, value, color=LIGHT_B):
        x0 = self.get_x()
        y0 = self.get_y()
        self.set_fill_color(*color)
        self.set_draw_color(*GRAY_LN)
        self.rect(x0, y0, 80, 14, "FD")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*NAVY)
        self.set_xy(x0 + 3, y0 + 2)
        self.cell(74, 5, label)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BLACK)
        self.set_xy(x0 + 3, y0 + 7)
        self.cell(74, 5, str(value))

    def kpi_row(self, kpis):
        """kpis = [(label, value, color), ...]"""
        y0 = self.get_y()
        x0 = self.l_margin
        cell_w = (210 - self.l_margin - self.r_margin) / len(kpis)
        for label, value, color in kpis:
            self.set_fill_color(*color)
            self.set_draw_color(*GRAY_LN)
            self.rect(x0, y0, cell_w - 1, 18, "FD")
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*NAVY)
            self.set_xy(x0 + 2, y0 + 2)
            self.cell(cell_w - 5, 8, str(value), align="C")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*BLACK)
            self.set_xy(x0 + 2, y0 + 10)
            self.cell(cell_w - 5, 6, label, align="C")
            x0 += cell_w
        self.set_xy(self.l_margin, y0 + 20)
        self.set_text_color(*BLACK)

    def h_table(self, headers, rows, col_widths=None, header_bg=NAVY, stripe=True):
        """Tableau générique avec en-tête colorée."""
        avail = 210 - self.l_margin - self.r_margin
        if col_widths is None:
            col_widths = [avail / len(headers)] * len(headers)

        # En-tête
        self.set_fill_color(*header_bg)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        self.set_draw_color(*GRAY_LN)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, f"  {h}", border=1, fill=True)
        self.ln()

        # Lignes
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*BLACK)
        for r_idx, row in enumerate(rows):
            if stripe:
                bg = GRAY_BG if r_idx % 2 == 0 else WHITE
                self.set_fill_color(*bg)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6.5, f"  {cell}", border=1, fill=stripe)
            self.ln()
        self.ln(2)

    def code_block(self, lines, title=""):
        if title:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*NAVY)
            self.cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_fill_color(240, 240, 240)
        self.set_draw_color(*GRAY_LN)
        total_h = len(lines) * 5 + 4
        self.rect(self.l_margin, self.get_y(), 170, total_h, "FD")
        self.set_font("Courier", "", 8)
        self.set_text_color(40, 40, 40)
        y0 = self.get_y() + 2
        for i, line in enumerate(lines):
            self.set_xy(self.l_margin + 3, y0 + i * 5)
            self.cell(164, 5, line)
        self.set_y(y0 + len(lines) * 5 + 2)
        self.set_text_color(*BLACK)
        self.ln(2)

    def divider(self):
        self.set_draw_color(*GRAY_LN)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(3)

    def note_box(self, text, color=None):
        if color is None:
            color = (255, 248, 220)
        y0 = self.get_y()
        self.set_fill_color(*color)
        self.set_draw_color(*ORANGE)
        h_est = max(12, len(text) // 90 * 5 + 12)
        self.rect(self.l_margin, y0, 170, h_est, "FD")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 60, 0)
        self.set_xy(self.l_margin + 4, y0 + 3)
        self.multi_cell(162, 5, text)
        self.set_y(y0 + h_est + 3)
        self.set_text_color(*BLACK)


# ===========================================================================
# CONSTRUCTION DU RAPPORT
# ===========================================================================
def build_report():
    pdf = ReportPDF()

    # -----------------------------------------------------------------------
    # PAGE 1 - COUVERTURE
    # -----------------------------------------------------------------------
    pdf.add_page()

    # Fond haut
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 80, "F")

    # Titre principal
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(20, 20)
    pdf.multi_cell(170, 12, "Système de Prévision\ndes Livraisons Client", align="C")

    pdf.set_font("Helvetica", "", 15)
    pdf.set_xy(20, 56)
    pdf.cell(170, 8, "Phase 1 - Data Engineering", align="C")

    # Bandeau bleu
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 80, 210, 14, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(20, 83)
    pdf.cell(170, 8, "Rapport technique détaillé - Période 2021-2025", align="C")

    # Corps couverture
    pdf.set_text_color(*BLACK)
    pdf.set_xy(20, 105)

    # Carte métadonnées
    meta = [
        ("Auteur",        "Ada Makchi"),
        ("Formation",     "Master - Supply Chain & Intelligence Artificielle"),
        ("Entreprise",    "GE - Groupe industriel"),
        ("Période",       "2021 - 2025"),
        ("Date du rapport","Avril 2026"),
        ("Statut",        "Phase 1 terminée - Phase 2 en préparation"),
    ]
    pdf.set_draw_color(*GRAY_LN)
    for i, (k, v) in enumerate(meta):
        y = 105 + i * 14
        pdf.set_fill_color(*LIGHT_B if i % 2 == 0 else WHITE)
        pdf.rect(20, y, 170, 13, "FD")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.set_xy(23, y + 2)
        pdf.cell(55, 5, k)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*BLACK)
        pdf.set_xy(80, y + 2)
        pdf.cell(108, 5, v)

    # Résumé flash
    pdf.set_xy(20, 196)
    pdf.set_fill_color(*GRAY_BG)
    pdf.set_draw_color(*BLUE)
    pdf.rect(20, 196, 170, 30, "FD")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(23, 199)
    pdf.cell(0, 6, "Résultat de la Phase 1")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BLACK)
    pdf.set_xy(23, 206)
    pdf.multi_cell(164, 5,
        "À partir de deux fichiers CSV bruts (352 549 commandes / 353 325 livraisons), "
        "le pipeline produit dataset_ml_final.parquet : 349 390 lignes x 24 colonnes "
        "(23 features + 1 variable cible binaire en_retard). Taux de retard : 19,2 %.")

    # Pied de page couverture
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 282, 210, 15, "F")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(20, 285)
    pdf.cell(170, 8, "Rapport généré automatiquement - Projet Mémoire Master - Confidentiel", align="C")

    # -----------------------------------------------------------------------
    # PAGE 2 - TABLE DES MATIÈRES
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 12, "Table des matières", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.divider()

    toc = [
        ("1.", "Contexte et problématique",                  "3"),
        ("2.", "Sources de données",                          "3"),
        ("3.", "Architecture du pipeline",                    "4"),
        ("4.", "Étape 1 - Chargement et renommage",          "5"),
        ("5.", "Étape 2 - Valeurs manquantes",               "6"),
        ("6.", "Étape 3 - Normalisation des dates",          "8"),
        ("7.", "Étape 4 - Jointure commandes x livraisons",  "9"),
        ("8.", "Étape 5 - Feature engineering temporel",    "11"),
        ("9.", "Étape 6 - Encodage des catégorielles",      "13"),
        ("10.", "Étape 7 - Dataset ML final",               "14"),
        ("11.", "Décisions techniques",                     "16"),
        ("12.", "Bilan et prochaines étapes",               "17"),
    ]
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*BLACK)
    for num, title, page in toc:
        y = pdf.get_y()
        pdf.set_x(self_lm := 20)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        pdf.cell(12, 8, num)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*BLACK)
        pdf.cell(140, 8, title)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, page, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Ligne pointillée
        pdf.set_draw_color(*GRAY_LN)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    # -----------------------------------------------------------------------
    # PAGE 3 - CONTEXTE ET SOURCES
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("1", "Contexte et problématique")

    pdf.body_text(
        "L'entreprise GE opère dans le secteur industriel et traite chaque année plusieurs dizaines de "
        "milliers de commandes client impliquant des articles variés (élevage, construction, outillage...). "
        "La gestion de la chaîne d'approvisionnement repose aujourd'hui sur des objectifs de chiffre "
        "d'affaires, sans mécanisme prédictif pour anticiper les retards de livraison."
    )
    pdf.body_text(
        "Ce projet de mémoire vise à construire un système de prédiction basé sur l'Intelligence "
        "Artificielle, répondant à la problématique suivante :"
    )
    pdf.set_fill_color(*LIGHT_B)
    pdf.set_draw_color(*BLUE)
    pdf.rect(20, pdf.get_y(), 170, 16, "FD")
    pdf.set_font("Helvetica", "BI", 11)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(24, pdf.get_y() + 4)
    pdf.multi_cell(162, 6,
        "Comment une approche IA peut-elle prédire si une livraison sera en retard, "
        "afin d'optimiser la chaîne d'approvisionnement ?")
    pdf.set_text_color(*BLACK)
    pdf.ln(8)

    pdf.body_text(
        "La Phase 1 - objet du présent rapport - constitue le socle de données de ce projet. "
        "Elle transforme les extractions brutes du système ERP en un dataset structuré, propre, "
        "et exploitable directement par les algorithmes de Machine Learning."
    )

    # Objectif North Star
    pdf.sub_title("Objectif de performance")
    pdf.body_text("L'objectif quantitatif fixé pour la Phase 2 est :")
    pdf.bullet(["Précision de prédiction > 60 % (F1-score sur la classe 'retard')"])
    pdf.ln(3)

    # -----------------------------------------------------------------------
    pdf.section_title("2", "Sources de données")

    pdf.body_text(
        "Deux fichiers CSV sont fournis par le système ERP de GE, couvrant la période "
        "septembre 2020 - décembre 2025."
    )

    pdf.h_table(
        headers=["Fichier", "Lignes", "Colonnes", "Description"],
        rows=[
            ["Extraction commande client 2021-2025.csv", "352 549", "14",
             "Commandes passées par les clients"],
            ["Extraction livraison client 2021-2025.csv", "353 325", "13",
             "Livraisons effectives correspondantes"],
        ],
        col_widths=[80, 22, 20, 48],
    )

    pdf.sub_title("Colonnes brutes - Commandes (CMD)")
    pdf.h_table(
        headers=["Colonne brute", "Renommée en", "Type", "Rôle"],
        rows=[
            ["#", "row_id", "int", "Identifiant de ligne (ignoré)"],
            ["Num commande", "num_commande", "int", "Identifiant de commande"],
            ["Numéro d'article", "code_article", "str", "Code article commandé"],
            ["Quantité", "qte_demandee", "int", "Quantité demandée"],
            ["Date d'enregistrement", "date_enregistrement", "str->date", "Date de saisie commande"],
            ["Date de livraison demandée", "date_livraison_demandee", "str->date", "Livraison souhaitée"],
            ["Code client/fournisseur", "code_client", "str", "Identifiant client"],
            ["Activité stratégique client", "famille_activite_client", "str", "Secteur d'activité client"],
            ["Activité stratégique article", "famille_activite_article", "str", "Famille article"],
            ["Ségment stratégique", "segment", "str", "Segment commercial (S accentué)"],
            ["Type activité", "type_activite", "str", "Type de produit"],
            ["Pays/région", "pays", "str", "Pays du client"],
            ["Prix de vente", "prix", "float", "Prix unitaire"],
            ["Devise du prix", "devise", "str", "Devise (EUR, USD, CNY)"],
        ],
        col_widths=[52, 44, 20, 54],
    )

    pdf.sub_title("Colonnes brutes - Livraisons (LIV)")
    pdf.h_table(
        headers=["Colonne brute", "Renommée en", "Type", "Rôle"],
        rows=[
            ["#", "row_id", "int", "Identifiant de ligne (ignoré)"],
            ["Num commande", "num_commande", "int", "Clé de jointure avec CMD"],
            ["Numéro d'article", "code_article", "str", "Clé de jointure avec CMD"],
            ["Qté", "qte_livree", "int", "Quantité effectivement livrée"],
            ["Date de livraison réelle", "date_livraison_reelle", "str->date", "Date réelle de livraison"],
            ["Code client/fournisseur", "code_client", "str", "Identifiant client"],
            ["Activité stratégique client", "famille_activite_client", "str", "Redondant avec CMD"],
            ["Activité stratégique article", "famille_activite_article", "str", "Redondant avec CMD"],
            ["Ségment stratégique", "segment", "str", "Redondant avec CMD"],
            ["Type activité", "type_activite", "str", "Redondant avec CMD"],
            ["Pays/région", "pays", "str", "Redondant avec CMD"],
            ["Prix de vente", "prix", "float", "Redondant avec CMD"],
            ["Devise du prix", "devise", "str", "Redondant avec CMD"],
        ],
        col_widths=[52, 44, 20, 54],
    )

    # -----------------------------------------------------------------------
    # PAGE - ARCHITECTURE DU PIPELINE
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("3", "Architecture du pipeline de traitement")

    pdf.body_text(
        "Le pipeline est composé de 7 étapes séquentielles. Chaque étape produit un fichier "
        "intermédiaire en CSV et/ou Parquet, permettant la reprise à n'importe quel point "
        "sans relancer l'intégralité du traitement."
    )

    # Diagramme textuel
    steps_diag = [
        ("Fichiers CSV bruts", "352 549 CMD  /  353 325 LIV", GRAY_BG),
        ("Étape 1 - Chargement & renommage", "cmd_step1.csv  /  liv_step1.csv", LIGHT_B),
        ("Étape 2 - Valeurs manquantes", "cmd_step2.csv  /  liv_step2.csv", LIGHT_B),
        ("Étape 3 - Normalisation dates", "cmd_step3.csv  /  liv_step3.csv", LIGHT_B),
        ("Étape 4 - Jointure LEFT", "dataset_step4.parquet  (349 390 x 19)", LIGHT_B),
        ("Étape 5 - Feature engineering", "dataset_step5.parquet  (349 390 x 32)", LIGHT_B),
        ("Étape 6 - Encodage catégorielles", "dataset_step6.parquet  (349 390 x 41)", LIGHT_B),
        ("Étape 7 - Sélection & export", "dataset_ml_final.parquet  (349 390 x 24)", (200, 230, 200)),
    ]
    x0 = 35
    for i, (title, output, color) in enumerate(steps_diag):
        y0 = pdf.get_y()
        pdf.set_fill_color(*color)
        pdf.set_draw_color(*GRAY_LN)
        pdf.rect(x0, y0, 140, 11, "FD")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.set_xy(x0 + 4, y0 + 1.5)
        pdf.cell(80, 5, title)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(x0 + 4, y0 + 6)
        pdf.cell(132, 5, output)
        pdf.set_y(y0 + 11)
        if i < len(steps_diag) - 1:
            # Flèche
            pdf.set_font("Helvetica", "", 12)
            pdf.set_text_color(*BLUE)
            pdf.set_xy(x0 + 62, pdf.get_y())
            pdf.cell(20, 5, "v", align="C")
            pdf.ln(4)
    pdf.set_text_color(*BLACK)
    pdf.ln(5)

    # KPI globaux
    pdf.sub_title("Chiffres clés du dataset final")
    pdf.kpi_row([
        ("Lignes",        "349 390",   LIGHT_B),
        ("Features ML",   "23",        LIGHT_B),
        ("Taux de retard","19,2 %",    (255, 235, 205)),
        ("Clients uniques","3 465",    LIGHT_B),
        ("Articles uniques","1 068",   LIGHT_B),
    ])

    # -----------------------------------------------------------------------
    # ÉTAPE 1
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("4", "Étape 1 - Chargement, encodage et renommage")

    pdf.sub_title("4.1 - Diagnostic préliminaire des fichiers")
    pdf.body_text(
        "Avant tout chargement via pandas, une inspection binaire des premières lignes des fichiers "
        "CSV a été réalisée pour identifier sans ambiguïté l'encodage et le séparateur."
    )

    pdf.h_table(
        headers=["Paramètre", "Valeur détectée", "Méthode de détection"],
        rows=[
            ["Encodage", "UTF-8", "Octets 0xC3 0xA9 = é en UTF-8 (pas latin-1)"],
            ["Séparateur", "Virgule  ,", "Comptage des virgules vs points-virgules"],
            ["Colonne segment", "Ségment stratégique (S accentué)", "Lecture directe avec encodage UTF-8"],
        ],
        col_widths=[40, 42, 88],
    )

    pdf.note_box(
        "Attention : le nom de colonne 'Ségment stratégique' comporte un accent sur le S, "
        "contrairement à 'Activité stratégique' qui n'en a pas sur le A. "
        "Ce détail a nécessité un traitement spécifique lors du renommage."
    )

    pdf.sub_title("4.2 - Renommage en snake_case")
    pdf.body_text(
        "Les noms de colonnes bruts contiennent des caractères accentués, des espaces et des "
        "apostrophes, incompatibles avec les conventions Python et les API de Machine Learning. "
        "Un renommage complet en snake_case est appliqué sur les deux DataFrames."
    )

    pdf.code_block([
        "df_cmd = pd.read_csv('Extraction commande client 2021-2025.csv',",
        "                     encoding='utf-8', sep=',')",
        "df_cmd = df_cmd.rename(columns={",
        "    'Ségment stratégique' : 'segment',",
        "    \"Numéro d'article\"   : 'code_article',",
        "    'Quantité'            : 'qte_demandee',  ...",
        "})",
    ], title="Code - chargement et renommage")

    pdf.sub_title("4.3 - État après l'Étape 1")
    pdf.h_table(
        headers=["Dataset", "Lignes", "Colonnes", "Valeurs nulles (résumé)"],
        rows=[
            ["CMD (commandes)", "352 549", "14",
             "code_article:31 | pays:99 | devise:1987 | famille_act:17 | segment:19"],
            ["LIV (livraisons)", "353 325", "13",
             "code_article:30 | pays:100 | devise:1977 | famille_act:17 | segment:19"],
        ],
        col_widths=[38, 18, 20, 94],
    )

    # -----------------------------------------------------------------------
    # ÉTAPE 2
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("5", "Étape 2 - Traitement des valeurs manquantes")

    pdf.body_text(
        "Cinq colonnes présentent des valeurs manquantes. Une stratégie différenciée est appliquée "
        "selon la nature de chaque colonne et son rôle dans le modèle prédictif."
    )

    pdf.h_table(
        headers=["Colonne", "Nulls CMD", "Nulls LIV", "Stratégie", "Résultat"],
        rows=[
            ["code_article", "31", "30", "Suppression des lignes", "0 null - 31/30 lignes perdues"],
            ["segment", "19", "19", "Résolu par le point ci-dessus", "0 null (100% overlap)"],
            ["pays", "99", "100", "Mode par code_client, sinon UNKNOWN", "0 null"],
            ["devise", "1 987", "1 977", "Mode par pays, sinon EUR", "0 null"],
            ["famille_activite_client", "17", "17", "Mode par code_client, sinon AUTRE", "0 null"],
        ],
        col_widths=[44, 18, 18, 58, 32],
    )

    pdf.sub_title("5.1 - code_article : suppression ciblée")
    pdf.body_text(
        "Le modèle prédit au niveau de la paire (code_client, code_article). "
        "Une ligne sans article est structurellement inutilisable - elle ne peut être jointe, "
        "encodée ni utilisée pour l'entraînement. La suppression est retenue."
    )
    pdf.body_text(
        "Perte de données : 31 / 352 549 = 0,009 % pour CMD, négligeable. "
        "Les autres lignes de la même commande sont conservées (elles sont indépendantes)."
    )

    pdf.sub_title("5.2 - pays : imputation par mode du client")
    pdf.body_text(
        "98 % des 99 clients ayant un pays manquant disposent d'autres commandes avec un pays connu. "
        "L'imputation utilise le pays le plus fréquent observé pour ce client dans le dataset. "
        "Pour le client C12663 (cas extrême : 2 commandes, toutes sans pays), la valeur UNKNOWN est assignée."
    )
    pdf.code_block([
        "mode_pays = df.dropna(subset=['pays'])",
        "             .groupby('code_client')['pays']",
        "             .agg(lambda x: x.mode()[0])",
        "",
        "df['pays'] = df.apply(",
        "    lambda row: mode_pays.get(row['code_client'], 'UNKNOWN')",
        "                if pd.isna(row['pays']) else row['pays'], axis=1)",
    ], title="Code - imputation pays")

    pdf.sub_title("5.3 - devise : imputation par devise majoritaire du pays")
    pdf.body_text(
        "La devise est fortement corrélée au pays du client. La distribution observée est la suivante :"
    )
    pdf.h_table(
        headers=["Pays", "Devise majoritaire", "Couverture"],
        rows=[
            ["FR (France)", "EUR", "99,8 %"],
            ["US (États-Unis)", "USD", "100 %"],
            ["CA (Canada)", "USD", "100 %"],
            ["GB (Royaume-Uni)", "EUR", "97 %"],
            ["CN (Chine)", "CNY / USD", "mixte"],
            ["Autres", "EUR (fallback)", "-"],
        ],
        col_widths=[40, 50, 80],
    )

    pdf.sub_title("5.4 - famille_activite_client : mode par client")
    pdf.body_text(
        "L'activité stratégique client est un attribut stable par client (ELEVAGE, CONSTRUCTION, "
        "RETRACTION ou AUTRE). L'imputation par mode sur le code_client est donc fiable. "
        "Aucun client ne présente plus de 17 lignes concernées."
    )

    pdf.sub_title("5.5 - Résultat final Étape 2")
    pdf.kpi_row([
        ("CMD - lignes finales",  "352 518",  LIGHT_B),
        ("LIV - lignes finales",  "353 295",  LIGHT_B),
        ("Nulls restants",        "0",        (200, 230, 200)),
        ("Lignes supprimées CMD", "31",       GRAY_BG),
    ])

    # -----------------------------------------------------------------------
    # ÉTAPE 3
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("6", "Étape 3 - Normalisation et validation des dates")

    pdf.body_text(
        "Les trois colonnes de dates sont stockées sous forme de chaînes de caractères "
        "au format dd/mm/yyyy dans les fichiers sources. Elles sont converties en objets "
        "datetime64 pour permettre les calculs temporels (délais, extraction de composantes)."
    )

    pdf.h_table(
        headers=["Colonne", "Source", "Format brut", "Après conversion", "NaT"],
        rows=[
            ["date_enregistrement", "CMD", "dd/mm/yyyy", "datetime64[us]", "0"],
            ["date_livraison_demandee", "CMD", "dd/mm/yyyy", "datetime64[us]", "0"],
            ["date_livraison_reelle", "LIV", "dd/mm/yyyy", "datetime64[us]", "0"],
        ],
        col_widths=[50, 18, 28, 34, 16],
    )

    pdf.sub_title("6.1 - Distribution temporelle des données")
    pdf.h_table(
        headers=["Année", "Commandes enregistrées", "Livraisons réelles"],
        rows=[
            ["2020", "1 718", "0 (hors périmètre livraison)"],
            ["2021", "75 683", "76 161"],
            ["2022", "67 569", "66 548"],
            ["2023", "69 129", "70 078"],
            ["2024", "71 637", "72 004"],
            ["2025", "66 782", "68 504"],
        ],
        col_widths=[30, 60, 80],
    )
    pdf.body_text(
        "La répartition est homogène sur toutes les années, sans pic d'anomalie. "
        "Les données de 2020 correspondent à des commandes enregistrées en fin d'année "
        "mais livrées en 2021."
    )

    pdf.sub_title("6.2 - Anomalies temporelles détectées et traitées")
    pdf.body_text(
        "Une vérification de cohérence est effectuée : toute ligne vérifiant "
        "date_livraison_reelle < date_enregistrement constitue une anomalie physiquement "
        "impossible (livraison avant la commande)."
    )
    pdf.h_table(
        headers=["num_commande", "code_article", "date_enregistrement", "date_livraison_reelle", "Écart"],
        rows=[
            ["152881", "A0858", "2021-09-01", "2021-07-02", "-61 jours"],
            ["152881", "A0989", "2021-09-01", "2021-07-02", "-61 jours"],
            ["152881", "A0592", "2021-09-01", "2021-07-02", "-61 jours"],
        ],
        col_widths=[34, 28, 38, 38, 32],
    )
    pdf.note_box(
        "Diagnostic : la commande 152881 a été saisie dans l'ERP le 1er septembre 2021, "
        "mais la livraison (juillet 2021) est antérieure. Il s'agit d'une saisie tardive "
        "dans le système. Décision : suppression des 3 lignes (0,0008 % des données LIV). "
        "Conserver ces lignes produirait un delai_jours négatif qui polluerait l'apprentissage."
    )

    pdf.sub_title("6.3 - Résultat final Étape 3")
    pdf.kpi_row([
        ("Plage CMD", "23/09/2020->23/12/2025", LIGHT_B),
        ("Plage LIV", "04/01/2021->23/12/2025", LIGHT_B),
        ("Anomalies supprimées", "3 lignes", (255, 235, 205)),
        ("NaT après conversion", "0", (200, 230, 200)),
    ])

    # -----------------------------------------------------------------------
    # ÉTAPE 4
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("7", "Étape 4 - Jointure commandes x livraisons")

    pdf.body_text(
        "La jointure est la transformation centrale du pipeline. Elle relie chaque ligne de "
        "commande à sa ou ses livraisons correspondantes, créant le dataset analytique unifié."
    )

    pdf.sub_title("7.1 - Problématique des paires dupliquées")
    pdf.body_text(
        "La clé de jointure naturelle est (num_commande, code_article). Or les deux tables "
        "présentent des paires non uniques pour des raisons distinctes :"
    )
    pdf.h_table(
        headers=["Table", "Cause du doublon", "Paires dupliquées", "Agrégation retenue"],
        rows=[
            ["CMD", "Ré-ouvertures de commandes dans l'ERP",
             "3 128", "sum(qte_demandee), max(prix)"],
            ["LIV", "Livraisons fractionnées (plusieurs envois partiels)",
             "4 201", "sum(qte_livree), max(date_livraison_reelle)"],
        ],
        col_widths=[15, 62, 30, 63],
    )
    pdf.body_text(
        "La quantité commandée est sommée car les ré-ouvertures représentent des ajouts réels. "
        "La date de livraison réelle retient le maximum (dernière livraison) car c'est elle "
        "qui détermine si la commande est en retard au sens contractuel."
    )

    pdf.sub_title("7.2 - Choix du type de jointure")
    pdf.body_text(
        "Deux types de jointure étaient envisageables :"
    )
    pdf.h_table(
        headers=["Type", "Commandes conservées", "Avantage", "Inconvénient"],
        rows=[
            ["INNER JOIN", "Uniquement livrées", "Cible toujours connue",
             "Perte des 332 commandes en attente"],
            ["LEFT JOIN (retenu)", "Toutes (livrées + en_attente)",
             "Dataset complet pour production", "332 NaN dans en_retard"],
        ],
        col_widths=[28, 42, 52, 48],
    )
    pdf.body_text(
        "La jointure LEFT est retenue. Les 332 commandes en attente (statut='en_attente') "
        "sont exclues de l'entraînement via un filtre sur en_retard.notna(), mais restent "
        "disponibles pour les prédictions en production future."
    )

    pdf.sub_title("7.3 - Métriques dérivées calculées")
    pdf.body_text(
        "Trois colonnes analytiques sont calculées après la jointure. Elles servent à l'analyse "
        "exploratoire mais sont exclues des features ML pour éviter le data leakage."
    )
    pdf.h_table(
        headers=["Colonne", "Formule", "Interprétation", "Exclue du ML"],
        rows=[
            ["taux_satisfaction", "qte_livree / qte_demandee  (clip 0-1)",
             "Taux de service (0,999 en moyenne)", "Oui (post-livraison)"],
            ["livraison_excedentaire", "qte_livree > qte_demandee",
             "55 sur-livraisons détectées", "Oui (post-livraison)"],
            ["delai_jours", "date_liv_reelle - date_liv_demandee  (jours)",
             "Retard (>0) ou avance (<0)", "Oui (post-livraison)"],
        ],
        col_widths=[44, 52, 48, 26],
    )

    pdf.sub_title("7.4 - Résultat final Étape 4")
    pdf.kpi_row([
        ("Shape", "349 390 x 19", LIGHT_B),
        ("Livrées", "349 058 (99,9 %)", (200, 230, 200)),
        ("En attente", "332 (0,1 %)", (255, 235, 205)),
        ("Délai médian", "0 jour", LIGHT_B),
        ("Délai max", "+139 jours", LIGHT_B),
    ])

    # -----------------------------------------------------------------------
    # ÉTAPE 5
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("8", "Étape 5 - Feature engineering temporel")

    pdf.body_text(
        "L'objectif est d'extraire des variables prédictives à partir des trois colonnes de dates, "
        "afin de capturer la saisonnalité, les cycles budgétaires clients et le délai contractuel. "
        "Ces features sont connues au moment de la commande - elles ne constituent pas un data leakage."
    )

    pdf.sub_title("8.1 - Features issues de date_enregistrement")
    pdf.h_table(
        headers=["Feature", "Formule", "Plage", "Justification métier"],
        rows=[
            ["annee_cmd", "dt.year", "2020-2025", "Tendance temporelle / drift"],
            ["mois_cmd", "dt.month", "1-12", "Saisonnalité mensuelle"],
            ["trimestre_cmd", "dt.quarter", "1-4", "Cycles budgétaires trimestriels"],
            ["semaine_cmd", "dt.isocalendar().week", "1-53", "Granularité hebdomadaire"],
            ["jour_semaine_cmd", "dt.dayofweek", "0=Lun ... 6=Dim", "Comportement lié au jour ouvré"],
            ["est_fin_mois_cmd", "day >= 25 -> 0/1", "0 ou 1", "Pic de commandes fin de mois"],
        ],
        col_widths=[40, 42, 30, 58],
    )

    pdf.sub_title("8.2 - Features issues de date_livraison_demandee")
    pdf.h_table(
        headers=["Feature", "Formule", "Plage", "Justification métier"],
        rows=[
            ["annee_liv_dem", "dt.year", "2021-2025", "Tendance de la demande future"],
            ["mois_liv_dem", "dt.month", "1-12", "Saisonnalité de la demande"],
            ["trimestre_liv_dem", "dt.quarter", "1-4", "Pression de fin de trimestre"],
            ["jour_semaine_liv_dem", "dt.dayofweek", "0-6", "Jour de livraison souhaité"],
            ["est_weekend_liv_dem", "dayofweek >= 5 -> 0/1", "0 ou 1",
             "504 livraisons demandées un weekend (0,1 %)"],
        ],
        col_widths=[44, 38, 28, 60],
    )

    pdf.sub_title("8.3 - Délai contractuel")
    pdf.body_text(
        "La feature delai_demande_jours mesure le délai accordé par le client entre la date "
        "de commande et la date de livraison souhaitée. C'est une information disponible dès "
        "la prise de commande - sans leakage."
    )
    pdf.h_table(
        headers=["Statistique", "Valeur"],
        rows=[
            ["Minimum", "-61 jours (livraison souhaitée avant la commande - 96 cas)"],
            ["Médiane", "5 jours"],
            ["Maximum", "388 jours"],
        ],
        col_widths=[40, 130],
    )
    pdf.body_text(
        "Les 96 cas de délai négatif correspondent à des commandes avec une date de livraison "
        "demandée antérieure à la date d'enregistrement - vraisemblablement des saisies de "
        "régularisation. Ces lignes sont conservées."
    )

    pdf.sub_title("8.4 - Variable cible : en_retard")
    pdf.body_text(
        "La variable cible est une classification binaire dérivée de delai_jours :"
    )
    pdf.h_table(
        headers=["Valeur", "Condition", "Interprétation", "Effectif"],
        rows=[
            ["0", "delai_jours <= 0", "Livraison à temps ou en avance", "281 975 (80,8 %)"],
            ["1", "delai_jours > 0", "Livraison en retard", "67 083 (19,2 %)"],
            ["NaN", "statut = en_attente", "Cible inconnue - exclue de l'entraînement", "332 (0,1 %)"],
        ],
        col_widths=[15, 38, 70, 47],
    )
    pdf.note_box(
        "Déséquilibre de classes : 80,8 % / 19,2 %. Ce déséquilibre modéré sera traité en "
        "Phase 2 via class_weight='balanced' (Random Forest / XGBoost) ou SMOTE. "
        "La métrique principale sera le F1-score sur la classe '1' (retard), "
        "plus pertinente que l'accuracy en contexte déséquilibré."
    )

    pdf.sub_title("8.5 - Résultat final Étape 5")
    pdf.kpi_row([
        ("Colonnes total", "32", LIGHT_B),
        ("Nouvelles features", "13", LIGHT_B),
        ("Taux de retard", "19,2 %", (255, 235, 205)),
        ("Cibles inconnues", "332 NaN", GRAY_BG),
    ])

    # -----------------------------------------------------------------------
    # ÉTAPE 6
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("9", "Étape 6 - Encodage des variables catégorielles")

    pdf.body_text(
        "Les algorithmes de Machine Learning opèrent sur des valeurs numériques. "
        "Les neuf colonnes catégorielles du dataset sont encodées selon leur cardinalité."
    )

    pdf.sub_title("9.1 - Stratégie par colonne")
    pdf.h_table(
        headers=["Colonne", "Cardinalité", "Méthode", "Colonne créée"],
        rows=[
            ["statut", "2", "Binaire (livre=1, en_attente=0)", "statut_enc"],
            ["devise", "3", "Label Encoding", "devise_enc"],
            ["pays", "79", "Label Encoding", "pays_enc"],
            ["famille_activite_client", "4", "Label Encoding", "famille_activite_client_enc"],
            ["famille_activite_article", "3", "Label Encoding", "famille_activite_article_enc"],
            ["segment", "9", "Label Encoding", "segment_enc"],
            ["type_activite", "12", "Label Encoding", "type_activite_enc"],
            ["code_client", "3 465", "Frequency Encoding", "code_client_freq"],
            ["code_article", "1 068", "Frequency Encoding", "code_article_freq"],
        ],
        col_widths=[50, 22, 52, 46],
    )

    pdf.sub_title("9.2 - Justification du Frequency Encoding")
    pdf.body_text(
        "Pour code_client (3 465 valeurs uniques) et code_article (1 068 valeurs), "
        "un One-Hot Encoding créerait plus de 4 500 colonnes supplémentaires, "
        "rendant le dataset extrêmement sparse et coûteux en mémoire."
    )
    pdf.body_text(
        "Le Frequency Encoding remplace chaque valeur par son nombre d'occurrences dans le dataset. "
        "Cette approche capture une information métier utile : un client très actif (fréquence élevée) "
        "est différent d'un client occasionnel - cette distinction peut être prédictive du risque de retard."
    )
    pdf.h_table(
        headers=["Feature", "Min", "Max", "Médiane", "Top client"],
        rows=[
            ["code_client_freq", "1", "4 578", "365", "C12289 (4 578 commandes)"],
            ["code_article_freq", "1", "11 553", "2 573", "Article le plus commandé"],
        ],
        col_widths=[40, 18, 20, 22, 70],
    )

    pdf.sub_title("9.3 - Exemple d'encodage Label")
    pdf.h_table(
        headers=["Valeur brute", "Valeur encodée"],
        rows=[
            ["devise : CNY -> 0, EUR -> 1, USD -> 2", ""],
            ["famille_activite_client : AUTRE=0, CONSTRUCTION=1, ELEVAGE=2, RETRACTION=3", ""],
            ["segment : BITUME=0, CONNECTIQUE=1, CONTENTION=2, COUVERTURE=3...", ""],
        ],
        col_widths=[150, 20],
    )

    pdf.sub_title("9.4 - Résultat final Étape 6")
    pdf.kpi_row([
        ("Colonnes total", "41", LIGHT_B),
        ("Colonnes encodées", "9", LIGHT_B),
        ("Nulls dans _enc", "0", (200, 230, 200)),
        ("Type de toutes les _enc", "int64", LIGHT_B),
    ])

    # -----------------------------------------------------------------------
    # ÉTAPE 7
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("10", "Étape 7 - Dataset ML final")

    pdf.body_text(
        "La dernière étape sélectionne uniquement les colonnes utilisables par un modèle prédictif "
        "au moment de la prise de commande. Le critère de sélection est strict : "
        "toute information connue seulement après la livraison est exclue."
    )

    pdf.sub_title("10.1 - Colonnes exclues et justification")
    pdf.h_table(
        headers=["Colonne exclue", "Raison de l'exclusion"],
        rows=[
            ["delai_jours", "Data leakage : connu seulement après livraison réelle"],
            ["taux_satisfaction", "Data leakage : connu seulement après livraison réelle"],
            ["livraison_excedentaire", "Data leakage : connu seulement après livraison réelle"],
            ["qte_livree", "Data leakage : inconnue au moment de la commande"],
            ["date_livraison_reelle", "Data leakage : inconnue au moment de la commande"],
            ["date_enregistrement", "Décomposée en annee_cmd, mois_cmd, etc."],
            ["date_livraison_demandee", "Décomposée en annee_liv_dem, mois_liv_dem, etc."],
            ["code_client (texte)", "Remplacé par code_client_freq (numérique)"],
            ["code_article (texte)", "Remplacé par code_article_freq (numérique)"],
            ["num_commande", "Identifiant technique sans pouvoir prédictif"],
            ["statut, devise, pays...", "Remplacés par colonnes _enc correspondantes"],
        ],
        col_widths=[62, 108],
    )

    pdf.sub_title("10.2 - Les 23 features retenues")
    pdf.h_table(
        headers=["#", "Feature", "Type", "Description"],
        rows=[
            ["1", "qte_demandee", "int64", "Quantité commandée"],
            ["2", "prix", "float64", "Prix unitaire de vente"],
            ["3", "annee_cmd", "int32", "Année d'enregistrement de la commande"],
            ["4", "mois_cmd", "int32", "Mois d'enregistrement (1-12)"],
            ["5", "trimestre_cmd", "int32", "Trimestre d'enregistrement (1-4)"],
            ["6", "semaine_cmd", "int64", "Semaine ISO (1-53)"],
            ["7", "jour_semaine_cmd", "int32", "Jour de la semaine (0=Lun ... 6=Dim)"],
            ["8", "est_fin_mois_cmd", "int64", "Commande en fin de mois (0/1)"],
            ["9", "annee_liv_dem", "int32", "Année de livraison demandée"],
            ["10", "mois_liv_dem", "int32", "Mois de livraison demandée"],
            ["11", "trimestre_liv_dem", "int32", "Trimestre de livraison demandée"],
            ["12", "jour_semaine_liv_dem", "int32", "Jour semaine livraison demandée"],
            ["13", "est_weekend_liv_dem", "int64", "Livraison demandée un weekend (0/1)"],
            ["14", "delai_demande_jours", "int64", "Délai accordé par le client (jours)"],
            ["15", "statut_enc", "int64", "Statut encodé (0=en_attente, 1=livre)"],
            ["16", "devise_enc", "int64", "Devise encodée (0=CNY, 1=EUR, 2=USD)"],
            ["17", "pays_enc", "int64", "Pays encodé (Label Encoding, 79 classes)"],
            ["18", "famille_activite_client_enc", "int64", "Activité client encodée (4 classes)"],
            ["19", "famille_activite_article_enc", "int64", "Activité article encodée (3 classes)"],
            ["20", "segment_enc", "int64", "Segment commercial encodé (9 classes)"],
            ["21", "type_activite_enc", "int64", "Type d'activité encodé (12 classes)"],
            ["22", "code_client_freq", "int64", "Fréquence client dans le dataset"],
            ["23", "code_article_freq", "int64", "Fréquence article dans le dataset"],
        ],
        col_widths=[10, 58, 22, 80],
    )

    pdf.sub_title("10.3 - Statistiques descriptives du dataset final")
    pdf.h_table(
        headers=["Statistique", "Valeur"],
        rows=[
            ["Shape", "349 390 lignes x 24 colonnes (23 features + 1 cible)"],
            ["Nulls dans les features", "0 (aucun null dans X)"],
            ["Nulls dans la cible (en_retard)", "332 (commandes en_attente, exclues de l'entraînement)"],
            ["Taux de retard (classe 1)", "19,2 %  (67 083 / 349 058 commandes livrées)"],
            ["Taux à temps (classe 0)", "80,8 %  (281 975 / 349 058)"],
            ["Taille fichier Parquet", "~2,1 MB (vs 23 MB pour le CSV équivalent)"],
        ],
        col_widths=[58, 112],
    )

    # -----------------------------------------------------------------------
    # PAGE - DÉCISIONS TECHNIQUES
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("11", "Récapitulatif des décisions techniques")

    pdf.body_text(
        "Cette section consolide l'ensemble des choix techniques réalisés au cours du pipeline, "
        "avec leur justification et les alternatives écartées."
    )

    decisions = [
        ("Encodage UTF-8 (pas latin-1)",
         "Les octets 0xC3 0xA9 indiquent un é UTF-8. Charger en latin-1 aurait produit des caractères "
         "corrompus dans les noms de colonnes accentués.",
         "Lecture binaire des premiers octets des fichiers CSV."),

        ("Suppression (et non imputation) pour code_article null",
         "Une ligne sans article ne peut pas être jointe, encodée ni utilisée pour la prédiction. "
         "L'imputation d'un code article fictif n'aurait aucun sens métier.",
         "31 CMD + 30 LIV = 61 lignes supprimées (0,009 %)."),

        ("Jointure LEFT (pas INNER)",
         "Les 332 commandes en attente sont des données de production futures. "
         "Les exclure via INNER JOIN appauvrirait inutilement le dataset et rendrait le pipeline "
         "inutilisable pour la prédiction en temps réel.",
         "332 NaN dans en_retard, filtrés à l'entraînement via df[df.en_retard.notna()]."),

        ("Agrégation LIV : sum(qte_livree) + max(date_livraison_reelle)",
         "Une commande avec 3 livraisons fractionnées est considérée comme livrée à la date de la "
         "dernière livraison. La quantité totale est la somme des fractions.",
         "Alternative écartée : garder toutes les lignes aurait créé des faux doublons."),

        ("Frequency Encoding pour code_client / code_article",
         "Cardinalité de 3 465 et 1 068 valeurs respectivement. Le One-Hot créerait >4 500 colonnes, "
         "rendant le dataset extrêmement sparse et les forêts aléatoires peu efficaces.",
         "Capture l'importance relative d'un client/article sans explosion dimensionnelle."),

        ("Exclusion de delai_jours, taux_satisfaction, livraison_excedentaire",
         "Ces trois colonnes sont inconnues au moment de la prise de commande. "
         "Les inclure constituerait un data leakage : le modèle apprendrait à prédire "
         "le retard en connaissant déjà le retard.",
         "Garde-fou fondamental pour la validité de l'évaluation en production."),

        ("Variable cible binaire en_retard plutôt que régression sur delai_jours",
         "La régression sur delai_jours est un problème plus difficile avec distribution très asymétrique "
         "(médiane = 0 jour). La classification binaire (retard / pas retard) correspond mieux "
         "au besoin opérationnel : savoir si une commande risque d'être en retard.",
         "Déséquilibre 80/19 plus gérable que la distribution continue de delai_jours."),

        ("Suppression des 3 anomalies date_livraison_reelle < date_enregistrement",
         "Ces lignes (commande 152881) ont une date de livraison antérieure à l'enregistrement, "
         "ce qui est physiquement impossible. Il s'agit d'une erreur de saisie ERP.",
         "Perte : 3 lignes sur 353 295 = 0,0008 %."),
    ]

    for i, (title, justif, impact) in enumerate(decisions):
        if pdf.get_y() > 230:
            pdf.add_page()
        y0 = pdf.get_y()
        pdf.set_fill_color(*LIGHT_B)
        pdf.set_draw_color(*BLUE)
        pdf.rect(20, y0, 170, 7, "FD")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.set_xy(23, y0 + 1.5)
        pdf.cell(164, 5, f"Décision {i+1} : {title}")
        pdf.set_y(y0 + 8)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*BLACK)
        pdf.set_x(25)
        pdf.multi_cell(162, 5, f"Justification : {justif}")
        pdf.set_x(25)
        pdf.set_text_color(60, 100, 60)
        pdf.multi_cell(162, 5, f"Impact : {impact}")
        pdf.set_text_color(*BLACK)
        pdf.ln(2)

    # -----------------------------------------------------------------------
    # PAGE - BILAN ET PROCHAINES ÉTAPES
    # -----------------------------------------------------------------------
    pdf.add_page()
    pdf.section_title("12", "Bilan et prochaines étapes")

    pdf.sub_title("12.1 - Bilan de la Phase 1")
    pdf.h_table(
        headers=["Étape", "Action principale", "Données en entrée", "Données en sortie"],
        rows=[
            ["1", "Chargement + renommage snake_case",
             "352 549 CMD / 353 325 LIV", "Colonnes normalisées"],
            ["2", "Traitement valeurs manquantes",
             "Divers nulls", "0 null restant"],
            ["3", "Normalisation dates + anomalies",
             "Chaînes dd/mm/yyyy", "datetime64 - 3 anomalies supprimées"],
            ["4", "Jointure LEFT CMD x LIV",
             "2 tables séparées", "349 390 x 19"],
            ["5", "Feature engineering temporel + cible",
             "349 390 x 19", "349 390 x 32"],
            ["6", "Encodage catégorielles",
             "9 colonnes texte", "9 colonnes numériques ajoutées"],
            ["7", "Sélection features + export",
             "349 390 x 41", "dataset_ml_final.parquet (x 24)"],
        ],
        col_widths=[12, 58, 50, 50],
    )

    pdf.sub_title("12.2 - Fichiers produits")
    pdf.h_table(
        headers=["Fichier", "Localisation", "Taille", "Usage"],
        rows=[
            ["cmd_step1/2/3.csv", "data/processed/", "~39 MB chacun", "Intermédiaires CMD"],
            ["liv_step1/2/3.csv", "data/processed/", "~35 MB chacun", "Intermédiaires LIV"],
            ["dataset_step4.parquet", "data/processed/", "3,4 MB", "Post-jointure"],
            ["dataset_step5.parquet", "data/processed/", "3,7 MB", "Post-feature-eng."],
            ["dataset_step6.parquet", "data/processed/", "4,7 MB", "Post-encodage"],
            ["dataset_ml_final.parquet", "data/processed/", "2,2 MB", "Entrée Phase 2 (ML)"],
            ["dataset_ml_final.csv", "data/processed/", "23 MB", "Référence lisible"],
        ],
        col_widths=[52, 38, 24, 56],
    )

    pdf.sub_title("12.3 - Phase 2 : Modélisation (à venir)")
    pdf.body_text("Le dataset_ml_final.parquet sera utilisé pour entraîner et évaluer trois modèles :")

    phase2 = [
        ("1.", "Train/test split stratifié 80/20",
         "Stratification sur en_retard pour respecter le ratio 80/19 dans les deux splits"),
        ("2.", "Gestion du déséquilibre",
         "Option A : class_weight='balanced' (Random Forest / XGBoost)\n"
         "Option B : SMOTE (Synthetic Minority Oversampling Technique)"),
        ("3.", "Modèles entraînés",
         "Régression Logistique (baseline)\nRandom Forest (interprétabilité)\nXGBoost (performance)"),
        ("4.", "Métriques d'évaluation",
         "F1-score (classe 1), AUC-ROC, matrice de confusion, précision/rappel"),
        ("5.", "Interprétabilité",
         "Feature importance (Random Forest / XGBoost), SHAP values"),
    ]
    for num, title, detail in phase2:
        y0 = pdf.get_y()
        pdf.set_fill_color(*LIGHT_B)
        pdf.set_draw_color(*GRAY_LN)
        pdf.rect(20, y0, 170, 6, "FD")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.set_xy(23, y0 + 1)
        pdf.cell(10, 4, num)
        pdf.cell(158, 4, title)
        pdf.set_y(y0 + 7)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*BLACK)
        pdf.set_x(30)
        pdf.multi_cell(157, 5, detail)
        pdf.ln(1)

    # Calendrier
    pdf.ln(4)
    pdf.sub_title("12.4 - Calendrier prévisionnel")
    pdf.h_table(
        headers=["Phase", "Période", "Livrable"],
        rows=[
            ["Phase 1 - Data Engineering", "10-18 Avril 2026", "dataset_ml_final.parquet (terminé)"],
            ["Phase 2 - Modélisation", "18 Avril - 1er Mai 2026", "notebooks/02_modelisation.ipynb"],
            ["Phase 3 - Dashboard", "1-15 Mai 2026", "Application Streamlit"],
            ["Phase 4 - Rédaction mémoire", "1-28 Mai 2026", "Mémoire complet (40-50 pages)"],
            ["Dépôt final", "28 Mai 2026", "Mémoire + Code + Rapport"],
        ],
        col_widths=[62, 48, 60],
    )

    # Page finale
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 100, 210, 90, "F")
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(20, 118)
    pdf.cell(170, 12, "Phase 1 - Data Engineering", align="C")
    pdf.set_font("Helvetica", "", 13)
    pdf.set_xy(20, 134)
    pdf.cell(170, 8, "Terminée avec succès", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, 150)
    pdf.cell(170, 7, "349 390 lignes x 24 colonnes  |  Taux de retard : 19,2 %", align="C")
    pdf.set_xy(20, 160)
    pdf.cell(170, 7, "Fichier : data/processed/dataset_ml_final.parquet", align="C")
    pdf.set_text_color(*BLACK)

    # -----------------------------------------------------------------------
    pdf.output(OUT_PATH)
    print(f"Rapport PDF généré : {OUT_PATH}")
    size_mb = os.path.getsize(OUT_PATH) / (1024 * 1024)
    print(f"Taille : {size_mb:.2f} MB")


if __name__ == "__main__":
    build_report()
