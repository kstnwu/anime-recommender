import html

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Anime Finder", page_icon="🎬", layout="wide")


@st.cache_data
def load_data():
    catalog = pd.read_parquet("data/processed/catalog.parquet")
    neighbors = pd.read_parquet("data/processed/neighbors.parquet")
    return catalog, neighbors


catalog, neighbors = load_data()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&display=swap');
    html, body, h1, h2, h3, p, label, .stMarkdown {
        font-family: 'M PLUS Rounded 1c', 'Hiragino Maru Gothic ProN', system-ui, sans-serif;
    }
    h1 { font-weight: 800; letter-spacing: -0.02em; }
    .card {
        background: #FFFFFF;
        border: 1px solid #DCE2EE;
        border-radius: 14px;
        overflow: hidden;
        height: 100%;
    }
    .card img {
        display: block;
        width: 100%;
        aspect-ratio: 2 / 3;
        object-fit: cover;
        background: #E3E8F2;
    }
    .card .body { padding: 12px 14px 16px; }
    .match { font-size: 2rem; font-weight: 800; color: #2B59C3; line-height: 1; }
    .match small { font-size: 0.8rem; font-weight: 700; color: #5B6785; margin-left: 4px; }
    .name { font-size: 1rem; font-weight: 700; color: #1C2541; line-height: 1.3; margin: 8px 0 8px; }
    .pills { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
    .pill {
        font-size: 0.75rem; padding: 2px 9px; border-radius: 999px;
        background: #E3E8F2; color: #1C2541;
    }
    .genres { font-size: 0.8rem; color: #5B6785; line-height: 1.45; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Find your next anime")
st.write("Pick a title you liked. You'll get five shows from other franchises with the closest story, genres, studio, and format.")

# Most-watched titles first, so common searches show up at the top of the list.
# Each option shows the English title in brackets when it differs, so either name can be typed.
def label(r):
    en = r["english_name"]
    if isinstance(en, str) and en and en != r["name"]:
        return f'{r["name"]} ({en})'
    return r["name"]

catalog["label"] = catalog.apply(label, axis=1)
ordered = catalog.sort_values("members", ascending=False)
label_to_id = dict(zip(ordered["label"], ordered["anime_id"]))

query = st.selectbox(
    "Anime you liked",
    list(label_to_id),
    index=None,
    placeholder="Start typing, e.g. Hunter x Hunter or Attack on Titan",
)

if query is None:
    st.info("Type a title above to see your recommendations.")
    st.stop()

source_id = label_to_id[query]
recs = (
    neighbors[neighbors["source_id"] == source_id]
    .nsmallest(5, "rank")
    .merge(catalog, left_on="rec_id", right_on="anime_id", how="left")
)

if recs.empty:
    st.warning("No matches found for this title. Try another one.")
    st.stop()


def card_html(r: dict) -> str:
    year = "Year unknown" if pd.isna(r["year"]) else str(int(r["year"]))
    anime_type = r["type"] if isinstance(r["type"], str) and r["type"] else "Type unknown"
    genres = r["genres"] if r["genres"] else "No genre listed"
    en = r["english_name"]
    title = en if isinstance(en, str) and en else r["name"]
    match = round(r["similarity"] * 100)
    return f"""
    <div class="card">
        <img src="{html.escape(str(r['image_url']))}" alt="Poster of {html.escape(title)}" loading="lazy">
        <div class="body">
            <div class="match">{match}%<small>match</small></div>
            <div class="name">{html.escape(title)}</div>
            <div class="pills">
                <span class="pill">{year}</span>
                <span class="pill">{html.escape(anime_type)}</span>
            </div>
            <div class="genres">{html.escape(genres)}</div>
        </div>
    </div>
    """


st.subheader(f"Because you liked {query}")
cols = st.columns(5)
for col, r in zip(cols, recs.to_dict("records")):
    with col:
        st.markdown(card_html(r), unsafe_allow_html=True)
