"""
FedSanitize — Centralized Theme Module
=======================================
Single source of truth for:
  - Color palette constants
  - Plotly shared dark template
  - Streamlit CSS overrides (injected once from app.py)
"""

# ──────────────────────────────────────────────────────────────────────────────
# PALETTE CONSTANTS  (never use raw hex values outside this file)
# ──────────────────────────────────────────────────────────────────────────────
COLORS = {
    # Core four
    "void_black":     "#050508",   # Page canvas
    "midnight_blue":  "#0C1E3E",   # Cards / surfaces
    "cyan":           "#38FBDB",   # Primary accent
    "purple":         "#8E52F5",   # Secondary accent

    # Derived text
    "text_primary":   "#E8F1F5",
    "text_muted":     "#7B8AA3",

    # Semantic (tinted to palette)
    "success":        "#20D9A0",   # Cyan-green — honest/trusted
    "danger":         "#FF3B5C",   # Warm red — malicious confirmed (critical only)
    "warning":        "#F5A623",   # Amber — suspicious / under-review

    # Border
    "border_dim":     "rgba(56,251,219,0.15)",
    "border_bright":  "#38FBDB",
}

# Plotly series cycle
PLOTLY_SERIES = ["#38FBDB", "#8E52F5", "#7B8AA3", "#20D9A0", "#FF3B5C"]

# Plotly colorscale for heatmaps (viridis-like but in palette)
PLOTLY_HEATMAP_SCALE = [
    [0.0,  "#050508"],
    [0.25, "#0C1E3E"],
    [0.5,  "#8E52F5"],
    [0.75, "#38FBDB"],
    [1.0,  "#E8F1F5"],
]


def get_plotly_layout_defaults():
    """Returns a dict of layout kwargs to apply to every Plotly figure."""
    return dict(
        paper_bgcolor=COLORS["void_black"],
        plot_bgcolor=COLORS["void_black"],
        font=dict(color=COLORS["text_primary"], family="monospace"),
        title_font=dict(color=COLORS["cyan"], family="monospace"),
        xaxis=dict(
            gridcolor="rgba(56,251,219,0.10)",
            zerolinecolor="rgba(56,251,219,0.20)",
            tickfont=dict(color=COLORS["text_muted"]),
        ),
        yaxis=dict(
            gridcolor="rgba(56,251,219,0.10)",
            zerolinecolor="rgba(56,251,219,0.20)",
            tickfont=dict(color=COLORS["text_muted"]),
        ),
        legend=dict(
            bgcolor="rgba(12,30,62,0.8)",
            bordercolor=COLORS["border_dim"],
            borderwidth=1,
            font=dict(color=COLORS["text_primary"]),
        ),
        margin=dict(l=40, r=40, t=50, b=40),
    )


