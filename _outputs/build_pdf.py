from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

OUTPUT = "_outputs/portfolio-gerresheimer-cphi-2025.pdf"

# ── Palette ──────────────────────────────────────────────────────────────────
INK        = colors.HexColor("#1A1A1A")
ACCENT     = colors.HexColor("#1B3A6B")   # deep navy — FR brand adjacent
LIGHT_RULE = colors.HexColor("#D8D8D8")
RULE       = colors.HexColor("#1B3A6B")
CELL_BG    = colors.HexColor("#F4F6FA")
QUOTE_BG   = colors.HexColor("#EEF2F8")

W, H = A4
MARGIN_L = 22*mm
MARGIN_R = 22*mm
MARGIN_T = 20*mm
MARGIN_B = 20*mm

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=MARGIN_L, rightMargin=MARGIN_R,
    topMargin=MARGIN_T, bottomMargin=MARGIN_B
)

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, **kw):
    s = ParagraphStyle(name, **kw)
    return s

EYEBROW = S("eyebrow",
    fontName="Helvetica", fontSize=8, leading=11,
    textColor=ACCENT, spaceAfter=1, tracking=1.5,
    alignment=TA_LEFT)

TITLE = S("title",
    fontName="Helvetica-Bold", fontSize=26, leading=30,
    textColor=INK, spaceAfter=4)

SUBTITLE = S("subtitle",
    fontName="Helvetica", fontSize=10, leading=14,
    textColor=colors.HexColor("#555555"), spaceAfter=2)

H2 = S("h2",
    fontName="Helvetica-Bold", fontSize=13, leading=17,
    textColor=ACCENT, spaceBefore=14, spaceAfter=5)

BODY = S("body",
    fontName="Helvetica", fontSize=10, leading=16,
    textColor=INK, spaceAfter=7, alignment=TA_LEFT)

BULLET = S("bullet",
    fontName="Helvetica", fontSize=10, leading=16,
    textColor=INK, spaceAfter=4, leftIndent=14, bulletIndent=0)

NUMLIST = S("numlist",
    fontName="Helvetica", fontSize=10, leading=16,
    textColor=INK, spaceAfter=4, leftIndent=14)

QUOTE = S("quote",
    fontName="Helvetica-Oblique", fontSize=13, leading=19,
    textColor=ACCENT, spaceAfter=4, alignment=TA_LEFT,
    leftIndent=6, rightIndent=6)

QUOTE_ATTR = S("quoteattr",
    fontName="Helvetica", fontSize=9, leading=13,
    textColor=colors.HexColor("#555555"), spaceAfter=2,
    leftIndent=6)

FOOTER = S("footer",
    fontName="Helvetica", fontSize=8, leading=11,
    textColor=colors.HexColor("#888888"), alignment=TA_CENTER)

LABEL = S("label",
    fontName="Helvetica-Bold", fontSize=8.5, leading=12,
    textColor=ACCENT)

VALUE = S("value",
    fontName="Helvetica", fontSize=10, leading=14,
    textColor=INK)

INSIGHT_HEAD = S("insighthead",
    fontName="Helvetica-Bold", fontSize=10, leading=14,
    textColor=INK, spaceAfter=2)

INSIGHT_BODY = S("insightbody",
    fontName="Helvetica", fontSize=10, leading=15,
    textColor=INK, spaceAfter=6)

NOTE = S("note",
    fontName="Helvetica-Oblique", fontSize=8.5, leading=12,
    textColor=colors.HexColor("#888888"), spaceAfter=2)

# ── Helpers ───────────────────────────────────────────────────────────────────
def rule(color=RULE, thickness=0.6, spaceB=4, spaceA=4):
    return HRFlowable(width="100%", thickness=thickness,
                      color=color, spaceAfter=spaceA, spaceBefore=spaceB)

def section(title, *paras):
    items = [H2_rule(title)]
    for p in paras:
        items.append(p)
    return items

def H2_rule(text):
    return KeepTogether([
        rule(ACCENT, 1.2, spaceB=12, spaceA=0),
        Paragraph(text, H2),
    ])

# ── Story ─────────────────────────────────────────────────────────────────────
story = []

# — Header block —
story.append(Spacer(1, 2*mm))
story.append(Paragraph("CASE STUDY", EYEBROW))
story.append(Paragraph("Gerresheimer at CPhI Worldwide 2025", TITLE))
story.append(Paragraph("Frankfurt &nbsp;·&nbsp; October 2025 &nbsp;·&nbsp; 18 sqm Island &nbsp;·&nbsp; Exec: Chinmay", SUBTITLE))
story.append(rule(ACCENT, 2, spaceB=6, spaceA=10))

