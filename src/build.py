"""
Generates the SVG assets for the GitHub profile README.

Every SVG is fully self-contained: the fonts are subset to exactly the
characters each file uses and embedded as base64 WOFF2. That matters because
GitHub serves README images through its image proxy as plain <img> tags, which
can't load external fonts, scripts or links.

Run:  python3 src/build.py      (needs: pip install fonttools brotli)
Edit the PROFILE dict below and re-run to update the text.
"""
import base64
import io
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

SRC = Path(__file__).parent
OUT = SRC.parent / "assets"
FONTS = SRC / "fonts"

# ----------------------------------------------------------------- content --
PROFILE = {
    "name": "Noah Klaholz",
    "kicker": "SECURITY OPERATIONS  /  COMPUTER SCIENCE",
    "tagline": "Security Operations · University of Basel",
    "footer_left": "BASEL, CH  ·  B.SC. COMPUTER SCIENCE",
    "whoami": [
        ("name", "Noah Valentin Klaholz"),
        ("role", "Student Assistant, Security Operations"),
        ("org", "University of Basel · IT Security & Architecture"),
        ("study", "B.Sc. Computer Science, University of Basel"),
        ("focus", "SecOps · Vulnerability Mgmt · Web App Security"),
        ("tools", "Nessus · Microsoft XDR · Azure · AD · Burp Suite"),
        ("code", "Java · Python · C · SQL"),
    ],
    "now": [
        ["Leaked-credential response", "& process design"],
        ["PortSwigger Web Security", "Academy"],
    ],
    "highlight": [["Hack the North 2026", "Winner"]],
    "buttons": [
        ("portfolio", "PORTFOLIO", "noahklaholz.netlify.app", "globe"),
        ("linkedin", "LINKEDIN", "in/noah-klaholz", "briefcase"),
        ("email", "EMAIL", "noahk2006@gmx.de", "mail"),
    ],
}

# ------------------------------------------------------------------ tokens --
C = {
    "bg": "#0A0F14",
    "panel": "#0D141B",
    "border": "#1D2A35",
    "line": "#1A252F",
    "text": "#E6EDF3",
    "muted": "#9AA7B4",
    "dim": "#5C6976",
    "accent": "#2DD4BF",
}

FONT_FILES = {
    "nk-sans": "SourceSans3-Regular.otf",
    "nk-sans-sb": "SourceSans3-Semibold.otf",
    "nk-mono": "JetBrainsMono-Regular.ttf",
    "nk-mono-md": "JetBrainsMono-Medium.ttf",
    "nk-mono-sb": "JetBrainsMono-SemiBold.ttf",
}
FALLBACK = {
    "nk-sans": "'Segoe UI',Helvetica,Arial,sans-serif",
    "nk-sans-sb": "'Segoe UI',Helvetica,Arial,sans-serif",
    "nk-mono": "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
    "nk-mono-md": "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
    "nk-mono-sb": "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
}


def subset_woff2(font_key: str, chars: str) -> str:
    font = TTFont(FONTS / FONT_FILES[font_key])
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = []
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=chars + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


