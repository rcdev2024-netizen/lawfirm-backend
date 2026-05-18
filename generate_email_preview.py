from PIL import Image, ImageDraw, ImageFont
import os

# Canvas
W, H = 680, 980
img = Image.new("RGB", (W, H), "#f4f4f4")
draw = ImageDraw.Draw(img)

# ── Fonts (fallback to default if no TTF available) ──────────────────────────
def font(size, bold=False):
    try:
        name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(name, size)
    except:
        return ImageFont.load_default()

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY      = "#1a1f36"
GOLD      = "#c9a84c"
WHITE     = "#ffffff"
LIGHT_BG  = "#f9f7f2"
MUTED     = "#6b7280"
BORDER    = "#e5e0d5"
DARK_TEXT = "#1a1f36"

# ── Helper ────────────────────────────────────────────────────────────────────
def rect(x1, y1, x2, y2, fill, radius=0):
    if radius:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)
    else:
        draw.rectangle([x1, y1, x2, y2], fill=fill)

def text(txt, x, y, color, size, bold=False, anchor="la"):
    draw.text((x, y), txt, fill=color, font=font(size, bold), anchor=anchor)

def hline(y, color=BORDER, x1=40, x2=640):
    draw.line([(x1, y), (x2, y)], fill=color, width=1)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER  (navy bar)
# ═══════════════════════════════════════════════════════════════════════════════
rect(0, 0, W, 110, NAVY)

# Gold accent bar at very top
rect(0, 0, W, 5, GOLD)

# Firm name
text("Atty Rochelle Cortez-Naz", W//2, 38, WHITE, 18, bold=True, anchor="mm")
text("LAW OFFICE", W//2, 60, GOLD, 11, anchor="mm")

# Tagline
text("Your Rights. My Commitment.", W//2, 85, "#c0bfba", 10, anchor="mm")

# ═══════════════════════════════════════════════════════════════════════════════
# HERO BANNER  (gold strip)
# ═══════════════════════════════════════════════════════════════════════════════
rect(0, 110, W, 160, GOLD)
text("APPOINTMENT NOTIFICATION", W//2, 135, NAVY, 15, bold=True, anchor="mm")

# ═══════════════════════════════════════════════════════════════════════════════
# BODY CARD
# ═══════════════════════════════════════════════════════════════════════════════
rect(30, 170, W-30, 820, WHITE, radius=6)

# Greeting
text("Dear Atty. Rochelle,", 60, 200, DARK_TEXT, 13, bold=True)

# Intro paragraph
intro = (
    "A new appointment transaction has been recorded on the Law Firm Portal.\n"
    "Please review the details below."
)
y = 228
for line in intro.split("\n"):
    text(line, 60, y, MUTED, 11)
    y += 20

# ── Details table ─────────────────────────────────────────────────────────────
y = 278
hline(y, GOLD, 60, W-60)
y += 14

rows = [
    ("Transaction Type",  "{{transaction_type}}"),
    ("Appointment ID",    "{{appointment_id}}"),
    ("Client Name",       "{{client_name}}"),
    ("Attorney",          "{{attorney_name}}"),
    ("Date & Time",       "{{appointment_date}}  ·  {{appointment_time}}"),
    ("Mode",              "{{appointment_mode}}"),
    ("Practice Area",     "{{practice_area}}"),
    ("Status",            "{{status}}"),
    ("Notes",             "{{notes}}"),
]

for label, value in rows:
    # label col
    rect(60, y, 230, y+30, LIGHT_BG, radius=3)
    text(label, 70, y+9, MUTED, 10, bold=True)
    # value col
    rect(235, y, W-60, y+30, WHITE, radius=3)
    draw.rectangle([235, y, W-60, y+30], outline=BORDER, width=1)
    text(value, 245, y+9, DARK_TEXT, 10)
    y += 36

hline(y, GOLD, 60, W-60)
y += 20

# ── Action button ─────────────────────────────────────────────────────────────
btn_x1, btn_y1 = W//2 - 120, y + 10
btn_x2, btn_y2 = W//2 + 120, y + 46
rect(btn_x1, btn_y1, btn_x2, btn_y2, NAVY, radius=4)
text("VIEW IN PORTAL", W//2, (btn_y1+btn_y2)//2, GOLD, 11, bold=True, anchor="mm")

y = btn_y2 + 30

# ── Closing note ──────────────────────────────────────────────────────────────
note = "This is an automated notification. Please do not reply to this email."
text(note, W//2, y, MUTED, 9, anchor="mm")

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
rect(0, 830, W, H, NAVY)
rect(0, 830, W, 833, GOLD)  # gold top border

text("Atty Rochelle Cortez-Naz Law Office", W//2, 858, WHITE, 11, bold=True, anchor="mm")
text("Legazpi City, Philippines  ·  attyrochellecortez.naz@gmail.com  ·  0917 123 4567", W//2, 878, "#9ca3af", 9, anchor="mm")
hline(900, "#2d3555", 60, W-60)
text("© 2025 Atty Rochelle Cortez-Naz Law Office. All Rights Reserved.", W//2, 918, "#6b7280", 8, anchor="mm")
text("Created by ZetaCodeSolutions | Your Automation Partner.", W//2, 938, "#4b5563", 8, anchor="mm")

# ── Save ──────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), "email_template_preview.png")
img.save(out, "PNG")
print(f"Saved: {out}")