# ──────────────────────────────────────────────────────────────────────────────
# THEME CSS  (injected once into app.py via st.markdown)
# ──────────────────────────────────────────────────────────────────────────────
THEME_CSS = """
/* ═══════════════════════════════════════════════════════════════
   FEDSANITIZE — CYBERSECURITY THEME CSS
   Injected once from app.py. All selectors target Streamlit DOM.
═══════════════════════════════════════════════════════════════ */

/* ---------- 1. GLOBAL PAGE & FONT -------------------------------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #050508 !important;
    color: #E8F1F5 !important;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace !important;
}

/* Subtle network-grid background pattern */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(56,251,219,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(56,251,219,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ---------- 2. SIDEBAR ------------------------------------------- */
[data-testid="stSidebar"] {
    background-color: #0C1E3E !important;
    border-right: 1px solid rgba(56,251,219,0.15) !important;
}
[data-testid="stSidebar"] * {
    color: #E8F1F5 !important;
}
/* Sidebar logo glow */
[data-testid="stSidebar"] img {
    filter: drop-shadow(0 0 12px rgba(56,251,219,0.45)) !important;
    transition: filter 0.3s ease !important;
}
[data-testid="stSidebar"]:hover img {
    filter: drop-shadow(0 0 20px rgba(56,251,219,0.70)) !important;
}

/* Nav radio items */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    color: #7B8AA3 !important;
    padding: 6px 10px !important;
    border-radius: 4px !important;
    transition: color 0.2s ease, background 0.2s ease !important;
    border-left: 2px solid transparent !important;
    cursor: pointer !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    color: #38FBDB !important;
    background: rgba(56,251,219,0.06) !important;
    border-left: 2px solid #38FBDB !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + label,
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div label {
    color: #38FBDB !important;
    border-left: 2px solid #8E52F5 !important;
    font-weight: 700 !important;
}

/* ---------- 3. MAIN CONTENT CONTAINER ---------------------------- */
[data-testid="stMain"], .main .block-container {
    background-color: #050508 !important;
    padding-top: 1rem !important;
}

/* ---------- 4. SECTION HEADERS (H1 / H2 gradient text) ----------- */
h1 {
    background: linear-gradient(90deg, #38FBDB, #8E52F5) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-family: monospace !important;
}
h2 {
    background: linear-gradient(90deg, #38FBDB, #8E52F5) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-family: monospace !important;
}
h3, h4, h5, h6 {
    color: #38FBDB !important;
    font-family: monospace !important;
}

/* ---------- 5. METRIC CARDS -------------------------------------- */
[data-testid="metric-container"] {
    background-color: #0C1E3E !important;
    border: 1px solid rgba(56,251,219,0.15) !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}
[data-testid="metric-container"]:hover {
    border-color: #38FBDB !important;
    box-shadow: 0 0 16px rgba(56,251,219,0.20) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #7B8AA3 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #38FBDB !important;
    font-weight: 700 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    color: #20D9A0 !important;
}

/* ---------- 6. BUTTONS ------------------------------------------- */
[data-testid="stButton"] > button,
[data-testid="stFormSubmitButton"] > button {
    background: transparent !important;
    border: 1px solid #38FBDB !important;
    color: #38FBDB !important;
    font-family: monospace !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    transition: all 0.25s ease !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #38FBDB, #8E52F5) !important;
    color: #050508 !important;
    border-color: transparent !important;
    box-shadow: 0 0 16px rgba(56,251,219,0.50) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stButton"] > button:active,
[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0px) !important;
    box-shadow: none !important;
}
/* Primary button variant */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #38FBDB, #8E52F5) !important;
    color: #050508 !important;
    border-color: transparent !important;
    font-weight: 700 !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 0 20px rgba(56,251,219,0.65) !important;
    transform: translateY(-1px) !important;
}

/* ---------- 7. TABS ---------------------------------------------- */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid rgba(56,251,219,0.15) !important;
    gap: 4px !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: #7B8AA3 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 8px 16px !important;
    font-family: monospace !important;
    transition: color 0.2s ease, border-color 0.2s ease !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: #38FBDB !important;
    border-bottom-color: rgba(56,251,219,0.4) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #38FBDB !important;
    border-bottom: 2px solid !important;
    border-image: linear-gradient(90deg, #38FBDB, #8E52F5) 1 !important;
    font-weight: 700 !important;
}
[data-testid="stTabs"] [role="tabpanel"] {
    background-color: #0C1E3E !important;
    border: 1px solid rgba(56,251,219,0.15) !important;
    border-radius: 0 8px 8px 8px !important;
    padding: 16px !important;
}

/* ---------- 8. EXPANDERS ----------------------------------------- */
[data-testid="stExpander"] {
    background-color: #0C1E3E !important;
    border: 1px solid rgba(56,251,219,0.15) !important;
    border-radius: 8px !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}
[data-testid="stExpander"]:hover {
    border-color: #38FBDB !important;
    box-shadow: 0 0 12px rgba(56,251,219,0.15) !important;
}
[data-testid="stExpander"] summary {
    color: #E8F1F5 !important;
    font-family: monospace !important;
}

/* ---------- 9. DATAFRAMES / TABLES ------------------------------- */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(56,251,219,0.15) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] thead tr th {
    background-color: #0C1E3E !important;
    color: #38FBDB !important;
    font-family: monospace !important;
    text-transform: uppercase !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.06em !important;
    border-bottom: 1px solid rgba(56,251,219,0.25) !important;
}
[data-testid="stDataFrame"] tbody tr {
    transition: background-color 0.2s ease !important;
    border-left: 2px solid transparent !important;
}
[data-testid="stDataFrame"] tbody tr:hover {
    background-color: rgba(12,30,62,0.9) !important;
    border-left-color: #38FBDB !important;
}
[data-testid="stDataFrame"] tbody tr td {
    color: #E8F1F5 !important;
    font-family: monospace !important;
    font-size: 0.85rem !important;
    background-color: transparent !important;
}

/* ---------- 10. SLIDERS ------------------------------------------ */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #38FBDB !important;
    border-color: #38FBDB !important;
    box-shadow: 0 0 8px rgba(56,251,219,0.60) !important;
    transition: box-shadow 0.2s ease !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"]:focus {
    box-shadow: 0 0 16px rgba(56,251,219,0.90) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stSliderThumbValue"] {
    color: #38FBDB !important;
    font-family: monospace !important;
}
/* Track: purple to cyan gradient */
[data-testid="stSlider"] [data-baseweb="track-background"] {
    background: linear-gradient(90deg, #8E52F5, #38FBDB) !important;
}

/* ---------- 11. INPUTS / SELECT ---------------------------------- */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] select,
[data-baseweb="select"] {
    background-color: #0C1E3E !important;
    border: 1px solid rgba(56,251,219,0.25) !important;
    color: #E8F1F5 !important;
    font-family: monospace !important;
    border-radius: 6px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #38FBDB !important;
    box-shadow: 0 0 8px rgba(56,251,219,0.35) !important;
}

/* ---------- 12. ALERT BOXES -------------------------------------- */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    border: none !important;
    border-left: 3px solid !important;
    font-family: monospace !important;
}
/* success */
div[data-testid="stAlert"][data-baseweb="notification"][kind="positive"],
.stSuccess, [data-testid="stSuccess"] {
    background-color: rgba(32,217,160,0.08) !important;
    border-left-color: #20D9A0 !important;
    color: #20D9A0 !important;
}
/* warning */
div[data-testid="stAlert"][data-baseweb="notification"][kind="warning"],
.stWarning, [data-testid="stWarning"] {
    background-color: rgba(245,166,35,0.08) !important;
    border-left-color: #F5A623 !important;
    color: #F5A623 !important;
}
/* error */
div[data-testid="stAlert"][data-baseweb="notification"][kind="negative"],
.stError, [data-testid="stError"] {
    background-color: rgba(255,59,92,0.08) !important;
    border-left-color: #FF3B5C !important;
    color: #FF3B5C !important;
}
/* info */
div[data-testid="stAlert"][data-baseweb="notification"][kind="info"],
.stInfo, [data-testid="stInfo"] {
    background-color: rgba(56,251,219,0.06) !important;
    border-left-color: #38FBDB !important;
    color: #38FBDB !important;
}

/* ---------- 13. PROGRESS BARS ------------------------------------ */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #8E52F5, #38FBDB) !important;
    border-radius: 4px !important;
}

/* ---------- 14. CODE BLOCKS -------------------------------------- */
pre, code, [data-testid="stCode"] {
    background-color: #0C1E3E !important;
    border: 1px solid rgba(56,251,219,0.15) !important;
    color: #38FBDB !important;
    font-family: monospace !important;
    border-radius: 6px !important;
}

/* ---------- 15. DIVIDER ------------------------------------------ */
hr {
    border-color: rgba(56,251,219,0.15) !important;
}

/* ---------- 16. CAPTIONS / SMALL TEXT ---------------------------- */
[data-testid="stCaption"], small, .stCaption {
    color: #7B8AA3 !important;
    font-family: monospace !important;
}

/* ---------- 17. STATUS PILLS ------------------------------------- */
.pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: monospace;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.pill-trusted  { background: rgba(32,217,160,0.12); color: #20D9A0; border: 1px solid rgba(32,217,160,0.4); }
.pill-review   { background: rgba(142,82,245,0.12); color: #8E52F5; border: 1px solid rgba(142,82,245,0.4); }
.pill-malicious{ background: rgba(255,59,92,0.12);  color: #FF3B5C; border: 1px solid rgba(255,59,92,0.4); }

/* ---------- 18. TELEMETRY PULSE (KPI cards, Overview only) ------- */
@keyframes telemetry-pulse {
    0%   { box-shadow: 0 0 0px rgba(56,251,219,0); }
    50%  { box-shadow: 0 0 18px rgba(56,251,219,0.35); }
    100% { box-shadow: 0 0 0px rgba(56,251,219,0); }
}
.telemetry-live [data-testid="metric-container"] {
    animation: telemetry-pulse 3s ease-in-out infinite !important;
}
@media (prefers-reduced-motion: reduce) {
    .telemetry-live [data-testid="metric-container"] {
        animation: none !important;
    }
}

/* ---------- 19. CUSTOM SCROLLBAR --------------------------------- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0C1E3E; }
::-webkit-scrollbar-thumb { background: #38FBDB; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #8E52F5; box-shadow: 0 0 6px rgba(56,251,219,0.6); }

/* ---------- 20. SPINNER ------------------------------------------ */
[data-testid="stSpinner"] > div {
    border-top-color: #38FBDB !important;
    border-right-color: rgba(56,251,219,0.3) !important;
    border-bottom-color: rgba(56,251,219,0.3) !important;
    border-left-color: rgba(56,251,219,0.3) !important;
}

/* ---------- 21. SELECTBOX dropdown ------------------------------- */
[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: #0C1E3E !important;
    border: 1px solid rgba(56,251,219,0.25) !important;
    border-radius: 6px !important;
}
[data-baseweb="menu"] li {
    color: #E8F1F5 !important;
    font-family: monospace !important;
}
[data-baseweb="menu"] li:hover {
    background: rgba(56,251,219,0.08) !important;
    color: #38FBDB !important;
}
"""


def apply_theme(st):
    """Inject THEME_CSS into Streamlit once. Call from app.py only."""
    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)
