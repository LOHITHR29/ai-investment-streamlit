import pandas as pd
import plotly.express as px
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
    df = pd.read_csv(CSV_URL)
    required = {"Year", *COLUMN_MAP.keys()}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError("The source schema changed. Missing columns: " + ", ".join(missing))

    clean = df[["Year", *COLUMN_MAP.keys()]].copy()
    clean = clean.rename(columns=COLUMN_MAP)
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
    selected_years = st.slider(
        "Year range", min_year, max_year, (min_year, max_year)
    )
    selected_types = st.multiselect(
        "Deal types", all_types, default=all_types
    )

if not selected_types:
    st.warning("Select at least one deal type to display the chart.")
    st.stop()

filtered = data[data["Year"].between(*selected_years)].copy()
long_df = filtered.melt(
    id_vars="Year",
    value_vars=selected_types,
    var_name="Deal type",
    value_name="Investment (US$)",
)
long_df["Investment (US$ billions)"] = long_df["Investment (US$)"] / 1_000_000_000

fig = px.bar(
    long_df,
    x="Year",
    y="Investment (US$ billions)",
    color="Deal type",
    barmode="stack",
    color_discrete_map=COLORS,
    category_orders={"Deal type": all_types},
)
fig.update_traces(
    hovertemplate="Year %{x}<br>%{fullData.name}: $%{y:.2f}B<extra></extra>"
)
fig.update_layout(
    height=620,
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend_title_text="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(l=20, r=20, t=55, b=20),
    hovermode="x unified",
)
fig.update_xaxes(dtick=1, title_text="", showgrid=False)
fig.update_yaxes(
    title_text="",
    tickprefix="$",
    ticksuffix="B",
    gridcolor="#E5E7EB",
    zeroline=False,
)

st.plotly_chart(fig, use_container_width=True)

st.markdown(
    f"**Source:** [Our World in Data]({SOURCE_PAGE}), adapted from Quid via the AI Index Report and the U.S. Bureau of Labor Statistics."
)
with st.expander("Methodology and limitations"):
    st.write(
        "The app reads the published OWID CSV directly and validates the named columns before plotting. "
        "Raw dollar values are divided by one billion only for display. The source covers external "
        "transactions involving privately held AI companies; it excludes public companies and internal "
        "corporate spending such as R&D and infrastructure."
    )