class SVG:
    """Tiny SVG builder that records which glyphs each font needs."""

    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.body = []
        self.used = {}
        self.css = []

    def add(self, s):
        self.body.append(s)

    def text(self, x, y, s, font="nk-sans", size=16, fill=None, ls=0,
             anchor="start", extra=""):
        self.used.setdefault(font, set()).update(s)
        fill = fill or C["text"]
        lsa = f' letter-spacing="{ls}"' if ls else ""
        self.add(
            f'<text x="{x}" y="{y}" class="{font}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"{lsa} {extra}>{escape(s)}</text>'
        )

    def tspan_text(self, x, y, parts, size=16, extra=""):
        """parts: list of (string, font, fill)"""
        spans = []
        for part in parts:
            s, font, fill = part[:3]
            cls = f"{font} {part[3]}" if len(part) > 3 else font
            self.used.setdefault(font, set()).update(s)
            spans.append(
                f'<tspan class="{cls}" fill="{fill}">{escape(s)}</tspan>')
        self.add(f'<text x="{x}" y="{y}" font-size="{size}" '
                 f'xml:space="preserve" {extra}>{"".join(spans)}</text>')

    def render(self):
        faces, classes = [], []
        for key, chars in sorted(self.used.items()):
            data = subset_woff2(key, "".join(sorted(chars)))
            faces.append(
                f"@font-face{{font-family:'{key}';"
                f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")
            classes.append(f".{key}{{font-family:'{key}',{FALLBACK[key]};}}")
        classes.append(".nk-sans,.nk-sans-sb{word-spacing:0.09em;}")
        style = "\n".join(faces + classes + self.css + [
            "@media (prefers-reduced-motion: reduce){"
            "*{animation:none!important;}}"
        ])
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
            f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
            f'role="img" aria-label="{escape(self.title)}">\n'
            f"<title>{escape(self.title)}</title>\n"
            f"<style>\n{style}\n</style>\n" + "\n".join(self.body) + "\n</svg>\n"
        )


def frame(svg, w, h, rx=14, brackets=True):
    """Card background, dot grid and corner brackets shared by all assets."""
    svg.add(f"""
<defs>
  <clipPath id="clip"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="1" fill="{C['muted']}" opacity="0.18"/>
  </pattern>
  <linearGradient id="fadeDots" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0.15"/>
    <stop offset="0.55" stop-color="#fff" stop-opacity="0.6"/>
    <stop offset="1" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="dotMask"><rect width="{w}" height="{h}" fill="url(#fadeDots)"/></mask>
</defs>
<g clip-path="url(#clip)">
  <rect width="{w}" height="{h}" fill="{C['bg']}"/>
  <rect width="{w}" height="{h}" fill="url(#dots)" mask="url(#dotMask)"/>
</g>""")
    if brackets:
        s, o = 18, 16
        col = C["dim"]
        svg.add(f"""<g stroke="{col}" stroke-width="1.5" fill="none">
  <path d="M{o} {o+s} V{o} H{o+s}"/>
  <path d="M{w-o-s} {o} H{w-o} V{o+s}"/>
  <path d="M{o} {h-o-s} V{h-o} H{o+s}"/>
  <path d="M{w-o-s} {h-o} H{w-o} V{h-o-s}"/>
</g>""")


def border(svg, w, h, rx=14):
    svg.add(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" '
            f'fill="none" stroke="{C["border"]}"/>')


