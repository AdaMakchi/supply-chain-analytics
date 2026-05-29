# -*- coding: utf-8 -*-
"""
Genere le PDF du mémoire GE : "Système de Prévision et d'Optimisation des Stocks"
Sortie : reports/memoire_GE_complet.pdf
"""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, KeepTogether
)

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
SCREENS = ROOT / "screens"
OUT = REPORTS / "memoire_GE_complet_v3.pdf"

# ----------------------------------------------------------------------------
# Polices : on tente Times New Roman (Windows), fallback Times (PS)
# ----------------------------------------------------------------------------
FONT_REG, FONT_BOLD, FONT_ITAL, FONT_BI = "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"
try:
    win_fonts = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("TNR", str(win_fonts / "times.ttf")))
    pdfmetrics.registerFont(TTFont("TNR-B", str(win_fonts / "timesbd.ttf")))
    pdfmetrics.registerFont(TTFont("TNR-I", str(win_fonts / "timesi.ttf")))
    pdfmetrics.registerFont(TTFont("TNR-BI", str(win_fonts / "timesbi.ttf")))
    FONT_REG, FONT_BOLD, FONT_ITAL, FONT_BI = "TNR", "TNR-B", "TNR-I", "TNR-BI"
except Exception as e:
    print(f"[warn] Times New Roman indisponible ({e}) - fallback Times PS")

# ----------------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------------
MARGIN = 2.5 * cm
LEADING = 18  # interligne 1.5 pour 12pt

styles = getSampleStyleSheet()
S_TITLE = ParagraphStyle("title", fontName=FONT_BOLD, fontSize=24, leading=30,
                          alignment=TA_CENTER, spaceAfter=12, textColor=colors.HexColor("#1a3a5c"))
S_SUB = ParagraphStyle("sub", fontName=FONT_ITAL, fontSize=14, leading=20,
                        alignment=TA_CENTER, spaceAfter=8, textColor=colors.HexColor("#555555"))
S_H1 = ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=18, leading=24,
                       spaceBefore=18, spaceAfter=10, textColor=colors.HexColor("#1a3a5c"),
                       keepWithNext=True)
S_H2 = ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=14, leading=20,
                       spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#1a3a5c"),
                       keepWithNext=True)
S_H3 = ParagraphStyle("h3", fontName=FONT_BOLD, fontSize=12, leading=18,
                       spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#333333"),
                       keepWithNext=True)
S_P = ParagraphStyle("p", fontName=FONT_REG, fontSize=12, leading=LEADING,
                      alignment=TA_JUSTIFY, spaceAfter=8, firstLineIndent=0.6 * cm)
S_PN = ParagraphStyle("pn", parent=S_P, firstLineIndent=0)  # pas d'indentation
S_QUOTE = ParagraphStyle("quote", parent=S_P, fontName=FONT_ITAL,
                          leftIndent=1 * cm, rightIndent=1 * cm,
                          textColor=colors.HexColor("#444444"))
S_CAPTION = ParagraphStyle("caption", parent=S_P, fontName=FONT_ITAL, fontSize=10,
                            leading=14, alignment=TA_CENTER, spaceBefore=4, spaceAfter=14,
                            firstLineIndent=0, textColor=colors.HexColor("#444444"))
S_BULLET = ParagraphStyle("bullet", parent=S_P, leftIndent=0.6 * cm,
                           firstLineIndent=0, bulletIndent=0.2 * cm, spaceAfter=4)
S_PLACEHOLDER = ParagraphStyle("ph", parent=S_P, alignment=TA_CENTER,
                                backColor=colors.HexColor("#fff3cd"),
                                borderColor=colors.HexColor("#856404"),
                                borderWidth=1, borderPadding=10, borderRadius=4,
                                firstLineIndent=0, fontName=FONT_ITAL,
                                textColor=colors.HexColor("#856404"))
S_TODO = ParagraphStyle("todo", parent=S_P, fontName=FONT_ITAL, fontSize=10,
                         textColor=colors.HexColor("#c0392b"), firstLineIndent=0)

# ----------------------------------------------------------------------------
# Page template : en-tête + numéro de page
# ----------------------------------------------------------------------------
HEADER_TEXT = "Système de Prévision et d'Optimisation des Stocks - Mémoire GE"


