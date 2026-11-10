import html
import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Find your next anime", page_icon="🌸", layout="wide")

NAVY = "#1F2B5B"
BLUE = "#5A74D0"
PERI = "#9DB0EE"
MIST = "#D6DFF8"
CREAM = "#F6F1E4"
PAPER = "#FFFCF4"


@st.cache_data
def load_data():
    catalog = pd.read_parquet("data/processed/catalog.parquet")
    neighbors = pd.read_parquet("data/processed/neighbors.parquet")
    return catalog, neighbors


catalog, neighbors = load_data()


# ---------- pixel art (original sprites drawn as SVG rectangles) ----------
def sprite(rows, colors, x0=0, y0=0):
    rects = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colors:
                rects.append(f'<rect x="{x0 + x}" y="{y0 + y}" width="1" height="1" fill="{colors[ch]}"/>')
    return "".join(rects)


SPARKLE = ["...a...", "...a...", "..aba..", "aabbbaa", "..aba..", "...a...", "...a..."]
SMALL_SPARKLE = [".a.", "aba", ".a."]
FLOWER = [
    "..aaa..",
    ".abbba.",
    "abbcbba",
    ".abbba.",
    "..aaa..",
    "...g...",
    "gg.g.gg",
    ".ggggg.",
    "...g...",
]
TULIP = [
    "a.a.a",
    "abababa"[:5],
    "abbba",
    ".aba.",
    "..g..",
    "g.g.g",
    ".ggg.",
    "..g..",
]
SPARKLE_COLORS = {"a": BLUE, "b": PAPER}
FLOWER_COLORS = {"a": NAVY, "b": PERI, "c": PAPER, "g": BLUE}
TULIP_COLORS = {"a": NAVY, "b": MIST, "g": BLUE}


def sparkle_svg(size_px, small=False):
    rows = SMALL_SPARKLE if small else SPARKLE
    n = len(rows)
    return (f'<svg width="{size_px}" height="{size_px}" viewBox="0 0 {n} {n}" '
            f'shape-rendering="crispEdges" aria-hidden="true">{sprite(rows, SPARKLE_COLORS)}</svg>')


def garden_svg():
    w, h = 220, 12
    parts = []
    plants = [(6, "f"), (20, "t"), (31, "f"), (52, "t"), (64, "f"), (90, "f"), (101, "t"),
              (128, "t"), (140, "f"), (162, "f"), (175, "t"), (196, "f"), (209, "t")]
    for x, kind in plants:
        if kind == "f":
            parts.append(sprite(FLOWER, FLOWER_COLORS, x, h - len(FLOWER) - 1))
        else:
            parts.append(sprite(TULIP, TULIP_COLORS, x, h - len(TULIP) - 1))
    for x, y in [(40, 1), (78, 3), (115, 0), (152, 2), (186, 1)]:
        parts.append(sprite(SMALL_SPARKLE, SPARKLE_COLORS, x, y))
    parts.append(f'<rect x="0" y="{h - 1}" width="{w}" height="1" fill="{NAVY}"/>')
    return (f'<svg class="garden" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMax meet" '
            f'shape-rendering="crispEdges" aria-hidden="true">{"".join(parts)}</svg>')


