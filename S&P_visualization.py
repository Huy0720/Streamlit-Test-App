import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry
import json
import urllib.request
from streamlit_folium import st_folium
import folium

# ------------------------------------------------------
# 1. Page setup
# ------------------------------------------------------
st.set_page_config(
    page_title="Global Company Reports Map",
    layout="wide",
    page_icon="🌍"
)

st.title("🌍 Global Company Reports Visualization")
st.markdown("This dashboard visualizes report availability by country, year, and file type.")

# ------------------------------------------------------
# 2. Load data
# ------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("File_Download_Report_2000_2025_v3.xlsx")   # <-- your Excel file
    return df

df = load_data()

# ------------------------------------------------------
# 3. Preprocessing
# ------------------------------------------------------
# Clean column names just in case
df.columns = df.columns.str.strip().str.lower()

# Map country name to ISO3 for choropleth compatibility
def get_iso3(country_name):
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except:
        return None

if "iso3" not in df.columns:
    df["iso3"] = df["country"].apply(get_iso3)

# Remove rows with missing country codes
df = df.dropna(subset=["iso3", "year", "filetype"])
# Group by country, year, file type
grouped = (
    df.groupby(["country", "iso3", "year", "filetype"])
    .size()
    .reset_index(name="report_count")
)

# ------------------------------------------------------
# 4. Sidebar filters
# ------------------------------------------------------
st.sidebar.header("Filters")

years = sorted(grouped["year"].unique())
filetypes = sorted(grouped["filetype"].unique())





# selected_years = [
#     y for y in years if st.sidebar.checkbox(str(y), value=True, key=f"year_{y}")
# ]

selected_years = st.sidebar.selectbox("Select Year", years)




# File type checkboxes
st.sidebar.subheader("📂 Select File Types")
if "selected_filetypes" not in st.session_state:
    st.session_state["selected_filetypes"] = filetypes.copy()

# --- Select/Clear buttons ---
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Select all", key="btn_select_all_types"):
        st.session_state["selected_filetypes"] = filetypes.copy()

with col2:
    if st.button("Clear all", key="btn_clear_all_types"):
        st.session_state["selected_filetypes"] = []

# --- Multiselect (always reflects session state) ---
selected_filetypes = st.sidebar.multiselect(
    "Select file types",
    options=filetypes,
    default=st.session_state["selected_filetypes"],
    label_visibility="collapsed",
    key="multi_filetypes"   # unique key
)

# --- Update session state when user manually changes selection ---
st.session_state["selected_filetypes"] = selected_filetypes


filtered = grouped[
    (grouped["year"] == selected_years)
    & (grouped["filetype"].isin(selected_filetypes))
]

# filtered = grouped[
#     (grouped["year"] == selected_year) &
#     (grouped["filetype"].isin(selected_filetypes))
# ]







# ------------------------------------------------------
# 5. Choropleth map
# ------------------------------------------------------
st.subheader(f"🌐 Report Distribution — {selected_years}")

# @st.cache_data
# def load_geojson():
#     url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
#     with urllib.request.urlopen(url) as response:
#         geojson = json.load(response)
#     return geojson

# geojson = load_geojson()

# fig = px.choropleth_mapbox(
#     filtered,
#     geojson=geojson,
#     locations="iso3",
#     featureidkey="properties.ISO3166-1-Alpha-3",  
#     color="report_count",
#     hover_name="country",
#     hover_data={"report_count": True, "filetype": True, "iso3": False},
#     mapbox_style="carto-positron",
#     color_continuous_scale="YlGnBu",
#     zoom=1,
#     center={"lat": 20, "lon": 0},
#     opacity=0.3,
#     height=800,
#     title=f"Number of Reports by Country ({selected_year})"
# )


# fig.update_layout(
#     margin=dict(l=0, r=0, t=40, b=0),
#     hoverlabel=dict(bgcolor="white", font_size=12),
# )


# fig.update_geos(
#     showcoastlines=True,
#     coastlinecolor="Gray",
#     showland=True,
#     landcolor="#ECECEC",
#     showcountries=True,
#     countrycolor="white",
#     resolution=50  # 50 = high res, 110 = medium
# )

# st.plotly_chart(fig, use_container_width=True)

#------------------------------------------------------------------------------------------------
# fig = px.scatter_mapbox(
#     lat=[], lon=[],  # empty data
#     zoom=1,
# )



# fig.update_layout(
#     mapbox_style="open-street-map",  # or 'carto-positron', 'stamen-terrain', etc.
#     mapbox_center={"lat": 20, "lon": 0},
#     margin={"r":0, "t":0, "l":0, "b":0},
#     height=700
# )

# st.plotly_chart(fig, use_container_width=True)

#------------------------------------------------------------------------------------------------


# Aggregate data by country
country_summary = (
    filtered.groupby("country")["report_count"]
    .sum()
    .reset_index()
)

# Convert country names to ISO alpha-3 codes
import pycountry
def get_iso3(country_name):
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except:
        return None

country_summary["iso_alpha"] = country_summary["country"].apply(get_iso3)
country_summary = country_summary.dropna(subset=["iso_alpha"])

# Create choropleth map
fig_map = px.choropleth(
    country_summary,
    locations="iso_alpha",
    color="report_count",
    hover_name="country",
    color_continuous_scale="YlGnBu",
    title="Report Availability by Country",
    labels={"report_count": "Total Reports"},
)

# ---- Improve visual aesthetics ----
fig_map.update_geos(
    projection_type="equirectangular",   # flat world map
    showcoastlines=True,
    coastlinecolor="white",
    showland=True,
    landcolor="#f5f5f5",                 # light gray land background
    showcountries=True,
    countrycolor="white",
)

fig_map.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>Total Reports: %{z}<extra></extra>",
    marker_line_width=0.5,
    marker_line_color="white",
)

fig_map.update_layout(
    geo_bgcolor="#d9d9d9",              # light gray background for oceans
    coloraxis_colorbar=dict(title="Reports"),
    margin=dict(l=0, r=0, t=40, b=0),
    height=550
)

fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(dragmode=False)

st.plotly_chart(fig_map, use_container_width=True)
















# ------------------------------------------------------
# 6. Additional visualizations
# ------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Top 10 Countries by Report Count")
    top_countries = (
        filtered.groupby("country")["report_count"]
        .sum()
        .nlargest(10)
        .reset_index()
    )
    fig_bar = px.bar(
        top_countries,
        x="country",
        y="report_count",
        color="report_count",
        color_continuous_scale="YlGnBu",
        text_auto=True,
        title="Top 10 Countries"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("📈 Report Type Distribution")
    type_counts = (
        filtered.groupby("filetype")["report_count"]
        .sum()
        .reset_index()
    )
    fig_pie = px.pie(
        type_counts,
        values="report_count",
        names="filetype",
        title="Share of File Types"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ------------------------------------------------------
# 7. Optional: Data table
# ------------------------------------------------------
with st.expander("🔍 View Underlying Data"):
    st.dataframe(filtered.sort_values("report_count", ascending=False))