# ------------------------------------------------------------------ banner --
def banner():
    W, H = 1200, 320
    svg = SVG(W, H, f"{PROFILE['name']} — {PROFILE['tagline']}")
    frame(svg, W, H)
    cx, cy = 1010, 138
    svg.css.append(
        f"@keyframes sweep{{to{{transform:rotate(360deg);}}}}"
        f".sweep{{transform-origin:{cx}px {cy}px;animation:sweep 9s linear infinite;}}"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        ".cursor{animation:blink 1.1s steps(1) infinite;}"
        "@keyframes ping{0%{opacity:0}8%{opacity:1}40%{opacity:0}100%{opacity:0}}"
        ".ping{opacity:0;animation:ping 9s linear infinite;}"
    )
    # glow + radar scope
    svg.add(f"""
<defs>
  <radialGradient id="glow" cx="{cx}" cy="{cy}" r="420" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="{C['accent']}" stop-opacity="0.14"/>
    <stop offset="1" stop-color="{C['accent']}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="sweepGrad" x1="{cx}" y1="{cy}" x2="{cx+106}" y2="{cy-50}" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="{C['accent']}" stop-opacity="0"/>
    <stop offset="1" stop-color="{C['accent']}" stop-opacity="0.35"/>
  </linearGradient>
</defs>
<g clip-path="url(#clip)">
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <g fill="none" stroke="{C['accent']}" stroke-opacity="0.22">
    <circle cx="{cx}" cy="{cy}" r="36"/>
    <circle cx="{cx}" cy="{cy}" r="72"/>
    <circle cx="{cx}" cy="{cy}" r="108" stroke-dasharray="2 6"/>
    <path d="M{cx-124} {cy} H{cx+124} M{cx} {cy-108} V{cy+108}" stroke-opacity="0.12"/>
  </g>
  <g class="sweep">
    <path d="M{cx} {cy} L{cx+108} {cy} A108 108 0 0 0 {cx+93.5} {cy-54} Z" fill="url(#sweepGrad)"/>
    <line x1="{cx}" y1="{cy}" x2="{cx+108}" y2="{cy}" stroke="{C['accent']}" stroke-opacity="0.7"/>
  </g>
  <circle cx="{cx}" cy="{cy}" r="3" fill="{C['accent']}"/>
  <g class="ping" style="animation-delay:-6.6s"><circle cx="{cx+50}" cy="{cy+46}" r="3.5" fill="{C['accent']}"/>
    <circle cx="{cx+50}" cy="{cy+46}" r="9" fill="none" stroke="{C['accent']}" stroke-opacity="0.5"/></g>
  <g class="ping" style="animation-delay:-2.1s"><circle cx="{cx-58}" cy="{cy-30}" r="3" fill="{C['accent']}"/>
    <circle cx="{cx-58}" cy="{cy-30}" r="8" fill="none" stroke="{C['accent']}" stroke-opacity="0.5"/></g>
</g>""")
    X = 72
    svg.text(X, 104, PROFILE["kicker"], "nk-mono-md", 13, C["accent"], ls=3)
    svg.text(X - 3, 176, PROFILE["name"], "nk-sans-sb", 68, C["text"], ls=-0.5)
    svg.tspan_text(X, 218, [("$ ", "nk-mono-md", C["accent"]),
                            (PROFILE["tagline"] + " ", "nk-mono", C["muted"]),
                            ("\u2588", "nk-mono", C["accent"], "cursor")], size=18)
    # footer
    svg.add(f'<line x1="{X}" y1="258" x2="{W-72}" y2="258" stroke="{C["line"]}"/>')
    svg.text(X, 285, PROFILE["footer_left"], "nk-mono", 12, C["dim"], ls=2.2)
    pill_w = 92
    px = W - 72 - pill_w
    svg.add(f'<rect x="{px}" y="270" width="{pill_w}" height="22" rx="4" '
            f'fill="none" stroke="{C["muted"]}" stroke-opacity="0.55"/>')
    svg.text(px + pill_w / 2, 285.5, "TLP:CLEAR", "nk-mono-md", 11.5,
             C["text"], ls=1.5, anchor="middle")
    border(svg, W, H)
    return svg