# ---------- state ----------
hero_mode = st.session_state.get("query") is None

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {{ background: {CREAM}; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    html, body, p, label, button, input, .stMarkdown, [data-baseweb] {{
        font-family: 'IBM Plex Mono', 'Menlo', monospace;
    }}
    .block-container {{
        max-width: 1120px;
        padding-top: {"8vh" if hero_mode else "2.5rem"};
        padding-bottom: 3rem;
    }}

    /* hero */
    .hero {{ position: relative; text-align: center; }}
    .hero .title-xl {{
        font-family: 'Pixelify Sans', 'Courier New', monospace; font-weight: 700;
        font-size: {"clamp(2.6rem, 7vw, 4.8rem)" if hero_mode else "clamp(1.8rem, 4vw, 2.6rem)"};
        line-height: 1; letter-spacing: 0.01em; color: {NAVY}; margin: 0 0 0.8rem; padding: 0;
    }}
    .hero .title-xl .accent {{ color: {BLUE}; }}
    .hero p {{ font-size: 1.05rem; color: {NAVY}; margin: 0 auto 1.6rem; max-width: 34rem; line-height: 1.7; }}
    .hero .spark {{ position: absolute; }}
    .hero .s1 {{ left: -1%; top: -46px; }}
    .hero .s2 {{ right: -1%; top: -30px; }}
    .hero .s3 {{ left: 9%; top: 62%; }}
    .hero .s4 {{ right: 10%; top: 74%; }}
    @media (max-width: 640px) {{
        .hero .s3, .hero .s4 {{ display: none; }}
        .hero .s1 {{ top: -40px; }} .hero .s2 {{ top: -34px; }}
    }}

    /* search bar */
    [data-testid="stSelectbox"] [role="group"] {{
        background: {PAPER} !important; border: 3px solid {NAVY} !important; border-radius: 6px !important;
        box-shadow: 5px 5px 0 {NAVY} !important; min-height: 58px !important;
    }}
    [data-testid="stSelectbox"] [role="group"]:focus-within {{ border-color: {BLUE} !important; box-shadow: 5px 5px 0 {BLUE} !important; }}
    [data-testid="stSelectbox"] input {{ font-size: 1.05rem !important; color: {NAVY} !important; }}

    /* quick picks */
    .try-label, .card, .picked, .pill, .footer, .hero p {{ font-family: 'IBM Plex Mono', 'Menlo', monospace !important; }}
    .try-label {{ text-align: center; font-size: 0.9rem; color: {NAVY}; margin: 1.4rem 0 0.6rem; }}
    .st-key-posters {{ gap: 16px; }}
    .pop-poster {{
        width: 100%; aspect-ratio: 2 / 3; background-color: {MIST};
        background-size: cover; background-position: center;
        border: 3px solid {NAVY}; border-radius: 6px; box-shadow: 4px 4px 0 {NAVY};
        transition: transform 0.1s, box-shadow 0.1s;
    }}
    [class*="st-key-pop_"]:hover .pop-poster {{ transform: translate(-2px, -2px); box-shadow: 6px 6px 0 {BLUE}; }}
    [class*="st-key-pop_"] .stButton, [class*="st-key-pop_"] .stButton button {{ width: 100%; }}
    [class*="st-key-pop_"] .stButton button {{
        background: {PAPER}; color: {NAVY}; border: 2px solid {NAVY}; border-radius: 4px;
        box-shadow: 3px 3px 0 {NAVY}; font-size: 0.8rem; padding: 0.25rem 0.4rem;
        height: 3.2em; min-height: 3.2em; line-height: 1.25; white-space: normal;
        transition: transform 0.08s, box-shadow 0.08s;
    }}
    [class*="st-key-pop_"] .stButton button:hover {{ color: {BLUE}; border-color: {NAVY}; box-shadow: 3px 3px 0 {BLUE}; }}
    [class*="st-key-pop_"] .stButton button:active {{ transform: translate(2px, 2px); box-shadow: 1px 1px 0 {NAVY}; }}
    @media (max-width: 640px) {{
        [class*="st-key-pop_"] {{ width: 140px !important; }}
    }}

    .garden {{ display: block; width: 100%; height: auto; margin-top: 5vh; }}

    /* selected title */
    .picked {{
        display: flex; gap: 18px; align-items: center; background: {PAPER};
        border: 3px solid {NAVY}; border-radius: 6px; box-shadow: 5px 5px 0 {NAVY};
        padding: 14px; margin: 2rem 0 1.6rem;
    }}
    .picked img {{ width: 70px; aspect-ratio: 2 / 3; object-fit: cover; border: 2px solid {NAVY}; background: {MIST}; }}
    .picked .kicker {{ font-size: 0.9rem; color: {BLUE}; }}
    .picked .title {{
        font-family: 'Pixelify Sans', monospace; font-weight: 700; font-size: 1.5rem;
        color: {NAVY}; line-height: 1.2; margin: 2px 0 6px;
    }}

    /* cards */
    .card {{
        background: {PAPER}; border: 3px solid {NAVY}; border-radius: 6px; box-shadow: 5px 5px 0 {NAVY};
        overflow: hidden; height: 100%; transition: transform 0.1s, box-shadow 0.1s;
    }}
    .card:hover {{ transform: translate(-2px, -2px); box-shadow: 7px 7px 0 {BLUE}; }}
    .card img {{ display: block; width: 100%; aspect-ratio: 2 / 3; object-fit: cover; background: {MIST}; border-bottom: 3px solid {NAVY}; }}
    .card .body {{ padding: 10px 12px 14px; }}
    .match {{ font-family: 'Pixelify Sans', monospace; font-weight: 700; font-size: 1.8rem; color: {BLUE}; line-height: 1; }}
    .match small {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; color: {NAVY}; margin-left: 4px; }}
    .name {{ font-size: 1rem; font-weight: 600; color: {NAVY}; line-height: 1.35; margin: 8px 0 8px; }}
    .pills {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }}
    .pill {{ font-size: 0.78rem; padding: 1px 7px; border: 2px solid {NAVY}; background: {MIST}; color: {NAVY}; }}
    .genres {{ font-size: 0.84rem; color: {NAVY}; opacity: 0.85; line-height: 1.5; }}

    .footer {{ margin-top: 3rem; text-align: center; font-size: 0.88rem; color: {NAVY}; line-height: 1.7; }}
    .footer a {{ color: {BLUE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- helpers ----------
def display_title(r) -> str:
    en = r["english_name"]
    return en if isinstance(en, str) and en else r["name"]


def label(r) -> str:
    en = r["english_name"]
    if isinstance(en, str) and en and en != r["name"]:
        return f'{r["name"]} ({en})'
    return r["name"]


def meta_pills(r) -> str:
    year = "Year unknown" if pd.isna(r["year"]) else str(int(r["year"]))
    anime_type = r["type"] if isinstance(r["type"], str) and r["type"] else "Type unknown"
    return (f'<div class="pills"><span class="pill">{year}</span>'
            f'<span class="pill">{html.escape(anime_type)}</span></div>')


def card_html(r) -> str:
    title = display_title(r)
    genres = html.escape(r["genres"]) if r["genres"] else "No genre listed"
    return f"""
    <div class="card">
        <img src="{html.escape(str(r['image_url']))}" alt="Poster of {html.escape(title)}" loading="lazy">
        <div class="body">
            <div class="match">{round(r['similarity'] * 100)}%<small>match</small></div>
            <div class="name">{html.escape(title)}</div>
            {meta_pills(r)}
            <div class="genres">{genres}</div>
        </div>
    </div>
    """


catalog["label"] = catalog.apply(label, axis=1)
ordered = catalog.sort_values("members", ascending=False)
label_to_id = dict(zip(ordered["label"], ordered["anime_id"]))
name_to_label = dict(zip(catalog["name"], catalog["label"]))

POPULAR_SINCE = 2022
N_POPULAR = 6


def franchise_key(name: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(name).lower())[:2])


def short_title(title: str) -> str:
    """Main title only: drops subtitles after a colon and season or part labels."""
    t = title.split(":")[0]
    t = re.sub(r"\s+(Season\s*\d+|\d+(st|nd|rd|th)\s+Season|Part\s*\d+|The Final Season.*)$", "", t,
               flags=re.IGNORECASE)
    return t.strip() or title


def popular_recent(n=N_POPULAR):
    """Most-watched recent titles, one per franchise."""
    recent = catalog[catalog["year"] >= POPULAR_SINCE].sort_values("members", ascending=False)
    picks, seen = [], set()
    for r in recent.to_dict("records"):
        key = franchise_key(r["name"])
        if key in seen:
            continue
        seen.add(key)
        picks.append(r)
        if len(picks) == n:
            break
    return picks


def pick(lbl: str):
    st.session_state["query"] = lbl


# ---------- hero ----------
st.markdown(
    f"""
    <div class="hero">
        <span class="spark s1">{sparkle_svg(42)}</span>
        <span class="spark s2">{sparkle_svg(30)}</span>
        <span class="spark s3">{sparkle_svg(18, small=True)}</span>
        <span class="spark s4">{sparkle_svg(22, small=True)}</span>
        <div class="title-xl">Find your <span class="accent">next anime</span></div>
        <p>Pick a show you liked. Get five from other series with a similar story, genre and style.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

_, mid, _ = st.columns([1, 4, 1])
with mid:
    query = st.selectbox(
        "Anime you liked",
        list(label_to_id),
        index=None,
        key="query",
        placeholder="🔍  Search an anime title",
        label_visibility="collapsed",
    )

if hero_mode:
    st.markdown('<div class="try-label">or try one of these</div>', unsafe_allow_html=True)
    with st.container(horizontal=True, horizontal_alignment="center", key="posters"):
        for r in popular_recent():
            title = display_title(r)
            short = short_title(title)
            with st.container(width=140, key=f"pop_{r['anime_id']}"):
                st.markdown(
                    f'<div class="pop-poster" role="img" aria-label="Poster of {html.escape(title)}" '
                    f'style="background-image: url(\'{html.escape(str(r["image_url"]))}\')"></div>',
                    unsafe_allow_html=True,
                )
                st.button(short, key=f"btn_{r['anime_id']}", help=title, width="stretch",
                          on_click=pick, args=(r["label"],))

if hero_mode:
    st.markdown(garden_svg(), unsafe_allow_html=True)

# ---------- results ----------
if query is not None:
    source_id = label_to_id[query]
    src = catalog.loc[catalog["anime_id"] == source_id].iloc[0]
    st.markdown(
        f"""
        <div class="picked">
            <img src="{html.escape(str(src['image_url']))}" alt="Poster of {html.escape(display_title(src))}">
            <div>
                <div class="kicker">Because you liked</div>
                <div class="title">{html.escape(display_title(src))}</div>
                {meta_pills(src)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    recs = (
        neighbors[neighbors["source_id"] == source_id]
        .nsmallest(5, "rank")
        .merge(catalog, left_on="rec_id", right_on="anime_id", how="left")
    )
    if recs.empty:
        st.warning("No recommendations for this title yet. Try another one.")
    else:
        cols = st.columns(5)
        for col, r in zip(cols, recs.to_dict("records")):
            with col:
                st.markdown(card_html(r), unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="footer">
            Recommendations compare story, genre, studio and format across {len(catalog):,} titles from MyAnimeList.
            Sequels and spin-offs of the show you picked are left out.<br>
            <a href="https://github.com/kstnwu/anime-recommender" target="_blank">See how it works on GitHub</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
