import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Global Extreme Poverty Dashboard", page_icon="🌍", layout="wide")

st.markdown(
    """
    <style>
    .kpi-card {
        background-color: #E8E8E8;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid rgba(0,0,0,0.1);
    }
    .kpi-card .kpi-label {
        font-size: 14px;
        color: #555;
        margin-bottom: 4px;
    }
    .kpi-card .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #262730;
    }
    div[data-testid="stExpander"] summary p {
        font-size: 18px !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ACCENT_COLOR = "#14B8A6"  # turquoise — matches the primaryColor in .streamlit/config.toml

DATA_PATH = "data/share-of-population-in-extreme-poverty.csv"

CHART_TEMPLATE = "plotly_white"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "Share of population in poverty ($3 a day)": "PovertyRate",
            "World region according to OWID": "Region",
        }
    )
    # The raw file includes population estimates going back to 10,000 BCE
    # (Year = -10000, etc.) merged in from OWID's population dataset, with
    # no poverty figure for those years. Drop rows with no poverty value —
    # this also naturally restricts the data to years with real survey coverage.
    df = df.dropna(subset=["PovertyRate"])
    df["Year"] = df["Year"].astype(int)
    return df


df = load_data(DATA_PATH)
country_df = df[df["Code"].notna() & (df["Code"].str.len() == 3)]

st.title("Global Extreme Poverty Dashboard")
st.caption("Share of population living below the $3/day International Poverty Line.")
st.caption("Source: World Bank Poverty and Inequality Platform, via Our World in Data (CC BY).")

# ---- Sidebar controls ----
st.sidebar.header("Filters")

regions = sorted(country_df["Region"].dropna().unique())
region_choice = st.sidebar.selectbox("Region", ["All regions"] + regions)

filtered_df = country_df if region_choice == "All regions" else country_df[country_df["Region"] == region_choice]

years = sorted(filtered_df["Year"].unique())
year = st.sidebar.slider(
    "Year", min_value=min(years), max_value=max(years), value=max(years), format="%d"
)

all_countries = sorted(filtered_df["Entity"].unique())
# No particular logic behind this default — just a starting selection so the
# chart isn't empty on first load. Pick your own countries below.
default_countries = [c for c in ["Kenya", "Nigeria", "India", "Brazil", "Ethiopia"] if c in all_countries] or all_countries[:5]
selected_countries = st.sidebar.multiselect("Countries to compare (trend line)", all_countries, default=default_countries)

top_n = st.sidebar.slider("Top N countries (bar chart)", min_value=5, max_value=30, value=10)

# ---- KPI summary cards (bordered, like Power BI card visuals) ----
year_df = filtered_df[filtered_df["Year"] == year]
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Countries with data</div>
            <div class="kpi-value">{year_df['Entity'].nunique()}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Average poverty rate</div>
            <div class="kpi-value">{year_df['PovertyRate'].mean():.1f}%</div>
        </div>""",
        unsafe_allow_html=True,
    )
with col3:
    highest_display = f"{year_df['PovertyRate'].max():.1f}%" if not year_df.empty else "—"
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Highest rate</div>
            <div class="kpi-value">{highest_display}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# Region averages, computed once and reused by both the insights section and the chart below
region_avg = (
    country_df[country_df["Year"] == year]
    .groupby("Region", as_index=False)["PovertyRate"]
    .mean()
    .sort_values("PovertyRate")
)

# ---- Key insights (generated from the currently filtered data) ----
st.subheader("Key insights")

insights = []

if not year_df.empty:
    top_country = year_df.loc[year_df["PovertyRate"].idxmax()]
    low_country = year_df.loc[year_df["PovertyRate"].idxmin()]
    insights.append(
        f"In {year}, **{top_country['Entity']}** had the highest poverty rate in view "
        f"at **{top_country['PovertyRate']:.1f}%**, while **{low_country['Entity']}** had the lowest "
        f"at **{low_country['PovertyRate']:.1f}%**."
    )

# Biggest improvement / worsening: compare each country's earliest vs latest available year
trend_all = filtered_df.sort_values("Year")
first_vals = trend_all.groupby("Entity").first()[["Year", "PovertyRate"]]
last_vals = trend_all.groupby("Entity").last()[["Year", "PovertyRate"]]
change = (last_vals["PovertyRate"] - first_vals["PovertyRate"]).dropna()
# Only consider countries with a real time span, not a single data point
span_years = last_vals["Year"] - first_vals["Year"]
change = change[span_years >= 5]

