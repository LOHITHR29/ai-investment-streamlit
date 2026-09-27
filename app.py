
from io import StringIO

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="AI Corporate Deals", page_icon="📊", layout="wide")

SOURCE_PAGE = "https://ourworldindata.org/grapher/corporate-investment-in-artificial-intelligence-by-type"
CSV_URL = "https://ourworldindata.org/grapher/corporate-investment-in-artificial-intelligence-by-type.csv?v=1&csvType=full&useColumnShortNames=false"

ENTITY_MAP = {
    "merger/acquisition": "Merger/acquisition",
    "private investment": "Private investment",
    "public offering": "Public offering",
    "minority stake": "Minority stake",
}

COLORS = {
    "Merger/acquisition": "#4C78A8",
    "Private investment": "#F58518",
    "Public offering": "#E45756",
    "Minority stake": "#72B7B2",
}


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    response = requests.get(
        CSV_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; Streamlit data visualization project)"},
        timeout=30,
    )
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))

    required = {"Entity", "Year"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    value_cols = [column for column in df.columns if column not in {"Entity", "Code", "Year"}]
    if len(value_cols) != 1:
        raise ValueError(f"Expected one value column, found: {value_cols}")

    value_col = value_cols[0]
    clean = df[["Entity", "Year", value_col]].copy()
    clean["Deal type"] = clean["Entity"].astype(str).str.strip().str.lower().map(ENTITY_MAP)
    clean["Year"] = pd.to_numeric(clean["Year"], errors="coerce")
    clean["Investment"] = pd.to_numeric(clean[value_col], errors="coerce")
    clean = clean.dropna(subset=["Deal type", "Year", "Investment"])
    clean["Year"] = clean["Year"].astype(int)
    return clean[["Year", "Deal type", "Investment"]].sort_values(["Year", "Deal type"])


st.title("Global external corporate deals involving AI companies, by type")
st.caption(
    "Annual corporate-finance transactions involving privately held AI companies. "
    "Values are constant 2021 US dollars, adjusted for inflation."
)

try:
    data = load_data()
except Exception as exc:
    st.error(f"Unable to load the published dataset: {exc}")
    st.stop()

if data.empty:
    st.error("The dataset loaded, but none of the expected deal categories were found.")
    st.stop()

all_types = list(ENTITY_MAP.values())
min_year = int(data["Year"].min())
max_year = int(data["Year"].max())

with st.sidebar:
    st.header("Explore the chart")
    selected_years = st.slider(
        "Year range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
    )
    selected_types = st.multiselect(
        "Deal types",
        options=all_types,
        default=all_types,
    )

filtered = data[
    data["Year"].between(selected_years[0], selected_years[1])
    & data["Deal type"].isin(selected_types)
].copy()
filtered["Investment (billions)"] = filtered["Investment"] / 1_000_000_000

if filtered.empty:
    st.warning("Choose at least one deal type to display the chart.")
else:
    fig = px.bar(
        filtered,
        x="Year",
        y="Investment (billions)",
        color="Deal type",
        color_discrete_map=COLORS,
        category_orders={"Deal type": all_types},
        labels={"Investment (billions)": "Investment (constant 2021 US$ billions)"},
    )
    fig.update_layout(
        barmode="stack",
        height=610,
        legend_title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=20, t=70, b=20),
        plot_bgcolor="white",
        hovermode="x unified",
    )
    fig.update_xaxes(dtick=1, showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E6E6E6", rangemode="tozero")
    st.plotly_chart(fig, use_container_width=True)

st.markdown(
    "**Source:** Quid via AI Index Report (2026) and U.S. Bureau of Labor Statistics (2026), "
    "processed by Our World in Data. "
    f"[View the original chart and methodology]({SOURCE_PAGE})."
)
st.caption("Interactive recreation created for RCEL 506. Use the sidebar to change years and categories.")