# — Stat bar —
stat_data = [
    [Paragraph("STAND SIZE", LABEL),  Paragraph("18 sqm island", VALUE),
     Paragraph("MEETINGS", LABEL),    Paragraph("47 qualified", VALUE),
     Paragraph("RFQs ON FLOOR", LABEL), Paragraph("3", VALUE)],
]
stat_table = Table(stat_data, colWidths=[28*mm, 32*mm, 22*mm, 32*mm, 30*mm, 22*mm])
stat_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), CELL_BG),
    ("TOPPADDING",    (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ("RIGHTPADDING",  (0,0), (-1,-1), 4),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("BOX",           (0,0), (-1,-1), 0.5, LIGHT_RULE),
    ("LINEAFTER",     (1,0), (3,0),   0.4, LIGHT_RULE),
]))
story.append(stat_table)
story.append(Spacer(1, 8*mm))

# — The Brief —
story += section("The Brief")
story.append(Paragraph(
    "Gerresheimer came to us with a specific problem.", BODY))
story.append(Paragraph(
    "They were launching a new range of plastic primary packaging for biologics — "
    "high-precision, high-trust product category. The ask: make it feel premium. "
    "Make it feel like a pharmaceutical lab. But don't make it cold.", BODY))
story.append(Paragraph(
    "That's a harder brief than it sounds. Most pharma stands at CPhI look like hospital "
    "waiting rooms. White walls, catalogue stands, fluorescent overheads. Clinical without "
    "being credible. Sterile without being sophisticated.", BODY))
story.append(Paragraph(
    "Gerresheimer needed something different. Their buyers — formulation scientists, "
    "procurement heads, VP-level packaging decisions — walk past 300 booths in three days. "
    "The stand had to stop them. Then hold them.", BODY))

# — The Challenge —
story += section("The Challenge")
story.append(Paragraph(
    "18 sqm island at CPhI Worldwide is not a lot of real estate. Frankfurt Messe is one "
    "of the most competitive exhibition floors in the world — pharma companies routinely "
    "spend €300k+ on double-deck builds in the halls.", BODY))
story.append(Paragraph("Our constraints:", BODY))
for item in [
    "18 sqm, all four sides open",
    "Premium feel without oversized budget",
    "Product must be hero — not just displayed, but <i>experienced</i>",
    "Space for qualified conversations, not foot traffic",
]:
    story.append(Paragraph(f"&bull; &nbsp; {item}", BULLET))
story.append(Spacer(1, 3*mm))
story.append(Paragraph(
    "The risk: try to compete with the big builds on size and lose. Design something "
    "forgettable with the money saved. Neither option works for a client at this level.", BODY))

# — The Key Move —
story += section("The Key Move")
story.append(Paragraph("One decision changed everything.", BODY))
story.append(Paragraph(
    "We suspended a backlit ceiling panel at 2.8m — full footprint of the stand, "
    "slightly inset from the edges to create a floating halo effect. Warm white LED, "
    "diffused through frosted acrylic. No harsh downlight. No fluorescent flicker.", BODY))
story.append(Paragraph(
    "Under that ceiling, the product display became a lit island. A custom plinth, "
    "400mm raised, backlit from below in cool white. Each piece of packaging placed "
    "individually, spaced like objects in a design museum rather than a product catalogue.", BODY))
story.append(Paragraph("The ceiling did three things simultaneously:", BODY))
for i, item in enumerate([
    "<b>Created an immediate visual boundary</b> — you knew when you were 'inside' the Gerresheimer space",
    "<b>Lifted the ambient light temperature</b> to feel warm, not clinical",
    "<b>Made the product glow from two directions</b> — above and below — giving depth to objects that are, functionally, transparent containers",
], 1):
    story.append(Paragraph(f"{i}. &nbsp; {item}", NUMLIST))
story.append(Spacer(1, 3*mm))
story.append(Paragraph(
    "The meeting area sat in the rear quadrant: two chairs, one low table, brand graphic "
    "at eye height. Private enough for real conversation. Open enough to not feel trapped.", BODY))
story.append(Paragraph(
    "Brochure display: flush-mounted into the back column. Nothing on stands. Nothing cluttered.", BODY))

