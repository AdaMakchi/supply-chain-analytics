# -*- coding: utf-8 -*-
"""
Genere le PDF du memoire GE : "Systeme de Prevision et d'Optimisation des Stocks"
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
# Page template : en-tete + numero de page
# ----------------------------------------------------------------------------
HEADER_TEXT = "Systeme de Prevision et d'Optimisation des Stocks - Memoire GE"


def header_footer(canvas, doc):
    canvas.saveState()
    # En-tete
    canvas.setFont(FONT_ITAL, 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(MARGIN, A4[1] - 1.3 * cm, HEADER_TEXT)
    canvas.setStrokeColor(colors.HexColor("#bbbbbb"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, A4[1] - 1.5 * cm, A4[0] - MARGIN, A4[1] - 1.5 * cm)
    # Pied : numero de page
    canvas.setFont(FONT_REG, 10)
    canvas.setFillColor(colors.HexColor("#444444"))
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"- {doc.page} -")
    canvas.restoreState()


def cover_page(canvas, doc):
    """Page de garde sans en-tete ni numero."""
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
                    "Insertion manuelle requise apres generation.", S_PLACEHOLDER)
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
    P("Ecole 89 - Deep Tech",
      ParagraphStyle("g_school", parent=S_SUB, fontSize=13,
                     fontName=FONT_BOLD, textColor=colors.HexColor("#1a3a5c"))),
    Spacer(1, 0.1 * cm),
    P("M1 Expert IT - IA et Big Data", S_SUB),
    Spacer(1, 0.9 * cm),
    P("Systeme de Prevision et d'Optimisation des Stocks", S_TITLE),
    Spacer(1, 0.2 * cm),
    P("Une approche Demand-Driven appuyee sur l'Intelligence Artificielle "
      "pour la prediction de la demande client chez GE",
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
    P("Annee universitaire 2025 - 2026",
      ParagraphStyle("g2", parent=S_SUB, fontSize=12)),
    PageBreak(),
]

# ---------- RESUME ----------
story += [
    H1("Resume"),
    P("Ce memoire presente la conception, l'implementation et la critique d'un systeme de "
      "prevision de la demande client base sur l'intelligence artificielle, applique aux donnees "
      "operationnelles de GE pour la periode 2021-2025. "
      "Le projet repond a une problematique industrielle concrete : depasser le pilotage "
      "traditionnel par objectifs de chiffre d'affaires, source recurrente de ruptures de stock "
      "et de surstocks, en adoptant une approche <i>Demand-Driven</i> structuree autour d'une "
      "double prediction (quantite et date de prochaine commande).", S_PN),
    P("La methodologie articule un pipeline complet couvrant la consolidation des donnees, "
      "l'analyse statistique, la modelisation et la mise en service operationnelle. La "
      "consolidation a produit un jeu de donnees de 349 390 lignes nettoyees et enrichies de "
      "35 colonnes incluant des sources exogenes (indice de production industrielle INSEE, "
      "donnees meteo, jours feries, calendrier scolaire), portees a 47 features modele apres "
      "ingenierie autoregressive. Les etudes statistiques ont confirme "
      "la presence de cycles budgetaires et meteorologiques et identifie sept variables "
      "exogenes Granger-causales sur la demande. Quatre familles de modeles ont ete confrontees "
      "(XGBoost, LightGBM, CatBoost, LSTM) avec optimisation Optuna et stacking Ridge. "
      "Le modele XGBoost v2 (47 features, 300 essais Optuna) atteint une MAE de 8.42 unites "
      "sur le test 2025 (1 - WAPE = 61.7 pourcents), depassant la cible <i>North Star</i> de "
      "60 pourcents. L'architecture <i>Stacking Ridge</i> (XGBoost + LightGBM Quantile + "
      "CatBoost) ameliore le RMSE et le R^2 (97.55 et 0.694), tandis qu'une baseline DDMRP "
      "academique sert de point de comparaison metier. Un dashboard Streamlit multipage a ete "
      "livre, integrant score de confiance composite, simulation what-if, backtest semaine "
      "par semaine et detection de derive (Population Stability Index).", S_PN),
    P("L'analyse critique discute honnetement les limites observees (precision a sept jours "
      "limitee a 25.5 pourcents pour la prediction de date, sous-performance sur la longue "
      "traine), documente la conformite RGPD du traitement et formalise une matrice de "
      "gouvernance humain-dans-la-boucle (HITL). Le memoire conclut sur une feuille de route "
      "de mise en production (FastAPI, PostgreSQL, MLflow, Evidently) et sur la valeur "
      "reproductible d'une approche academique honnete confrontee a un terrain industriel "
      "reel.", S_PN),
    Spacer(1, 0.3 * cm),
    P("<b>Mots-cles :</b> prevision de la demande, supply chain, XGBoost, LightGBM, CatBoost, "
      "stacking, regression quantile, LSTM, DDMRP, drift PSI, human-in-the-loop, RGPD, "
      "Streamlit.", S_PN),
    PageBreak(),
]

# ---------- ABSTRACT EN ----------
story += [
    H1("Abstract"),
    P("This master's thesis presents the design, implementation and critical evaluation of an "
      "AI-driven demand forecasting system applied to five years (2021-2025) of operational data "
      "from GE. The project addresses a concrete industrial "
      "problem: moving beyond traditional revenue-target driven planning, which is a recurring "
      "source of stockouts and overstocks, by adopting a Demand-Driven approach structured "
      "around two complementary predictions (quantity and date of next order).", S_PN),
    P("The methodology articulates an end-to-end pipeline spanning data consolidation, "
      "statistical analysis, modeling and operational deployment. The consolidation produced "
      "a 349,390-row cleaned dataset enriched with 35 columns including exogenous sources "
      "(industrial production index, weather data, public holidays, school calendar), "
      "expanded to 47 model features after autoregressive feature engineering. "
      "Statistical studies confirmed budgetary and weather cycles and identified seven "
      "Granger-causal exogenous drivers of demand. Four model families (XGBoost, LightGBM, "
      "CatBoost, LSTM) were compared with Optuna tuning and Ridge stacking. The XGBoost v2 "
      "model (47 features, 300 Optuna trials) reaches a test MAE of 8.42 units on 2025 "
      "(1 - WAPE = 61.7 percent), exceeding the 60 percent <i>North Star</i> target. "
      "A Stacking Ridge architecture (XGBoost + LightGBM Quantile + CatBoost) improves RMSE "
      "and R-squared (97.55 and 0.694), while a DDMRP academic baseline serves as a domain "
      "reference. An interactive Streamlit multipage dashboard was delivered with composite "
      "confidence scoring, what-if simulation, weekly backtest and Population Stability Index "
      "drift detection.", S_PN),
    P("The critical analysis honestly discusses observed limitations (date prediction accuracy "
      "of only 25.5 percent within +/-7 days, underperformance on the long tail), documents "
      "GDPR compliance and formalizes a human-in-the-loop governance matrix. The thesis "
      "concludes with a productionization roadmap (FastAPI, PostgreSQL, MLflow, Evidently) "
      "and reflects on the reproducible value of an academically honest approach confronted "
      "with a real industrial setting.", S_PN),
    Spacer(1, 0.3 * cm),
    P("<b>Keywords:</b> demand forecasting, supply chain, XGBoost, LightGBM, CatBoost, "
      "stacking, quantile regression, LSTM, DDMRP, PSI drift, human-in-the-loop, GDPR, "
      "Streamlit.", S_PN),
    PageBreak(),
]

# ---------- SOMMAIRE ----------
from reportlab.pdfbase.pdfmetrics import stringWidth as _string_width
import re as _re

_TOC_LINE_WIDTH_PT = 16 * cm  # largeur totale ligne sommaire (A4 - marges)
_TOC_FONT_SIZE = 12


def _toc(label, page, bold=False):
    """Ligne de sommaire : titre + points de conduite + page (numero collee a droite)."""
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
    _toc("Introduction generale", 7),
    Spacer(1, 0.2 * cm),
    _toc("Partie 1 - Contexte et Problematique", 9, bold=True),
    _toc("1.1 Presentation de GE et perimetre du memoire", 9),
    _toc("1.2 Limites de la gestion par objectifs de chiffre d'affaires", 11),
    _toc("1.3 Problematique et question de recherche", 13),
    _toc("1.4 Revue de litterature", 15),
    Spacer(1, 0.2 * cm),
    _toc("Partie 2 - Solution Technique", 18, bold=True),
    _toc("2.1 Methodologie Data Engineering", 18),
    _toc("2.2 Resultats des etudes statistiques", 21),
    _toc("2.3 Architecture et performances des modeles IA", 28),
    _toc("2.4 Presentation du dashboard Human-in-the-loop", 35),
    Spacer(1, 0.2 * cm),
    _toc("Partie 3 - Analyse Critique", 43, bold=True),
    _toc("3.1 Comparaison IA versus intuition commerciale", 43),
    _toc("3.2 Limites du modele", 44),
    _toc("3.3 Conformite RGPD et ethique du traitement", 46),
    _toc("3.4 Importance de la validation humaine (Human-in-the-loop)", 49),
    _toc("3.5 Perspectives d'amelioration et de mise en production", 50),
    _toc("3.6 Conclusion generale", 52),
    Spacer(1, 0.2 * cm),
    _toc("Bibliographie", 54),
    _toc("Annexes", 56),
    PageBreak(),
]

# ---------- LISTES FIGURES / TABLEAUX ----------
story += [
    H2("Liste des figures"),
    P("Figure 1 - Decomposition STL globale de la demande 2021-2025", S_PN),
    P("Figure 2 - Decomposition STL par famille d'article", S_PN),
    P("Figure 3 - Cycles budgetaires clients (pics de fin de trimestre)", S_PN),
    P("Figure 4 - Cycles meteorologiques et impact sur la demande", S_PN),
    P("Figure 5 - Matrice de correlation de Pearson", S_PN),
    P("Figure 6 - P-values du test de causalite de Granger", S_PN),
    P("Figure 7 - Distribution de la cible (qte_demandee) avant et apres log1p", S_PN),
    P("Figure 8 - Auto-correlation (ACF) et partial ACF (PACF)", S_PN),
    P("Figure 9 - Split temporel train / val / test", S_PN),
    P("Figure 10 - Feature importance du modele XGBoost v2", S_PN),
    P("Figure 11 - Capture dashboard : page Gestion des Donnees", S_PN),
    P("Figure 12 - Capture dashboard : page Intelligence Artificielle", S_PN),
    P("Figure 13 - Capture dashboard : page Previsions de Ventes (tableau et badges)", S_PN),
    P("Figure 14 - Capture dashboard : page Previsions (graphique pred vs reel)", S_PN),
    P("Figure 15 - Capture dashboard : page Previsions (simulation what-if)", S_PN),
    P("Figure 16 - Capture dashboard : page Analyse", S_PN),
    P("Figure 17 - Capture dashboard : page Drift Detection", S_PN),
    P("Figure 18 - Capture dashboard : page Backtest interactif", S_PN),
    P("Figure 19 - Capture dashboard : page d'accueil", S_PN),
    Spacer(1, 0.6 * cm),
    H2("Liste des tableaux"),
    P("Tableau 1 - Synthese de la qualite des donnees apres nettoyage", S_PN),
    P("Tableau 2 - Variables exogenes Granger-causales", S_PN),
    P("Tableau 3 - Comparaison des modeles de premiere generation (test 2025)", S_PN),
    P("Tableau 4 - Performance LSTM time-to-event", S_PN),
    P("Tableau 5 - Benchmark complet des architectures (XGBoost v2, LightGBM Quantile, "
      "CatBoost, Stacking Ridge, DDMRP)", S_PN),
    P("Tableau 6 - Comparaison IA vs DDMRP sur articles strategiques", S_PN),
    P("Tableau 7 - PSI des features critiques sur le test 2025", S_PN),
    P("Tableau 8 - Matrice de gouvernance Human-in-the-loop", S_PN),
    P("Tableau 9 - Registre simplifie des traitements (RGPD)", S_PN),
    PageBreak(),
]

# ============================================================================
# INTRODUCTION GENERALE
# ============================================================================
story += [
    H1("Introduction generale"),
    P("Les chaines d'approvisionnement industrielles ont ete soumises, depuis la crise sanitaire "
      "de 2020 et les tensions geopolitiques qui ont suivi, a une pression sans precedent sur "
      "leur capacite a anticiper la demande client. Dans ce contexte, les approches traditionnelles "
      "de planification basees sur l'extrapolation lineaire d'objectifs commerciaux montrent "
      "leurs limites : ruptures de stock qui erodent la satisfaction client, surstocks qui "
      "immobilisent un capital significatif, decisions de reapprovisionnement reactives plutot "
      "qu'anticipatives.", S_PN),
    P("Le present memoire s'inscrit dans cette problematique a partir d'un terrain industriel "
      "concret : la chaine d'approvisionnement de l'entreprise GE, commanditaire de la "
      "mission. Le materiau principal est constitue d'un historique de cinq annees (2021-2025) "
      "de commandes et de livraisons clients, soit pres de 350 000 lignes de transactions, "
      "complete par des sources exogenes publiques (indice de production industrielle de "
      "l'INSEE, donnees meteorologiques via Open-Meteo, calendrier des jours feries).", S_PN),
    P("L'objectif central est de demontrer qu'une approche <i>Demand-Driven</i> appuyee sur "
      "l'intelligence artificielle peut produire une prediction operationnelle exploitable de "
      "la demande client - en quantite ET en date - et offrir ainsi un appui scientifique au "
      "planificateur sans le remplacer. La cible declaree au lancement du projet, une precision "
      "moyenne superieure a 60 pourcents (mesuree par 1 - WAPE), sert de fil conducteur. "
      "Comme nous le verrons, cet objectif est atteint sur la quantite demandee "
      "(61.7 pourcents constates sur le jeu de test 2025 avec le modele XGBoost v2), tandis "
      "que la prediction de date par LSTM reste insuffisante (25.5 pourcents +/-7 jours). "
      "Cette dualite des resultats - reussite sur la quantite, echec relatif sur la date - "
      "constitue un materiau methodologique riche : elle obligera a documenter les limites du "
      "modele de date, a expliciter les biais structurels du jeu de donnees, et a formaliser "
      "une gouvernance hybride associant systematiquement l'expertise humaine.", S_PN),
    P("Le memoire est organise en trois parties. La premiere partie pose le contexte industriel "
      "de GE, decrit les limites de la gestion par objectifs commerciaux, formule la "
      "problematique et restitue l'etat de l'art sur la prevision de la demande (DDMRP, gradient "
      "boosting, deep learning temporel, regression quantile, Human-in-the-Loop). La deuxieme "
      "partie deploie la solution technique : pipeline de donnees, etudes statistiques, "
      "comparaison de quatre familles de modeles avec optimisation et stacking, et description "
      "du dashboard interactif livre. La troisieme partie ouvre l'analyse critique - "
      "comparaison de l'IA aux pratiques actuelles, discussion des limites, conformite RGPD, "
      "matrice de gouvernance humain-dans-la-boucle, perspectives de mise en production - et "
      "conclut sur l'apport de cette demarche academique au terrain industriel.", S_PN),
    PageBreak(),
]

# ============================================================================
# PARTIE 1
# ============================================================================
story += [
    Spacer(1, 6 * cm),
    P("PARTIE 1", ParagraphStyle("part", parent=S_TITLE, fontSize=20)),
    Spacer(1, 0.4 * cm),
    P("Contexte et Problematique", S_TITLE),
    PageBreak(),
]

# ---------- 1.1 GE ----------
story += [
    H1("1.1 Presentation de GE et perimetre du mémoire"),
    H2("1.1.1 L'entreprise GE et la mission confiee"),
    P("L'entreprise GE est le commanditaire de la mission ayant donne lieu au present memoire. "
      "Conformement aux termes de la mission, le perimetre etudie est circonscrit a la chaine "
      "d'approvisionnement de l'entreprise et aux donnees operationnelles de commande et de "
      "livraison clients sur la periode 2021-2025. Le presente document ne formule aucune "
      "affirmation supplementaire sur l'activite, le secteur, l'organisation ou la strategie de "
      "GE au-dela de ce qui se deduit directement des donnees etudiees ou du cahier des charges "
      "transmis a l'etudiant.", S_PN),
    P("Le constat de depart documente dans le brief de mission est clair : la gestion actuelle "
      "des stocks s'appuie sur des objectifs de chiffre d'affaires negocies, et ce mode de "
      "pilotage genere des ruptures et des surstocks recurrents. La section 1.2 du present "
      "memoire detaillera les limites structurelles de cette approche ; la presente section se "
      "borne a decrire le materiau exploite.", S_PN),

    H2("1.1.2 Materiau exploite : structure du dataset"),
    P("Le materiau analytique mis a disposition par GE est un export consolide des commandes "
      "et livraisons clients couvrant la periode 2021 a 2025. Apres consolidation et nettoyage "
      "(detail en section 2.1), le jeu final comprend 349 390 lignes de transactions. Chaque "
      "ligne represente une commande individuelle d'un client sur un article a une date "
      "donnee. Les variables exploitees, telles qu'identifiees dans le brief de mission et "
      "verifiees dans les fichiers sources, sont les suivantes :", S_PN),
    *bullets([
        "<b>Identifiants</b> : <i>code_article</i>, <i>code_client</i>, "
        "<i>num_commande</i>.",
        "<b>Cibles a predire</b> : <i>qte_demandee</i> (quantite commandee), "
        "<i>date_livraison_demandee</i> (date a laquelle le client souhaite etre livre).",
        "<b>Variables descriptives client</b> : <i>famille_activite_client</i>, "
        "<i>pays</i>, <i>devise</i>, <i>type_activite</i>.",
        "<b>Variables descriptives article</b> : <i>famille_activite_article</i>, "
        "<i>segment</i>, <i>prix</i>.",
        "<b>Variables de contexte</b> : <i>qte_livree</i> (utilisee pour evaluer l'ecart "
        "entre demande exprimee et demande effectivement servie), <i>statut</i> de la "
        "commande, dates d'enregistrement et de livraison effective.",
    ]),
    P("Le contenu metier specifique des modalites (par exemple le sens precis des libelles de "
      "<i>famille_activite_article</i> ou des <i>segment</i> du catalogue) n'est pas decrit "
      "dans ce memoire : ces informations relevent du detail operationnel interne de GE et ne "
      "sont pas necessaires a la conduite des analyses statistiques presentees, qui reposent "
      "sur la structure du jeu de donnees et non sur l'interpretation semantique des "
      "modalites.", S_PN),

    H2("1.1.3 Perimetre et exclusions explicites"),
    P("Le perimetre temporel couvre exclusivement les commandes et livraisons de 2021 a 2025 "
      "inclus. Sont en revanche en dehors du perimetre, par indisponibilite ou par choix "
      "methodologique : les operations promotionnelles, les retours clients, les transferts "
      "internes inter-sites, et toute affirmation qualitative sur les pratiques commerciales "
      "de GE qui ne se deduirait pas directement du jeu de donnees fourni. L'utilisateur cible "
      "du systeme propose est le planificateur supply chain de GE, conformement au scenario "
      "Human-in-the-loop defini dans le brief de mission (section 5 du cahier des charges).", S_PN),
    PageBreak(),
]

# ---------- 1.2 Limites CA ----------
story += [
    H1("1.2 Limites de la gestion par objectifs de chiffre d'affaires"),
    H2("1.2.1 Le pilotage par objectifs commerciaux"),
    P("Le brief de mission communique par GE indique explicitement que la gestion des stocks "
      "s'appuie sur des objectifs de chiffre d'affaires, et que ce mode de pilotage genere "
      "des ruptures et des surstocks recurrents. Sans documenter ici le detail des processus "
      "internes de planification de GE, on peut identifier trois limites structurelles "
      "generiques d'une planification orientee CA, documentees dans la litterature supply "
      "chain (Hyndman et Athanasopoulos, 2018) et coherentes avec le constat opere par "
      "l'entreprise.", S_PN),
    P("Premierement, ce type de pilotage confond l'objectif (volume cible) et la prevision "
      "(volume probable), ce qui introduit un biais d'optimisme systematique. Deuxiemement, "
      "il est par construction insensible aux dynamiques infra-mensuelles : un objectif "
      "mensuel ne dit rien des pics de fin de semaine ou des creux post-vacances mis en "
      "evidence dans l'analyse exploratoire (sections 2.2.3 et 2.2.4). Troisiemement, il "
      "ne capte pas les facteurs exogenes (cycles macro-economiques, conditions "
      "meteorologiques, calendrier des jours feries) qui modulent la demande reelle "
      "independamment des intentions commerciales, comme le confirmera le test de causalite "
      "de Granger conduit en section 2.2.6.", S_PN),

    H2("1.2.2 Phenomenes de rupture et de surstock observables dans les donnees"),
    P("Le brief identifie deux phenomenes recurrents que le pilotage par objectifs CA ne "
      "previent pas : les ruptures et les surstocks. Le jeu de donnees fourni permet d'en "
      "objectiver le premier par comparaison directe entre la <i>quantite demandee</i> et "
      "la <i>quantite livree</i> : lorsque le ratio livraison / demande descend sous "
      "100 pourcents, on est en presence d'une rupture, totale ou partielle. Le surstock "
      "n'est pas directement observable dans le seul historique de commandes (il faudrait "
      "un releve de stock que ce dataset ne contient pas), mais sa manifestation indirecte - "
      "ecart entre demande anticipee et demande effective - est neanmoins mesurable a travers "
      "les biais de prediction etudies en section 3.1.", S_PN),
    P("Au-dela de la mesure brute, ces deux phenomenes ont un cout economique reconnu dans "
      "la litterature supply chain : pour la rupture, perte de marge sur la vente non "
      "realisee et erosion de la confiance commerciale ; pour le surstock, immobilisation "
      "de tresorerie, couts de stockage et risque d'obsolescence. Une approche predictive "
      "qui reduit l'amplitude moyenne de ces ecarts apporte donc une valeur economique "
      "directe, dont la quantification precise relevera de la direction supply chain de GE.", S_PN),

    H2("1.2.3 Asymetrie des couts et metrique business"),
    P("La litterature operationnelle souligne que le cout d'une unite manquante au moment "
      "ou le client en a besoin est generalement superieur au cout d'une unite excedentaire "
      "stockee. Cette asymetrie a une consequence methodologique directe : la qualite d'une "
      "prevision doit pouvoir etre evaluee avec une fonction de cout asymetrique, et non "
      "avec la seule erreur absolue moyenne (MAE) classique. Le memoire integre donc, dans "
      "le dashboard <i>Backtest 2025</i> (section 2.4.7), une <i>fonction de cout business</i> "
      "configurable definie par <i>cost = alpha * max(0, y - y_pred) + beta * "
      "max(0, y_pred - y)</i>, ou alpha et beta sont parametrables par l'utilisateur ; les "
      "valeurs effectives a retenir en production relevent d'un arbitrage de GE et ne sont "
      "pas fixees dans le present document.", S_PN),
    PageBreak(),
]

# ---------- 1.3 Probleme ----------
story += [
    H1("1.3 Problematique et question de recherche"),
    H2("1.3.1 Enonce de la problematique"),
    P("La problematique centrale du memoire est formulee de la maniere suivante :", S_PN),
    P("<i>Comment une approche Demand-Driven s'appuyant sur l'intelligence artificielle peut-elle "
      "predire la demande client reelle - en quantite et en date - pour optimiser la chaine "
      "d'approvisionnement d'un distributeur d'equipements electriques industriels, tout en "
      "preservant le role decisionnel de l'expertise humaine ?</i>", S_QUOTE),
    P("Cette formulation contient trois engagements methodologiques explicites. Le premier est "
      "le passage d'un pilotage par objectifs a un pilotage par demande effective predite. Le "
      "deuxieme est la double prediction quantite + date, qui releve de deux familles de "
      "problemes statistiques distincts (regression numerique pour la quantite, analyse de "
      "survie ou prevision de serie pour la date). Le troisieme est l'integration explicite "
      "d'une boucle humain-dans-la-boucle : le systeme n'a pas vocation a automatiser "
      "integralement la decision, mais a fournir au planificateur une recommandation "
      "transparente et interpretable.", S_PN),

    H2("1.3.2 Sous-questions operationnelles et hypotheses"),
    P("De cette problematique decoulent quatre sous-questions operationnelles :", S_PN),
    *bullets([
        "Q1 : Quelles variables internes et exogenes contribuent significativement a la "
        "prediction de la demande sur le perimetre etudie ?",
        "Q2 : Quel modele predictif maximise la precision sur la quantite demandee tout en "
        "restant interpretable pour un planificateur metier ?",
        "Q3 : Le probleme de prediction de la date prochaine commande est-il aborde plus "
        "efficacement par un reseau recurrent (LSTM) ou par une formulation alternative "
        "(analyse de survie, Prophet par couple) ?",
        "Q4 : Comment articuler le modele predictif et l'expertise du planificateur dans une "
        "matrice de gouvernance operationnelle ?",
    ]),
    P("Les hypotheses testees sont coherentes avec la litterature recente. H1 : l'ajout de "
      "variables exogenes (indice de production industrielle, meteo) ameliore significativement "
      "la prediction par rapport aux variables internes seules. H2 : les modeles d'ensemble "
      "de type gradient boosting (XGBoost, LightGBM, CatBoost) surpassent les modeles lineaires "
      "et un reseau neuronal generique sur ce type de donnees tabulaires bruitees. H3 : la "
      "transformation log1p de la cible reduit suffisamment l'asymetrie de la distribution "
      "pour stabiliser l'apprentissage. H4 : un dashboard interactif assorti d'un score de "
      "confiance ameliore l'adoption operationnelle par rapport a une simple sortie numerique.", S_PN),

    H2("1.3.3 Perimetre, exclusions et North Star"),
    P("Le perimetre temporel couvre les commandes et livraisons des annees 2021 a 2025 inclus, "
      "decoupees en train (2021-2023), validation (2024) et test (2025) selon un split "
      "strictement temporel pour eviter toute fuite d'information future. Sont explicitement "
      "exclus du perimetre : les operations promotionnelles ponctuelles (donnees non "
      "disponibles), les retours clients, les transferts inter-sites internes, et les commandes "
      "exceptionnelles liees a des projets de plus de cinq millions d'euros. La cible <i>North "
      "Star</i> declaree en debut de projet, une precision moyenne superieure a 60 pourcents, "
      "a constitue le repere d'amelioration tout au long du developpement.", S_PN),
    PageBreak(),
]

# ---------- 1.4 Litterature ----------
story += [
    H1("1.4 Revue de litterature"),
    H2("1.4.1 De la prevision statistique classique au gradient boosting"),
    P("La litterature sur la prevision de la demande s'est structuree en trois grandes vagues. "
      "La premiere, anteriorement aux annees 2010, repose sur les methodes statistiques "
      "classiques : moyennes mobiles, lissages exponentiels de la famille Holt-Winters, "
      "modeles ARIMA et SARIMA. Ces methodes restent une reference forte sur les series "
      "stables et lisses, et constituent la baseline traditionnelle dans la communaute supply "
      "chain (Hyndman et Athanasopoulos, 2018). Pour les demandes intermittentes - tres "
      "frequentes dans la longue traine d'un catalogue industriel - les methodes specialisees "
      "comme Croston (1972) et leurs raffinements (TSB, ADIDA) demeurent l'etat de l'art.", S_PN),
    P("La seconde vague, deployee massivement a partir de la decennie 2010, introduit les "
      "modeles d'ensemble par gradient boosting. XGBoost (Chen et Guestrin, 2016) a domine les "
      "competitions Kaggle sur donnees tabulaires pendant pres d'une decennie, suivi par "
      "LightGBM (Ke et al., 2017) plus efficient sur les volumetries elevees et CatBoost "
      "(Prokhorenkova et al., 2018) qui gere nativement les variables categorielles. Le rapport "
      "M5 Forecasting Competition (Makridakis et al., 2022) a confirme experimentalement la "
      "superiorite empirique de cette famille de modeles sur les problemes de prevision retail "
      "et supply chain, devant les approches deep learning classiques sur la majorite des "
      "configurations testees.", S_PN),

    H2("1.4.2 Deep learning temporel et formulations alternatives"),
    P("La troisieme vague repose sur les architectures de deep learning specifiques aux series "
      "temporelles. Les reseaux recurrents de type LSTM (Hochreiter et Schmidhuber, 1997) ont "
      "longtemps constitue le standard pour la modelisation sequentielle, avant d'etre "
      "concurrences par les architectures convolutives causales (Bai et al., 2018), les "
      "Transformers temporels comme Informer (Zhou et al., 2021) et le <i>Temporal Fusion "
      "Transformer</i> (Lim et al., 2021), qui combinent attention multi-tete et "
      "interpretabilite. Pour les problemes de prediction de date - reformulables en "
      "<i>time-to-event</i> - les techniques d'analyse de survie (Cox proportional hazards, "
      "Random Survival Forests, DeepSurv) offrent un cadre statistique rigoureux qui contourne "
      "la difficulte classique des modeles de regression sur des delais censures.", S_PN),
    P("La litterature recente insiste egalement sur l'importance de la quantification de "
      "l'incertitude. Les modeles de regression quantile (Koenker et Bassett, 1978 ; "
      "implementation LightGBM <i>objective='quantile'</i>) permettent de produire des "
      "intervalles de prediction P10/P50/P90 plus honnetes qu'un simple intervalle gaussien "
      "calcule sur les residus, et plus exploitables operationnellement qu'un score de "
      "confiance ad hoc. Cette approche est integree au present projet comme indicateur de "
      "robustesse propose au planificateur.", S_PN),

    H2("1.4.3 Demand-Driven MRP : le cadre operationnel de reference"),
    P("Le cadre conceptuel <i>Demand-Driven Material Requirements Planning</i> (DDMRP), "
      "formalise par Ptak et Smith (2016) sur la base des travaux pionniers de Goldratt sur la "
      "theorie des contraintes, structure une alternative operationnelle au MRP classique "
      "deconnecte de la demande reelle. DDMRP s'articule autour de cinq composantes : "
      "<i>Strategic Inventory Positioning</i> (placement strategique des stocks), "
      "<i>Buffer Profiles and Levels</i> (dimensionnement de buffers vert/jaune/rouge par "
      "article), <i>Dynamic Adjustments</i> (ajustement des buffers selon la saisonnalite), "
      "<i>Demand-Driven Planning</i> (declenchement de reapprovisionnement sur la base du "
      "<i>Net Flow Position</i>), et <i>Visible and Collaborative Execution</i> (suivi visuel "
      "des etats critiques).", S_PN),
    P("Cette grille de lecture est essentielle pour positionner academiquement le present "
      "travail. Une approche IA pure sans ancrage DDMRP risque de produire un modele "
      "statistiquement performant mais operationnellement deconnecte des regles metier "
      "etablies. Inversement, une approche DDMRP pure n'exploite pas la richesse des variables "
      "exogenes desormais disponibles a faible cout. Le memoire propose une articulation "
      "hybride : un modele IA produit une prediction de demande qui alimente le calcul du "
      "<i>Net Flow Position</i> DDMRP, lui-meme arbitre par le planificateur. La comparaison "
      "directe entre IA pure et DDMRP de reference est restituee en section 2.3.3.", S_PN),

    H2("1.4.4 Human-in-the-loop et IA responsable"),
    P("La litterature recente sur le deploiement industriel de l'IA insiste sur la necessite "
      "d'integrer l'expertise humaine dans la boucle de decision, particulierement pour les "
      "domaines a fort enjeu economique. L'approche <i>Human-in-the-Loop Machine Learning</i> "
      "(Wu et al., 2022) propose plusieurs patrons d'integration, dont l'arbitrage par seuil "
      "de confiance, l'apprentissage actif sur les decisions correctives et la documentation "
      "systematique via des <i>model cards</i> (Mitchell et al., 2019). Le present projet "
      "deploie une matrice de gouvernance a trois niveaux (vert : automatisation, orange : "
      "revue rapide, rouge : decision humaine obligatoire) coherente avec ces principes et "
      "compatible avec les exigences emergentes de l'AI Act europeen sur les systemes a risque "
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
    H1("2.1 Methodologie Data Engineering"),
    H2("2.1.1 Audit des sources et qualite des donnees brutes"),
    P("Le materiau brut consolide pour ce memoire est constitue de deux exports operationnels "
      "fournis par GE : un export des commandes clients de 2021 a 2025 et un export "
      "des livraisons effectivement realisees sur la meme periode. Les deux fichiers, au format "
      "Excel a l'origine, ont d'abord ete convertis en CSV puis charges en Python via "
      "<i>pandas</i> pour traitement. L'audit initial a porte sur quatre dimensions : "
      "completude (taux de valeurs nulles par colonne), unicite (detection des doublons sur "
      "les cles fonctionnelles), validite (verification des plages de valeurs numeriques et "
      "des formats de dates), et coherence inter-fichiers (rapprochement commande/livraison).", S_PN),
    P("Les principaux defauts identifies a ce stade ont ete les suivants : presence de lignes "
      "de commande sans correspondance livraison (commandes annulees ou differees), heterogeneite "
      "des formats de date selon la source (mix DD/MM/YYYY et YYYY-MM-DD), codification "
      "incoherente des references articles entre certaines periodes (renumerotation partielle "
      "en 2023), et presence residuelle de lignes de test informatique inserees lors des "
      "operations de maintenance ERP. Ces defauts ont fait l'objet d'un nettoyage trace dans "
      "le notebook <i>01_data_cleaning.ipynb</i>.", S_PN),

    H2("2.1.2 Pipeline de nettoyage et imputation"),
    P("Le pipeline de nettoyage a ete implemente comme une succession d'etapes idempotentes "
      "documentees pour garantir la reproductibilite scientifique. Chaque etape consigne le "
      "nombre de lignes avant et apres operation et la raison de chaque suppression : "
      "deduplication exacte, suppression des lignes de test, harmonisation des formats de "
      "date, imputation des valeurs manquantes par la mediane pour les variables numeriques "
      "et par la modalite la plus frequente pour les variables categorielles dont le taux de "
      "nullite est inferieur a 5 pourcents, suppression des lignes dont les variables critiques "
      "(code_client, code_article, qte_demandee, date_cmd) sont manquantes.", S_PN),
    P("Le dataset consolide final, sauvegarde au format Parquet sous "
      "<i>data/processed/dataset_ml_final.parquet</i>, comporte 349 390 lignes pour 24 colonnes. "
      "Le taux de rapprochement commande/livraison atteint 94.2 pourcents, valeur jugee "
      "satisfaisante pour la suite des analyses. Le tableau ci-dessous synthese la qualite "
      "des donnees apres nettoyage.", S_PN),

    table([
        ["Indicateur", "Avant nettoyage", "Apres nettoyage"],
        ["Lignes commande", "362 480", "349 390"],
        ["Lignes livraison", "338 215", "329 174"],
        ["Taux de rapprochement", "85.3 %", "94.2 %"],
        ["Valeurs nulles (qte_demandee)", "1.8 %", "0.0 %"],
        ["Doublons", "3 211", "0"],
        ["Lignes de test ERP", "412", "0"],
        ["Periode couverte", "2021-01 a 2025-12", "2021-01 a 2025-12"],
    ], col_widths=[6.5 * cm, 4.5 * cm, 4.5 * cm]),
    P("<b>Tableau 1</b> - Synthese de la qualite des donnees avant et apres pipeline de "
      "nettoyage (notebook <i>01_data_cleaning.ipynb</i>).", S_CAPTION),

    H2("2.1.3 Feature engineering et enrichissement exogene"),
    P("La phase d'enrichissement, conduite dans le notebook <i>02_statistical_study.ipynb</i>, "
      "a augmente le jeu de donnees de 24 a 35 colonnes en integrant des sources externes "
      "publiques. Trois categories d'enrichissement ont ete realisees : enrichissement "
      "temporel par decomposition fine de chaque date (annee, mois, trimestre, semaine ISO, "
      "jour de la semaine, indicateurs de fin de mois et de fin de trimestre), enrichissement "
      "calendaire par integration des jours feries francais (via la librairie "
      "<i>workalendar</i>) et des periodes de vacances scolaires (zones A/B/C agregees), "
      "et enrichissement exogene par l'indice de production industrielle (IPI) de l'INSEE et "
      "par les donnees meteorologiques quotidiennes (temperatures, pluviometrie, vitesse de "
      "vent maximale) interrogees via l'API publique Open-Meteo sur les coordonnees du "
      "principal centre de distribution.", S_PN),
    P("Vingt-huit features finales ont ete retenues apres une selection iterative combinant "
      "analyse univariee, calcul du facteur d'inflation de la variance (VIF) pour traiter la "
      "colinearite, et tests bivaries par groupes pour les variables categorielles. Les "
      "variables categorielles a forte cardinalite (code_client, code_article) ont ete encodees "
      "par <i>frequency encoding</i> plutot que par one-hot, choix justifie par la dimension "
      "elevee (plusieurs milliers de modalites) et l'efficience des algorithmes de gradient "
      "boosting sur des entrees compactes.", S_PN),

    H2("2.1.4 Strategie de split temporel et prevention du data leakage"),
    P("Un point methodologique critique pour la validite des conclusions est la strategie de "
      "split. Tout split aleatoire est ici prohibe, car il introduirait une fuite d'information "
      "future dans le jeu d'entrainement (par exemple, une commande de fin 2025 utilisee pour "
      "predire une commande de debut 2023). Le split adopte est strictement temporel : "
      "2021-2023 pour l'entrainement (210 641 lignes, 60.3 pourcents), 2024 pour la validation "
      "(70 871 lignes, 20.3 pourcents) et 2025 pour le test final (66 174 lignes, 18.9 "
      "pourcents).", S_PN),
    P("Toutes les statistiques d'agregation servant a generer des features (frequences, "
      "moyennes historiques, lags) sont calculees exclusivement sur le set d'entrainement, "
      "puis projetees sur validation et test sans recalcul global. Cette discipline, parfois "
      "negligee dans les notebooks exploratoires, conditionne la validite des chiffres reportes "
      "et permet d'eviter la situation classique de modeles surperformants en validation mais "
      "decevants en production.", S_PN),

    fig("eda_split_temporel.png",
        "Figure 9 - Split temporel train (2021-2023) / val (2024) / test (2025). "
        "Source : notebook 02bis_eda_dataset_enrichi.ipynb."),
    PageBreak(),
]

# ---------- 2.2 Etudes statistiques ----------
story += [
    H1("2.2 Resultats des etudes statistiques"),
    H2("2.2.1 Decomposition de la serie agregee"),
    P("La premiere analyse a porte sur la serie de demande agregee a la maille mensuelle, tous "
      "articles et tous clients confondus. La decomposition STL (Seasonal-Trend decomposition "
      "using Loess) implementee dans <i>statsmodels</i> a mis en evidence trois composantes "
      "stables : une tendance de fond legerement croissante sur la periode 2021-2025, une "
      "composante saisonniere annuelle marquee par un creux estival systematique (juillet-aout) "
      "et un pic d'automne (septembre-novembre), et un residu de variabilite eleve traduisant "
      "la diversite intra-mensuelle de la demande client.", S_PN),
    P("La figure 1 ci-dessous restitue cette decomposition. Le pic d'automne represente en "
      "moyenne 30 pourcents de volume supplementaire par rapport au creux estival, "
      "amplitude tres significative qui justifie a elle seule l'attention portee aux features "
      "temporelles. Le residu, bien qu'eleve en valeur absolue, ne presente pas de structure "
      "manifeste apres decomposition, ce qui suggere qu'une part substantielle de la "
      "variabilite restante est imputable a des facteurs exogenes (clients, articles, "
      "evenements exterieurs) non encore introduits dans la decomposition.", S_PN),

    fig("decomposition_globale.png",
        "Figure 1 - Decomposition STL de la demande mensuelle agregee 2021-2025. "
        "De haut en bas : serie observee, tendance, composante saisonniere annuelle, residu."),

    H2("2.2.2 Decomposition par famille d'article"),
    P("La decomposition globale masque des dynamiques sensiblement differentes selon les "
      "valeurs de la variable <i>famille_activite_article</i>. La meme decomposition STL "
      "appliquee separement aux principales familles du catalogue fait apparaitre deux "
      "profils contrastes : un premier profil presente une amplitude saisonniere marquee, "
      "synchrone avec un calendrier annuel net, tandis qu'un second profil presente une "
      "demande plus reguliere, peu sensible aux cycles annuels. Le contenu metier specifique "
      "des familles concernees n'est pas detaille ici, conformement au perimetre defini en "
      "section 1.1.2 ; l'observation reste exploitable a partir de la seule structure des "
      "donnees. Cette dichotomie a une implication operationnelle directe : un modele "
      "generaliste unique sous-performera systematiquement sur l'une ou l'autre population, "
      "argument qui motivera l'enrichissement autoregressif au niveau du couple, du client "
      "et de l'article presente en section 2.3.4.", S_PN),

    fig("decomposition_par_famille.png",
        "Figure 2 - Decompositions STL comparees par famille d'article."),

    H2("2.2.3 Cycles budgetaires clients"),
    P("L'analyse des dates de commande agregees a la maille hebdomadaire fait ressortir un "
      "pattern budgetaire net : la derniere semaine de chaque trimestre concentre regulierement "
      "un volume superieur de 15 a 25 pourcents a la moyenne du trimestre. Ce phenomene, "
      "documente dans la litterature comme effet d'absorption du budget restant en fin de "
      "periode budgetaire, se manifeste de maniere heterogene selon les segments de "
      "clientele identifies dans la variable <i>famille_activite_client</i> du jeu de donnees, "
      "sans qu'une interpretation metier supplementaire ne soit avancee ici. La feature "
      "binaire <i>est_fin_mois_cmd</i> capte partiellement ce signal mais reste insuffisamment "
      "fine ; une amelioration possible serait l'ajout d'une feature <i>est_fin_trimestre</i> "
      "dediee.", S_PN),

    fig("cycles_budgetaires.png",
        "Figure 3 - Distribution hebdomadaire des commandes - mise en evidence des pics de "
        "fin de trimestre."),

    H2("2.2.4 Cycles meteorologiques"),
    P("Le couplage des donnees de commande avec les donnees meteorologiques Open-Meteo a "
      "permis de tester quantitativement l'hypothese d'une influence de la meteo sur la "
      "demande. Trois variables ont ete retenues : temperature minimale, pluviometrie cumulee "
      "journaliere et vitesse de vent maximale, associees a la <i>date_livraison_demandee</i> "
      "et non a la date d'enregistrement de la commande, afin de capter l'effet meteo a "
      "l'horizon d'execution plutot qu'a l'horizon de saisie.", S_PN),
    P("La correlation marginale entre meteo et quantite demandee reste faible (Pearson "
      "inferieur a 0.10 en valeur absolue pour les trois variables), mais l'analyse "
      "decomposee par famille d'article revele un effet legerement plus marque sur le "
      "profil saisonnier identifie en section 2.2.2 : une pluviometrie elevee la semaine "
      "precedant la date de livraison demandee y est associee a une legere baisse du "
      "volume effectif. Aucune interpretation metier specifique de ce signal n'est avancee "
      "au-dela de l'observation statistique brute.", S_PN),

    fig("cycles_meteo.png",
        "Figure 4 - Relations meteo / demande par famille d'article."),

    H2("2.2.5 Matrice de correlation et selection de variables"),
    P("La matrice de correlation de Pearson calculee sur l'ensemble des features numeriques "
      "et de la cible <i>qte_demandee</i> fournit une premiere lecture des dependances "
      "lineaires. Comme attendu, aucune feature seule n'explique massivement la cible : la "
      "correlation maximale, obtenue avec la frequence du couple client-article, atteint "
      "0.27, ce qui est coherent avec une cible eclatee a forte variance individuelle. La "
      "matrice a egalement guide l'elimination de variables fortement colineaires : "
      "<i>est_weekend_liv_dem</i> et <i>jour_semaine_liv_dem</i> presentent un VIF eleve et "
      "ont fait l'objet d'un arbitrage au profit de la seconde, plus informative.", S_PN),

    fig("matrice_correlation_pearson.png",
        "Figure 5 - Matrice de correlation de Pearson - features et cible."),

    H2("2.2.6 Test de causalite de Granger et features exogenes"),
    P("Le test de causalite de Granger a ete applique sur les sept variables exogenes "
      "candidates (IPI, variables meteo agregees a la semaine, jours feries) avec des lags de "
      "1 a 6 semaines. Les p-values obtenues, restituees figure 6, font apparaitre une "
      "causalite significative (p < 0.05) pour l'IPI au lag 1 et au lag 3, pour la temperature "
      "moyenne hebdomadaire au lag 2, et pour les jours feries sans decalage. Ces resultats "
      "justifient l'integration des features exogenes correspondantes dans le modele final, "
      "et auraient pu motiver l'ajout de versions laggees explicites (<i>ipi_valeur_lag1</i>, "
      "<i>ipi_valeur_lag3</i>) si le temps de developpement avait permis cet enrichissement "
      "supplementaire.", S_PN),

    fig("granger_pvalues.png",
        "Figure 6 - P-values du test de causalite de Granger entre variables exogenes "
        "candidates et demande hebdomadaire agregee."),

    table([
        ["Variable exogene", "Lag optimal", "p-value", "Significatif"],
        ["IPI INSEE", "1 semaine", "0.012", "Oui"],
        ["IPI INSEE", "3 semaines", "0.034", "Oui"],
        ["Temperature moyenne", "2 semaines", "0.041", "Oui"],
        ["Pluviometrie cumulee", "1 semaine", "0.118", "Marginal"],
        ["Vent maximal", "1 semaine", "0.234", "Non"],
        ["Jour ferie", "0 (immediat)", "0.008", "Oui"],
        ["Vacances scolaires", "0 (immediat)", "0.067", "Marginal"],
    ], col_widths=[5 * cm, 3 * cm, 2.5 * cm, 3 * cm]),
    P("<b>Tableau 2</b> - Variables exogenes et significativite Granger sur la demande "
      "hebdomadaire agregee. Source : notebook <i>02_statistical_study.ipynb</i>.", S_CAPTION),

    H2("2.2.7 Stationnarite, distribution de la cible et acf"),
    P("La distribution de la cible <i>qte_demandee</i> presente une asymetrie tres marquee "
      "(skewness = 80.73) et une queue lourde a droite caracteristique des distributions de "
      "type demande client industrielle. La transformation <i>log1p</i> (logarithme de "
      "1 + x) ramene cette asymetrie a 1.44, valeur acceptable pour les modeles de regression "
      "sur cible continue. Cette transformation est appliquee systematiquement en entree des "
      "modeles, l'inversion <i>expm1</i> etant operee avant tout calcul de metrique pour "
      "garantir la comparabilite des resultats.", S_PN),

    fig("eda_target_distribution.png",
        "Figure 7 - Distribution de la cible avant (gauche) et apres (droite) "
        "transformation log1p."),

    fig("eda_acf_pacf.png",
        "Figure 8 - ACF et PACF de la demande hebdomadaire agregee - structure "
        "autoregressive faible mais presente aux lags 1 et 4."),
    PageBreak(),
]

# ---------- 2.3 Modeles ----------
story += [
    H1("2.3 Architecture et performances des modeles IA"),
    P("Cette section detaille les modeles entraines, restitue leurs performances comparees "
      "sur le jeu de test 2025 (jamais vu pendant l'entrainement ni la selection de modele), "
      "et discute les choix faits aux moments cles. Le code source des entrainements est "
      "reparti dans les notebooks <i>03_model_training.ipynb</i> (premiere generation de "
      "modeles), <i>04_feature_engineering_lags.ipynb</i> (enrichissement autoregressif) et "
      "<i>10_catboost_stacking.ipynb</i> (architectures avancees). Les modeles serialises sont "
      "disponibles dans le dossier <i>models/</i>.", S_PN),

    H2("2.3.1 Baseline historique et baseline naive"),
    P("Toute affirmation de performance d'un modele machine learning n'a de sens que par "
      "comparaison a une baseline credible. Deux baselines sont utilisees ici. La baseline "
      "<i>naive</i> consiste a predire pour chaque commande de test la moyenne globale de la "
      "quantite demandee sur le set d'entrainement (ignorance maximale). La baseline "
      "<i>historique</i>, plus exigeante, predit pour chaque couple (client, article) la "
      "moyenne historique observee de ce couple sur 2021-2023, et la moyenne globale en "
      "fallback pour les couples inconnus. Sur le test 2025, la baseline historique atteint "
      "une MAE de 13.04 et un RMSE de 145.11. Tout modele apportant une valeur ajoutee "
      "scientifique doit dominer cette baseline statistiquement, idealement de plusieurs "
      "points.", S_PN),

    H2("2.3.2 Premiere generation de modeles - Regression sur 28 features"),
    P("La premiere generation de modeles vise la prediction directe de la quantite demandee "
      "(<i>qte_demandee</i>) par chaque commande individuelle. Quatre modeles ont ete entraines "
      "successivement avec le meme jeu de 28 features exogenes et statiques, le meme split "
      "temporel, et la meme transformation logarithmique de la cible :", S_PN),
    *bullets([
        "<b>XGBoost log+MSE</b> : modele de reference du gradient boosting, fonction de cout "
        "MSE sur cible log-transformee, parametrisation par defaut.",
        "<b>XGBoost Tweedie</b> : meme architecture mais fonction de cout Tweedie "
        "(<i>objective='reg:tweedie'</i>), adaptee aux distributions positives a queue "
        "lourde et a la fraction non negligeable de petites quantites.",
        "<b>LightGBM log</b> : alternative implementee dans la librairie de Microsoft, "
        "convergence generalement plus rapide que XGBoost a equivalent fonctionnel.",
        "<b>XGBoost v1 (Optuna 50 essais)</b> : meme moteur que XGBoost log mais "
        "hyperparametrisation optimisee par 50 essais bayesiens (<i>Optuna</i>) sur le jeu "
        "de validation 2024, avec recherche conjointe sur <i>n_estimators</i>, "
        "<i>max_depth</i>, <i>learning_rate</i>, <i>subsample</i>, <i>colsample_bytree</i>, "
        "<i>min_child_weight</i>, <i>reg_alpha</i> et <i>reg_lambda</i>.",
    ]),
    P("Les meilleurs hyperparametres retenus a cette etape sont : <i>n_estimators</i> = 498, "
      "<i>max_depth</i> = 10, <i>learning_rate</i> = 0.0776, <i>subsample</i> = 0.96, "
      "<i>colsample_bytree</i> = 0.73, <i>min_child_weight</i> = 3, <i>reg_alpha</i> = 0.021, "
      "<i>reg_lambda</i> = 0.284. La valeur de <i>n_estimators</i> proche de la borne haute "
      "de l'espace de recherche (500) suggere qu'un elargissement du nombre d'essais et de "
      "l'espace de recherche apporterait un gain supplementaire ; cette intuition motivera "
      "l'iteration suivante (XGBoost v2, section 2.3.4).", S_PN),

    table([
        ["Modele", "MAE", "RMSE", "R^2", "WAPE", "Gain vs baseline"],
        ["Baseline naive", "23.50", "210.30", "-", "1.041", "ref"],
        ["Baseline historique", "13.04", "145.11", "-", "0.620", "-44.5 % MAE"],
        ["XGBoost log + MSE", "14.36", "153.11", "0.246", "0.654", "+10.1 %"],
        ["XGBoost Tweedie", "13.74", "138.98", "0.379", "0.626", "+5.4 %"],
        ["LightGBM log", "14.74", "158.43", "0.192", "0.671", "+13.0 %"],
        ["<b>XGBoost v1 (Optuna 50)</b>", "<b>11.87</b>", "<b>132.17</b>",
         "<b>0.438</b>", "<b>0.541</b>", "<b>-9.0 %</b>"],
    ], col_widths=[4.5 * cm, 2 * cm, 2 * cm, 1.7 * cm, 1.7 * cm, 2.5 * cm]),
    P("<b>Tableau 3</b> - Comparaison des modeles de premiere generation sur le test 2025 "
      "(28 features statiques, sans variables autoregressives). Seul XGBoost v1 optimise par "
      "Optuna domine la baseline historique sur toutes les metriques. Source : "
      "<i>reports/rapport_modelisation.json</i>.", S_CAPTION),

    P("La lecture du tableau 3 conduit a trois constats. Premierement, XGBoost et LightGBM "
      "en configuration par defaut ne battent pas la baseline historique en MAE, ce qui est "
      "souvent observe sur des cibles a forte variance intra-couple et confirme l'importance "
      "de l'optimisation hyperparametrique. Deuxiemement, la variante Tweedie ameliore "
      "sensiblement le RMSE et le R^2 par rapport a la variante MSE, en captant mieux la queue "
      "de distribution des petites quantites. Troisiemement, XGBoost v1 optimise par Optuna est "
      "le seul modele a battre la baseline historique sur la MAE, avec un gain de 9 pourcents. "
      "Ce resultat est encourageant mais reste loin de la cible <i>North Star</i> (60 "
      "pourcents de precision agregee, soit WAPE inferieur a 0.40) ; il motive l'enrichissement "
      "feature et la refonte d'hyperparametrisation conduits dans la generation suivante.", S_PN),

    fig("feature_importance_xgb.png",
        "Figure 10 - Importance des 15 features les plus contributrices du modele "
        "XGBoost v2 (gain XGBoost). Les rolling means client et article dominent, suivies "
        "par les frequences, le prix, l'IPI et le target encoding."),

    H2("2.3.3 Architecture 2 - LSTM time-to-event pour la date de prochaine commande"),
    P("L'architecture 2 traite un probleme statistiquement different : la prediction du delai "
      "(en jours) avant la prochaine commande du meme couple client-article. La cible est "
      "construite par calcul de la difference entre dates de commande successives pour chaque "
      "couple ayant au moins deux commandes dans l'historique. Le modele est un LSTM "
      "implemente en PyTorch avec deux couches, 64 unites cachees, longueur de sequence SEQ_LEN "
      "= 6, batch size 256, optimiseur Adam et fonction de cout MSE sur le delai en jours.", S_PN),
    P("Les huit features d'entree sequentielles sont : <i>prix</i>, "
      "<i>delai_demande_jours</i> du couple precedent, frequence client, frequence article, "
      "<i>ipi_valeur</i>, <i>mois_cmd</i>, <i>jour_semaine_cmd</i>, et <i>est_fin_mois_cmd</i>. "
      "L'entrainement converge en environ 30 epoques sans surapprentissage marque sur la "
      "validation, mais les performances finales sur le test 2025 sont decevantes au regard "
      "de l'enjeu operationnel.", S_PN),

    table([
        ["Metrique", "Valeur observee", "Cible operationnelle", "Verdict"],
        ["MAE delai (jours)", "24.5", "< 10 jours", "Insuffisant"],
        ["Precision +/-7 jours", "25.5 %", "> 50 %", "Insuffisant"],
        ["Precision +/-14 jours", "43.2 %", "> 70 %", "Insuffisant"],
        ["Couverture (couples eval.)", "78.4 %", "> 60 %", "Acceptable"],
    ], col_widths=[5 * cm, 3 * cm, 3.5 * cm, 3 * cm]),
    P("<b>Tableau 4</b> - Performance du LSTM time-to-event sur le test 2025. La precision "
      "+/-7 jours, metrique centrale pour l'usage planificateur, reste tres en deca de la "
      "cible operationnelle. Source : <i>reports/rapport_modelisation.json</i>.", S_CAPTION),

    P("Ces resultats appellent une analyse honnete des causes possibles. La longueur de "
      "sequence SEQ_LEN = 6 est probablement insuffisante pour capter une saisonnalite "
      "annuelle ou semestrielle ; l'absence de features autoregressives sur le delai lui-meme "
      "(<i>delai_lag_1</i>, ... <i>delai_lag_6</i>) prive le modele d'un signal fort ; "
      "l'absence de scaling explicite des features numeriques (le LSTM y est tres sensible) a "
      "pu ralentir la convergence ; et la formulation du probleme en regression sur un delai "
      "continu n'est pas la plus naturelle compte tenu de la nature reellement temporelle "
      "du probleme. La litterature recente plaide pour une reformulation en analyse de survie "
      "(<i>lifelines</i>, <i>scikit-survival</i>, <i>pycox</i>), ou alternativement en "
      "classification multi-classes par bucket de delai ([0-7], [7-14], [14-30], [30-60], [60+] "
      "jours), ce qui simplifie la tache et facilite l'interpretation. Cette voie est "
      "explicitement listee dans les perspectives (section 3.5).", S_PN),

    H2("2.3.4 Evolution methodologique - Enrichissement feature et architectures avancees"),
    P("A l'issue de la premiere generation de modeles, l'analyse du tableau 3 a fait apparaitre "
      "un ecart significatif entre la performance obtenue (precision agregee 45.95 pourcents) "
      "et l'objectif <i>North Star</i> declare (60 pourcents). Trois axes methodologiques ont "
      "ete explores pour reduire cet ecart : l'enrichissement du signal autoregressif, "
      "l'extension du benchmark a d'autres familles d'algorithmes, et la confrontation a une "
      "baseline metier de reference (DDMRP).", S_PN),

    H3("Enrichissement autoregressif et XGBoost v2"),
    P("Le premier axe a consiste a augmenter le jeu de 28 a 47 features par ajout de 19 "
      "variables autoregressives : lags 1/7/30 jours sur la quantite, rolling mean et std a "
      "7/30/90 jours au niveau du couple, du client seul et de l'article seul, target encoding "
      "couple / client / article par fold temporel (pour eviter toute fuite), nombre de "
      "commandes du couple sur les 30 derniers jours, nombre de jours depuis la derniere "
      "commande, lag de prix et delta de prix. Ces variables capturent explicitement la "
      "dynamique temporelle qui restait masquee dans la premiere generation. Sur cette base "
      "enrichie, un modele <i>XGBoost v2</i> a ete optimise par 300 essais Optuna (contre 50 "
      "pour la version v1), avec un espace de recherche elargi (jusqu'a 1500 estimateurs, "
      "profondeur jusqu'a 14). Les meilleurs parametres retenus sont <i>n_estimators</i> = "
      "1108, <i>max_depth</i> = 12, <i>learning_rate</i> = 0.0077, <i>subsample</i> = 0.82, "
      "<i>colsample_bytree</i> = 0.96.", S_PN),

    H3("Architectures complementaires : LightGBM Quantile, CatBoost, Stacking Ridge"),
    P("Le second axe a etendu le benchmark a trois architectures complementaires entrainees "
      "sur le meme jeu de 47 features et le meme split temporel : <i>LightGBM Quantile</i> "
      "configure aux quantiles 0.1, 0.5 et 0.9 pour produire des intervalles de prediction "
      "P10 / P50 / P90 directement exploitables operationnellement ; <i>CatBoost v2</i> "
      "entraine avec 200 essais Optuna, qui exploite nativement les features categorielles "
      "et leurs interactions ; et un meta-modele <i>Stacking Ridge</i> qui combine les "
      "predictions out-of-fold de XGBoost v2, LightGBM Quantile P50 et CatBoost via une "
      "regression Ridge regularisee (alpha optimal = 10). Le stacking est entraine sur des "
      "predictions issues d'une <i>TimeSeriesSplit</i> a 5 folds pour eviter toute fuite "
      "d'information.", S_PN),

    H3("Baseline DDMRP de reference"),
    P("Le troisieme axe a implemente une baseline <i>Demand-Driven Material Requirements "
      "Planning</i> selon les specifications de Ptak et Smith (notebook "
      "<i>09_baseline_ddmrp.ipynb</i>). Le perimetre couvre les 22 articles strategiques "
      "selectionnes par regle de Pareto (80 pourcents du volume cumule). Pour chaque article, "
      "trois zones de stock sont calculees - vert, jaune, rouge - a partir de l'<i>Average "
      "Daily Usage</i> sur 60 jours, du <i>Lead Time</i> moyen, et de facteurs de variabilite "
      "calibres sur la distribution historique. La simulation hebdomadaire du <i>Net Flow "
      "Position</i> compare ensuite les decisions de reapprovisionnement DDMRP aux predictions "
      "du modele IA sur la meme periode.", S_PN),

    table([
        ["Modele / Methode", "MAE", "RMSE", "R^2", "WAPE", "1 - WAPE"],
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
      "Trois architectures depassent l'objectif <i>North Star</i> de 60 pourcents (1 - WAPE) : "
      "LightGBM Quantile P50, XGBoost v2 et Stacking Ridge. XGBoost v2 domine sur la MAE, "
      "Stacking Ridge sur RMSE et R^2. Sources : <i>reports/sprint_a_chantier1_metrics.json</i> "
      "et <i>reports/sprint_b_chantier1_stacking.json</i>.", S_CAPTION),

    P("Le tableau 5 invite a une lecture comparative qui evite la tentation du <i>modele "
      "gagnant unique</i>. Trois architectures repondent au cahier des charges global : "
      "LightGBM Quantile P50 offre la meilleure MAE pure (8.32) et fournit nativement des "
      "intervalles de prediction ; XGBoost v2 propose le meilleur compromis MAE / WAPE / "
      "interpretabilite et constitue une base eprouvee ; Stacking Ridge domine sur les "
      "metriques de dispersion (RMSE 97.55, R^2 0.694) en corrigeant les grandes erreurs grace "
      "a la complementarite des composants. Le choix d'une architecture de production releve "
      "donc d'un arbitrage explicite entre criteres operationnels (cout d'inference, "
      "simplicite de maintenance, disponibilite des intervalles d'incertitude) plutot que "
      "d'un classement statistique unidimensionnel.", S_PN),

    H3("Confrontation IA vs DDMRP sur articles strategiques"),
    P("La comparaison directe entre les predictions IA et la simulation DDMRP, restreinte au "
      "perimetre des 22 articles strategiques selectionnes par regle de Pareto, livre les "
      "resultats suivants sur le test 2025 agrege en semaines.", S_PN),

    table([
        ["Methode", "MAE hebdo", "Biais hebdo", "Lecture"],
        ["IA seule (XGBoost v2)", "260.1", "-223.0",
         "Tres precis mais sous-estime structurel"],
        ["DDMRP simulee (Ptak & Smith)", "660.8", "-179.0",
         "Marges de securite, MAE elevee"],
        ["<b>Hybride 50 / 50</b>", "<b>242.0</b>", "<b>-20.9</b>",
         "<b>Meilleur compromis</b>"],
    ], col_widths=[5 * cm, 2.5 * cm, 2.5 * cm, 5 * cm]),
    P("<b>Tableau 6</b> - Comparaison IA, DDMRP et combinaison hybride sur 22 articles "
      "strategiques (perimetre 80 pourcents du volume). L'hybridation a parts egales "
      "minimise simultanement la MAE hebdomadaire et le biais. Source : "
      "<i>reports/sprint_b_chantier3_ddmrp.json</i>.", S_CAPTION),

    P("Cette comparaison delivre un message methodologique central : l'IA et DDMRP ne sont "
      "pas substituables mais complementaires. L'IA fournit une prediction precise mais "
      "structurellement sous-estimee de la demande (biais negatif eleve), tandis que DDMRP "
      "introduit des marges de securite operationnelles qui evitent la rupture mais "
      "augmentent l'erreur moyenne. Une combinaison hybride a parts egales reduit "
      "simultanement la MAE hebdomadaire (242 contre 260 pour l'IA seule) et le biais "
      "structurel (-20.9 contre -223). Le taux de rupture observe sur la simulation DDMRP "
      "(11.2 pourcents) confirme par ailleurs la valeur operationnelle de l'approche "
      "metier classique, qui ne disparait pas avec l'arrivee de l'IA.", S_PN),

    H2("2.3.5 Analyse comparative et selection du modele de service"),
    P("La selection d'une architecture pour le service operationnel resulte d'un arbitrage "
      "multicritere : performance brute, interpretabilite, simplicite d'industrialisation, "
      "cout de maintenance. Le memoire ne tranche pas en faveur d'un modele unique mais "
      "documente trois configurations recommandees selon le profil d'usage :", S_PN),

    *bullets([
        "<b>XGBoost v2 (47 features)</b> : configuration recommandee pour un service "
        "monomodele privilegiant simplicite operationnelle et interpretabilite. MAE 8.42, "
        "WAPE 0.383, precision agregee 61.7 pourcents. Modele actif dans le dashboard livre.",
        "<b>LightGBM Quantile P10 / P50 / P90</b> : configuration recommandee lorsque "
        "l'utilisateur metier exige des intervalles d'incertitude explicites (badge de "
        "confiance, marges de securite). Performances P50 comparables a XGBoost v2 et "
        "intervalles directement exploitables.",
        "<b>Stacking Ridge (XGBoost v2 + LightGBM P50 + CatBoost)</b> : configuration "
        "recommandee lorsque la metrique de dispersion (RMSE, R^2) est prioritaire et "
        "que le cout d'inference triple est acceptable. Gain de 4 points sur le RMSE et "
        "de 4 points sur le R^2 par rapport au monomodele.",
    ]),

    P("Cette presentation neutre des trois configurations est defendue dans la <i>model card</i> "
      "publiee en annexe : elle expose au jury et aux praticiens la realite d'un projet "
      "industriel ou plusieurs architectures coexistent legitimement selon le profil d'usage, "
      "et ou la decision de service finale est documentee, datee et susceptible d'evoluer.", S_PN),
    PageBreak(),
]

# ---------- 2.4 Dashboard ----------
story += [
    H1("2.4 Presentation du dashboard Human-in-the-loop"),
    H2("2.4.1 Architecture technique et choix de stack"),
    P("Le dashboard livre repose sur la stack Streamlit, choisie apres comparaison avec les "
      "alternatives Dash (Plotly), Panel et FastAPI + React. Trois criteres ont determine ce "
      "choix : la rapidite de developpement (un planificateur teste l'interface des la "
      "semaine 5 du projet), l'integration native avec l'ecosysteme Python scientifique "
      "deja utilise pour la modelisation, et la possibilite d'embarquer Plotly pour les "
      "graphiques interactifs sans pont JavaScript. La contrepartie reconnue est une "
      "scalabilite limitee a quelques utilisateurs simultanes, acceptable pour un MVP "
      "interne mais qui necessitera une migration vers une architecture decouplee (FastAPI "
      "+ React) pour une mise en production a l'echelle.", S_PN),
    P("L'application est structuree en une page d'accueil et six pages metier accessibles "
      "via la sidebar Streamlit native : <i>Gestion des Donnees</i>, <i>Intelligence "
      "Artificielle</i>, <i>Previsions de Ventes</i>, <i>Analyse</i>, <i>Drift Detection</i>, "
      "<i>Backtest 2025</i>. Les utilitaires de chargement de donnees, d'inference, de calcul "
      "du score de confiance et de simulation what-if sont centralises dans le package "
      "<i>dashboard/utils/</i> pour eviter la duplication.", S_PN),

    H2("2.4.2 Page Gestion des Donnees"),
    P("La page <i>Gestion des Donnees</i> assure deux fonctions : la consultation du jeu de "
      "donnees historique et l'import de nouveaux fichiers pour inference. Le tableau "
      "consultation propose un filtrage par client, par article, par periode, et un export "
      "CSV des resultats filtres. L'import accepte un fichier CSV au format <i>Mode A</i> "
      "(deja encode avec les suffixes <i>_freq</i> et <i>_enc</i>), choix de simplification "
      "explicitement documente dans la limite operationnelle pour le MVP - un Mode B "
      "(encodage automatique cote serveur) est positionne en perspective.", S_PN),

    screen("donnees.png",
           "Figure 11 - Page Gestion des Donnees du dashboard. Le tableau filtrable consulte "
           "l'historique 2021-2025 ; le bandeau d'import en haut accepte les CSV Mode A."),

    H2("2.4.3 Page Intelligence Artificielle"),
    P("La page <i>Intelligence Artificielle</i> centralise les informations sur le modele "
      "actif et l'historique des versions. Elle expose la version active, la date de dernier "
      "entrainement, la liste des features utilisees (lue dynamiquement depuis l'attribut "
      "<i>feature_names_in_</i> du modele serialise pour eviter toute divergence avec la "
      "liste hardcodee), et un tableau historique des runs avec leurs metriques principales. "
      "Un bouton <i>Re-entrainer le modele</i> declenche le script "
      "<i>src/retrain.py</i> en arriere-plan et streame le log d'execution dans la page.", S_PN),

    screen("ia.png",
           "Figure 12 - Page Intelligence Artificielle. Le panneau central affiche les "
           "metriques du modele actif, l'historique des versions et le bouton de "
           "re-entrainement."),

    H2("2.4.4 Page Previsions de Ventes et score de confiance composite"),
    P("La page <i>Previsions de Ventes</i> constitue le coeur fonctionnel du dashboard. Elle "
      "propose au planificateur la liste des couples client-article a horizon M+1 a M+3 avec "
      "leur quantite predite, leur intervalle d'incertitude P10-P90 et un indicateur visuel "
      "de confiance (vert / orange / rouge) lisible en un coup d'oeil. La page integre un "
      "filtrage par client, par famille d'article et par segment ABC, ainsi qu'un export "
      "CSV / Excel des lignes selectionnees.", S_PN),
    P("Le score de confiance affiche est calcule par une formule composite a trois facteurs "
      "documentee dans le fichier <i>dashboard/utils/confidence.py</i> : (1) familiarite du "
      "couple (article et client deja vus ensemble en entrainement, partiellement vus, ou "
      "inconnus), (2) ecart entre la prediction et la mediane historique du couple "
      "(indicateur de surprise statistique), et (3) decile de la valeur predite dans la "
      "distribution d'entrainement (les valeurs extremes sont moins fiables). Le score "
      "composite est mappe sur trois etats : vert si confiance superieure a 0.75, orange "
      "entre 0.4 et 0.75, rouge en dessous. Ce mapping est configurable depuis la page "
      "<i>Analyse</i> via un slider, materialisant la matrice de gouvernance HITL "
      "(detaillee section 3.4).", S_PN),

    screen("previsions.png",
           "Figure 13 - Page Previsions de Ventes (vue principale). Tableau central : un "
           "couple client-article par ligne, colonnes Quantite predite, P10-P90, Confiance "
           "(badge couleur), Action recommandee. Le panneau de filtres lateral autorise une "
           "selection multidimensionnelle."),

    screen("previsions 1.png",
           "Figure 14 - Page Previsions, sous-section <i>Prediction vs valeur reelle</i>. "
           "Scatter plot interactif Plotly : abscisse valeur reelle, ordonnee prediction. "
           "La couleur encode le score de confiance et la diagonale grise materialise la "
           "prediction parfaite."),

    screen("previsions 2.png",
           "Figure 15 - Page Previsions, sous-section <i>Simulation what-if</i>. Sliders et "
           "toggles permettant au planificateur de simuler l'effet d'une variation de prix, "
           "de delai, d'IPI ou d'un passage en jour ferie sur la prediction d'une ligne "
           "selectionnee, avec affichage de la prediction simulee et de l'intervalle P10 - "
           "P90 associe."),

    H2("2.4.5 Page Analyse - IA vs baseline et exploration des erreurs"),
    P("La page <i>Analyse</i> centralise le travail de storytelling autour des resultats de "
      "modelisation. Elle confronte d'abord la MAE de la baseline historique a la MAE du "
      "modele XGBoost v2 et affiche le gain relatif obtenu sur le jeu de test 2025. Elle "
      "presente ensuite le top des erreurs maximales : un tableau classe les couples "
      "client-article ou l'ecart entre quantite reelle et quantite predite est le plus eleve. "
      "Cette vue est essentielle pour la lecture critique du modele car elle materialise les "
      "regions de l'espace ou la prediction reste fragile et oriente les ameliorations futures.", S_PN),
    P("Une lecture explicite accompagne le tableau : les erreurs maximales correspondent "
      "generalement a des commandes de gros volume sur des articles ou des clients peu "
      "representes dans le set d'entrainement, ce qui justifie l'usage du badge de confiance "
      "(orange ou rouge) pour signaler ces situations au planificateur avant validation.", S_PN),

    screen("Analyse.png",
           "Figure 16 - Page Analyse. Le tableau central liste le top des erreurs absolues "
           "du modele XGBoost v2 sur le test 2025 ; la lecture en bas de page guide "
           "l'interpretation et le rattachement au score de confiance. Le bandeau inferieur "
           "expose la comparaison IA vs DDMRP et la decomposition par architectures avancees."),

    H2("2.4.6 Page Drift Detection - monitoring de la stabilite des features"),
    P("La page <i>Drift Detection</i> implemente un monitoring de la <i>Population Stability "
      "Index</i> (PSI) sur les six features les plus contributrices du modele XGBoost v2, "
      "identifiees par importance de permutation : <i>qte_roll_mean_7</i>, "
      "<i>qte_roll_mean_30_article</i>, <i>qte_roll_mean_30</i>, "
      "<i>qte_roll_mean_30_client</i>, <i>prix</i> et <i>ipi_valeur</i>. La distribution de "
      "reference est calculee sur le set d'entrainement (2021-2023) et confrontee soit au "
      "test 2025 par defaut, soit a une distribution courante uploadee par l'utilisateur "
      "(CSV ou Parquet).", S_PN),
    P("Pour chaque feature surveillee, l'application calcule le PSI selon la formule "
      "standard <i>somme(p_cur - p_ref) * log(p_cur / p_ref)</i> sur dix bins definis par "
      "quantiles de la distribution de reference. Une classification a trois niveaux est "
      "appliquee : <i>stable</i> (PSI inferieur a 0.10), <i>drift modere</i> (PSI entre 0.10 "
      "et 0.25), <i>drift significatif</i> (PSI superieur a 0.25). Un bandeau d'alerte synthese "
      "le verdict global et conseille un re-entrainement lorsqu'au moins une feature critique "
      "passe en zone rouge. Cette mecanique est conforme aux pratiques de monitoring credit "
      "risk industriel (Karakoulas, 2011) et constitue le socle d'une mise en production "
      "responsable.", S_PN),

    screen("drift.png",
           "Figure 17 - Page Drift Detection. Panneau gauche : tableau PSI par feature avec "
           "code couleur (vert / orange / rouge) ; panneau droit : histogramme des PSI pour "
           "lecture visuelle rapide. Le bandeau superieur synthese le verdict de stabilite "
           "du modele."),

    H2("2.4.7 Page Backtest interactif - retroprojection 2025"),
    P("La page <i>Backtest 2025</i> propose au planificateur de retroprojeter l'usage du "
      "modele sur l'annee 2025 a l'aide d'un slider hebdomadaire ISO. Pour chaque <i>semaine "
      "d'arret</i> selectionnee, l'application affiche la quantite reelle cumulee, la quantite "
      "predite cumulee par chacun des modeles selectionnes (XGBoost v2, LightGBM Quantile P50, "
      "CatBoost, Stacking Ridge, baseline historique), ainsi que des metriques rolling sur les "
      "quatre dernieres semaines.", S_PN),
    P("Au-dela des metriques statistiques (MAE et WAPE par fenetre), la page expose une "
      "<i>fonction de cout business</i> parametrable par l'utilisateur : <i>cout = alpha * "
      "ruptures + beta * sur-stock</i>, ou alpha et beta sont fixes par sliders en euros par "
      "unite. Cette fonction permet une lecture economique directe du comportement des "
      "modeles dans des contextes ou la rupture coute plus cher que le surstock (alpha "
      "grand), ou inversement (beta grand). Le tableau des dix erreurs absolues maximales sur "
      "la semaine d'arret complete la lecture par une vue qualitative des cas extremes.", S_PN),

    screen("backtest.png",
           "Figure 18 - Page Backtest interactif. Graphique central : cumul de la quantite "
           "reelle et des predictions cumulees des modeles selectionnes en abscisse semaine "
           "ISO. Panneaux secondaires : metriques rolling 4 semaines, fonction de cout "
           "business parametrable, tableau des dix plus grandes erreurs."),

    H2("2.4.8 Page d'accueil - synthese executive et navigation"),
    P("La page d'accueil du dashboard joue le role de tableau de bord executif. Elle expose "
      "en bandeau superieur les indicateurs cles du modele actif (MAE, R^2, WAPE, taille du "
      "dataset), rappelle la problematique en quelques lignes et restitue visuellement le "
      "pipeline complet du projet (Data Engineering, Etudes statistiques, Modelisation IA, "
      "Dashboard). Le panneau de navigation a droite oriente l'utilisateur vers les quatre "
      "pages metier en fonction du besoin du moment : exploration des donnees, monitoring du "
      "modele, previsions a horizon M+1/M+3, analyse comparative.", S_PN),
    P("Au-dela de la fonction navigation, cette page d'accueil constitue le premier contact "
      "visuel pour un decideur non technique. Elle permet de mesurer instantanement la "
      "valeur ajoutee du modele par rapport a la baseline historique (badge <i>-9.0 % "
      "vs baseline</i>) sans avoir a entrer dans les details statistiques de chaque page.", S_PN),

    screen("app.png",
           "Figure 19 - Page d'accueil du dashboard. KPIs du modele actif en bandeau, "
           "rappel de la problematique au centre, schema du pipeline et navigation rapide "
           "vers les six pages metier."),

    H3("Synthese PSI mesuree sur le test 2025"),
    P("Les valeurs de PSI mesurees sur le test 2025 par la page <i>Drift Detection</i> "
      "fournissent une calibration empirique des seuils. Le tableau ci-dessous restitue les "
      "PSI obtenus sur les six features critiques entre la reference train (2021-2023) et "
      "la distribution test (2025).", S_PN),

    table([
        ["Feature surveillee", "PSI test 2025", "Statut"],
        ["prix", "0.07", "Stable"],
        ["qte_roll_mean_7", "0.11", "Drift modere"],
        ["ipi_valeur", "0.19", "Drift modere"],
        ["qte_roll_mean_30_article", "0.18", "Drift modere"],
        ["qte_roll_mean_30_client", "0.09", "Stable"],
        ["qte_roll_mean_30", "0.14", "Drift modere"],
    ], col_widths=[6.5 * cm, 3.5 * cm, 5.5 * cm]),
    P("<b>Tableau 7</b> - PSI mesures sur les six features les plus contributrices entre "
      "train et test 2025. Aucune feature ne franchit le seuil rouge (0.25), ce qui justifie "
      "le maintien du modele en service sans declencher de re-entrainement immediat.", S_CAPTION),
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
    H2("3.1.1 Methodologie de comparaison"),
    P("La comparaison entre la prediction IA et le pilotage par objectifs commerciaux ne "
      "peut s'appuyer, dans le perimetre du present memoire, que sur des donnees "
      "objectives disponibles dans le dataset. Faute d'acces aux objectifs commerciaux "
      "negocies par GE, l'evaluation prend pour reference la <i>baseline historique</i> "
      "(moyenne par couple client-article calculee sur 2021-2023), qui constitue un proxy "
      "mesurable de ce que produirait une planification non assistee par IA au-dela d'une "
      "simple moyenne glissante. Cette baseline est volontairement exigeante : un modele "
      "qui ne la depasse pas significativement n'apporterait aucune valeur ajoutee "
      "scientifique.", S_PN),

    H2("3.1.2 Gains mesures par rapport a la baseline"),
    P("Sur le perimetre du test 2025 (66 174 lignes), le gain absolu du modele XGBoost v2 par "
      "rapport a la baseline historique est de 4.62 unites en MAE (8.42 contre 13.04), soit "
      "un gain relatif de 35.4 pourcents. En precision agregee (1 - WAPE), le modele atteint "
      "61.7 pourcents contre 38.0 pourcents pour la baseline, soit un gain absolu de "
      "23.7 points et un depassement de 1.7 point de l'objectif <i>North Star</i> declare "
      "(60 pourcents). Le modele <i>Stacking Ridge</i>, qui ameliore le RMSE de 4 points "
      "(97.55 contre 101.83) et le R^2 de 4 points (0.694 contre 0.666), constitue une "
      "alternative interessante lorsque la metrique de dispersion est prioritaire.", S_PN),
    P("Le test de Diebold-Mariano applique sur les residus du modele XGBoost v2 versus "
      "la baseline historique donne une p-value tres significativement inferieure a 0.01, "
      "ce qui permet d'affirmer statistiquement la superiorite du modele sur l'ensemble du "
      "test. Cette validation statistique est essentielle pour anticiper la question - "
      "frequemment posee en soutenance - de la significativite du gain observe.", S_PN),

    H2("3.1.3 Cadre d'estimation business"),
    P("La traduction du gain statistique en valeur economique necessite la connaissance de "
      "deux parametres metier : <i>alpha</i>, le cout unitaire d'une rupture, et <i>beta</i>, "
      "le cout unitaire d'un surstock (par mois immobilise). Ces parametres ne sont pas "
      "fournis dans le brief de mission et ne peuvent donc pas etre fixes ici sans "
      "approximation arbitraire. La page <i>Backtest 2025</i> du dashboard permet a "
      "l'utilisateur metier de saisir lui-meme ces deux parametres et d'observer le cout "
      "cumule des differents modeles sur l'annee 2025 sous l'hypothese choisie. Cette "
      "demarche evite de propager une estimation chiffree non sourcee dans le memoire "
      "tout en laissant a GE la possibilite de quantifier le gain sur ses propres barèmes.", S_PN),
    PageBreak(),
]

# ---------- 3.2 Limites ----------
story += [
    H1("3.2 Limites du modele"),
    H2("3.2.1 Imprevus geopolitiques et ruptures de regime"),
    P("La premiere limite structurelle de toute approche basee sur l'apprentissage statistique "
      "est sa difficulte intrinseque a anticiper les ruptures de regime. La periode "
      "d'entrainement 2021-2023 comprend deux contextes economiquement atypiques : la phase "
      "post-Covid (chaines d'approvisionnement perturbees, prix volatiles) et la phase "
      "consecutive a la guerre en Ukraine declenchee en fevrier 2022 (envolee des prix de "
      "l'energie, tensions sur les composants). Le modele a donc appris des correlations "
      "potentiellement biaisees par ces contextes ; un changement de regime aussi violent "
      "que ces deux precedents pendant la periode d'inference invaliderait localement les "
      "predictions. Aucune technique d'apprentissage statistique ne corrige integralement "
      "ce defaut ; la detection de derive PSI integree au dashboard est un palliatif partiel "
      "qui declenche une alerte sans pour autant fournir un nouveau modele adapte.", S_PN),

    H2("3.2.2 Donnees manquantes et perimetres non couverts"),
    P("Plusieurs sources d'information potentiellement utiles n'ont pas pu etre integrees, "
      "soit par indisponibilite, soit par contrainte de temps. Les donnees promotionnelles "
      "(remises tarifaires accordees ponctuellement) ne sont pas tracees dans l'export ERP "
      "exploite ; or, une remise significative declenche typiquement un effet d'anticipation "
      "de commande qui n'est pas capte par le modele. Les operations de transfert inter-sites "
      "sont egalement absentes : un transfert de stock entre deux centres de distribution "
      "pour repondre a une rupture locale n'apparait pas comme une commande dans le perimetre "
      "etudie. Enfin, les retours clients - faibles en volume mais structurellement biaises "
      "vers certaines familles d'article - ne sont pas integres.", S_PN),

    H2("3.2.3 Biais identifies"),
    P("Trois categories de biais structurels du jeu de donnees ont ete identifiees comme "
      "points de vigilance pour une exploitation industrielle. Les ordres de grandeur "
      "associes restent qualitatifs : leur quantification precise depasse le perimetre du "
      "present memoire mais est facilement instrumentable en relancant les notebooks "
      "d'EDA et de modelisation sur les colonnes concernees.", S_PN),
    *bullets([
        "<b>Biais de frequence client</b> : les comptes a faible activite (peu de "
        "commandes par an) representent une part importante du nombre de clients mais "
        "une part marginale du volume. Le modele leur attribue mecaniquement une erreur "
        "plus elevee, ce qui implique un risque de rupture silencieuse sur cette "
        "population si la prediction est utilisee sans badge de confiance.",
        "<b>Biais d'article</b> : la longue traine du catalogue (articles a faible "
        "volume) presente une demande intermittente structurellement difficile a "
        "predire par un modele de regression continue. Une exploitation industrielle "
        "exigerait une approche specialisee de type Croston / TSB / ADIDA pour ce "
        "segment.",
        "<b>Biais temporel</b> : la presence de regimes economiquement atypiques dans "
        "l'entrainement (post-Covid, choc energetique 2022) peut conduire a sur-ponderer "
        "ces regimes lors d'une inference dans un contexte revenu a la normale.",
    ]),

    H2("3.2.4 Echec relatif du LSTM time-to-event et honnetete metrique"),
    P("La precision +/-7 jours de 25.5 pourcents obtenue par l'architecture LSTM time-to-event "
      "est tres inferieure a la cible operationnelle (50 pourcents). Cet ecart constitue le "
      "point faible le plus visible du memoire et ne saurait etre dissimule. L'analyse "
      "honnete des causes (longueur de sequence insuffisante, absence d'autoregression sur "
      "le delai, absence de scaling, formulation potentiellement inadaptee) a deja ete "
      "exposee section 2.3.3. Plutot que de retirer cette architecture du livrable, elle est "
      "explicitement signalee dans le dashboard par un badge rouge par defaut sur toute "
      "prediction de date : la transparence sur la fiabilite limitee de ce modele est ici un "
      "engagement methodologique, qui prepare la reformulation par analyse de survie "
      "annoncee en perspectives.", S_PN),

    H2("3.2.5 Atteinte du North Star sur la quantite, echec sur la date"),
    P("La cible <i>North Star</i> declaree en debut de projet, 60 pourcents de precision "
      "agregee (1 - WAPE), est atteinte sur la quantite : le modele XGBoost v2 livre une "
      "precision de 61.7 pourcents sur le test 2025, soit un depassement de 1.7 point. La "
      "configuration <i>Stacking Ridge</i> atteint 60.4 pourcents avec une amelioration "
      "significative de la metrique de dispersion (R^2 0.694 contre 0.666 pour XGBoost v2). "
      "Trois architectures distinctes franchissent ainsi le seuil cible (XGBoost v2 a 61.7 "
      "pourcents, LightGBM Quantile P50 a 62.1 pourcents, Stacking Ridge a 60.4 pourcents), "
      "ce qui constitue un acquis robuste et reproductible.", S_PN),
    P("L'objectif n'est en revanche pas atteint sur la prediction de date par LSTM, qui "
      "plafonne a 25.5 pourcents +/-7 jours (cible operationnelle : 50 pourcents). Cette "
      "dissymetrie des resultats - reussite sur la quantite, echec relatif sur la date - "
      "structure la lecture critique du memoire : le livrable opere une transformation "
      "demontrable sur le pilotage des volumes mais ne resout pas la question du <i>timing</i> "
      "exact des commandes, qui devra etre repris via une reformulation par analyse de "
      "survie (perspectives en section 3.5).", S_PN),
    PageBreak(),
]

# ---------- 3.3 RGPD ----------
story += [
    H1("3.3 Conformite RGPD et ethique du traitement"),
    P("Le present memoire mobilisant des donnees d'entreprise contenant indirectement des "
      "informations relatives a des personnes physiques (interlocuteurs commerciaux, "
      "demandeurs ERP, planificateurs identifies dans certains champs metadata), une "
      "analyse de conformite au Reglement General sur la Protection des Donnees (RGPD, "
      "reglement UE 2016/679, applicable depuis le 25 mai 2018) est imperative. Cette section "
      "documente cette analyse et identifie les mesures techniques et organisationnelles "
      "mises en oeuvre.", S_PN),

    H2("3.3.1 Donnees personnelles potentiellement concernees"),
    P("Au sens de l'article 4 du RGPD, constitue une donnee personnelle toute information se "
      "rapportant a une personne physique identifiee ou identifiable. L'examen des colonnes "
      "presentes dans le dataset effectivement utilise (<i>data/processed/dataset_ml_enrichi."
      "parquet</i>) permet d'identifier le statut des champs vis-a-vis du RGPD :", S_PN),
    *bullets([
        "<b>Identifiants entreprise (codes opaques)</b> : <i>code_client</i> et "
        "<i>code_article</i> sont des identifiants numeriques internes a GE. Ils ne "
        "designent pas directement une personne physique mais peuvent y conduire en "
        "presence d'une table de correspondance interne. Dans le pipeline d'apprentissage, "
        "ces champs sont remplaces par leur <i>frequency encoding</i> "
        "(<i>code_client_freq</i>, <i>code_article_freq</i>), ce qui rompt le lien direct.",
        "<b>Variables descriptives clients</b> : <i>famille_activite_client</i>, "
        "<i>type_activite</i>, <i>pays</i>, <i>segment</i>. Ces champs decrivent l'activite "
        "commerciale et le pays du client, qui peut etre une personne morale ou physique. "
        "Lorsqu'un client est une personne physique (entrepreneur individuel par exemple), "
        "ces variables constituent indirectement des donnees personnelles.",
        "<b>Variables transactionnelles</b> : <i>qte_demandee</i>, <i>qte_livree</i>, "
        "<i>prix</i>, dates. Donnees commerciales standard non personnelles en elles-memes.",
    ]),
    P("Le dataset utilise pour l'entrainement ne contient en revanche aucun champ "
      "directement nominatif (nom, prenom, contact, identifiant operateur ERP). Aucune "
      "donnee sensible au sens de l'article 9 du RGPD (sante, opinion politique, syndicale, "
      "religieuse, biometrique, sexuelle) n'est traitee dans le perimetre du projet.", S_PN),

    H2("3.3.2 Bases legales du traitement"),
    P("Le traitement realise dans le cadre du present memoire mobilise deux bases legales "
      "principales selon l'article 6 du RGPD :", S_PN),
    *bullets([
        "<b>Article 6.1.b (execution d'un contrat)</b> : le traitement des donnees "
        "client necessaires a l'execution des commandes (raison sociale, adresse de "
        "livraison, code interlocuteur) est legitime par l'execution du contrat "
        "commercial entre GE et ses clients.",
        "<b>Article 6.1.f (interet legitime)</b> : le traitement statistique anonymise "
        "des historiques de commande aux fins d'amelioration de la prevision de demande "
        "est legitime par l'interet legitime de GE a optimiser sa chaine "
        "d'approvisionnement, sous reserve que les droits et libertes des personnes "
        "concernees ne prevalent pas. Une analyse d'impact (AIPD / DPIA) formelle "
        "complementaire est recommandee avant tout deploiement en production etendu.",
    ]),

    H2("3.3.3 Mesures techniques et organisationnelles mises en oeuvre"),
    P("Trois mesures techniques et organisationnelles ont ete adoptees au cours du projet "
      "pour minimiser la sensibilite des donnees manipulees :", S_PN),
    *bullets([
        "<b>Pseudonymisation des identifiants</b> : les champs <i>code_client</i> et "
        "<i>code_article</i> sont remplaces par leur frequency encoding "
        "(<i>code_client_freq</i>, <i>code_article_freq</i>) lors de la preparation "
        "(notebook <i>02bis_eda_dataset_enrichi.ipynb</i>), ce qui rompt le lien direct "
        "entre une transaction et un identifiant commercial dans les modeles serialises.",
        "<b>Minimisation</b> : le dataset utilise pour l'apprentissage ne contient aucun "
        "champ nominatif (nom, prenom, contact, identifiant operateur), conformement au "
        "perimetre defini en 1.1.2 et a l'inspection des colonnes effectivement chargees.",
        "<b>Maitrise de la diffusion</b> : aucune des donnees brutes ou enrichies n'est "
        "publiee dans le depot Git du projet (les fichiers Parquet sont exclus par "
        "<i>.gitignore</i>) ; seuls les rapports agreges et les modeles serialises sont "
        "versionnes.",
    ]),

    H2("3.3.4 Droits des personnes concernees"),
    P("Les droits prevus aux articles 15 a 22 du RGPD sont applicables aux donnees "
      "operateurs ERP traitees dans le projet, meme si leur volume est limite et leur "
      "exploitation indirecte. Le tableau ci-dessous synthese le statut de ces droits dans "
      "le perimetre du projet.", S_PN),

    table([
        ["Droit", "Reference", "Modalite d'exercice"],
        ["Acces", "Art. 15", "Sur demande au DPO GE"],
        ["Rectification", "Art. 16", "Mise a jour ERP source"],
        ["Effacement", "Art. 17", "Anonymisation totale dans le dataset"],
        ["Limitation", "Art. 18", "Suspension de l'inclusion dans le pipeline"],
        ["Portabilite", "Art. 20", "Export structure sur demande"],
        ["Opposition", "Art. 21", "Exclusion sur demande motivee"],
        ["Decision automatisee", "Art. 22", "Non applicable - decision finale humaine"],
    ], col_widths=[3.5 * cm, 2.5 * cm, 9 * cm]),
    P("<b>Tableau 9</b> - Droits RGPD et modalites d'exercice dans le perimetre du projet.",
      S_CAPTION),

    P("Le point essentiel a souligner est l'article 22 : le RGPD interdit en principe les "
      "decisions produisant des effets juridiques ou affectant significativement une "
      "personne, prises sur la seule base d'un traitement automatise. Dans le cas present, "
      "la decision de reapprovisionnement finale reste imperativement humaine (le "
      "planificateur valide la commande generee), ce qui place le systeme hors du perimetre "
      "des decisions purement automatisees. Cette caracteristique est centrale dans "
      "l'architecture <i>Human-in-the-loop</i> defendue en section 3.4.", S_PN),

    H2("3.3.5 Duree de conservation et registre des traitements"),
    P("La duree de conservation des donnees brutes 2021-2025 reste celle definie par les "
      "politiques internes de GE - non documentees dans le perimetre du present memoire - "
      "et par les obligations legales applicables aux donnees commerciales (article L.123-22 "
      "du Code de commerce). Les artefacts produits dans le cadre du projet (jeux de "
      "donnees enrichis, modeles serialises) sont conserves pour la duree du memoire et "
      "feront l'objet d'une revue post-soutenance pour decider de leur sort. Le traitement "
      "specifique realise dans le cadre du projet doit etre inscrit, le cas echeant, dans "
      "le registre des activites de traitement de GE, sous une categorie d'analyse "
      "statistique interne, avec mention explicite du perimetre temporel (2021-2025) et de "
      "la finalite (prevision de la demande client).", S_PN),

    H2("3.3.6 Positionnement vis-a-vis de l'AI Act europeen"),
    P("Au-dela du RGPD, le reglement europeen sur l'intelligence artificielle (AI Act, "
      "adopte en 2024, applicable de maniere echelonnee a partir de 2025) introduit une "
      "classification des systemes d'IA par niveau de risque. Le systeme decrit dans ce "
      "memoire releve de la categorie <i>risque limite</i> : il ne participe pas a une "
      "decision affectant directement une personne physique au sens de l'AI Act (recrutement, "
      "credit, education, infrastructures critiques), et son usage est interne a "
      "l'organisation. Les obligations applicables a cette categorie - transparence sur "
      "l'usage d'un systeme IA, documentation technique, supervision humaine - sont "
      "explicitement couvertes par la model card publiee en annexe, le present memoire et "
      "la matrice de gouvernance HITL exposee section 3.4. Une evolution du systeme vers "
      "une automatisation totale du reapprovisionnement le ferait basculer en categorie "
      "<i>risque eleve</i>, ce qui necessiterait des obligations renforcees (audit "
      "independant, conformite ex ante) explicitement evoquees dans les perspectives de "
      "mise en production.", S_PN),
    PageBreak(),
]

# ---------- 3.4 HITL ----------
story += [
    H1("3.4 Importance de la validation humaine (Human-in-the-loop)"),
    H2("3.4.1 Principe et formalisation"),
    P("Le principe <i>Human-in-the-loop</i> (HITL) constitue la cle de voute de la "
      "philosophie operationnelle du systeme. Plutot que d'opposer intelligence artificielle "
      "et expertise humaine, il s'agit de les articuler : le modele fournit une recommandation "
      "transparente assortie d'un score de confiance, le planificateur arbitre en fonction "
      "de ce score, du contexte connu de lui seul (relations commerciales, evenements "
      "anticipes) et de sa propre estimation. La validation humaine demeure le dernier "
      "maillon de la chaine de decision, conformement aux exigences de l'article 22 du RGPD "
      "et de l'AI Act europeen pour les systemes de risque limite.", S_PN),

    H2("3.4.2 Matrice de gouvernance a trois niveaux"),
    P("La matrice de gouvernance retenue, configurable via la page <i>Analyse</i> du "
      "dashboard, articule trois niveaux de decision en fonction du score de confiance "
      "composite calcule pour chaque prediction.", S_PN),

    table([
        ["Niveau", "Critere (score)", "Action recommandee"],
        ["Vert", "score > 0.75",
         "Automatisation totale - commande validee sans revue"],
        ["Orange", "0.40 < score < 0.75",
         "Revue rapide - validation 1 clic par le planificateur"],
        ["Rouge", "score < 0.40",
         "Decision humaine obligatoire et saisie d'une justification"],
    ], col_widths=[2.5 * cm, 4 * cm, 9 * cm]),
    P("<b>Tableau 8</b> - Matrice de gouvernance Human-in-the-loop. Les seuils 0.40 et 0.75 "
      "sont configurables depuis la page <i>Analyse</i> du dashboard ; la repartition "
      "effective entre les trois niveaux se calcule dynamiquement sur le perimetre courant "
      "et n'est pas figee dans ce document.",
      S_CAPTION),

    H2("3.4.3 Boucle d'amelioration continue"),
    P("Au-dela de la simple validation, le HITL ouvre une boucle d'amelioration continue : "
      "chaque correction operee par un planificateur sur une prediction (acceptation, "
      "modification, refus avec justification libre) est tracee et constitue un signal "
      "supplementaire d'apprentissage potentiel. Une iteration ulterieure du systeme "
      "pourrait integrer cette boucle de feedback dans un schema d'apprentissage actif "
      "(<i>active learning</i>) ou de fine-tuning periodique. Cette piste est documentee "
      "dans les perspectives de la section 3.5 et constituerait un gain majeur d'adoption "
      "et de robustesse en production.", S_PN),
    PageBreak(),
]

# ---------- 3.5 Perspectives ----------
story += [
    H1("3.5 Perspectives d'amelioration et de mise en production"),
    H2("3.5.1 Ameliorations methodologiques a court terme"),
    P("Trois ameliorations methodologiques ont ete identifiees comme prioritaires pour une "
      "iteration ulterieure du projet. Premiere priorite : la reformulation de la prediction "
      "de date par analyse de survie (modeles <i>Cox proportional hazards</i> via "
      "<i>lifelines</i>, <i>Random Survival Forests</i> via <i>scikit-survival</i>, ou "
      "<i>DeepSurv</i> via <i>pycox</i>), qui devrait permettre de depasser largement la "
      "precision actuelle de 25.5 pourcents +/-7 jours en exploitant correctement la nature "
      "<i>time-to-event</i> du probleme. Deuxieme priorite : un traitement dedie de la longue "
      "traine via les methodes Croston, TSB et ADIDA specialisees dans la demande "
      "intermittente, susceptible de reduire significativement la MAE residuelle sur la "
      "longue traine d'articles a faible volume. Troisieme priorite : l'integration des "
      "features exogenes laggees "
      "(<i>ipi_valeur_lag1</i>, <i>ipi_valeur_lag3</i>, <i>temperature_lag2</i>), motivee "
      "par les resultats du test de Granger (tableau 2) et restee non implementee pour des "
      "raisons d'agenda.", S_PN),

    H2("3.5.2 Architecture cible de mise en production"),
    P("L'architecture cible de mise en production decrite ci-dessous demeure un livrable "
      "conceptuel du present memoire et n'a pas ete deployee dans le perimetre du Master ; "
      "elle constitue la principale perspective industrielle du projet et formalise les "
      "briques attendues pour un usage operationnel a l'echelle.", S_PN),
    *bullets([
        "<b>API d'inference</b> : <i>FastAPI</i> avec validation de schemas par "
        "<i>Pydantic</i>, deployee derriere un reverse proxy <i>Nginx</i>. Endpoints "
        "<i>/predict</i>, <i>/explain</i> (SHAP par ligne), <i>/health</i>, "
        "<i>/metrics</i>.",
        "<b>Base de donnees relationnelle</b> : <i>PostgreSQL</i> avec schemas dedies "
        "pour les predictions historiques, les feedbacks planificateur (boucle HITL) et "
        "les snapshots de modeles. SQLAlchemy comme couche ORM.",
        "<b>Versioning modele</b> : <i>MLflow Model Registry</i> avec stages "
        "<i>Staging</i> et <i>Production</i>, permettant un retour arriere instantane "
        "en cas de regression detectee.",
        "<b>Versioning donnees</b> : <i>DVC</i> avec remote S3 ou MinIO interne, pour "
        "reproduire toute experience anterieure a partir de son commit Git.",
        "<b>Monitoring drift</b> : <i>Evidently AI</i> avec rapport HTML genere "
        "automatiquement chaque semaine, integre au dashboard via iframe.",
        "<b>Orchestration retrain</b> : <i>Prefect</i> ou <i>Airflow</i> avec un DAG "
        "hebdomadaire de re-entrainement, declenche soit par planification, soit par "
        "alerte de drift PSI superieure a 0.25 sur une feature critique.",
        "<b>Containerisation</b> : <i>Docker</i> + <i>docker-compose</i> avec services "
        "<i>app</i>, <i>db</i>, <i>mlflow</i>, <i>worker</i>, <i>monitoring</i>.",
        "<b>Observabilite</b> : logs structures via <i>loguru</i> ou <i>structlog</i>, "
        "exporter Prometheus, dashboards Grafana, alerting Sentry sur erreurs "
        "applicatives.",
    ]),

    H2("3.5.3 Roadmap operationnelle a six mois"),
    P("Sur la base de cette architecture cible, une roadmap operationnelle a six mois est "
      "proposee : mois 1 - dockerisation du dashboard actuel et exposition d'une API "
      "interne FastAPI minimaliste. Mois 2 - migration de l'inference vers FastAPI, ajout "
      "de PostgreSQL pour l'historisation. Mois 3 - integration MLflow Model Registry. "
      "Mois 4 - integration DVC pour le versioning data. Mois 5 - boucle de feedback "
      "planificateur (apprentissage actif sur corrections). Mois 6 - mise en place du "
      "monitoring de drift automatise (Evidently) et activation du retrain planifie. Cette "
      "roadmap reste indicative et necessitera un arbitrage budgetaire dedie de la direction "
      "supply chain de GE.", S_PN),

    H2("3.5.4 Convergence avec DDMRP en production"),
    P("Une perspective specifique merite d'etre soulignee : l'articulation operationnelle "
      "entre le modele predictif et la grille DDMRP. La comparaison conduite en section 2.3.4 "
      "a montre que l'IA et DDMRP ne sont pas substituables mais complementaires. Une "
      "implementation cible coherente consisterait a utiliser la prediction IA comme entree "
      "du calcul du <i>Net Flow Position</i> de DDMRP, et a maintenir les buffers vert / "
      "jaune / rouge comme indicateurs visuels lisibles par les planificateurs. Cette "
      "hybridation IA + DDMRP constituerait une contribution methodologique reutilisable au-dela "
      "du seul perimetre GE et meriterait une formalisation academique distincte.", S_PN),
    PageBreak(),
]

# ---------- 3.6 Conclusion ----------
story += [
    H1("3.6 Conclusion generale"),
    P("Ce memoire a entrepris de demontrer qu'une approche <i>Demand-Driven</i> appuyee sur "
      "l'intelligence artificielle peut produire une prediction operationnelle exploitable "
      "de la demande client - en quantite et en date - pour soutenir un planificateur supply "
      "chain dans son arbitrage quotidien, sans le remplacer. Au terme du parcours methodologique "
      "qui a structure les trois parties du document, plusieurs apports complementaires "
      "meritent d'etre recapitules pour formaliser le bilan du travail.", S_PN),

    H2("3.6.1 Apports methodologiques"),
    P("Le premier apport est la mise en place d'un pipeline complet et reproductible : "
      "audit, nettoyage, enrichissement, etudes statistiques, modelisation, dashboard, "
      "evaluation. Une dizaine de notebooks principaux et un dossier <i>models/</i> serialise "
      "documentent ce pipeline et garantissent sa reproductibilite par tout lecteur disposant "
      "des donnees sources. Le second apport est l'integration d'une demarche d'evaluation "
      "honnete : definition explicite d'une baseline historique exigeante, test statistique "
      "de Diebold-Mariano pour valider la superiorite du modele, monitoring de derive par "
      "Population Stability Index sur les features critiques, et confrontation systematique "
      "a une baseline DDMRP de reference academique. Le troisieme apport est l'articulation "
      "entre IA pure et DDMRP, qui rompt avec la dichotomie habituelle entre <i>methodes "
      "traditionnelles</i> et <i>methodes machine learning</i> pour proposer une hybridation "
      "operationnelle defendable devant un jury comme devant un comite operationnel.", S_PN),

    H2("3.6.2 Apports professionnels pour GE"),
    P("Les livrables remis a GE comprennent : un dataset propre "
      "et enrichi de 349 390 lignes (utilisable pour d'autres analyses ulterieures), cinq "
      "modeles serialises avec leur historique d'hyperparametres et leurs metriques mesurees "
      "(directement re-entrainables via le script <i>src/retrain.py</i>), un dashboard "
      "Streamlit multipage operationnel sur un poste planificateur standard, un document "
      "<i>model card</i> conforme aux standards en vigueur (Google, Hugging Face), une "
      "<i>matrice de gouvernance HITL</i> directement integree au dashboard et un document "
      "de feuille de route a six mois pour la mise en production. Cet ensemble constitue un "
      "MVP complet, immediatement testable en interne, et structure pour preparer un "
      "deploiement plus ambitieux.", S_PN),

    H2("3.6.3 Apports academiques et personnels"),
    P("Sur le plan academique, le memoire propose une demonstration pas-a-pas qu'un projet "
      "machine learning industriel peut etre honnete sur ses reussites comme sur ses limites. "
      "La precision agregee de 61.7 pourcents obtenue sur la quantite par XGBoost v2 depasse "
      "l'objectif <i>North Star</i> de 60 pourcents et constitue un acquis robuste, tandis "
      "que la prediction de date par LSTM (25.5 pourcents +/-7 jours) reste un echec relatif "
      "assume et documente. Cette dualite assumee - reussite quantite, echec date - est "
      "paradoxalement l'un des principaux apports methodologiques du document, dans un "
      "contexte ou la litterature applicative tend a sur-promettre les performances "
      "obtenues. Sur le plan personnel, ce travail a permis de cumuler une experience "
      "concrete sur l'ensemble de la chaine data science (de l'ingenierie au deploiement), "
      "d'approfondir la litterature DDMRP a l'interface entre supply chain academique et "
      "machine learning applique, et de prendre la mesure des compromis necessaires entre "
      "performance brute, interpretabilite et gouvernance humaine.", S_PN),

    H2("3.6.4 Limites du travail et ouverture"),
    P("Les limites du travail ont ete listees au fil du document et ne seront pas reprises "
      "exhaustivement ici. Quatre points appellent neanmoins une mention finale. "
      "Premierement, le perimetre temporel d'entrainement (2021-2023) contient deux regimes "
      "atypiques (Covid puis crise energetique 2022) dont l'effet residuel sur le modele "
      "ne sera entierement quantifiable qu'a posteriori, apres plusieurs annees de regime "
      "normalise. Deuxiemement, l'absence de donnees promotionnelles dans le jeu source "
      "constitue une limite informationnelle structurelle, dont la levee passerait par une "
      "evolution du systeme ERP source. Troisiemement, le perimetre purement quantitatif "
      "du projet n'integre pas la dimension qualitative des relations commerciales (verbatim "
      "client, signaux faibles d'evolution de strategie), dimension qui constitue pourtant "
      "une part importante de l'expertise reelle d'un planificateur. Quatriemement, le "
      "deploiement en production reste un livrable conceptuel ; la traduction operationnelle "
      "complete du systeme passera par les six mois de roadmap detailles section 3.5.3, "
      "qui ne relevent plus du Master mais d'un projet professionnel ulterieur.", S_PN),
    P("Au-dela de ces limites, et de l'humilite que doit conserver tout praticien d'un "
      "domaine ou les modeles vieillissent plus vite que les pratiques metier, le projet "
      "demontre qu'une approche scientifique rigoureuse peut etre conjuguee a une exigence "
      "operationnelle sans renoncer a la honnetete intellectuelle qui doit caracteriser un "
      "travail academique. La trajectoire ainsi tracee - de la donnee brute a la "
      "recommandation explicable, du score statistique a la matrice de gouvernance, du "
      "tableau de metriques au dashboard interactif - vaut, espere-t-on, comme contribution "
      "modeste mais reproductible au champ encore jeune de l'IA appliquee a la chaine "
      "d'approvisionnement industrielle.", S_PN),
    PageBreak(),
]

# ---------- BIBLIO ----------
story += [
    H1("Bibliographie"),
    P("Bai, S., Kolter, J. Z., & Koltun, V. (2018). An Empirical Evaluation of Generic "
      "Convolutional and Recurrent Networks for Sequence Modeling. <i>arXiv:1803.01271</i>.",
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
      "(2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. <i>Advances "
      "in Neural Information Processing Systems</i>, 30.", S_PN),
    P("Koenker, R., & Bassett, G. (1978). Regression Quantiles. <i>Econometrica</i>, "
      "46(1), 33-50.", S_PN),
    P("Lim, B., Arik, S. O., Loeff, N., & Pfister, T. (2021). Temporal Fusion Transformers "
      "for interpretable multi-horizon time series forecasting. <i>International Journal "
      "of Forecasting</i>, 37(4), 1748-1764.", S_PN),
    P("Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting Model "
      "Predictions. <i>Advances in Neural Information Processing Systems</i>, 30.", S_PN),
    P("Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022). The M5 competition: "
      "Background, organization, and implementation. <i>International Journal of "
      "Forecasting</i>, 38(4), 1325-1336.", S_PN),
    P("Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., "
      "Spitzer, E., Raji, I. D., & Gebru, T. (2019). Model Cards for Model Reporting. "
      "<i>Proceedings of the Conference on Fairness, Accountability, and Transparency</i>, "
      "220-229.", S_PN),
    P("Parlement europeen et Conseil de l'Union europeenne (2016). Reglement (UE) 2016/679 "
      "du 27 avril 2016 relatif a la protection des personnes physiques a l'egard du "
      "traitement des donnees a caractere personnel (RGPD).", S_PN),
    P("Parlement europeen et Conseil de l'Union europeenne (2024). Reglement etablissant "
      "des regles harmonisees concernant l'intelligence artificielle (AI Act).", S_PN),
    P("Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., & Gulin, A. (2018). "
      "CatBoost: unbiased boosting with categorical features. <i>Advances in Neural "
      "Information Processing Systems</i>, 31.", S_PN),
    P("Ptak, C., & Smith, C. (2016). <i>Demand Driven Material Requirements Planning "
      "(DDMRP)</i>. Industrial Press.", S_PN),
    P("Wu, X., Xiao, L., Sun, Y., Zhang, J., Ma, T., & He, L. (2022). A survey of "
      "human-in-the-loop for machine learning. <i>Future Generation Computer Systems</i>, "
      "135, 364-381.", S_PN),
    P("Zhou, H., Zhang, S., Peng, J., Zhang, S., Li, J., Xiong, H., & Zhang, W. (2021). "
      "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting. "
      "<i>Proceedings of the AAAI Conference on Artificial Intelligence</i>, 35(12), "
      "11106-11115.", S_PN),
    PageBreak(),
]

# ---------- ANNEXES ----------
story += [
    H1("Annexes"),
    H2("Annexe A - Liste des notebooks et livrables"),
    *bullets([
        "<i>notebooks/01_data_cleaning.ipynb</i> - Pipeline de nettoyage des donnees brutes",
        "<i>notebooks/02_statistical_study.ipynb</i> - Etudes statistiques et "
        "enrichissement exogene",
        "<i>notebooks/02bis_eda_dataset_enrichi.ipynb</i> - EDA pre-modelisation",
        "<i>notebooks/03_model_training.ipynb</i> - Entrainement de la premiere "
        "generation de modeles (XGBoost, LightGBM, LSTM)",
        "<i>notebooks/04_feature_engineering_lags.ipynb</i> - Enrichissement "
        "autoregressif (lags, rolling, target encoding) et XGBoost v2",
        "<i>notebooks/09_baseline_ddmrp.ipynb</i> - Baseline DDMRP",
        "<i>notebooks/10_catboost_stacking.ipynb</i> - CatBoost v2 et Stacking Ridge",
        "<i>notebooks/11_backtest_2025_precompute.ipynb</i> - Precomputation du "
        "backtest hebdomadaire",
        "<i>dashboard/app.py</i> + <i>dashboard/pages/*.py</i> - Dashboard Streamlit",
        "<i>src/retrain.py</i> - Script de re-entrainement",
        "<i>reports/rapport_phase1_data_engineering.pdf</i>, "
        "<i>reports/rapport_phase2.md</i>",
        "<i>reports/rapport_modelisation.json</i>, "
        "<i>reports/sprint_a_chantier1_metrics.json</i>, "
        "<i>reports/sprint_b_chantier1_stacking.json</i>, "
        "<i>reports/sprint_b_chantier3_ddmrp.json</i>",
        "<i>docs/MODEL_CARD.md</i> - Model card complete",
    ]),

    H2("Annexe B - Extrait Model Card (synthese)"),
    P("<b>Identification</b> : XGBoost v2 - <i>models/xgboost_optuna_v2.pkl</i> "
      "(configuration de service principale). Architecture alternative : Stacking Ridge - "
      "<i>models/stacking_ridge.pkl</i>. Auteur : redacteur du memoire - date : mai 2026.", S_PN),
    P("<b>Usage prevu</b> : prediction de la quantite demandee par couple "
      "client-article-mois, horizon M+1 a M+3, en appui d'un planificateur "
      "supply chain.", S_PN),
    P("<b>Usage non recommande</b> : articles jamais vus en entrainement (couples "
      "totalement inconnus), ruptures de regime geopolitique brutales, "
      "premieres commandes de nouveaux clients.", S_PN),
    P("<b>Donnees d'entrainement</b> : 210 641 lignes, perimetre 2021-2023, 47 features "
      "(28 statiques + 19 autoregressives).", S_PN),
    P("<b>Metriques globales</b> (test 2025) : MAE 8.42, RMSE 101.83, R^2 0.666, "
      "WAPE 0.383, precision agregee 61.7 pourcents. Configuration <i>Stacking Ridge</i> "
      "alternative : MAE 8.70, RMSE 97.55, R^2 0.694. Voir tableau 5.", S_PN),
    P("<b>Limites identifiees</b> : precision LSTM date faible (a remplacer par survival "
      "analysis), longue traine sous-performante (a traiter par Croston / TSB).", S_PN),
    P("<b>Biais ethiques</b> : sous-performance sur les petits clients et les articles "
      "rares (cf. section 3.2.3).", S_PN),
    P("<b>Date de prochaine revue</b> : decembre 2026, ou plus tot si une alerte de "
      "drift PSI superieure a 0.25 est levee sur une feature critique.", S_PN),
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
                         title="Memoire GE - Systeme de Prevision et d'Optimisation des Stocks",
                         author="Adham Marrakchi",
                         subject="M1 Expert IT - IA et Big Data - Memoire de fin d'etudes")
        frame = Frame(MARGIN, MARGIN, A4[0] - 2 * MARGIN, A4[1] - 2 * MARGIN,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                      id="normal")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=frame, onPage=cover_page),
            PageTemplate(id="main", frames=frame, onPage=header_footer),
        ])

    def afterPage(self):
        # passe en template "main" apres la premiere page
        if self.page == 1:
            self._handle_nextPageTemplate("main")


print(f"[gen] Construction du PDF -> {OUT}")
doc = MyDoc(str(OUT))
doc.build(story)
print(f"[gen] OK - PDF genere : {OUT}")
print(f"[gen] Taille : {OUT.stat().st_size / 1024:.1f} KB")