# ---------------------------------------------------------------- identity --
def identity():
    W, H = 1200, 400
    rows = PROFILE["whoami"]
    svg = SVG(W, H, " · ".join(v for _, v in rows[1:4]))
    frame(svg, W, H, brackets=False)
    svg.css.append(
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        ".cursor{animation:blink 1.1s steps(1) infinite;}")
    # window header
    svg.add(f'<path d="M0 14 A14 14 0 0 1 14 0 H{W-14} A14 14 0 0 1 {W} 14 V48 H0 Z" '
            f'fill="{C["panel"]}"/>')
    svg.add(f'<line x1="0" y1="48.5" x2="{W}" y2="48.5" stroke="{C["border"]}"/>')
    for i in range(3):
        svg.add(f'<circle cx="{28 + i*18}" cy="24" r="5" fill="none" '
                f'stroke="{C["dim"]}" stroke-width="1.5"/>')
    svg.text(W / 2, 29, "noah@basel: ~", "nk-mono", 13, C["muted"], anchor="middle")
    svg.add(f'<circle cx="{W-110}" cy="24.5" r="4" fill="{C["accent"]}"/>')
    svg.text(W - 98, 29, "ONLINE", "nk-mono-md", 11.5, C["muted"], ls=2)

    # left: whoami
    X, Y0, LH = 48, 98, 32
    svg.tspan_text(X, Y0, [("$ ", "nk-mono-md", C["accent"]),
                           ("whoami --verbose", "nk-mono", C["text"])], size=16)
    for i, (k, v) in enumerate(rows):
        y = Y0 + 40 + i * LH
        svg.text(X + 18, y, k, "nk-mono", 15.5, C["dim"])
        svg.text(X + 118, y, v, "nk-mono", 15.5, C["text"])
    ylast = Y0 + 40 + len(rows) * LH + 8
    svg.tspan_text(X, ylast, [("$ ", "nk-mono-md", C["accent"]),
                              ("\u2588", "nk-mono", C["accent"], "cursor")], size=16)

    # divider
    DX = 832
    svg.add(f'<line x1="{DX}" y1="84" x2="{DX}" y2="{H-36}" stroke="{C["line"]}"/>')

    # right: now / highlight
    RX = DX + 40
    y = 104

    def section(label, items, y):
        svg.text(RX, y, label, "nk-mono-md", 12, C["accent"], ls=2.5)
        y += 34
        for lines in items:
            svg.add(f'<path d="M{RX} {y-11} l7 5 -7 5" fill="none" '
                    f'stroke="{C["muted"]}" stroke-width="1.6" stroke-linecap="round" '
                    f'stroke-linejoin="round"/>')
            for j, ln in enumerate(lines):
                svg.text(RX + 20, y + j * 22, ln,
                         "nk-sans-sb" if j == 0 else "nk-sans", 17,
                         C["text"] if j == 0 else C["muted"])
            y += 22 * len(lines) + 16
        return y

    y = section("NOW", PROFILE["now"], y)
    y = section("HIGHLIGHT", PROFILE["highlight"], y + 14)
    border(svg, W, H)
    return svg


# ----------------------------------------------------------------- buttons --
ICONS = {
    "globe": '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/>'
             '<path d="M3 12h18M4.6 7.5h14.8M4.6 16.5h14.8"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/>'
                 '<path d="M8.5 7V5.5A1.5 1.5 0 0 1 10 4h4a1.5 1.5 0 0 1 1.5 1.5V7"/>'
                 '<path d="M3 12.5h18"/><path d="M11 12.5v1.5h2v-1.5"/>',
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="2"/>'
            '<path d="M3.5 7l8.5 6.2L20.5 7"/>',
}


def button(idx, key, label, handle, icon):
    W, H = 400, 92
    svg = SVG(W, H, f"{label.title()} — {handle}")
    frame(svg, W, H, rx=12, brackets=False)
    # accent rail
    svg.add(f'<rect x="0" y="0" width="3" height="{H}" fill="{C["accent"]}" '
            f'clip-path="url(#clip)"/>')
    # icon box
    svg.add(f'<rect x="24.5" y="22.5" width="47" height="47" rx="9" '
            f'fill="{C["panel"]}" stroke="{C["border"]}"/>')
    svg.add(f'<g transform="translate(36 34)" fill="none" stroke="{C["accent"]}" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONS[icon]}</g>')
    svg.text(92, 44, label, "nk-mono-sb", 15, C["text"], ls=3)
    svg.text(92, 67, handle, "nk-mono", 13, C["muted"])
    svg.text(W - 24, 30, f"0{idx}", "nk-mono", 11, C["dim"], ls=1.5, anchor="end")
    svg.add(f'<path d="M{W-34} 52 l6 6 -6 6" fill="none" stroke="{C["accent"]}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    border(svg, W, H, rx=12)
    return svg


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {"banner.svg": banner(), "identity.svg": identity()}
    for i, (key, label, handle, icon) in enumerate(PROFILE["buttons"], 1):
        files[f"btn-{key}.svg"] = button(i, key, label, handle, icon)
    for name, svg in files.items():
        data = svg.render()
        (OUT / name).write_text(data, encoding="utf-8")
        print(f"{name:18s} {len(data)/1024:6.1f} KB")


if __name__ == "__main__":
    main()
