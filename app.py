
from io import StringIO

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="AI Corporate Deals", page_icon="📊", layout="wide")

SOURCE_PAGE = "https://ourworldindata.org/grapher/corporate-investment-in-artificial-intelligence-by-type"
CSV_URL = "https://ourworldindata.org/grapher/corporate-investment-in-artificial-intelligence-by-type.csv?v=1&csvType=full&useColumnShortNames=false"

COLUMN_MAP = {
    "Annual corporate investment in artificial intelligence by type - Private investment": "Private investment",
    "Annual corporate investment in artificial intelligence by type - Merger/acquisition": "Merger/acquisition",
    "Annual corporate investment in artificial intelligence by type - Public offering": "Public offering",
    "Annual corporate investment in artificial intelligence by type - Minority stake": "Minority stake",
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
    required = {"Year", *COLUMN_MAP.keys()}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError("The source schema changed. Missing columns: " + ", ".join(missing))

    clean = df[["Year", *COLUMN_MAP.keys()]].copy().rename(columns=COLUMN_MAP)
    clean["Year"] = pd.to_numeric(clean["Year"], errors="coerce")
    deal_types = list(COLUMN_MAP.values())
    clean[deal_types] = clean[deal_types].apply(pd.to_numeric, errors="coerce")
    clean = clean.dropna(subset=["Year"]).sort_values("Year")
    clean["Year"] = clean["Year"].astype(int)
    return clean

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

all_types = list(COLUMN_MAP.values())
min_year, max_year = int(data["Year"].min()), int(data["Year"].max())

with st.sidebar:
    st.header("Explore the chart")
    selected_years = st.slider("Year range", min_year, max_year, (min_year, max_year))
    selected_types = st.multiselect("Deal types", all_types, default=all_types)

if not selected_types:
    st.info("Select at least one deal type to display the chart.")
    st.stop()

filtered = data[data["Year"].between(*selected_years)]
long_data = filtered.melt(
    id_vars="Year",
    value_vars=selected_types,
    var_name="Deal type",
    value_name="Investment",
)
long_data["Investment (billions)"] = long_data["Investment"] / 1_000_000_000

fig = px.bar(
    long_data,
    x="Year",
    y="Investment (billions)",
    color="Deal type",
    color_discrete_map=COLORS,
    category_orders={"Deal type": all_types},
)
fig.update_layout(
    barmode="stack",
    xaxis_title=None,
    yaxis_title="Constant 2021 US$ (billions)",
    legend_title=None,
    legend_orientation="h",
    legend_yanchor="bottom",
    legend_y=1.02,
    legend_x=0,
    hovermode="x unified",
    margin=dict(l=20, r=20, t=70, b=20),
)
fig.update_xaxes(dtick=1)
fig.update_yaxes(tickprefix="$", ticksuffix="B", gridcolor="rgba(0,0,0,0.12)")
fig.update_traces(hovertemplate="$%{y:,.1f}B<extra></extra>")

st.plotly_chart(fig, use_container_width=True)
st.markdown(f"**Source:** [Our World in Data]({SOURCE_PAGE}), based on Quid via the AI Index Report and U.S. Bureau of Labor Statistics data.")
st.caption(
    "Recreated for educational purposes. The interactive controls filter years and deal types. "
    "Values and category definitions follow the published source; styling is an approximation."
)