# — What Happened —
story += section("What Happened on the Floor")
story.append(Paragraph("Three days. Frankfurt. One of the busiest pharma shows in the calendar.", BODY))
for item in [
    "<b>47 qualified meetings</b> held at the stand over three days",
    "<b>3 RFQs generated on the floor</b> — packaging decisions initiated without leaving the booth",
    "Client contact described it as <i>\u201cthe best stand we\u2019ve had at CPhI\u201d</i>",
    "Within 4 weeks of the show: Gerresheimer briefed us for their <b>USA show</b> — unprompted",
]:
    story.append(Paragraph(f"&bull; &nbsp; {item}", BULLET))

# — Metrics table —
story.append(Spacer(1, 5*mm))
metrics = [
    ["Show", "CPhI Worldwide 2025, Frankfurt"],
    ["Stand size", "18 sqm island"],
    ["Meetings on floor", "47 qualified"],
    ["RFQs generated", "3"],
    ["Follow-on brief", "USA show (same client, same year)"],
    ["Images", "8 available (including 1 hero shot)"],
]
col_w = [(W - MARGIN_L - MARGIN_R) * f for f in [0.35, 0.65]]
t = Table([[Paragraph(k, LABEL), Paragraph(v, VALUE)] for k, v in metrics],
          colWidths=col_w)
t.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,-1), CELL_BG),
    ("BACKGROUND",    (0,0), (0,-1),  colors.HexColor("#E8EDF5")),
    ("TOPPADDING",    (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ("LINEBELOW",     (0,0), (-1,-2), 0.3, LIGHT_RULE),
    ("BOX",           (0,0), (-1,-1), 0.5, LIGHT_RULE),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
]))
story.append(t)
story.append(Spacer(1, 8*mm))

# — What This Proves —
story += section("What This Proves")
story.append(Paragraph("<b>Budget is not the constraint. Light is.</b>", BODY))
story.append(Paragraph(
    "Most exhibitors spend money on size and structure. They add walls, levels, features. "
    "Gerresheimer spent money on quality of experience within a tight footprint. "
    "The suspended ceiling cost less than a second storey. It worked harder.", BODY))
story.append(Paragraph("Three rules that apply to every pharma and high-trust brand brief:", BODY))

insights = [
    ("The product must be the hero.",
     "Not the brand wall. Not the architecture. The product. Everything else is a frame."),
    ("Warm light in a cold category creates contrast.",
     "Pharmaceutical = clinical = white and cold. Break that association and you stand out by default."),
    ("A small stand with one strong idea beats a large stand with no idea.",
     "Gerresheimer's 18 sqm held 47 qualified meetings. The double-deck next door held a lot of brochure giveaways."),
]
for head, body in insights:
    story.append(KeepTogether([
        Paragraph(f"<b>{head}</b>", INSIGHT_HEAD),
        Paragraph(body, INSIGHT_BODY),
    ]))

# — Quote block —
story.append(Spacer(1, 4*mm))
quote_data = [[
    Paragraph(
        "&ldquo;Best stand we've had at CPhI.<br/>We want to do the same for the USA show.&rdquo;",
        QUOTE),
    Paragraph("— Ravikumar, Gerresheimer", QUOTE_ATTR),
]]
qt = Table([[quote_data[0][0]], [quote_data[0][1]]],
           colWidths=[W - MARGIN_L - MARGIN_R])
qt.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,-1), QUOTE_BG),
    ("LEFTPADDING",   (0,0), (-1,-1), 14),
    ("RIGHTPADDING",  (0,0), (-1,-1), 14),
    ("TOPPADDING",    (0,0), (0,0),   12),
    ("BOTTOMPADDING", (0,0), (0,0),   4),
    ("TOPPADDING",    (0,1), (0,1),   2),
    ("BOTTOMPADDING", (0,1), (0,1),   12),
    ("LINEBEFORE",    (0,0), (-1,-1), 3, ACCENT),
]))
story.append(qt)
story.append(Spacer(1, 8*mm))

# — Footer —
story.append(rule(LIGHT_RULE, 0.5, spaceB=6, spaceA=6))
story.append(Paragraph(
    "First Rain Exhibits India Pvt. Ltd. &nbsp;·&nbsp; "
    "Custom exhibition stands — never modular &nbsp;·&nbsp; "
    "firstrain.in &nbsp;·&nbsp; Filed April 2026",
    FOOTER))

# ── Build ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f"PDF written: {OUTPUT}")