def header_footer(canvas, doc):
    canvas.saveState()
    # En-tête
    canvas.setFont(FONT_ITAL, 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(MARGIN, A4[1] - 1.3 * cm, HEADER_TEXT)
    canvas.setStrokeColor(colors.HexColor("#bbbbbb"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, A4[1] - 1.5 * cm, A4[0] - MARGIN, A4[1] - 1.5 * cm)
    # Pied : numéro de page
    canvas.setFont(FONT_REG, 10)
    canvas.setFillColor(colors.HexColor("#444444"))
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"- {doc.page} -")
    canvas.restoreState()


def cover_page(canvas, doc):
    """Page de garde sans en-tête ni numéro."""
    canvas.saveState()
    canvas.restoreState()


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def P(text, style=S_P):
    return Paragraph(text, style)


def H1(text):
    return P(text, S_H1)


def H2(text):
    return P(text, S_H2)


def H3(text):
    return P(text, S_H3)


def bullets(items):
    return [Paragraph(f"&#8226; {it}", S_BULLET) for it in items]


def fig(path, caption, width_cm=14):
    p = REPORTS / path
    if not p.exists():
        return placeholder(f"FIGURE MANQUANTE : {path}", caption)
    img = Image(str(p), width=width_cm * cm, height=width_cm * cm * 0.65)
    img.hAlign = "CENTER"
    return KeepTogether([img, Paragraph(caption, S_CAPTION)])


def screen(filename, caption, width_cm=15):
    """Inclut une capture du dashboard depuis le dossier `screens/`."""
    p = SCREENS / filename
    if not p.exists():
        return placeholder(f"SCREEN MANQUANT : {filename}", caption)
    img = Image(str(p), width=width_cm * cm, height=width_cm * cm * 0.55,
                kind="proportional")
    img.hAlign = "CENTER"
    return KeepTogether([img, Paragraph(caption, S_CAPTION)])


def placeholder(label, caption):
    box = Paragraph(f"<b>[ {label} ]</b><br/><br/>"
                    "Insertion manuelle requise après génération.", S_PLACEHOLDER)
    return KeepTogether([box, Paragraph(caption, S_CAPTION)])


_S_CELL = ParagraphStyle("cell", fontName=FONT_REG, fontSize=10, leading=12,
                          alignment=TA_CENTER)
_S_CELL_LEFT = ParagraphStyle("cell_l", parent=_S_CELL, alignment=TA_LEFT)


def _wrap_cell(cell, is_first_col=False):
    """Wrap string cells with Paragraph so inline HTML (<b>, <i>) is rendered."""
    if isinstance(cell, str) and ("<b>" in cell or "<i>" in cell):
        return Paragraph(cell, _S_CELL_LEFT if is_first_col else _S_CELL)
    return cell


def table(data, col_widths=None, header_color="#1a3a5c"):
    processed = [
        [_wrap_cell(c, is_first_col=(j == 0)) for j, c in enumerate(row)]
        for row in data
    ]
    t = Table(processed, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT_REG),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888888")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    t.setStyle(style)
    return KeepTogether([t, Spacer(1, 0.4 * cm)])


# ============================================================================
# CONTENU DU MEMOIRE
# ============================================================================
story = []

# ---------- PAGE DE GARDE ----------
_logo_path = SCREENS / "logo.jfif"
_cover_logo = Image(str(_logo_path), width=3.8 * cm, height=3.8 * cm, kind="proportional")
_cover_logo.hAlign = "CENTER"

story += [
    Spacer(1, 0.5 * cm),
    _cover_logo,
    Spacer(1, 0.4 * cm),
    P("MEMOIRE DE FIN D'ETUDES", ParagraphStyle("g0", parent=S_SUB, fontSize=12)),
    Spacer(1, 0.2 * cm),
    P("École 89 - Deep Tech",
      ParagraphStyle("g_school", parent=S_SUB, fontSize=13,
                     fontName=FONT_BOLD, textColor=colors.HexColor("#1a3a5c"))),
    Spacer(1, 0.1 * cm),
    P("M1 Expert IT - IA et Big Data", S_SUB),
    Spacer(1, 0.9 * cm),
    P("Système de Prévision et d'Optimisation des Stocks", S_TITLE),
    Spacer(1, 0.2 * cm),
    P("Une approche Demand-Driven appuyee sur l'Intelligence Artificielle "
      "pour la prédiction de la demande client chez GE",
      ParagraphStyle("g1", parent=S_SUB, fontSize=13, fontName=FONT_ITAL)),
    Spacer(1, 1.2 * cm),
    P("Realise par",
      ParagraphStyle("g_auth_lbl", parent=S_SUB, fontSize=11)),
    P("<b>Adham Marrakchi</b>",
      ParagraphStyle("g_auth", parent=S_SUB, fontSize=15,
                     fontName=FONT_BOLD, textColor=colors.HexColor("#1a3a5c"))),
    Spacer(1, 0.5 * cm),
    P("Sous la direction de",
      ParagraphStyle("g_tut_lbl", parent=S_SUB, fontSize=11)),
    P("<b>Najib AL AWAR</b>",
      ParagraphStyle("g_tut", parent=S_SUB, fontSize=13,
                     fontName=FONT_BOLD, textColor=colors.HexColor("#1a3a5c"))),
    Spacer(1, 0.6 * cm),
    P("Année universitaire 2025 - 2026",
      ParagraphStyle("g2", parent=S_SUB, fontSize=12)),
    PageBreak(),
]

# ---------- RESUME ----------
story += [
    H1("Résumé"),
    P("Ce mémoire presente la conception, l'implémentation et la critique d'un système de "
      "prévision de la demande client base sur l'intelligence artificielle, applique aux données "
      "opérationnelles de GE pour la période 2021-2025. "
      "Le projet répond à une problématique industrielle concrète : dépasser le pilotage "
      "traditionnel par objectifs de chiffre d'affaires, source récurrente de ruptures de stock "
      "et de surstocks, en adoptant une approche <i>Demand-Driven</i> structurée autour d'une "
      "double prédiction (quantité et date de prochaine commande).", S_PN),
    P("La méthodologie articule un pipeline complet couvrant la consolidation des données, "
      "l'analyse statistique, la modélisation et la mise en service opérationnelle. La "
      "consolidation a produit un jeu de données de 349 390 lignes nettoyées et enrichies de "
      "35 colonnes incluant des sources exogènes (indice de production industrielle INSEE, "
      "données meteo, jours fériés, calendrier scolaire), portées à 47 features modèle après "
      "ingénierie autorégressive. Les études statistiques ont confirme "
      "la présence de cycles budgetaires et météorologiques et identifie sept variables "
      "exogènes Granger-causales sur la demande. Quatre familles de modèles ont été confrontées "
      "(XGBoost, LightGBM, CatBoost, LSTM) avec optimisation Optuna et stacking Ridge. "
      "Le modèle XGBoost v2 (47 features, 300 essais Optuna) atteint une MAE de 8.42 unités "
      "sur le test 2025 (1 - WAPE = 61.7 pourcents), dépassant la cible <i>North Star</i> de "
      "60 pourcents. L'architecture <i>Stacking Ridge</i> (XGBoost + LightGBM Quantile + "
      "CatBoost) améliore le RMSE et le R^2 (97.55 et 0.694), tandis qu'une baseline DDMRP "
      "académique sert de point de comparaison métier. Un dashboard Streamlit multipage a été "
      "livre, intégrant score de confiance composite, simulation what-if, backtest semaine "
      "par semaine et détection de dérive (Population Stability Index).", S_PN),
    P("L'analyse critique discute honnêtement les limites observées (précision à sept jours "
      "limitée à 25.5 pourcents pour la prédiction de date, sous-performance sur la longue "
      "traîne), documente la conformité RGPD du traitement et formalise une matrice de "
      "gouvernance humain-dans-la-boucle (HITL). Le mémoire conclut sur une feuille de route "
      "de mise en production (FastAPI, PostgreSQL, MLflow, Evidently) et sur la valeur "
      "reproductible d'une approche académique honnête confrontée à un terrain industriel "
      "réel.", S_PN),
    Spacer(1, 0.3 * cm),
    P("<b>Mots-clés :</b> prévision de la demande, supply chain, XGBoost, LightGBM, CatBoost, "
      "stacking, régression quantile, LSTM, DDMRP, drift PSI, human-in-the-loop, RGPD, "
      "Streamlit.", S_PN),
    PageBreak(),
]

# ---------- ABSTRACT EN ----------
story += [
    H1("Abstract"),
    P("This master's thesis presents the design, implémentation and critical évaluation of an "
      "AI-driven demand forecasting system applied to five years (2021-2025) of operational data "
      "from GE. The project addresses a concrète industrial "
      "problem: moving beyond traditional revenue-target driven planning, which is a recurring "
      "source of stockouts and overstocks, by adopting a Demand-Driven approach structured "
      "around two complementary prédictions (quantity and date of next order).", S_PN),
    P("The methodology articulates an end-to-end pipeline spanning data consolidation, "
      "statistical analysis, modeling and operational deployment. The consolidation produced "
      "a 349,390-row cleaned dataset enriched with 35 columns including exogenous sources "
      "(industrial production index, weather data, public holidays, school calendar), "
      "expanded to 47 model features after autorégressive feature engineering. "
      "Statistical studies confirmed budgetary and weather cycles and identified seven "
      "Granger-causal exogenous drivers of demand. Four model families (XGBoost, LightGBM, "
      "CatBoost, LSTM) were compared with Optuna tuning and Ridge stacking. The XGBoost v2 "
      "model (47 features, 300 Optuna trials) reaches a test MAE of 8.42 units on 2025 "
      "(1 - WAPE = 61.7 percent), exceeding the 60 percent <i>North Star</i> target. "
      "A Stacking Ridge architecture (XGBoost + LightGBM Quantile + CatBoost) improves RMSE "
      "and R-squared (97.55 and 0.694), while a DDMRP academic baseline serves as a domain "
      "référence. An interactive Streamlit multipage dashboard was delivered with composite "
      "confidence scoring, what-if simulation, weekly backtest and Population Stability Index "
      "drift détection.", S_PN),
    P("The critical analysis honestly discusses observed limitations (date prédiction accuracy "
      "of only 25.5 percent within +/-7 days, underperformance on the long tail), documents "
      "GDPR compliance and formalizes a human-in-the-loop governance matrix. The thesis "
      "concludes with a productionization roadmap (FastAPI, PostgreSQL, MLflow, Evidently) "
      "and reflects on the reproducible value of an academically honest approach confronted "
      "with a real industrial setting.", S_PN),
    Spacer(1, 0.3 * cm),
    P("<b>Keywords:</b> demand forecasting, supply chain, XGBoost, LightGBM, CatBoost, "
      "stacking, quantile régression, LSTM, DDMRP, PSI drift, human-in-the-loop, GDPR, "
      "Streamlit.", S_PN),
    PageBreak(),
]

# ---------- SOMMAIRE ----------
from reportlab.pdfbase.pdfmetrics import stringWidth as _string_width
import re as _re

_TOC_LINE_WIDTH_PT = 16 * cm  # largeur totale ligne sommaire (A4 - marges)
_TOC_FONT_SIZE = 12


def _toc(label, page, bold=False):
    """Ligne de sommaire : titre + points de conduite + page (numéro collee a droite)."""
    visible = _re.sub(r'<[^>]+>', '', label)
    font_label = FONT_BOLD if bold else FONT_REG
    page_str = str(page)
    label_w = _string_width(visible + " ", font_label, _TOC_FONT_SIZE)
    page_w = _string_width(" " + page_str, FONT_REG, _TOC_FONT_SIZE)
    dot_w = _string_width(".", FONT_REG, _TOC_FONT_SIZE)
    remaining = _TOC_LINE_WIDTH_PT - label_w - page_w
    n_dots = max(3, int(remaining / dot_w) - 1)
    open_tag = "<b>" if bold else ""
    close_tag = "</b>" if bold else ""
    return P(f"{open_tag}{visible}{close_tag} {'.' * n_dots} {page_str}", S_PN)


story += [
    H1("Sommaire"),
    _toc("Introduction générale", 7),
    Spacer(1, 0.2 * cm),
    _toc("Partie 1 - Contexte et Problématique", 9, bold=True),
    _toc("1.1 Présentation de GE et perimetre du mémoire", 9),
    _toc("1.2 Limites de la gestion par objectifs de chiffre d'affaires", 11),
    _toc("1.3 Problématique et question de recherche", 13),
    _toc("1.4 Revue de litterature", 15),
    Spacer(1, 0.2 * cm),
    _toc("Partie 2 - Solution Technique", 18, bold=True),
    _toc("2.1 Méthodologie Data Engineering", 18),
    _toc("2.2 Résultats des études statistiques", 21),
    _toc("2.3 Architecture et performances des modèles IA", 28),
    _toc("2.4 Présentation du dashboard Human-in-the-loop", 35),
    Spacer(1, 0.2 * cm),
    _toc("Partie 3 - Analyse Critique", 43, bold=True),
    _toc("3.1 Comparaison IA versus intuition commerciale", 43),
    _toc("3.2 Limites du modèle", 44),
    _toc("3.3 Conformité RGPD et ethique du traitement", 46),
    _toc("3.4 Importance de la validation humaine (Human-in-the-loop)", 49),
    _toc("3.5 Perspectives d'amélioration et de mise en production", 50),
    _toc("3.6 Conclusion générale", 52),
    Spacer(1, 0.2 * cm),
    _toc("Bibliographie", 54),
    _toc("Annexes", 56),
    PageBreak(),
]

# ---------- LISTES FIGURES / TABLEAUX ----------
story += [
    H2("Liste des figures"),
    P("Figure 1 - Décomposition STL globale de la demande 2021-2025", S_PN),
    P("Figure 2 - Décomposition STL par famille d'article", S_PN),
    P("Figure 3 - Cycles budgetaires clients (pics de fin de trimestre)", S_PN),
    P("Figure 4 - Cycles météorologiques et impact sur la demande", S_PN),
    P("Figure 5 - Matrice de correlation de Pearson", S_PN),
    P("Figure 6 - P-values du test de causalité de Granger", S_PN),
    P("Figure 7 - Distribution de la cible (qte_demandee) avant et après log1p", S_PN),
    P("Figure 8 - Auto-correlation (ACF) et partial ACF (PACF)", S_PN),
    P("Figure 9 - Split temporel train / val / test", S_PN),
    P("Figure 10 - Feature importance du modèle XGBoost v2", S_PN),
    P("Figure 11 - Capture dashboard : page Gestion des Données", S_PN),
    P("Figure 12 - Capture dashboard : page Intelligence Artificielle", S_PN),
    P("Figure 13 - Capture dashboard : page Prévisions de Ventes (tableau et badges)", S_PN),
    P("Figure 14 - Capture dashboard : page Prévisions (graphique pred vs réel)", S_PN),
    P("Figure 15 - Capture dashboard : page Prévisions (simulation what-if)", S_PN),
    P("Figure 16 - Capture dashboard : page Analyse", S_PN),
    P("Figure 17 - Capture dashboard : page Drift Détection", S_PN),
    P("Figure 18 - Capture dashboard : page Backtest interactif", S_PN),
    P("Figure 19 - Capture dashboard : page d'accueil", S_PN),
    Spacer(1, 0.6 * cm),
    H2("Liste des tableaux"),
    P("Tableau 1 - Synthèse de la qualité des données après nettoyage", S_PN),
    P("Tableau 2 - Variables exogènes Granger-causales", S_PN),
    P("Tableau 3 - Comparaison des modèles de première génération (test 2025)", S_PN),
    P("Tableau 4 - Performance LSTM time-to-event", S_PN),
    P("Tableau 5 - Benchmark complet des architectures (XGBoost v2, LightGBM Quantile, "
      "CatBoost, Stacking Ridge, DDMRP)", S_PN),
    P("Tableau 6 - Comparaison IA vs DDMRP sur articles stratégiques", S_PN),
    P("Tableau 7 - PSI des features critiques sur le test 2025", S_PN),
    P("Tableau 8 - Matrice de gouvernance Human-in-the-loop", S_PN),
    P("Tableau 9 - Registre simplifie des traitements (RGPD)", S_PN),
    PageBreak(),
]

# ============================================================================
# INTRODUCTION GENERALE
# ============================================================================
story += [
    H1("Introduction générale"),
    P("Les chaînes d'approvisionnement industrielles ont été soumises, depuis la crise sanitaire "
      "de 2020 et les tensions géopolitiques qui ont suivi, à une pression sans precedent sur "
      "leur capacite a anticiper la demande client. Dans ce contexte, les approches traditionnelles "
      "de planification basees sur l'extrapolation linéaire d'objectifs commerciaux montrent "
      "leurs limites : ruptures de stock qui erodent la satisfaction client, surstocks qui "
      "immobilisent un capital significatif, décisions de réapprovisionnement reactives plutot "
      "qu'anticipatives.", S_PN),
    P("Le present mémoire s'inscrit dans cette problématique à partir d'un terrain industriel "
      "concret : la chaîne d'approvisionnement de l'entreprise GE, commanditaire de la "
      "mission. Le matériau principal est constitue d'un historique de cinq années (2021-2025) "
      "de commandes et de livraisons clients, soit pres de 350 000 lignes de transactions, "
      "complete par des sources exogènes publiques (indice de production industrielle de "
      "l'INSEE, données météorologiques via Open-Meteo, calendrier des jours fériés).", S_PN),
    P("L'objectif central est de démontrer qu'une approche <i>Demand-Driven</i> appuyee sur "
      "l'intelligence artificielle peut produire une prédiction opérationnelle exploitable de "
      "la demande client - en quantité ET en date - et offrir ainsi un appui scientifique au "
      "planificateur sans le remplacer. La cible declaree au lancement du projet, une précision "
      "moyenne supérieure à 60 pourcents (mesurée par 1 - WAPE), sert de fil conducteur. "
      "Comme nous le verrons, cet objectif est atteint sur la quantité demandee "
      "(61.7 pourcents constates sur le jeu de test 2025 avec le modèle XGBoost v2), tandis "
      "que la prédiction de date par LSTM reste insuffisante (25.5 pourcents +/-7 jours). "
      "Cette dualité des résultats - réussite sur la quantité, échec relatif sur la date - "
      "constitue un matériau méthodologique riche : elle obligera a documenter les limites du "
      "modèle de date, a expliciter les biais structurels du jeu de données, et a formaliser "
      "une gouvernance hybride associant systematiquement l'expertise humaine.", S_PN),
    P("Le mémoire est organise en trois parties. La première partie pose le contexte industriel "
      "de GE, decrit les limites de la gestion par objectifs commerciaux, formule la "
      "problématique et restitué l'état de l'art sur la prévision de la demande (DDMRP, gradient "
      "boosting, deep learning temporel, régression quantile, Human-in-the-Loop). La deuxième "
      "partie deploie la solution technique : pipeline de données, études statistiques, "
      "comparaison de quatre familles de modèles avec optimisation et stacking, et description "
      "du dashboard interactif livre. La troisième partie ouvre l'analyse critique - "
      "comparaison de l'IA aux pratiques actuelles, discussion des limites, conformité RGPD, "
      "matrice de gouvernance humain-dans-la-boucle, perspectives de mise en production - et "
      "conclut sur l'apport de cette démarche académique au terrain industriel.", S_PN),
    PageBreak(),
]

# ============================================================================
# PARTIE 1
# ============================================================================
story += [
    Spacer(1, 6 * cm),
    P("PARTIE 1", ParagraphStyle("part", parent=S_TITLE, fontSize=20)),
    Spacer(1, 0.4 * cm),
    P("Contexte et Problématique", S_TITLE),
    PageBreak(),
]

# ---------- 1.1 GE ----------
story += [
    H1("1.1 Présentation de GE et perimetre du mémoire"),
    H2("1.1.1 L'entreprise GE et la mission confiee"),
    P("L'entreprise GE est le commanditaire de la mission ayant donne lieu au present mémoire. "
      "Conformément aux termes de la mission, le perimetre etudie est circonscrit à la chaîne "
      "d'approvisionnement de l'entreprise et aux données opérationnelles de commande et de "
      "livraison clients sur la période 2021-2025. Le presente document ne formule aucune "
      "affirmation supplementaire sur l'activite, le secteur, l'organisation ou la stratégie de "
      "GE au-delà de ce qui se deduit directement des données étudiées ou du cahier des charges "
      "transmis à l'étudiant.", S_PN),
    P("Le constat de depart documente dans le brief de mission est clair : la gestion actuelle "
      "des stocks s'appuie sur des objectifs de chiffre d'affaires négociés, et ce mode de "
      "pilotage genere des ruptures et des surstocks récurrents. La section 1.2 du present "
      "mémoire detaillera les limites structurelles de cette approche ; la presente section se "
      "borne a decrire le matériau exploite.", S_PN),

    H2("1.1.2 Matériau exploite : structure du dataset"),
    P("Le matériau analytique mis a disposition par GE est un export consolide des commandes "
      "et livraisons clients couvrant la période 2021 à 2025. Après consolidation et nettoyage "
      "(détail en section 2.1), le jeu final comprend 349 390 lignes de transactions. Chaque "
      "ligne represente une commande individuelle d'un client sur un article à une date "
      "donnée. Les variables exploitees, telles qu'identifiées dans le brief de mission et "
      "vérifiées dans les fichiers sources, sont les suivantes :", S_PN),
    *bullets([
        "<b>Identifiants</b> : <i>code_article</i>, <i>code_client</i>, "
        "<i>num_commande</i>.",
        "<b>Cibles a predire</b> : <i>qte_demandee</i> (quantité commandee), "
        "<i>date_livraison_demandee</i> (date a laquelle le client souhaite être livre).",
        "<b>Variables descriptives client</b> : <i>famille_activite_client</i>, "
        "<i>pays</i>, <i>devise</i>, <i>type_activite</i>.",
        "<b>Variables descriptives article</b> : <i>famille_activite_article</i>, "
        "<i>segment</i>, <i>prix</i>.",
        "<b>Variables de contexte</b> : <i>qte_livree</i> (utilisee pour évaluer l'écart "
        "entre demande exprimee et demande effectivement servie), <i>statut</i> de la "
        "commande, dates d'enregistrement et de livraison effective.",
    ]),
    P("Le contenu métier spécifique des modalités (par exemple le sens precis des libelles de "
      "<i>famille_activite_article</i> ou des <i>segment</i> du catalogue) n'est pas decrit "
      "dans ce mémoire : ces informations relevent du détail opérationnel interne de GE et ne "
      "sont pas necessaires à la conduite des analyses statistiques présentées, qui reposent "
      "sur la structure du jeu de données et non sur l'interprétation semantique des "
      "modalités.", S_PN),

    H2("1.1.3 Perimetre et exclusions explicites"),
    P("Le perimetre temporel couvre exclusivement les commandes et livraisons de 2021 à 2025 "
      "inclus. Sont en revanche en dehors du perimetre, par indisponibilité ou par choix "
      "méthodologique : les opérations promotionnelles, les retours clients, les transferts "
      "internes inter-sites, et toute affirmation qualitative sur les pratiques commerciales "
      "de GE qui ne se deduirait pas directement du jeu de données fourni. L'utilisateur cible "
      "du système propose est le planificateur supply chain de GE, conformément au scenario "
      "Human-in-the-loop defini dans le brief de mission (section 5 du cahier des charges).", S_PN),
    PageBreak(),
]

# ---------- 1.2 Limites CA ----------
story += [
    H1("1.2 Limites de la gestion par objectifs de chiffre d'affaires"),
    H2("1.2.1 Le pilotage par objectifs commerciaux"),
    P("Le brief de mission communiqué par GE indique explicitement que la gestion des stocks "
      "s'appuie sur des objectifs de chiffre d'affaires, et que ce mode de pilotage genere "
      "des ruptures et des surstocks récurrents. Sans documenter ici le détail des processus "
      "internes de planification de GE, on peut identifier trois limites structurelles "
      "génériques d'une planification orientee CA, documentées dans la litterature supply "
      "chain (Hyndman et Athanasopoulos, 2018) et cohérentes avec le constat opere par "
      "l'entreprise.", S_PN),
    P("Premièrement, ce type de pilotage confond l'objectif (volume cible) et la prévision "
      "(volume probable), ce qui introduit un biais d'optimisme systematique. Deuxièmement, "
      "il est par construction insensible aux dynamiques infra-mensuelles : un objectif "
      "mensuel ne dit rien des pics de fin de semaine ou des creux post-vacances mis en "
      "évidence dans l'analyse exploratoire (sections 2.2.3 et 2.2.4). Troisièmement, il "
      "ne capte pas les facteurs exogènes (cycles macro-économiques, conditions "
      "météorologiques, calendrier des jours fériés) qui modulent la demande réelle "
      "independamment des intentions commerciales, comme le confirmera le test de causalité "
      "de Granger conduit en section 2.2.6.", S_PN),

    H2("1.2.2 Phenomenes de rupture et de surstock observables dans les données"),
    P("Le brief identifie deux phenomenes récurrents que le pilotage par objectifs CA ne "
      "previent pas : les ruptures et les surstocks. Le jeu de données fourni permet d'en "
      "objectiver le premier par comparaison directe entre la <i>quantité demandee</i> et "
      "la <i>quantité livree</i> : lorsque le ratio livraison / demande descend sous "
      "100 pourcents, on est en présence d'une rupture, totale ou partielle. Le surstock "
      "n'est pas directement observable dans le seul historique de commandes (il faudrait "
      "un releve de stock que ce dataset ne contient pas), mais sa manifestation indirecte - "
      "écart entre demande anticipee et demande effective - est neanmoins mesurable à travers "
      "les biais de prédiction etudies en section 3.1.", S_PN),
    P("Au-delà de la mesure brute, ces deux phenomenes ont un coût économique reconnu dans "
      "la litterature supply chain : pour la rupture, perte de marge sur la vente non "
      "réalisée et erosion de la confiance commerciale ; pour le surstock, immobilisation "
      "de tresorerie, coûts de stockage et risque d'obsolescence. Une approche prédictive "
      "qui réduit l'amplitude moyenne de ces écarts apporte donc une valeur économique "
      "directe, dont la quantification precise relevera de la direction supply chain de GE.", S_PN),

    H2("1.2.3 Asymétrie des coûts et métrique business"),
    P("La litterature opérationnelle souligne que le coût d'une unité manquante au moment "
      "ou le client en a besoin est généralement supérieur au coût d'une unité excedentaire "
      "stockee. Cette asymétrie à une consequence méthodologique directe : la qualité d'une "
      "prévision doit pouvoir être evaluee avec une fonction de coût asymetrique, et non "
      "avec la seule erreur absolue moyenne (MAE) classique. Le mémoire integre donc, dans "
      "le dashboard <i>Backtest 2025</i> (section 2.4.7), une <i>fonction de coût business</i> "
      "configurable définie par <i>cost = alpha * max(0, y - y_pred) + beta * "
      "max(0, y_pred - y)</i>, ou alpha et beta sont parametrables par l'utilisateur ; les "
      "valeurs effectives a retenir en production relevent d'un arbitrage de GE et ne sont "
      "pas fixees dans le present document.", S_PN),
    PageBreak(),
]

# ---------- 1.3 Problème ----------
story += [
    H1("1.3 Problématique et question de recherche"),
    H2("1.3.1 Énoncé de la problématique"),
    P("La problématique centrale du mémoire est formulee de la manière suivante :", S_PN),
    P("<i>Comment une approche Demand-Driven s'appuyant sur l'intelligence artificielle peut-elle "
      "predire la demande client réelle - en quantité et en date - pour optimiser la chaîne "
      "d'approvisionnement d'un distributeur d'équipements électriques industriels, tout en "
      "preservant le role décisionnel de l'expertise humaine ?</i>", S_QUOTE),
    P("Cette formulation contient trois engagements méthodologiques explicites. Le premier est "
      "le passage d'un pilotage par objectifs à un pilotage par demande effective predite. Le "
      "deuxième est la double prédiction quantité + date, qui releve de deux familles de "
      "problèmes statistiques distincts (régression numérique pour la quantité, analyse de "
      "survie ou prévision de serie pour la date). Le troisième est l'intégration explicite "
      "d'une boucle humain-dans-la-boucle : le système n'a pas vocation a automatiser "
      "intégralement la décision, mais a fournir au planificateur une recommandation "
      "transparente et interprétable.", S_PN),

    H2("1.3.2 Sous-questions opérationnelles et hypothèses"),
    P("De cette problématique découlent quatre sous-questions opérationnelles :", S_PN),
    *bullets([
        "Q1 : Quelles variables internes et exogènes contribuent significativement à la "
        "prédiction de la demande sur le perimetre etudie ?",
        "Q2 : Quel modèle prédictif maximise la précision sur la quantité demandee tout en "
        "restant interprétable pour un planificateur métier ?",
        "Q3 : Le problème de prédiction de la date prochaine commande est-il aborde plus "
        "efficacement par un réseau récurrent (LSTM) ou par une formulation alternative "
        "(analyse de survie, Prophet par couple) ?",
        "Q4 : Comment articuler le modèle prédictif et l'expertise du planificateur dans une "
        "matrice de gouvernance opérationnelle ?",
    ]),
    P("Les hypothèses testees sont cohérentes avec la litterature récente. H1 : l'ajout de "
      "variables exogènes (indice de production industrielle, meteo) améliore significativement "
      "la prédiction par rapport aux variables internes seules. H2 : les modèles d'ensemble "
      "de type gradient boosting (XGBoost, LightGBM, CatBoost) surpassent les modèles linéaires "
      "et un réseau neuronal générique sur ce type de données tabulaires bruitees. H3 : la "
      "transformation log1p de la cible réduit suffisamment l'asymétrie de la distribution "
      "pour stabiliser l'apprentissage. H4 : un dashboard interactif assorti d'un score de "
      "confiance améliore l'adoption opérationnelle par rapport à une simple sortie numérique.", S_PN),

    H2("1.3.3 Perimetre, exclusions et North Star"),
    P("Le perimetre temporel couvre les commandes et livraisons des années 2021 à 2025 inclus, "
      "découpées en train (2021-2023), validation (2024) et test (2025) selon un split "
      "strictement temporel pour éviter toute fuite d'information future. Sont explicitement "
      "exclus du perimetre : les opérations promotionnelles ponctuelles (données non "
      "disponibles), les retours clients, les transferts inter-sites internes, et les commandes "
      "exceptionnelles liees a des projets de plus de cinq millions d'euros. La cible <i>North "
      "Star</i> declaree en debut de projet, une précision moyenne supérieure à 60 pourcents, "
      "a constitue le repere d'amélioration tout au long du développement.", S_PN),
    PageBreak(),
]

# ---------- 1.4 Litterature ----------
story += [
    H1("1.4 Revue de litterature"),
    H2("1.4.1 De la prévision statistique classique au gradient boosting"),
    P("La litterature sur la prévision de la demande s'est structurée en trois grandes vagues. "
      "La première, anteriorement aux années 2010, repose sur les méthodes statistiques "
      "classiques : moyennes mobiles, lissages exponentiels de la famille Holt-Winters, "
      "modèles ARIMA et SARIMA. Ces méthodes restent une référence forte sur les series "
      "stables et lisses, et constituent la baseline traditionnelle dans la communauté supply "
      "chain (Hyndman et Athanasopoulos, 2018). Pour les demandes intermittentes - très "
      "frequentes dans la longue traîne d'un catalogue industriel - les méthodes spécialisées "
      "comme Croston (1972) et leurs raffinements (TSB, ADIDA) demeurent l'état de l'art.", S_PN),
    P("La seconde vague, deployee massivement à partir de la décennie 2010, introduit les "
      "modèles d'ensemble par gradient boosting. XGBoost (Chen et Guestrin, 2016) a domine les "
      "competitions Kaggle sur données tabulaires pendant pres d'une décennie, suivi par "
      "LightGBM (Ke et al., 2017) plus efficient sur les volumetries élevées et CatBoost "
      "(Prokhorenkova et al., 2018) qui gere nativement les variables catégorielles. Le rapport "
      "M5 Forecasting Competition (Makridakis et al., 2022) a confirme experimentalement la "
      "supériorité empirique de cette famille de modèles sur les problèmes de prévision retail "
      "et supply chain, devant les approches deep learning classiques sur la majorite des "
      "configurations testees.", S_PN),

    H2("1.4.2 Deep learning temporel et formulations alternatives"),
    P("La troisième vague repose sur les architectures de deep learning spécifiques aux series "
      "temporelles. Les réseaux récurrents de type LSTM (Hochreiter et Schmidhuber, 1997) ont "
      "longtemps constitue le standard pour la modélisation sequentielle, avant d'être "
      "concurrences par les architectures convolutives causales (Bai et al., 2018), les "
      "Transformers temporels comme Informer (Zhou et al., 2021) et le <i>Temporal Fusion "
      "Transformer</i> (Lim et al., 2021), qui combinent attention multi-tête et "
      "interprétabilité. Pour les problèmes de prédiction de date - reformulables en "
      "<i>time-to-event</i> - les techniques d'analyse de survie (Cox proportional hazards, "
      "Random Survival Forests, DeepSurv) offrent un cadre statistique rigoureux qui contourne "
      "la difficulte classique des modèles de régression sur des delais censures.", S_PN),
    P("La litterature récente insiste egalement sur l'importance de la quantification de "
      "l'incertitude. Les modèles de régression quantile (Koenker et Bassett, 1978 ; "
      "implémentation LightGBM <i>objective='quantile'</i>) permettent de produire des "
      "intervalles de prédiction P10/P50/P90 plus honnêtes qu'un simple intervalle gaussien "
      "calcule sur les residus, et plus exploitables opérationnellement qu'un score de "
      "confiance ad hoc. Cette approche est integree au present projet comme indicateur de "
      "robustesse propose au planificateur.", S_PN),

    H2("1.4.3 Demand-Driven MRP : le cadre opérationnel de référence"),
    P("Le cadre conceptuel <i>Demand-Driven Material Requirements Planning</i> (DDMRP), "
      "formalise par Ptak et Smith (2016) sur la base des travaux pionniers de Goldratt sur la "
      "théorie des contraintes, structure une alternative opérationnelle au MRP classique "
      "deconnecte de la demande réelle. DDMRP s'articule autour de cinq composantes : "
      "<i>Strategic Inventory Positioning</i> (placement stratégique des stocks), "
      "<i>Buffer Profiles and Levels</i> (dimensionnement de buffers vert/jaune/rouge par "
      "article), <i>Dynamic Adjustments</i> (ajustement des buffers selon la saisonnalite), "
      "<i>Demand-Driven Planning</i> (declenchement de réapprovisionnement sur la base du "
      "<i>Net Flow Position</i>), et <i>Visible and Collaborative Exécution</i> (suivi visuel "
      "des états critiques).", S_PN),
    P("Cette grille de lecture est essentielle pour positionner academiquement le present "
      "travail. Une approche IA pure sans ancrage DDMRP risque de produire un modèle "
      "statistiquement performant mais opérationnellement deconnecte des règles métier "
      "établies. Inversement, une approche DDMRP pure n'exploite pas la richesse des variables "
      "exogènes desormais disponibles à faible coût. Le mémoire propose une articulation "
      "hybride : un modèle IA produit une prédiction de demande qui alimente le calcul du "
      "<i>Net Flow Position</i> DDMRP, lui-meme arbitre par le planificateur. La comparaison "
      "directe entre IA pure et DDMRP de référence est restituée en section 2.3.3.", S_PN),

    H2("1.4.4 Human-in-the-loop et IA responsable"),
    P("La litterature récente sur le deploiement industriel de l'IA insiste sur la necessite "
      "d'integrer l'expertise humaine dans la boucle de décision, particulièrement pour les "
      "domaines à fort enjeu économique. L'approche <i>Human-in-the-Loop Machine Learning</i> "
      "(Wu et al., 2022) propose plusieurs patrons d'intégration, dont l'arbitrage par seuil "
      "de confiance, l'apprentissage actif sur les décisions correctives et la documentation "
      "systematique via des <i>model cards</i> (Mitchell et al., 2019). Le present projet "
      "deploie une matrice de gouvernance à trois niveaux (vert : automatisation, orange : "
      "revue rapide, rouge : décision humaine obligatoire) cohérente avec ces principes et "
      "compatible avec les exigences émergentes de l'AI Act européen sur les systèmes a risque "
      "limite.", S_PN),
    PageBreak(),
]

# ============================================================================
# PARTIE 2
# ============================================================================
story += [
    Spacer(1, 6 * cm),
    P("PARTIE 2", ParagraphStyle("part", parent=S_TITLE, fontSize=20)),
    Spacer(1, 0.4 * cm),
    P("Solution Technique", S_TITLE),
    PageBreak(),
]

# ---------- 2.1 Data Engineering ----------
story += [
    H1("2.1 Méthodologie Data Engineering"),
    H2("2.1.1 Audit des sources et qualité des données brutes"),
    P("Le matériau brut consolide pour ce mémoire est constitue de deux exports opérationnels "
      "fournis par GE : un export des commandes clients de 2021 à 2025 et un export "
      "des livraisons effectivement réalisées sur la meme période. Les deux fichiers, au format "
      "Excel à l'origine, ont d'abord été convertis en CSV puis charges en Python via "
      "<i>pandas</i> pour traitement. L'audit initial a porte sur quatre dimensions : "
      "complétude (taux de valeurs nulles par colonne), unicite (détection des doublons sur "
      "les clés fonctionnelles), validité (vérification des plages de valeurs numériques et "
      "des formats de dates), et cohérence inter-fichiers (rapprochement commande/livraison).", S_PN),
    P("Les principaux défauts identifies à ce stade ont été les suivants : présence de lignes "
      "de commande sans correspondance livraison (commandes annulees ou differees), hétérogénéité "
      "des formats de date selon la source (mix DD/MM/YYYY et YYYY-MM-DD), codification "
      "incoherente des références articles entre certaines périodes (renumerotation partielle "
      "en 2023), et présence residuelle de lignes de test informatique insérées lors des "
      "opérations de maintenance ERP. Ces défauts ont fait l'objet d'un nettoyage trace dans "
      "le notebook <i>01_data_cleaning.ipynb</i>.", S_PN),

    H2("2.1.2 Pipeline de nettoyage et imputation"),
    P("Le pipeline de nettoyage a été implemente comme une succession d'étapes idempotentes "
      "documentées pour garantir la reproductibilité scientifique. Chaque étape consigne le "
      "nombre de lignes avant et après opération et la raison de chaque suppression : "
      "deduplication exacte, suppression des lignes de test, harmonisation des formats de "
      "date, imputation des valeurs manquantes par la médiane pour les variables numériques "
      "et par la modalité la plus frequente pour les variables catégorielles dont le taux de "
      "nullite est inférieur à 5 pourcents, suppression des lignes dont les variables critiques "
      "(code_client, code_article, qte_demandee, date_cmd) sont manquantes.", S_PN),
    P("Le dataset consolide final, sauvegarde au format Parquet sous "
      "<i>data/processed/dataset_ml_final.parquet</i>, comporte 349 390 lignes pour 24 colonnes. "
      "Le taux de rapprochement commande/livraison atteint 94.2 pourcents, valeur jugee "
      "satisfaisante pour la suite des analyses. Le tableau ci-dessous synthèse la qualité "
      "des données après nettoyage.", S_PN),

    table([
        ["Indicateur", "Avant nettoyage", "Après nettoyage"],
        ["Lignes commande", "362 480", "349 390"],
        ["Lignes livraison", "338 215", "329 174"],
        ["Taux de rapprochement", "85.3 %", "94.2 %"],
        ["Valeurs nulles (qte_demandee)", "1.8 %", "0.0 %"],
        ["Doublons", "3 211", "0"],
        ["Lignes de test ERP", "412", "0"],
        ["Période couverte", "2021-01 à 2025-12", "2021-01 à 2025-12"],
    ], col_widths=[6.5 * cm, 4.5 * cm, 4.5 * cm]),
    P("<b>Tableau 1</b> - Synthèse de la qualité des données avant et après pipeline de "
      "nettoyage (notebook <i>01_data_cleaning.ipynb</i>).", S_CAPTION),

    H2("2.1.3 Feature engineering et enrichissement exogène"),
    P("La phase d'enrichissement, conduite dans le notebook <i>02_statistical_study.ipynb</i>, "
      "a augmente le jeu de données de 24 à 35 colonnes en intégrant des sources externes "
      "publiques. Trois catégories d'enrichissement ont été réalisées : enrichissement "
      "temporel par décomposition fine de chaque date (année, mois, trimestre, semaine ISO, "
      "jour de la semaine, indicateurs de fin de mois et de fin de trimestre), enrichissement "
      "calendaire par intégration des jours fériés francais (via la librairie "
      "<i>workalendar</i>) et des périodes de vacances scolaires (zones A/B/C agrégées), "
      "et enrichissement exogène par l'indice de production industrielle (IPI) de l'INSEE et "
      "par les données météorologiques quotidiennes (températures, pluviométrie, vitesse de "
      "vent maximale) interrogees via l'API publique Open-Meteo sur les coordonnees du "
      "principal centre de distribution.", S_PN),
    P("Vingt-huit features finales ont été retenues après une sélection itérative combinant "
      "analyse univariee, calcul du facteur d'inflation de la variance (VIF) pour traiter la "
      "colinéarité, et tests bivaries par groupes pour les variables catégorielles. Les "
      "variables catégorielles à forte cardinalité (code_client, code_article) ont été encodées "
      "par <i>frequency encoding</i> plutot que par one-hot, choix justifie par la dimension "
      "élevée (plusieurs milliers de modalités) et l'efficience des algorithmes de gradient "
      "boosting sur des entrees compactes.", S_PN),

    H2("2.1.4 Stratégie de split temporel et prevention du data leakage"),
    P("Un point méthodologique critique pour la validité des conclusions est la stratégie de "
      "split. Tout split aléatoire est ici prohibe, car il introduirait une fuite d'information "
      "future dans le jeu d'entraînement (par exemple, une commande de fin 2025 utilisee pour "
      "predire une commande de debut 2023). Le split adopte est strictement temporel : "
      "2021-2023 pour l'entraînement (210 641 lignes, 60.3 pourcents), 2024 pour la validation "
      "(70 871 lignes, 20.3 pourcents) et 2025 pour le test final (66 174 lignes, 18.9 "
      "pourcents).", S_PN),
    P("Toutes les statistiques d'agrégation servant a générer des features (fréquences, "
      "moyennes historiques, lags) sont calculées exclusivement sur le set d'entraînement, "
      "puis projetees sur validation et test sans recalcul global. Cette discipline, parfois "
      "négligée dans les notebooks exploratoires, conditionne la validité des chiffres reportes "
      "et permet d'éviter la situation classique de modèles surperformants en validation mais "
      "décevants en production.", S_PN),

    fig("eda_split_temporel.png",
        "Figure 9 - Split temporel train (2021-2023) / val (2024) / test (2025). "
        "Source : notebook 02bis_eda_dataset_enrichi.ipynb."),
    PageBreak(),
]

# ---------- 2.2 Études statistiques ----------
story += [
    H1("2.2 Résultats des études statistiques"),
    H2("2.2.1 Décomposition de la serie agrégée"),
    P("La première analyse a porte sur la serie de demande agrégée à la maille mensuelle, tous "
      "articles et tous clients confondus. La décomposition STL (Seasonal-Trend décomposition "
      "using Loess) implémentée dans <i>statsmodels</i> a mis en évidence trois composantes "
      "stables : une tendance de fond legerement croissante sur la période 2021-2025, une "
      "composante saisonniere annuelle marquee par un creux estival systematique (juillet-août) "
      "et un pic d'automne (septembre-novembre), et un residu de variabilite eleve traduisant "
      "la diversite intra-mensuelle de la demande client.", S_PN),
    P("La figure 1 ci-dessous restitué cette décomposition. Le pic d'automne represente en "
      "moyenne 30 pourcents de volume supplementaire par rapport au creux estival, "
      "amplitude très significative qui justifie a elle seule l'attention portée aux features "
      "temporelles. Le residu, bien qu'eleve en valeur absolue, ne presente pas de structure "
      "manifeste après décomposition, ce qui suggere qu'une part substantielle de la "
      "variabilite restante est imputable a des facteurs exogènes (clients, articles, "
      "evenements extérieurs) non encore introduits dans la décomposition.", S_PN),

    fig("decomposition_globale.png",
        "Figure 1 - Décomposition STL de la demande mensuelle agrégée 2021-2025. "
        "De haut en bas : serie observée, tendance, composante saisonniere annuelle, residu."),

    H2("2.2.2 Décomposition par famille d'article"),
    P("La décomposition globale masque des dynamiques sensiblement differentes selon les "
      "valeurs de la variable <i>famille_activite_article</i>. La meme décomposition STL "
      "appliquee separement aux principales familles du catalogue fait apparaitre deux "
      "profils contrastes : un premier profil presente une amplitude saisonniere marquee, "
      "synchrone avec un calendrier annuel net, tandis qu'un second profil presente une "
      "demande plus régulière, peu sensible aux cycles annuels. Le contenu métier spécifique "
      "des familles concernees n'est pas détaillé ici, conformément au perimetre defini en "
      "section 1.1.2 ; l'observation reste exploitable à partir de la seule structure des "
      "données. Cette dichotomie à une implication opérationnelle directe : un modèle "
      "generaliste unique sous-performera systematiquement sur l'une ou l'autre population, "
      "argument qui motivera l'enrichissement autorégressif au niveau du couple, du client "
      "et de l'article presente en section 2.3.4.", S_PN),

    fig("decomposition_par_famille.png",
        "Figure 2 - Décompositions STL comparées par famille d'article."),

    H2("2.2.3 Cycles budgetaires clients"),
    P("L'analyse des dates de commande agrégées à la maille hebdomadaire fait ressortir un "
      "pattern budgetaire net : la dernière semaine de chaque trimestre concentre régulièrement "
      "un volume supérieur de 15 à 25 pourcents à la moyenne du trimestre. Ce phenomene, "
      "documente dans la litterature comme effet d'absorption du budget restant en fin de "
      "période budgetaire, se manifeste de manière hétérogène selon les segments de "
      "clientele identifies dans la variable <i>famille_activite_client</i> du jeu de données, "
      "sans qu'une interprétation métier supplementaire ne soit avancée ici. La feature "
      "binaire <i>est_fin_mois_cmd</i> capte partiellement ce signal mais reste insuffisamment "
      "fine ; une amélioration possible serait l'ajout d'une feature <i>est_fin_trimestre</i> "
      "dediee.", S_PN),

    fig("cycles_budgetaires.png",
        "Figure 3 - Distribution hebdomadaire des commandes - mise en évidence des pics de "
        "fin de trimestre."),

    H2("2.2.4 Cycles météorologiques"),
    P("Le couplage des données de commande avec les données météorologiques Open-Meteo a "
      "permis de tester quantitativement l'hypothèse d'une influence de la meteo sur la "
      "demande. Trois variables ont été retenues : température minimale, pluviométrie cumulee "
      "journaliere et vitesse de vent maximale, associées à la <i>date_livraison_demandee</i> "
      "et non à la date d'enregistrement de la commande, afin de capter l'effet meteo a "
      "l'horizon d'exécution plutot qu'a l'horizon de saisie.", S_PN),
    P("La correlation marginale entre meteo et quantité demandee reste faible (Pearson "
      "inférieur à 0.10 en valeur absolue pour les trois variables), mais l'analyse "
      "decomposee par famille d'article revele un effet legerement plus marque sur le "
      "profil saisonnier identifie en section 2.2.2 : une pluviométrie élevée la semaine "
      "precedant la date de livraison demandee y est associée à une legere baisse du "
      "volume effectif. Aucune interprétation métier spécifique de ce signal n'est avancée "
      "au-delà de l'observation statistique brute.", S_PN),

    fig("cycles_meteo.png",
        "Figure 4 - Relations meteo / demande par famille d'article."),

    H2("2.2.5 Matrice de correlation et sélection de variables"),
    P("La matrice de correlation de Pearson calculée sur l'ensemble des features numériques "
      "et de la cible <i>qte_demandee</i> fournit une première lecture des dependances "
      "linéaires. Comme attendu, aucune feature seule n'explique massivement la cible : la "
      "correlation maximale, obtenue avec la fréquence du couple client-article, atteint "
      "0.27, ce qui est cohérent avec une cible eclatee à forte variance individuelle. La "
      "matrice a egalement guide l'élimination de variables fortement colineaires : "
      "<i>est_weekend_liv_dem</i> et <i>jour_semaine_liv_dem</i> presentent un VIF eleve et "
      "ont fait l'objet d'un arbitrage au profit de la seconde, plus informative.", S_PN),

    fig("matrice_correlation_pearson.png",
        "Figure 5 - Matrice de correlation de Pearson - features et cible."),

    H2("2.2.6 Test de causalité de Granger et features exogènes"),
    P("Le test de causalité de Granger a été applique sur les sept variables exogènes "
      "candidates (IPI, variables meteo agrégées à la semaine, jours fériés) avec des lags de "
      "1 à 6 semaines. Les p-values obtenues, restituées figure 6, font apparaitre une "
      "causalité significative (p < 0.05) pour l'IPI au lag 1 et au lag 3, pour la température "
      "moyenne hebdomadaire au lag 2, et pour les jours fériés sans decalage. Ces résultats "
      "justifient l'intégration des features exogènes correspondantes dans le modèle final, "
      "et auraient pu motiver l'ajout de versions laggees explicites (<i>ipi_valeur_lag1</i>, "
      "<i>ipi_valeur_lag3</i>) si le temps de développement avait permis cet enrichissement "
      "supplementaire.", S_PN),

    fig("granger_pvalues.png",
        "Figure 6 - P-values du test de causalité de Granger entre variables exogènes "
        "candidates et demande hebdomadaire agrégée."),

    table([
        ["Variable exogène", "Lag optimal", "p-value", "Significatif"],
        ["IPI INSEE", "1 semaine", "0.012", "Oui"],
        ["IPI INSEE", "3 semaines", "0.034", "Oui"],
        ["Température moyenne", "2 semaines", "0.041", "Oui"],
        ["Pluviométrie cumulee", "1 semaine", "0.118", "Marginal"],
        ["Vent maximal", "1 semaine", "0.234", "Non"],
        ["Jour férié", "0 (immediat)", "0.008", "Oui"],
        ["Vacances scolaires", "0 (immediat)", "0.067", "Marginal"],
    ], col_widths=[5 * cm, 3 * cm, 2.5 * cm, 3 * cm]),
    P("<b>Tableau 2</b> - Variables exogènes et significativité Granger sur la demande "
      "hebdomadaire agrégée. Source : notebook <i>02_statistical_study.ipynb</i>.", S_CAPTION),

    H2("2.2.7 Stationnarite, distribution de la cible et acf"),
    P("La distribution de la cible <i>qte_demandee</i> presente une asymétrie très marquee "
      "(skewness = 80.73) et une queue lourde a droite caractéristique des distributions de "
      "type demande client industrielle. La transformation <i>log1p</i> (logarithme de "
      "1 + x) ramene cette asymétrie à 1.44, valeur acceptable pour les modèles de régression "
      "sur cible continue. Cette transformation est appliquee systematiquement en entree des "
      "modèles, l'inversion <i>expm1</i> etant opérée avant tout calcul de métrique pour "
      "garantir la comparabilite des résultats.", S_PN),

    fig("eda_target_distribution.png",
        "Figure 7 - Distribution de la cible avant (gauche) et après (droite) "
        "transformation log1p."),

    fig("eda_acf_pacf.png",
        "Figure 8 - ACF et PACF de la demande hebdomadaire agrégée - structure "
        "autorégressive faible mais presente aux lags 1 et 4."),
    PageBreak(),
]

# ---------- 2.3 Modèles ----------
story += [
    H1("2.3 Architecture et performances des modèles IA"),
    P("Cette section détaillé les modèles entraines, restitué leurs performances comparées "
      "sur le jeu de test 2025 (jamais vu pendant l'entraînement ni la sélection de modèle), "
      "et discute les choix faits aux moments clés. Le code source des entraînements est "
      "reparti dans les notebooks <i>03_model_training.ipynb</i> (première génération de "
      "modèles), <i>04_feature_engineering_lags.ipynb</i> (enrichissement autorégressif) et "
      "<i>10_catboost_stacking.ipynb</i> (architectures avancées). Les modèles serialises sont "
      "disponibles dans le dossier <i>models/</i>.", S_PN),

    H2("2.3.1 Baseline historique et baseline naive"),
    P("Toute affirmation de performance d'un modèle machine learning n'a de sens que par "
      "comparaison à une baseline credible. Deux baselines sont utilisees ici. La baseline "
      "<i>naive</i> consiste a predire pour chaque commande de test la moyenne globale de la "
      "quantité demandee sur le set d'entraînement (ignorance maximale). La baseline "
      "<i>historique</i>, plus exigeante, predit pour chaque couple (client, article) la "
      "moyenne historique observée de ce couple sur 2021-2023, et la moyenne globale en "
      "fallback pour les couples inconnus. Sur le test 2025, la baseline historique atteint "
      "une MAE de 13.04 et un RMSE de 145.11. Tout modèle apportant une valeur ajoutee "
      "scientifique doit dominer cette baseline statistiquement, idealement de plusieurs "
      "points.", S_PN),

    H2("2.3.2 Première génération de modèles - Régression sur 28 features"),
    P("La première génération de modèles vise la prédiction directe de la quantité demandee "
      "(<i>qte_demandee</i>) par chaque commande individuelle. Quatre modèles ont été entraines "
      "successivement avec le meme jeu de 28 features exogènes et statiques, le meme split "
      "temporel, et la meme transformation logarithmique de la cible :", S_PN),
    *bullets([
        "<b>XGBoost log+MSE</b> : modèle de référence du gradient boosting, fonction de coût "
        "MSE sur cible log-transformee, parametrisation par défaut.",
        "<b>XGBoost Tweedie</b> : meme architecture mais fonction de coût Tweedie "
        "(<i>objective='reg:tweedie'</i>), adaptée aux distributions positives a queue "
        "lourde et à la fraction non négligeable de petites quantités.",
        "<b>LightGBM log</b> : alternative implémentée dans la librairie de Microsoft, "
        "convergence généralement plus rapide que XGBoost a equivalent fonctionnel.",
        "<b>XGBoost v1 (Optuna 50 essais)</b> : meme moteur que XGBoost log mais "
        "hyperparametrisation optimisée par 50 essais bayesiens (<i>Optuna</i>) sur le jeu "
        "de validation 2024, avec recherche conjointe sur <i>n_estimators</i>, "
        "<i>max_depth</i>, <i>learning_rate</i>, <i>subsample</i>, <i>colsample_bytree</i>, "
        "<i>min_child_weight</i>, <i>reg_alpha</i> et <i>reg_lambda</i>.",
    ]),
    P("Les meilleurs hyperparamètres retenus à cette étape sont : <i>n_estimators</i> = 498, "
      "<i>max_depth</i> = 10, <i>learning_rate</i> = 0.0776, <i>subsample</i> = 0.96, "
      "<i>colsample_bytree</i> = 0.73, <i>min_child_weight</i> = 3, <i>reg_alpha</i> = 0.021, "
      "<i>reg_lambda</i> = 0.284. La valeur de <i>n_estimators</i> proche de la borne haute "
      "de l'espace de recherche (500) suggere qu'un elargissement du nombre d'essais et de "
      "l'espace de recherche apporterait un gain supplementaire ; cette intuition motivera "
      "l'itération suivante (XGBoost v2, section 2.3.4).", S_PN),

    table([
        ["Modèle", "MAE", "RMSE", "R^2", "WAPE", "Gain vs baseline"],
        ["Baseline naive", "23.50", "210.30", "-", "1.041", "ref"],
        ["Baseline historique", "13.04", "145.11", "-", "0.620", "-44.5 % MAE"],
        ["XGBoost log + MSE", "14.36", "153.11", "0.246", "0.654", "+10.1 %"],
        ["XGBoost Tweedie", "13.74", "138.98", "0.379", "0.626", "+5.4 %"],
        ["LightGBM log", "14.74", "158.43", "0.192", "0.671", "+13.0 %"],
        ["<b>XGBoost v1 (Optuna 50)</b>", "<b>11.87</b>", "<b>132.17</b>",
         "<b>0.438</b>", "<b>0.541</b>", "<b>-9.0 %</b>"],
    ], col_widths=[4.5 * cm, 2 * cm, 2 * cm, 1.7 * cm, 1.7 * cm, 2.5 * cm]),
    P("<b>Tableau 3</b> - Comparaison des modèles de première génération sur le test 2025 "
      "(28 features statiques, sans variables autorégressives). Seul XGBoost v1 optimise par "
      "Optuna domine la baseline historique sur toutes les métriques. Source : "
      "<i>reports/rapport_modelisation.json</i>.", S_CAPTION),

    P("La lecture du tableau 3 conduit à trois constats. Premièrement, XGBoost et LightGBM "
      "en configuration par défaut ne battent pas la baseline historique en MAE, ce qui est "
      "souvent observe sur des cibles à forte variance intra-couple et confirme l'importance "
      "de l'optimisation hyperparametrique. Deuxièmement, la variante Tweedie améliore "
      "sensiblement le RMSE et le R^2 par rapport à la variante MSE, en captant mieux la queue "
      "de distribution des petites quantités. Troisièmement, XGBoost v1 optimise par Optuna est "
      "le seul modèle a battre la baseline historique sur la MAE, avec un gain de 9 pourcents. "
      "Ce résultat est encourageant mais reste loin de la cible <i>North Star</i> (60 "
      "pourcents de précision agrégée, soit WAPE inférieur à 0.40) ; il motive l'enrichissement "
      "feature et la refonte d'hyperparametrisation conduits dans la génération suivante.", S_PN),

    fig("feature_importance_xgb.png",
        "Figure 10 - Importance des 15 features les plus contributrices du modèle "
        "XGBoost v2 (gain XGBoost). Les rolling means client et article dominent, suivies "
        "par les fréquences, le prix, l'IPI et le target encoding."),

    H2("2.3.3 Architecture 2 - LSTM time-to-event pour la date de prochaine commande"),
    P("L'architecture 2 traite un problème statistiquement different : la prédiction du delai "
      "(en jours) avant la prochaine commande du meme couple client-article. La cible est "
      "construite par calcul de la difference entre dates de commande successives pour chaque "
      "couple ayant au moins deux commandes dans l'historique. Le modèle est un LSTM "
      "implemente en PyTorch avec deux couches, 64 unités cachees, longueur de séquence SEQ_LEN "
      "= 6, batch size 256, optimiseur Adam et fonction de coût MSE sur le delai en jours.", S_PN),
    P("Les huit features d'entree sequentielles sont : <i>prix</i>, "
      "<i>delai_demande_jours</i> du couple precedent, fréquence client, fréquence article, "
      "<i>ipi_valeur</i>, <i>mois_cmd</i>, <i>jour_semaine_cmd</i>, et <i>est_fin_mois_cmd</i>. "
      "L'entraînement converge en environ 30 époques sans surapprentissage marque sur la "
      "validation, mais les performances finales sur le test 2025 sont décevantes au regard "
      "de l'enjeu opérationnel.", S_PN),

    table([
        ["Métrique", "Valeur observée", "Cible opérationnelle", "Verdict"],
        ["MAE delai (jours)", "24.5", "< 10 jours", "Insuffisant"],
        ["Précision +/-7 jours", "25.5 %", "> 50 %", "Insuffisant"],
        ["Précision +/-14 jours", "43.2 %", "> 70 %", "Insuffisant"],
        ["Couverture (couples eval.)", "78.4 %", "> 60 %", "Acceptable"],
    ], col_widths=[5 * cm, 3 * cm, 3.5 * cm, 3 * cm]),
    P("<b>Tableau 4</b> - Performance du LSTM time-to-event sur le test 2025. La précision "
      "+/-7 jours, métrique centrale pour l'usage planificateur, reste très en deca de la "
      "cible opérationnelle. Source : <i>reports/rapport_modelisation.json</i>.", S_CAPTION),

    P("Ces résultats appellent une analyse honnête des causes possibles. La longueur de "
      "séquence SEQ_LEN = 6 est probablement insuffisante pour capter une saisonnalite "
      "annuelle ou semestrielle ; l'absence de features autorégressives sur le delai lui-meme "
      "(<i>delai_lag_1</i>, ... <i>delai_lag_6</i>) prive le modèle d'un signal fort ; "
      "l'absence de scaling explicite des features numériques (le LSTM y est très sensible) a "
      "pu ralentir la convergence ; et la formulation du problème en régression sur un delai "
      "continu n'est pas la plus naturelle compte tenu de la nature réellement temporelle "
      "du problème. La litterature récente plaide pour une reformulation en analyse de survie "
      "(<i>lifelines</i>, <i>scikit-survival</i>, <i>pycox</i>), ou alternativement en "
      "classification multi-classes par bucket de delai ([0-7], [7-14], [14-30], [30-60], [60+] "
      "jours), ce qui simplifie la tache et facilite l'interprétation. Cette voie est "
      "explicitement listee dans les perspectives (section 3.5).", S_PN),

    H2("2.3.4 Évolution méthodologique - Enrichissement feature et architectures avancées"),
    P("A l'issue de la première génération de modèles, l'analyse du tableau 3 a fait apparaitre "
      "un écart significatif entre la performance obtenue (précision agrégée 45.95 pourcents) "
      "et l'objectif <i>North Star</i> declare (60 pourcents). Trois axes méthodologiques ont "
      "été explores pour réduire cet écart : l'enrichissement du signal autorégressif, "
      "l'extension du benchmark a d'autres familles d'algorithmes, et la confrontation à une "
      "baseline métier de référence (DDMRP).", S_PN),

    H3("Enrichissement autorégressif et XGBoost v2"),
    P("Le premier axe a consiste a augmenter le jeu de 28 à 47 features par ajout de 19 "
      "variables autorégressives : lags 1/7/30 jours sur la quantité, rolling mean et std a "
      "7/30/90 jours au niveau du couple, du client seul et de l'article seul, target encoding "
      "couple / client / article par fold temporel (pour éviter toute fuite), nombre de "
      "commandes du couple sur les 30 derniers jours, nombre de jours depuis la dernière "
      "commande, lag de prix et delta de prix. Ces variables capturent explicitement la "
      "dynamique temporelle qui restait masquee dans la première génération. Sur cette base "
      "enrichie, un modèle <i>XGBoost v2</i> a été optimise par 300 essais Optuna (contre 50 "
      "pour la version v1), avec un espace de recherche elargi (jusqu'a 1500 estimateurs, "
      "profondeur jusqu'a 14). Les meilleurs paramètres retenus sont <i>n_estimators</i> = "
      "1108, <i>max_depth</i> = 12, <i>learning_rate</i> = 0.0077, <i>subsample</i> = 0.82, "
      "<i>colsample_bytree</i> = 0.96.", S_PN),

    H3("Architectures complementaires : LightGBM Quantile, CatBoost, Stacking Ridge"),
    P("Le second axe a etendu le benchmark à trois architectures complementaires entrainees "
      "sur le meme jeu de 47 features et le meme split temporel : <i>LightGBM Quantile</i> "
      "configure aux quantiles 0.1, 0.5 et 0.9 pour produire des intervalles de prédiction "
      "P10 / P50 / P90 directement exploitables opérationnellement ; <i>CatBoost v2</i> "
      "entraine avec 200 essais Optuna, qui exploite nativement les features catégorielles "
      "et leurs interactions ; et un meta-modèle <i>Stacking Ridge</i> qui combine les "
      "prédictions out-of-fold de XGBoost v2, LightGBM Quantile P50 et CatBoost via une "
      "régression Ridge regularisee (alpha optimal = 10). Le stacking est entraine sur des "
      "prédictions issues d'une <i>TimeSeriesSplit</i> à 5 folds pour éviter toute fuite "
      "d'information.", S_PN),

    H3("Baseline DDMRP de référence"),
    P("Le troisième axe a implemente une baseline <i>Demand-Driven Material Requirements "
      "Planning</i> selon les specifications de Ptak et Smith (notebook "
      "<i>09_baseline_ddmrp.ipynb</i>). Le perimetre couvre les 22 articles stratégiques "
      "sélectionnés par règle de Pareto (80 pourcents du volume cumule). Pour chaque article, "
      "trois zones de stock sont calculées - vert, jaune, rouge - à partir de l'<i>Average "
      "Daily Usage</i> sur 60 jours, du <i>Lead Time</i> moyen, et de facteurs de variabilite "
      "calibres sur la distribution historique. La simulation hebdomadaire du <i>Net Flow "
      "Position</i> compare ensuite les décisions de réapprovisionnement DDMRP aux prédictions "
      "du modèle IA sur la meme période.", S_PN),

    table([
        ["Modèle / Méthode", "MAE", "RMSE", "R^2", "WAPE", "1 - WAPE"],
        ["Baseline historique", "13.04", "145.11", "-", "0.620", "38.0 %"],
        ["XGBoost v1 (28 feat., Optuna 50)",
         "11.87", "132.17", "0.438", "0.541", "45.9 %"],
        ["LightGBM Quantile P50 (47 feat.)",
         "8.32", "121.87", "0.522", "0.379", "62.1 %"],
        ["CatBoost v2 (47 feat., Optuna 200)",
         "8.98", "120.05", "0.536", "0.409", "59.1 %"],
        ["<b>XGBoost v2 (47 feat., Optuna 300)</b>",
         "<b>8.42</b>", "101.83", "0.666", "<b>0.383</b>", "<b>61.7 %</b>"],
        ["<b>Stacking Ridge (XGB+LGBM+CatBoost)</b>",
         "8.70", "<b>97.55</b>", "<b>0.694</b>", "0.396", "60.4 %"],
    ], col_widths=[5.8 * cm, 1.6 * cm, 1.8 * cm, 1.5 * cm, 1.6 * cm, 1.7 * cm]),
    P("<b>Tableau 5</b> - Benchmark complet des architectures testees sur le test 2025. "
      "Trois architectures dépassent l'objectif <i>North Star</i> de 60 pourcents (1 - WAPE) : "
      "LightGBM Quantile P50, XGBoost v2 et Stacking Ridge. XGBoost v2 domine sur la MAE, "
      "Stacking Ridge sur RMSE et R^2. Sources : <i>reports/sprint_a_chantier1_metrics.json</i> "
      "et <i>reports/sprint_b_chantier1_stacking.json</i>.", S_CAPTION),

    P("Le tableau 5 invite à une lecture comparative qui evite la tentation du <i>modèle "
      "gagnant unique</i>. Trois architectures répondent au cahier des charges global : "
      "LightGBM Quantile P50 offre la meilleure MAE pure (8.32) et fournit nativement des "
      "intervalles de prédiction ; XGBoost v2 propose le meilleur compromis MAE / WAPE / "
      "interprétabilité et constitue une base eprouvee ; Stacking Ridge domine sur les "
      "métriques de dispersion (RMSE 97.55, R^2 0.694) en corrigeant les grandes erreurs grace "
      "a la complementarite des composants. Le choix d'une architecture de production releve "
      "donc d'un arbitrage explicite entre critères opérationnels (coût d'inférence, "
      "simplicite de maintenance, disponibilité des intervalles d'incertitude) plutot que "
      "d'un classement statistique unidimensionnel.", S_PN),

    H3("Confrontation IA vs DDMRP sur articles stratégiques"),
    P("La comparaison directe entre les prédictions IA et la simulation DDMRP, restreinte au "
      "perimetre des 22 articles stratégiques sélectionnés par règle de Pareto, livre les "
      "résultats suivants sur le test 2025 agrégé en semaines.", S_PN),

    table([
        ["Méthode", "MAE hebdo", "Biais hebdo", "Lecture"],
        ["IA seule (XGBoost v2)", "260.1", "-223.0",
         "Très precis mais sous-estime structurel"],
        ["DDMRP simulee (Ptak & Smith)", "660.8", "-179.0",
         "Marges de sécurité, MAE élevée"],
        ["<b>Hybride 50 / 50</b>", "<b>242.0</b>", "<b>-20.9</b>",
         "<b>Meilleur compromis</b>"],
    ], col_widths=[5 * cm, 2.5 * cm, 2.5 * cm, 5 * cm]),
    P("<b>Tableau 6</b> - Comparaison IA, DDMRP et combinaison hybride sur 22 articles "
      "stratégiques (perimetre 80 pourcents du volume). L'hybridation à parts egales "
      "minimise simultanement la MAE hebdomadaire et le biais. Source : "
      "<i>reports/sprint_b_chantier3_ddmrp.json</i>.", S_CAPTION),

    P("Cette comparaison delivre un message méthodologique central : l'IA et DDMRP ne sont "
      "pas substituables mais complementaires. L'IA fournit une prédiction precise mais "
      "structurellement sous-estimee de la demande (biais négatif eleve), tandis que DDMRP "
      "introduit des marges de sécurité opérationnelles qui evitent la rupture mais "
      "augmentent l'erreur moyenne. Une combinaison hybride à parts egales réduit "
      "simultanement la MAE hebdomadaire (242 contre 260 pour l'IA seule) et le biais "
      "structurel (-20.9 contre -223). Le taux de rupture observe sur la simulation DDMRP "
      "(11.2 pourcents) confirme par ailleurs la valeur opérationnelle de l'approche "
      "métier classique, qui ne disparait pas avec l'arrivee de l'IA.", S_PN),

    H2("2.3.5 Analyse comparative et sélection du modèle de service"),
    P("La sélection d'une architecture pour le service opérationnel resulte d'un arbitrage "
      "multicritere : performance brute, interprétabilité, simplicite d'industrialisation, "
      "coût de maintenance. Le mémoire ne tranche pas en faveur d'un modèle unique mais "
      "documente trois configurations recommandées selon le profil d'usage :", S_PN),

    *bullets([
        "<b>XGBoost v2 (47 features)</b> : configuration recommandée pour un service "
        "monomodele privilegiant simplicite opérationnelle et interprétabilité. MAE 8.42, "
        "WAPE 0.383, précision agrégée 61.7 pourcents. Modèle actif dans le dashboard livre.",
        "<b>LightGBM Quantile P10 / P50 / P90</b> : configuration recommandée lorsque "
        "l'utilisateur métier exige des intervalles d'incertitude explicites (badge de "
        "confiance, marges de sécurité). Performances P50 comparables a XGBoost v2 et "
        "intervalles directement exploitables.",
        "<b>Stacking Ridge (XGBoost v2 + LightGBM P50 + CatBoost)</b> : configuration "
        "recommandée lorsque la métrique de dispersion (RMSE, R^2) est prioritaire et "
        "que le coût d'inférence triple est acceptable. Gain de 4 points sur le RMSE et "
        "de 4 points sur le R^2 par rapport au monomodele.",
    ]),

    P("Cette présentation neutre des trois configurations est defendue dans la <i>model card</i> "
      "publiée en annexe : elle expose au jury et aux praticiens la realite d'un projet "
      "industriel ou plusieurs architectures coexistent legitimement selon le profil d'usage, "
      "et ou la décision de service finale est documentée, datee et susceptible d'evoluer.", S_PN),
    PageBreak(),
]

# ---------- 2.4 Dashboard ----------
story += [
    H1("2.4 Présentation du dashboard Human-in-the-loop"),
    H2("2.4.1 Architecture technique et choix de stack"),
    P("Le dashboard livre repose sur la stack Streamlit, choisie après comparaison avec les "
      "alternatives Dash (Plotly), Panel et FastAPI + React. Trois critères ont determine ce "
      "choix : la rapidite de développement (un planificateur teste l'interface des la "
      "semaine 5 du projet), l'intégration native avec l'ecosysteme Python scientifique "
      "déjà utilise pour la modélisation, et la possibilite d'embarquer Plotly pour les "
      "graphiques interactifs sans pont JavaScript. La contrepartie reconnue est une "
      "scalabilité limitée à quelques utilisateurs simultanes, acceptable pour un MVP "
      "interne mais qui necessitera une migration vers une architecture découplée (FastAPI "
      "+ React) pour une mise en production à l'échelle.", S_PN),
    P("L'application est structurée en une page d'accueil et six pages métier accessibles "
      "via la sidebar Streamlit native : <i>Gestion des Données</i>, <i>Intelligence "
      "Artificielle</i>, <i>Prévisions de Ventes</i>, <i>Analyse</i>, <i>Drift Détection</i>, "
      "<i>Backtest 2025</i>. Les utilitaires de chargement de données, d'inférence, de calcul "
      "du score de confiance et de simulation what-if sont centralises dans le package "
      "<i>dashboard/utils/</i> pour éviter la duplication.", S_PN),

    H2("2.4.2 Page Gestion des Données"),
    P("La page <i>Gestion des Données</i> assure deux fonctions : la consultation du jeu de "
      "données historique et l'import de nouveaux fichiers pour inférence. Le tableau "
      "consultation propose un filtrage par client, par article, par période, et un export "
      "CSV des résultats filtres. L'import accepte un fichier CSV au format <i>Mode A</i> "
      "(déjà encode avec les suffixes <i>_freq</i> et <i>_enc</i>), choix de simplification "
      "explicitement documente dans la limite opérationnelle pour le MVP - un Mode B "
      "(encodage automatique cote serveur) est positionne en perspective.", S_PN),

    screen("donnees.png",
           "Figure 11 - Page Gestion des Données du dashboard. Le tableau filtrable consulte "
           "l'historique 2021-2025 ; le bandeau d'import en haut accepte les CSV Mode A."),

    H2("2.4.3 Page Intelligence Artificielle"),
    P("La page <i>Intelligence Artificielle</i> centralise les informations sur le modèle "
      "actif et l'historique des versions. Elle expose la version active, la date de dernier "
      "entraînement, la liste des features utilisees (lue dynamiquement depuis l'attribut "
      "<i>feature_names_in_</i> du modèle serialise pour éviter toute divergence avec la "
      "liste hardcodee), et un tableau historique des runs avec leurs métriques principales. "
      "Un bouton <i>Re-entrainer le modèle</i> declenche le script "
      "<i>src/retrain.py</i> en arriere-plan et streame le log d'exécution dans la page.", S_PN),

    screen("ia.png",
           "Figure 12 - Page Intelligence Artificielle. Le panneau central affiche les "
           "métriques du modèle actif, l'historique des versions et le bouton de "
           "re-entraînement."),

    H2("2.4.4 Page Prévisions de Ventes et score de confiance composite"),
    P("La page <i>Prévisions de Ventes</i> constitue le cœur fonctionnel du dashboard. Elle "
      "propose au planificateur la liste des couples client-article à horizon M+1 a M+3 avec "
      "leur quantité predite, leur intervalle d'incertitude P10-P90 et un indicateur visuel "
      "de confiance (vert / orange / rouge) lisible en un coup d'oeil. La page integre un "
      "filtrage par client, par famille d'article et par segment ABC, ainsi qu'un export "
      "CSV / Excel des lignes sélectionnées.", S_PN),
    P("Le score de confiance affiche est calcule par une formule composite à trois facteurs "
      "documentée dans le fichier <i>dashboard/utils/confidence.py</i> : (1) familiarité du "
      "couple (article et client déjà vus ensemble en entraînement, partiellement vus, ou "
      "inconnus), (2) écart entre la prédiction et la médiane historique du couple "
      "(indicateur de surprise statistique), et (3) decile de la valeur predite dans la "
      "distribution d'entraînement (les valeurs extremes sont moins fiables). Le score "
      "composite est mappe sur trois états : vert si confiance supérieure à 0.75, orange "
      "entre 0.4 et 0.75, rouge en dessous. Ce mapping est configurable depuis la page "
      "<i>Analyse</i> via un slider, materialisant la matrice de gouvernance HITL "
      "(détaillée section 3.4).", S_PN),

    screen("previsions.png",
           "Figure 13 - Page Prévisions de Ventes (vue principale). Tableau central : un "
           "couple client-article par ligne, colonnes Quantité predite, P10-P90, Confiance "
           "(badge couleur), Action recommandée. Le panneau de filtres lateral autorise une "
           "sélection multidimensionnelle."),

    screen("previsions 1.png",
           "Figure 14 - Page Prévisions, sous-section <i>Prédiction vs valeur réelle</i>. "
           "Scatter plot interactif Plotly : abscisse valeur réelle, ordonnee prédiction. "
           "La couleur encode le score de confiance et la diagonale grise materialise la "
           "prédiction parfaite."),

    screen("previsions 2.png",
           "Figure 15 - Page Prévisions, sous-section <i>Simulation what-if</i>. Sliders et "
           "toggles permettant au planificateur de simuler l'effet d'une variation de prix, "
           "de delai, d'IPI ou d'un passage en jour férié sur la prédiction d'une ligne "
           "sélectionnée, avec affichage de la prédiction simulee et de l'intervalle P10 - "
           "P90 associe."),

    H2("2.4.5 Page Analyse - IA vs baseline et exploration des erreurs"),
    P("La page <i>Analyse</i> centralise le travail de storytelling autour des résultats de "
      "modélisation. Elle confronte d'abord la MAE de la baseline historique à la MAE du "
      "modèle XGBoost v2 et affiche le gain relatif obtenu sur le jeu de test 2025. Elle "
      "presente ensuite le top des erreurs maximales : un tableau classe les couples "
      "client-article ou l'écart entre quantité réelle et quantité predite est le plus eleve. "
      "Cette vue est essentielle pour la lecture critique du modèle car elle materialise les "
      "régions de l'espace ou la prédiction reste fragile et oriente les améliorations futures.", S_PN),
    P("Une lecture explicite accompagne le tableau : les erreurs maximales correspondent "
      "généralement a des commandes de gros volume sur des articles ou des clients peu "
      "representes dans le set d'entraînement, ce qui justifie l'usage du badge de confiance "
      "(orange ou rouge) pour signaler ces situations au planificateur avant validation.", S_PN),

    screen("Analyse.png",
           "Figure 16 - Page Analyse. Le tableau central liste le top des erreurs absolues "
           "du modèle XGBoost v2 sur le test 2025 ; la lecture en bas de page guide "
           "l'interprétation et le rattachement au score de confiance. Le bandeau inférieur "
           "expose la comparaison IA vs DDMRP et la décomposition par architectures avancées."),

    H2("2.4.6 Page Drift Détection - monitoring de la stabilité des features"),
    P("La page <i>Drift Détection</i> implemente un monitoring de la <i>Population Stability "
      "Index</i> (PSI) sur les six features les plus contributrices du modèle XGBoost v2, "
      "identifiées par importance de permutation : <i>qte_roll_mean_7</i>, "
      "<i>qte_roll_mean_30_article</i>, <i>qte_roll_mean_30</i>, "
      "<i>qte_roll_mean_30_client</i>, <i>prix</i> et <i>ipi_valeur</i>. La distribution de "
      "référence est calculée sur le set d'entraînement (2021-2023) et confrontée soit au "
      "test 2025 par défaut, soit à une distribution courante uploadee par l'utilisateur "
      "(CSV ou Parquet).", S_PN),
    P("Pour chaque feature surveillée, l'application calcule le PSI selon la formule "
      "standard <i>somme(p_cur - p_ref) * log(p_cur / p_ref)</i> sur dix bins definis par "
      "quantiles de la distribution de référence. Une classification à trois niveaux est "
      "appliquee : <i>stable</i> (PSI inférieur à 0.10), <i>drift modere</i> (PSI entre 0.10 "
      "et 0.25), <i>drift significatif</i> (PSI supérieur à 0.25). Un bandeau d'alerte synthèse "
      "le verdict global et conseille un re-entraînement lorsqu'au moins une feature critique "
      "passe en zone rouge. Cette mécanique est conforme aux pratiques de monitoring credit "
      "risk industriel (Karakoulas, 2011) et constitue le socle d'une mise en production "
      "responsable.", S_PN),

    screen("drift.png",
           "Figure 17 - Page Drift Détection. Panneau gauche : tableau PSI par feature avec "
           "code couleur (vert / orange / rouge) ; panneau droit : histogramme des PSI pour "
           "lecture visuelle rapide. Le bandeau supérieur synthèse le verdict de stabilité "
           "du modèle."),

    H2("2.4.7 Page Backtest interactif - retroprojection 2025"),
    P("La page <i>Backtest 2025</i> propose au planificateur de retroprojeter l'usage du "
      "modèle sur l'année 2025 à l'aide d'un slider hebdomadaire ISO. Pour chaque <i>semaine "
      "d'arret</i> sélectionnée, l'application affiche la quantité réelle cumulee, la quantité "
      "predite cumulee par chacun des modèles sélectionnés (XGBoost v2, LightGBM Quantile P50, "
      "CatBoost, Stacking Ridge, baseline historique), ainsi que des métriques rolling sur les "
      "quatre dernières semaines.", S_PN),
    P("Au-delà des métriques statistiques (MAE et WAPE par fenetre), la page expose une "
      "<i>fonction de coût business</i> parametrable par l'utilisateur : <i>coût = alpha * "
      "ruptures + beta * sur-stock</i>, ou alpha et beta sont fixes par sliders en euros par "
      "unité. Cette fonction permet une lecture économique directe du comportement des "
      "modèles dans des contextes ou la rupture coute plus cher que le surstock (alpha "
      "grand), ou inversement (beta grand). Le tableau des dix erreurs absolues maximales sur "
      "la semaine d'arret complete la lecture par une vue qualitative des cas extremes.", S_PN),

    screen("backtest.png",
           "Figure 18 - Page Backtest interactif. Graphique central : cumul de la quantité "
           "réelle et des prédictions cumulees des modèles sélectionnés en abscisse semaine "
           "ISO. Panneaux secondaires : métriques rolling 4 semaines, fonction de coût "
           "business parametrable, tableau des dix plus grandes erreurs."),

    H2("2.4.8 Page d'accueil - synthèse executive et navigation"),
    P("La page d'accueil du dashboard joue le role de tableau de bord executif. Elle expose "
      "en bandeau supérieur les indicateurs clés du modèle actif (MAE, R^2, WAPE, taille du "
      "dataset), rappelle la problématique en quelques lignes et restitué visuellement le "
      "pipeline complet du projet (Data Engineering, Études statistiques, Modélisation IA, "
      "Dashboard). Le panneau de navigation a droite oriente l'utilisateur vers les quatre "
      "pages métier en fonction du besoin du moment : exploration des données, monitoring du "
      "modèle, prévisions à horizon M+1/M+3, analyse comparative.", S_PN),
    P("Au-delà de la fonction navigation, cette page d'accueil constitue le premier contact "
      "visuel pour un decideur non technique. Elle permet de mesurer instantanement la "
      "valeur ajoutee du modèle par rapport à la baseline historique (badge <i>-9.0 % "
      "vs baseline</i>) sans avoir a entrer dans les détails statistiques de chaque page.", S_PN),

    screen("app.png",
           "Figure 19 - Page d'accueil du dashboard. KPIs du modèle actif en bandeau, "
           "rappel de la problématique au centre, schema du pipeline et navigation rapide "
           "vers les six pages métier."),

    H3("Synthèse PSI mesurée sur le test 2025"),
    P("Les valeurs de PSI mesurées sur le test 2025 par la page <i>Drift Détection</i> "
      "fournissent une calibration empirique des seuils. Le tableau ci-dessous restitué les "
      "PSI obtenus sur les six features critiques entre la référence train (2021-2023) et "
      "la distribution test (2025).", S_PN),

    table([
        ["Feature surveillée", "PSI test 2025", "Statut"],
        ["prix", "0.07", "Stable"],
        ["qte_roll_mean_7", "0.11", "Drift modere"],
        ["ipi_valeur", "0.19", "Drift modere"],
        ["qte_roll_mean_30_article", "0.18", "Drift modere"],
        ["qte_roll_mean_30_client", "0.09", "Stable"],
        ["qte_roll_mean_30", "0.14", "Drift modere"],
    ], col_widths=[6.5 * cm, 3.5 * cm, 5.5 * cm]),
    P("<b>Tableau 7</b> - PSI mesures sur les six features les plus contributrices entre "
      "train et test 2025. Aucune feature ne franchit le seuil rouge (0.25), ce qui justifie "
      "le maintien du modèle en service sans declencher de re-entraînement immediat.", S_CAPTION),
    PageBreak(),
]

# ============================================================================
# PARTIE 3
# ============================================================================
story += [
    Spacer(1, 6 * cm),
    P("PARTIE 3", ParagraphStyle("part", parent=S_TITLE, fontSize=20)),
    Spacer(1, 0.4 * cm),
    P("Analyse Critique", S_TITLE),
    PageBreak(),
]

# ---------- 3.1 IA vs CA ----------
story += [
    H1("3.1 Comparaison IA versus intuition commerciale"),
    H2("3.1.1 Méthodologie de comparaison"),
    P("La comparaison entre la prédiction IA et le pilotage par objectifs commerciaux ne "
      "peut s'appuyer, dans le perimetre du present mémoire, que sur des données "
      "objectives disponibles dans le dataset. Faute d'accès aux objectifs commerciaux "
      "négociés par GE, l'évaluation prend pour référence la <i>baseline historique</i> "
      "(moyenne par couple client-article calculée sur 2021-2023), qui constitue un proxy "
      "mesurable de ce que produirait une planification non assistee par IA au-delà d'une "
      "simple moyenne glissante. Cette baseline est volontairement exigeante : un modèle "
      "qui ne la dépasse pas significativement n'apporterait aucune valeur ajoutee "
      "scientifique.", S_PN),

    H2("3.1.2 Gains mesures par rapport à la baseline"),
    P("Sur le perimetre du test 2025 (66 174 lignes), le gain absolu du modèle XGBoost v2 par "
      "rapport à la baseline historique est de 4.62 unités en MAE (8.42 contre 13.04), soit "
      "un gain relatif de 35.4 pourcents. En précision agrégée (1 - WAPE), le modèle atteint "
      "61.7 pourcents contre 38.0 pourcents pour la baseline, soit un gain absolu de "
      "23.7 points et un dépassement de 1.7 point de l'objectif <i>North Star</i> declare "
      "(60 pourcents). Le modèle <i>Stacking Ridge</i>, qui améliore le RMSE de 4 points "
      "(97.55 contre 101.83) et le R^2 de 4 points (0.694 contre 0.666), constitue une "
      "alternative interessante lorsque la métrique de dispersion est prioritaire.", S_PN),
    P("Le test de Diebold-Mariano applique sur les residus du modèle XGBoost v2 versus "
      "la baseline historique donne une p-value très significativement inférieure à 0.01, "
      "ce qui permet d'affirmer statistiquement la supériorité du modèle sur l'ensemble du "
      "test. Cette validation statistique est essentielle pour anticiper la question - "
      "fréquemment posee en soutenance - de la significativité du gain observe.", S_PN),

    H2("3.1.3 Cadre d'estimation business"),
    P("La traduction du gain statistique en valeur économique necessite la connaissance de "
      "deux paramètres métier : <i>alpha</i>, le coût unitaire d'une rupture, et <i>beta</i>, "
      "le coût unitaire d'un surstock (par mois immobilise). Ces paramètres ne sont pas "
      "fournis dans le brief de mission et ne peuvent donc pas être fixes ici sans "
      "approximation arbitraire. La page <i>Backtest 2025</i> du dashboard permet a "
      "l'utilisateur métier de saisir lui-meme ces deux paramètres et d'observer le coût "
      "cumule des differents modèles sur l'année 2025 sous l'hypothèse choisie. Cette "
      "démarche evite de propager une estimation chiffrée non sourcée dans le mémoire "
      "tout en laissant a GE la possibilite de quantifier le gain sur ses propres barèmes.", S_PN),
    PageBreak(),
]

# ---------- 3.2 Limites ----------
story += [
    H1("3.2 Limites du modèle"),
    H2("3.2.1 Imprévus géopolitiques et ruptures de régime"),
    P("La première limite structurelle de toute approche basee sur l'apprentissage statistique "
      "est sa difficulte intrinseque a anticiper les ruptures de régime. La période "
      "d'entraînement 2021-2023 comprend deux contextes économiquement atypiques : la phase "
      "post-Covid (chaînes d'approvisionnement perturbees, prix volatiles) et la phase "
      "consecutive à la guerre en Ukraine declenchee en février 2022 (envolee des prix de "
      "l'énergie, tensions sur les composants). Le modèle a donc appris des correlations "
      "potentiellement biaisees par ces contextes ; un changement de régime aussi violent "
      "que ces deux precedents pendant la période d'inférence invaliderait localement les "
      "prédictions. Aucune technique d'apprentissage statistique ne corrige intégralement "
      "ce défaut ; la détection de dérive PSI integree au dashboard est un palliatif partiel "
      "qui declenche une alerte sans pour autant fournir un nouveau modèle adapte.", S_PN),

    H2("3.2.2 Données manquantes et perimetres non couverts"),
    P("Plusieurs sources d'information potentiellement utiles n'ont pas pu être integrees, "
      "soit par indisponibilité, soit par contrainte de temps. Les données promotionnelles "
      "(remises tarifaires accordees ponctuellement) ne sont pas tracées dans l'export ERP "
      "exploite ; or, une remise significative declenche typiquement un effet d'anticipation "
      "de commande qui n'est pas capte par le modèle. Les opérations de transfert inter-sites "
      "sont egalement absentes : un transfert de stock entre deux centres de distribution "
      "pour répondre à une rupture locale n'apparait pas comme une commande dans le perimetre "
      "etudie. Enfin, les retours clients - faibles en volume mais structurellement biaises "
      "vers certaines familles d'article - ne sont pas integres.", S_PN),

    H2("3.2.3 Biais identifies"),
    P("Trois catégories de biais structurels du jeu de données ont été identifiées comme "
      "points de vigilance pour une exploitation industrielle. Les ordres de grandeur "
      "associes restent qualitatifs : leur quantification precise dépasse le perimetre du "
      "present mémoire mais est facilement instrumentable en relancant les notebooks "
      "d'EDA et de modélisation sur les colonnes concernees.", S_PN),
    *bullets([
        "<b>Biais de fréquence client</b> : les comptes à faible activite (peu de "
        "commandes par an) representent une part importante du nombre de clients mais "
        "une part marginale du volume. Le modèle leur attribue mécaniquement une erreur "
        "plus élevée, ce qui implique un risque de rupture silencieuse sur cette "
        "population si la prédiction est utilisee sans badge de confiance.",
        "<b>Biais d'article</b> : la longue traîne du catalogue (articles à faible "
        "volume) presente une demande intermittente structurellement difficile a "
        "predire par un modèle de régression continue. Une exploitation industrielle "
        "exigerait une approche spécialisée de type Croston / TSB / ADIDA pour ce "
        "segment.",
        "<b>Biais temporel</b> : la présence de régimes économiquement atypiques dans "
        "l'entraînement (post-Covid, choc énergétique 2022) peut conduire a sur-ponderer "
        "ces régimes lors d'une inférence dans un contexte revenu à la normale.",
    ]),

    H2("3.2.4 Échec relatif du LSTM time-to-event et honnêteté métrique"),
    P("La précision +/-7 jours de 25.5 pourcents obtenue par l'architecture LSTM time-to-event "
      "est très inférieure à la cible opérationnelle (50 pourcents). Cet écart constitue le "
      "point faible le plus visible du mémoire et ne saurait être dissimule. L'analyse "
      "honnête des causes (longueur de séquence insuffisante, absence d'autorégression sur "
      "le delai, absence de scaling, formulation potentiellement inadaptée) a déjà été "
      "exposée section 2.3.3. Plutot que de retirer cette architecture du livrable, elle est "
      "explicitement signalee dans le dashboard par un badge rouge par défaut sur toute "
      "prédiction de date : la transparence sur la fiabilite limitée de ce modèle est ici un "
      "engagement méthodologique, qui prepare la reformulation par analyse de survie "
      "annoncee en perspectives.", S_PN),

    H2("3.2.5 Atteinte du North Star sur la quantité, échec sur la date"),
    P("La cible <i>North Star</i> declaree en debut de projet, 60 pourcents de précision "
      "agrégée (1 - WAPE), est atteinte sur la quantité : le modèle XGBoost v2 livre une "
      "précision de 61.7 pourcents sur le test 2025, soit un dépassement de 1.7 point. La "
      "configuration <i>Stacking Ridge</i> atteint 60.4 pourcents avec une amélioration "
      "significative de la métrique de dispersion (R^2 0.694 contre 0.666 pour XGBoost v2). "
      "Trois architectures distinctes franchissent ainsi le seuil cible (XGBoost v2 à 61.7 "
      "pourcents, LightGBM Quantile P50 à 62.1 pourcents, Stacking Ridge à 60.4 pourcents), "
      "ce qui constitue un acquis robuste et reproductible.", S_PN),
    P("L'objectif n'est en revanche pas atteint sur la prédiction de date par LSTM, qui "
      "plafonne à 25.5 pourcents +/-7 jours (cible opérationnelle : 50 pourcents). Cette "
      "dissymetrie des résultats - réussite sur la quantité, échec relatif sur la date - "
      "structure la lecture critique du mémoire : le livrable opere une transformation "
      "demontrable sur le pilotage des volumes mais ne resout pas la question du <i>timing</i> "
      "exact des commandes, qui devra être repris via une reformulation par analyse de "
      "survie (perspectives en section 3.5).", S_PN),
    PageBreak(),
]

# ---------- 3.3 RGPD ----------
story += [
    H1("3.3 Conformité RGPD et ethique du traitement"),
    P("Le present mémoire mobilisant des données d'entreprise contenant indirectement des "
      "informations relatives a des personnes physiques (interlocuteurs commerciaux, "
      "demandeurs ERP, planificateurs identifies dans certains champs metadata), une "
      "analyse de conformité au Règlement General sur la Protection des Données (RGPD, "
      "règlement UE 2016/679, applicable depuis le 25 mai 2018) est imperative. Cette section "
      "documente cette analyse et identifie les mesures techniques et organisationnelles "
      "mises en œuvre.", S_PN),

    H2("3.3.1 Données personnelles potentiellement concernees"),
    P("Au sens de l'article 4 du RGPD, constitue une donnée personnelle toute information se "
      "rapportant à une personne physique identifiée ou identifiable. L'examen des colonnes "
      "presentes dans le dataset effectivement utilise (<i>data/processed/dataset_ml_enrichi."
      "parquet</i>) permet d'identifier le statut des champs vis-à-vis du RGPD :", S_PN),
    *bullets([
        "<b>Identifiants entreprise (codes opaques)</b> : <i>code_client</i> et "
        "<i>code_article</i> sont des identifiants numériques internes a GE. Ils ne "
        "designent pas directement une personne physique mais peuvent y conduire en "
        "présence d'une table de correspondance interne. Dans le pipeline d'apprentissage, "
        "ces champs sont remplaces par leur <i>frequency encoding</i> "
        "(<i>code_client_freq</i>, <i>code_article_freq</i>), ce qui rompt le lien direct.",
        "<b>Variables descriptives clients</b> : <i>famille_activite_client</i>, "
        "<i>type_activite</i>, <i>pays</i>, <i>segment</i>. Ces champs decrivent l'activite "
        "commerciale et le pays du client, qui peut être une personne morale ou physique. "
        "Lorsqu'un client est une personne physique (entrepreneur individuel par exemple), "
        "ces variables constituent indirectement des données personnelles.",
        "<b>Variables transactionnelles</b> : <i>qte_demandee</i>, <i>qte_livree</i>, "
        "<i>prix</i>, dates. Données commerciales standard non personnelles en elles-memes.",
    ]),
    P("Le dataset utilise pour l'entraînement ne contient en revanche aucun champ "
      "directement nominatif (nom, prenom, contact, identifiant operateur ERP). Aucune "
      "donnée sensible au sens de l'article 9 du RGPD (santé, opinion politique, syndicale, "
      "religieuse, biometrique, sexuelle) n'est traitee dans le perimetre du projet.", S_PN),

    H2("3.3.2 Bases legales du traitement"),
    P("Le traitement realise dans le cadre du present mémoire mobilise deux bases legales "
      "principales selon l'article 6 du RGPD :", S_PN),
    *bullets([
        "<b>Article 6.1.b (exécution d'un contrat)</b> : le traitement des données "
        "client necessaires à l'exécution des commandes (raison sociale, adresse de "
        "livraison, code interlocuteur) est legitime par l'exécution du contrat "
        "commercial entre GE et ses clients.",
        "<b>Article 6.1.f (interet legitime)</b> : le traitement statistique anonymise "
        "des historiques de commande aux fins d'amélioration de la prévision de demande "
        "est legitime par l'interet legitime de GE a optimiser sa chaîne "
        "d'approvisionnement, sous reserve que les droits et libertes des personnes "
        "concernees ne prevalent pas. Une analyse d'impact (AIPD / DPIA) formelle "
        "complementaire est recommandée avant tout deploiement en production etendu.",
    ]),

    H2("3.3.3 Mesures techniques et organisationnelles mises en œuvre"),
    P("Trois mesures techniques et organisationnelles ont été adoptees au cours du projet "
      "pour minimiser la sensibilite des données manipulees :", S_PN),
    *bullets([
        "<b>Pseudonymisation des identifiants</b> : les champs <i>code_client</i> et "
        "<i>code_article</i> sont remplaces par leur frequency encoding "
        "(<i>code_client_freq</i>, <i>code_article_freq</i>) lors de la preparation "
        "(notebook <i>02bis_eda_dataset_enrichi.ipynb</i>), ce qui rompt le lien direct "
        "entre une transaction et un identifiant commercial dans les modèles serialises.",
        "<b>Minimisation</b> : le dataset utilise pour l'apprentissage ne contient aucun "
        "champ nominatif (nom, prenom, contact, identifiant operateur), conformément au "
        "perimetre defini en 1.1.2 et à l'inspection des colonnes effectivement chargees.",
        "<b>Maîtrise de la diffusion</b> : aucune des données brutes ou enrichies n'est "
        "publiée dans le dépôt Git du projet (les fichiers Parquet sont exclus par "
        "<i>.gitignore</i>) ; seuls les rapports agrégés et les modèles serialises sont "
        "versionnes.",
    ]),

    H2("3.3.4 Droits des personnes concernees"),
    P("Les droits prevus aux articles 15 à 22 du RGPD sont applicables aux données "
      "operateurs ERP traitees dans le projet, meme si leur volume est limite et leur "
      "exploitation indirecte. Le tableau ci-dessous synthèse le statut de ces droits dans "
      "le perimetre du projet.", S_PN),

    table([
        ["Droit", "Référence", "Modalité d'exercice"],
        ["Accès", "Art. 15", "Sur demande au DPO GE"],
        ["Rectification", "Art. 16", "Mise a jour ERP source"],
        ["Effacement", "Art. 17", "Anonymisation totale dans le dataset"],
        ["Limitation", "Art. 18", "Suspension de l'inclusion dans le pipeline"],
        ["Portabilite", "Art. 20", "Export structure sur demande"],
        ["Opposition", "Art. 21", "Exclusion sur demande motivee"],
        ["Décision automatisée", "Art. 22", "Non applicable - décision finale humaine"],
    ], col_widths=[3.5 * cm, 2.5 * cm, 9 * cm]),
    P("<b>Tableau 9</b> - Droits RGPD et modalités d'exercice dans le perimetre du projet.",
      S_CAPTION),

    P("Le point essentiel a souligner est l'article 22 : le RGPD interdit en principe les "
      "décisions produisant des effets juridiques ou affectant significativement une "
      "personne, prises sur la seule base d'un traitement automatisé. Dans le cas present, "
      "la décision de réapprovisionnement finale reste imperativement humaine (le "
      "planificateur valide la commande generee), ce qui place le système hors du perimetre "
      "des décisions purement automatisées. Cette caractéristique est centrale dans "
      "l'architecture <i>Human-in-the-loop</i> defendue en section 3.4.", S_PN),

    H2("3.3.5 Duree de conservation et registre des traitements"),
    P("La duree de conservation des données brutes 2021-2025 reste celle définie par les "
      "politiques internes de GE - non documentées dans le perimetre du present mémoire - "
      "et par les obligations legales applicables aux données commerciales (article L.123-22 "
      "du Code de commerce). Les artefacts produits dans le cadre du projet (jeux de "
      "données enrichis, modèles serialises) sont conserves pour la duree du mémoire et "
      "feront l'objet d'une revue post-soutenance pour décider de leur sort. Le traitement "
      "spécifique realise dans le cadre du projet doit être inscrit, le cas echeant, dans "
      "le registre des activites de traitement de GE, sous une catégorie d'analyse "
      "statistique interne, avec mention explicite du perimetre temporel (2021-2025) et de "
      "la finalite (prévision de la demande client).", S_PN),

    H2("3.3.6 Positionnement vis-à-vis de l'AI Act européen"),
    P("Au-delà du RGPD, le règlement européen sur l'intelligence artificielle (AI Act, "
      "adopte en 2024, applicable de manière échelonnée à partir de 2025) introduit une "
      "classification des systèmes d'IA par niveau de risque. Le système decrit dans ce "
      "mémoire releve de la catégorie <i>risque limite</i> : il ne participe pas à une "
      "décision affectant directement une personne physique au sens de l'AI Act (recrutement, "
      "credit, education, infrastructures critiques), et son usage est interne a "
      "l'organisation. Les obligations applicables à cette catégorie - transparence sur "
      "l'usage d'un système IA, documentation technique, supervision humaine - sont "
      "explicitement couvertes par la model card publiée en annexe, le present mémoire et "
      "la matrice de gouvernance HITL exposée section 3.4. Une évolution du système vers "
      "une automatisation totale du réapprovisionnement le ferait basculer en catégorie "
      "<i>risque eleve</i>, ce qui necessiterait des obligations renforcées (audit "
      "indépendant, conformité ex ante) explicitement évoquées dans les perspectives de "
      "mise en production.", S_PN),
    PageBreak(),
]

# ---------- 3.4 HITL ----------
story += [
    H1("3.4 Importance de la validation humaine (Human-in-the-loop)"),
    H2("3.4.1 Principe et formalisation"),
    P("Le principe <i>Human-in-the-loop</i> (HITL) constitue la clé de voûte de la "
      "philosophie opérationnelle du système. Plutot que d'opposer intelligence artificielle "
      "et expertise humaine, il s'agit de les articuler : le modèle fournit une recommandation "
      "transparente assortie d'un score de confiance, le planificateur arbitre en fonction "
      "de ce score, du contexte connu de lui seul (relations commerciales, evenements "
      "anticipes) et de sa propre estimation. La validation humaine demeure le dernier "
      "maillon de la chaîne de décision, conformément aux exigences de l'article 22 du RGPD "
      "et de l'AI Act européen pour les systèmes de risque limite.", S_PN),

    H2("3.4.2 Matrice de gouvernance à trois niveaux"),
    P("La matrice de gouvernance retenue, configurable via la page <i>Analyse</i> du "
      "dashboard, articule trois niveaux de décision en fonction du score de confiance "
      "composite calcule pour chaque prédiction.", S_PN),

    table([
        ["Niveau", "Critère (score)", "Action recommandée"],
        ["Vert", "score > 0.75",
         "Automatisation totale - commande validée sans revue"],
        ["Orange", "0.40 < score < 0.75",
         "Revue rapide - validation 1 clic par le planificateur"],
        ["Rouge", "score < 0.40",
         "Décision humaine obligatoire et saisie d'une justification"],
    ], col_widths=[2.5 * cm, 4 * cm, 9 * cm]),
    P("<b>Tableau 8</b> - Matrice de gouvernance Human-in-the-loop. Les seuils 0.40 et 0.75 "
      "sont configurables depuis la page <i>Analyse</i> du dashboard ; la repartition "
      "effective entre les trois niveaux se calcule dynamiquement sur le perimetre courant "
      "et n'est pas figee dans ce document.",
      S_CAPTION),

    H2("3.4.3 Boucle d'amélioration continue"),
    P("Au-delà de la simple validation, le HITL ouvre une boucle d'amélioration continue : "
      "chaque correction opérée par un planificateur sur une prédiction (acceptation, "
      "modification, refus avec justification libre) est tracée et constitue un signal "
      "supplementaire d'apprentissage potentiel. Une itération ultérieure du système "
      "pourrait integrer cette boucle de feedback dans un schema d'apprentissage actif "
      "(<i>active learning</i>) ou de fine-tuning periodique. Cette piste est documentée "
      "dans les perspectives de la section 3.5 et constituerait un gain majeur d'adoption "
      "et de robustesse en production.", S_PN),
    PageBreak(),
]

# ---------- 3.5 Perspectives ----------
story += [
    H1("3.5 Perspectives d'amélioration et de mise en production"),
    H2("3.5.1 Améliorations méthodologiques à court terme"),
    P("Trois améliorations méthodologiques ont été identifiées comme prioritaires pour une "
      "itération ultérieure du projet. Première priorite : la reformulation de la prédiction "
      "de date par analyse de survie (modèles <i>Cox proportional hazards</i> via "
      "<i>lifelines</i>, <i>Random Survival Forests</i> via <i>scikit-survival</i>, ou "
      "<i>DeepSurv</i> via <i>pycox</i>), qui devrait permettre de dépasser largement la "
      "précision actuelle de 25.5 pourcents +/-7 jours en exploitant correctement la nature "
      "<i>time-to-event</i> du problème. Deuxième priorite : un traitement dedie de la longue "
      "traîne via les méthodes Croston, TSB et ADIDA spécialisées dans la demande "
      "intermittente, susceptible de réduire significativement la MAE residuelle sur la "
      "longue traîne d'articles à faible volume. Troisième priorite : l'intégration des "
      "features exogènes laggees "
      "(<i>ipi_valeur_lag1</i>, <i>ipi_valeur_lag3</i>, <i>temperature_lag2</i>), motivee "
      "par les résultats du test de Granger (tableau 2) et restée non implémentée pour des "
      "raisons d'agenda.", S_PN),

    H2("3.5.2 Architecture cible de mise en production"),
    P("L'architecture cible de mise en production décrite ci-dessous demeure un livrable "
      "conceptuel du present mémoire et n'a pas été deployee dans le perimetre du Master ; "
      "elle constitue la principale perspective industrielle du projet et formalise les "
      "briques attendues pour un usage opérationnel à l'échelle.", S_PN),
    *bullets([
        "<b>API d'inférence</b> : <i>FastAPI</i> avec validation de schemas par "
        "<i>Pydantic</i>, deployee derriere un reverse proxy <i>Nginx</i>. Endpoints "
        "<i>/predict</i>, <i>/explain</i> (SHAP par ligne), <i>/health</i>, "
        "<i>/metrics</i>.",
        "<b>Base de données relationnelle</b> : <i>PostgreSQL</i> avec schemas dedies "
        "pour les prédictions historiques, les feedbacks planificateur (boucle HITL) et "
        "les snapshots de modèles. SQLAlchemy comme couche ORM.",
        "<b>Versioning modèle</b> : <i>MLflow Model Registry</i> avec stages "
        "<i>Staging</i> et <i>Production</i>, permettant un retour arriere instantane "
        "en cas de régression detectee.",
        "<b>Versioning données</b> : <i>DVC</i> avec remote S3 ou MinIO interne, pour "
        "reproduire toute experience antérieure à partir de son commit Git.",
        "<b>Monitoring drift</b> : <i>Evidently AI</i> avec rapport HTML genere "
        "automatiquement chaque semaine, integre au dashboard via iframe.",
        "<b>Orchestration retrain</b> : <i>Prefect</i> ou <i>Airflow</i> avec un DAG "
        "hebdomadaire de re-entraînement, declenche soit par planification, soit par "
        "alerte de drift PSI supérieure à 0.25 sur une feature critique.",
        "<b>Containerisation</b> : <i>Docker</i> + <i>docker-compose</i> avec services "
        "<i>app</i>, <i>db</i>, <i>mlflow</i>, <i>worker</i>, <i>monitoring</i>.",
        "<b>Observabilité</b> : logs structures via <i>loguru</i> ou <i>structlog</i>, "
        "exporter Prometheus, dashboards Grafana, alerting Sentry sur erreurs "
        "applicatives.",
    ]),

    H2("3.5.3 Roadmap opérationnelle à six mois"),
    P("Sur la base de cette architecture cible, une roadmap opérationnelle à six mois est "
      "proposee : mois 1 - dockerisation du dashboard actuel et exposition d'une API "
      "interne FastAPI minimaliste. Mois 2 - migration de l'inférence vers FastAPI, ajout "
      "de PostgreSQL pour l'historisation. Mois 3 - intégration MLflow Model Registry. "
      "Mois 4 - intégration DVC pour le versioning data. Mois 5 - boucle de feedback "
      "planificateur (apprentissage actif sur corrections). Mois 6 - mise en place du "
      "monitoring de drift automatisé (Evidently) et activation du retrain planifie. Cette "
      "roadmap reste indicative et necessitera un arbitrage budgetaire dedie de la direction "
      "supply chain de GE.", S_PN),

    H2("3.5.4 Convergence avec DDMRP en production"),
    P("Une perspective spécifique merite d'être soulignee : l'articulation opérationnelle "
      "entre le modèle prédictif et la grille DDMRP. La comparaison conduite en section 2.3.4 "
      "a montre que l'IA et DDMRP ne sont pas substituables mais complementaires. Une "
      "implémentation cible cohérente consisterait a utiliser la prédiction IA comme entree "
      "du calcul du <i>Net Flow Position</i> de DDMRP, et a maintenir les buffers vert / "
      "jaune / rouge comme indicateurs visuels lisibles par les planificateurs. Cette "
      "hybridation IA + DDMRP constituerait une contribution méthodologique reutilisable au-delà "
      "du seul perimetre GE et meriterait une formalisation académique distincte.", S_PN),
    PageBreak(),
]

# ---------- 3.6 Conclusion ----------
story += [
    H1("3.6 Conclusion générale"),
    P("Ce mémoire a entrepris de démontrer qu'une approche <i>Demand-Driven</i> appuyee sur "
      "l'intelligence artificielle peut produire une prédiction opérationnelle exploitable "
      "de la demande client - en quantité et en date - pour soutenir un planificateur supply "
      "chain dans son arbitrage quotidien, sans le remplacer. Au terme du parcours méthodologique "
      "qui a structure les trois parties du document, plusieurs apports complementaires "
      "meritent d'être recapitules pour formaliser le bilan du travail.", S_PN),

    H2("3.6.1 Apports méthodologiques"),
    P("Le premier apport est la mise en place d'un pipeline complet et reproductible : "
      "audit, nettoyage, enrichissement, études statistiques, modélisation, dashboard, "
      "évaluation. Une dizaine de notebooks principaux et un dossier <i>models/</i> serialise "
      "documentent ce pipeline et garantissent sa reproductibilité par tout lecteur disposant "
      "des données sources. Le second apport est l'intégration d'une démarche d'évaluation "
      "honnête : definition explicite d'une baseline historique exigeante, test statistique "
      "de Diebold-Mariano pour valider la supériorité du modèle, monitoring de dérive par "
      "Population Stability Index sur les features critiques, et confrontation systematique "
      "a une baseline DDMRP de référence académique. Le troisième apport est l'articulation "
      "entre IA pure et DDMRP, qui rompt avec la dichotomie habituelle entre <i>méthodes "
      "traditionnelles</i> et <i>méthodes machine learning</i> pour proposer une hybridation "
      "opérationnelle defendable devant un jury comme devant un comité opérationnel.", S_PN),

    H2("3.6.2 Apports professionnels pour GE"),
    P("Les livrables remis a GE comprennent : un dataset propre "
      "et enrichi de 349 390 lignes (utilisable pour d'autres analyses ultérieures), cinq "
      "modèles serialises avec leur historique d'hyperparamètres et leurs métriques mesurées "
      "(directement re-entrainables via le script <i>src/retrain.py</i>), un dashboard "
      "Streamlit multipage opérationnel sur un poste planificateur standard, un document "
      "<i>model card</i> conforme aux standards en vigueur (Google, Hugging Face), une "
      "<i>matrice de gouvernance HITL</i> directement integree au dashboard et un document "
      "de feuille de route à six mois pour la mise en production. Cet ensemble constitue un "
      "MVP complet, immediatement testable en interne, et structure pour preparer un "
      "deploiement plus ambitieux.", S_PN),

    H2("3.6.3 Apports académiques et personnels"),
    P("Sur le plan académique, le mémoire propose une démonstration pas-a-pas qu'un projet "
      "machine learning industriel peut être honnête sur ses réussites comme sur ses limites. "
      "La précision agrégée de 61.7 pourcents obtenue sur la quantité par XGBoost v2 dépasse "
      "l'objectif <i>North Star</i> de 60 pourcents et constitue un acquis robuste, tandis "
      "que la prédiction de date par LSTM (25.5 pourcents +/-7 jours) reste un échec relatif "
      "assume et documente. Cette dualité assumee - réussite quantité, échec date - est "
      "paradoxalement l'un des principaux apports méthodologiques du document, dans un "
      "contexte ou la litterature applicative tend a sur-promettre les performances "
      "obtenues. Sur le plan personnel, ce travail a permis de cumuler une experience "
      "concrète sur l'ensemble de la chaîne data science (de l'ingénierie au deploiement), "
      "d'approfondir la litterature DDMRP à l'interface entre supply chain académique et "
      "machine learning applique, et de prendre la mesure des compromis necessaires entre "
      "performance brute, interprétabilité et gouvernance humaine.", S_PN),

    H2("3.6.4 Limites du travail et ouverture"),
    P("Les limites du travail ont été listees au fil du document et ne seront pas reprises "
      "exhaustivement ici. Quatre points appellent neanmoins une mention finale. "
      "Premièrement, le perimetre temporel d'entraînement (2021-2023) contient deux régimes "
      "atypiques (Covid puis crise énergétique 2022) dont l'effet residuel sur le modèle "
      "ne sera entièrement quantifiable qu'a postériori, après plusieurs années de régime "
      "normalise. Deuxièmement, l'absence de données promotionnelles dans le jeu source "
      "constitue une limite informationnelle structurelle, dont la levée passerait par une "
      "évolution du système ERP source. Troisièmement, le perimetre purement quantitatif "
      "du projet n'integre pas la dimension qualitative des relations commerciales (verbatim "
      "client, signaux faibles d'évolution de stratégie), dimension qui constitue pourtant "
      "une part importante de l'expertise réelle d'un planificateur. Quatrièmement, le "
      "deploiement en production reste un livrable conceptuel ; la traduction opérationnelle "
      "complete du système passera par les six mois de roadmap détaillés section 3.5.3, "
      "qui ne relevent plus du Master mais d'un projet professionnel ultérieur.", S_PN),
    P("Au-delà de ces limites, et de l'humilite que doit conserver tout praticien d'un "
      "domaine ou les modèles vieillissent plus vite que les pratiques métier, le projet "
      "démontre qu'une approche scientifique rigoureuse peut être conjuguée à une exigence "
      "opérationnelle sans renoncer à la honnêteté intellectuelle qui doit caracteriser un "
      "travail académique. La trajectoire ainsi tracée - de la donnée brute à la "
      "recommandation explicable, du score statistique à la matrice de gouvernance, du "
      "tableau de métriques au dashboard interactif - vaut, espere-t-on, comme contribution "
      "modeste mais reproductible au champ encore jeune de l'IA appliquee à la chaîne "
      "d'approvisionnement industrielle.", S_PN),
    PageBreak(),
]

# ---------- BIBLIO ----------
story += [
    H1("Bibliographie"),
    P("Bai, S., Kolter, J. Z., & Koltun, V. (2018). An Empirical Évaluation of Generic "
      "Convolutional and Récurrent Networks for Séquence Modeling. <i>arXiv:1803.01271</i>.",
      S_PN),
    P("Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. "
      "<i>Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge "
      "Discovery and Data Mining</i>, 785-794.", S_PN),
    P("Croston, J. D. (1972). Forecasting and stock control for intermittent demands. "
      "<i>Operational Research Quarterly</i>, 23(3), 289-303.", S_PN),
    P("Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory. <i>Neural "
      "Computation</i>, 9(8), 1735-1780.", S_PN),
    P("Hyndman, R. J., & Athanasopoulos, G. (2018). <i>Forecasting: Principles and "
      "Practice</i> (2nd ed.). OTexts.", S_PN),
    P("Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. "
      "(2017). LightGBM: A Highly Efficient Gradient Boosting Décision Tree. <i>Advances "
      "in Neural Information Processing Systems</i>, 30.", S_PN),
    P("Koenker, R., & Bassett, G. (1978). Régression Quantiles. <i>Econometrica</i>, "
      "46(1), 33-50.", S_PN),
    P("Lim, B., Arik, S. O., Loeff, N., & Pfister, T. (2021). Temporal Fusion Transformers "
      "for interprétable multi-horizon time series forecasting. <i>International Journal "
      "of Forecasting</i>, 37(4), 1748-1764.", S_PN),
    P("Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting Model "
      "Prédictions. <i>Advances in Neural Information Processing Systems</i>, 30.", S_PN),
    P("Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022). The M5 competition: "
      "Background, organization, and implémentation. <i>International Journal of "
      "Forecasting</i>, 38(4), 1325-1336.", S_PN),
    P("Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., "
      "Spitzer, E., Raji, I. D., & Gebru, T. (2019). Model Cards for Model Reporting. "
      "<i>Proceedings of the Conference on Fairness, Accountability, and Transparency</i>, "
      "220-229.", S_PN),
    P("Parlement européen et Conseil de l'Union européenne (2016). Règlement (UE) 2016/679 "
      "du 27 avril 2016 relatif à la protection des personnes physiques à l'égard du "
      "traitement des données a caractère personnel (RGPD).", S_PN),
    P("Parlement européen et Conseil de l'Union européenne (2024). Règlement etablissant "
      "des règles harmonisees concernant l'intelligence artificielle (AI Act).", S_PN),
    P("Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., & Gulin, A. (2018). "
      "CatBoost: unbiased boosting with categorical features. <i>Advances in Neural "
      "Information Processing Systems</i>, 31.", S_PN),
    P("Ptak, C., & Smith, C. (2016). <i>Demand Driven Material Requirements Planning "
      "(DDMRP)</i>. Industrial Press.", S_PN),
    P("Wu, X., Xiao, L., Sun, Y., Zhang, J., Ma, T., & He, L. (2022). A survey of "
      "human-in-the-loop for machine learning. <i>Future Génération Computer Systems</i>, "
      "135, 364-381.", S_PN),
    P("Zhou, H., Zhang, S., Peng, J., Zhang, S., Li, J., Xiong, H., & Zhang, W. (2021). "
      "Informer: Beyond Efficient Transformer for Long Séquence Time-Series Forecasting. "
      "<i>Proceedings of the AAAI Conference on Artificial Intelligence</i>, 35(12), "
      "11106-11115.", S_PN),
    PageBreak(),
]

# ---------- ANNEXES ----------
story += [
    H1("Annexes"),
    H2("Annexe A - Liste des notebooks et livrables"),
    *bullets([
        "<i>notebooks/01_data_cleaning.ipynb</i> - Pipeline de nettoyage des données brutes",
        "<i>notebooks/02_statistical_study.ipynb</i> - Études statistiques et "
        "enrichissement exogène",
        "<i>notebooks/02bis_eda_dataset_enrichi.ipynb</i> - EDA pre-modélisation",
        "<i>notebooks/03_model_training.ipynb</i> - Entraînement de la première "
        "génération de modèles (XGBoost, LightGBM, LSTM)",
        "<i>notebooks/04_feature_engineering_lags.ipynb</i> - Enrichissement "
        "autorégressif (lags, rolling, target encoding) et XGBoost v2",
        "<i>notebooks/09_baseline_ddmrp.ipynb</i> - Baseline DDMRP",
        "<i>notebooks/10_catboost_stacking.ipynb</i> - CatBoost v2 et Stacking Ridge",
        "<i>notebooks/11_backtest_2025_precompute.ipynb</i> - Precomputation du "
        "backtest hebdomadaire",
        "<i>dashboard/app.py</i> + <i>dashboard/pages/*.py</i> - Dashboard Streamlit",
        "<i>src/retrain.py</i> - Script de re-entraînement",
        "<i>reports/rapport_phase1_data_engineering.pdf</i>, "
        "<i>reports/rapport_phase2.md</i>",
        "<i>reports/rapport_modelisation.json</i>, "
        "<i>reports/sprint_a_chantier1_metrics.json</i>, "
        "<i>reports/sprint_b_chantier1_stacking.json</i>, "
        "<i>reports/sprint_b_chantier3_ddmrp.json</i>",
        "<i>docs/MODEL_CARD.md</i> - Model card complete",
    ]),

    H2("Annexe B - Extrait Model Card (synthèse)"),
    P("<b>Identification</b> : XGBoost v2 - <i>models/xgboost_optuna_v2.pkl</i> "
      "(configuration de service principale). Architecture alternative : Stacking Ridge - "
      "<i>models/stacking_ridge.pkl</i>. Auteur : redacteur du mémoire - date : mai 2026.", S_PN),
    P("<b>Usage prevu</b> : prédiction de la quantité demandee par couple "
      "client-article-mois, horizon M+1 a M+3, en appui d'un planificateur "
      "supply chain.", S_PN),
    P("<b>Usage non recommande</b> : articles jamais vus en entraînement (couples "
      "totalement inconnus), ruptures de régime géopolitique brutales, "
      "premières commandes de nouveaux clients.", S_PN),
    P("<b>Données d'entraînement</b> : 210 641 lignes, perimetre 2021-2023, 47 features "
      "(28 statiques + 19 autorégressives).", S_PN),
    P("<b>Métriques globales</b> (test 2025) : MAE 8.42, RMSE 101.83, R^2 0.666, "
      "WAPE 0.383, précision agrégée 61.7 pourcents. Configuration <i>Stacking Ridge</i> "
      "alternative : MAE 8.70, RMSE 97.55, R^2 0.694. Voir tableau 5.", S_PN),
    P("<b>Limites identifiées</b> : précision LSTM date faible (a remplacer par survival "
      "analysis), longue traîne sous-performante (a traiter par Croston / TSB).", S_PN),
    P("<b>Biais ethiques</b> : sous-performance sur les petits clients et les articles "
      "rares (cf. section 3.2.3).", S_PN),
    P("<b>Date de prochaine revue</b> : décembre 2026, ou plus tot si une alerte de "
      "drift PSI supérieure à 0.25 est levée sur une feature critique.", S_PN),
    P("<b>Responsable</b> : a designer parmi les planificateurs senior et la direction "
      "supply chain GE.", S_PN),
]

# ============================================================================
# BUILD
# ============================================================================
class MyDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=A4,
                         leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=MARGIN, bottomMargin=MARGIN,
                         title="Mémoire GE - Système de Prévision et d'Optimisation des Stocks",
                         author="Adham Marrakchi",
                         subject="M1 Expert IT - IA et Big Data - Mémoire de fin d'études")
        frame = Frame(MARGIN, MARGIN, A4[0] - 2 * MARGIN, A4[1] - 2 * MARGIN,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                      id="normal")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=frame, onPage=cover_page),
            PageTemplate(id="main", frames=frame, onPage=header_footer),
        ])

    def afterPage(self):
        # passe en template "main" après la première page
        if self.page == 1:
            self._handle_nextPageTemplate("main")


print(f"[gen] Construction du PDF -> {OUT}")
doc = MyDoc(str(OUT))
doc.build(story)
print(f"[gen] OK - PDF genere : {OUT}")
print(f"[gen] Taille : {OUT.stat().st_size / 1024:.1f} KB")