if not change.empty:
    most_improved = change.idxmin()
    most_worsened = change.idxmax()
    insights.append(
        f"**{most_improved}** saw the largest drop in poverty rate between "
        f"{int(first_vals.loc[most_improved, 'Year'])} and {int(last_vals.loc[most_improved, 'Year'])} "
        f"({change[most_improved]:+.1f} percentage points)."
    )
    insights.append(
        f"**{most_worsened}** saw the largest increase over the same kind of period "
        f"({int(first_vals.loc[most_worsened, 'Year'])}–{int(last_vals.loc[most_worsened, 'Year'])}: "
        f"{change[most_worsened]:+.1f} percentage points)."
    )

if not region_avg.empty:
    highest_region = region_avg.iloc[-1]
    lowest_region = region_avg.iloc[0]
    insights.append(
        f"By region in {year}, **{highest_region['Region']}** has the highest average poverty rate "
        f"({highest_region['PovertyRate']:.1f}%), compared to **{lowest_region['Region']}** "
        f"({lowest_region['PovertyRate']:.1f}%)."
    )

for point in insights:
    st.markdown(f"- {point}")

st.caption("Insights are calculated automatically from the filtered data above and update as you change filters.")

st.divider()

# ---- World map ----
st.subheader(f"Poverty rate by country — {year}")
map_fig = px.choropleth(
    year_df,
    locations="Code",
    color="PovertyRate",
    hover_name="Entity",
    color_continuous_scale="Reds",
    range_color=(0, max(country_df["PovertyRate"].quantile(0.95), 1)),
    labels={"PovertyRate": "Poverty rate (%)"},
    template=CHART_TEMPLATE,
)
map_fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>Poverty rate: %{z:.1f}%<extra></extra>"
)
map_fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)"),
)
st.plotly_chart(map_fig, use_container_width=True)

# ---- Region comparison ----
st.subheader(f"Average poverty rate by region — {year}")
region_fig = px.bar(
    region_avg,
    x="PovertyRate",
    y="Region",
    orientation="h",
    labels={"PovertyRate": "Average poverty rate (%)", "Region": ""},
    template=CHART_TEMPLATE,
    color_discrete_sequence=[ACCENT_COLOR],
)
region_fig.update_traces(hovertemplate="<b>%{y}</b><br>Average: %{x:.1f}%<extra></extra>")
region_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(region_fig, use_container_width=True)

# ---- Trend line chart ----
st.subheader("Trend over time")
if selected_countries:
    trend_df = filtered_df[filtered_df["Entity"].isin(selected_countries)]
    line_fig = px.line(
        trend_df.sort_values("Year"),
        x="Year",
        y="PovertyRate",
        color="Entity",
        labels={"PovertyRate": "Poverty rate (%)"},
        template=CHART_TEMPLATE,
    )
    line_fig.update_layout(
        xaxis=dict(tickformat="d"),  # prevents "1,980" comma formatting
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    line_fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Rate: %{y:.1f}%<extra></extra>")
    st.plotly_chart(line_fig, use_container_width=True)
else:
    st.info("Select at least one country in the sidebar to see the trend.")

# ---- Top N bar chart for selected year ----
st.subheader(f"Highest poverty rates in {year}")
top_df = year_df.sort_values("PovertyRate", ascending=False).head(top_n)
bar_fig = px.bar(
    top_df.sort_values("PovertyRate"),
    x="PovertyRate",
    y="Entity",
    orientation="h",
    labels={"PovertyRate": "Poverty rate (%)", "Entity": ""},
    template=CHART_TEMPLATE,
    color_discrete_sequence=[ACCENT_COLOR],
)
bar_fig.update_traces(hovertemplate="<b>%{y}</b><br>Rate: %{x:.1f}%<extra></extra>")
bar_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(bar_fig, use_container_width=True)

# ---- Raw data ----
with st.expander("View raw data"):
    display_df = top_df[["Entity", "Year", "PovertyRate", "Region"]].reset_index(drop=True)
    st.dataframe(
        display_df,
        column_config={
            "Year": st.column_config.NumberColumn("Year", format="%d"),  # no thousands separator
            "PovertyRate": st.column_config.NumberColumn("Poverty Rate (%)", format="%.1f%%"),
        },
        use_container_width=True,
    )
    st.download_button(
        "Download this view as CSV",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name=f"poverty_rates_{region_choice.replace(' ', '_')}_{year}.csv",
        mime="text/csv",
    )
