import streamlit as st
import geopandas as gpd
import folium
import branca.colormap as cm
from folium.plugins import BeautifyIcon
from streamlit_folium import st_folium

# Title
st.title("Isochrone Map Viewer")

st.set_page_config(layout="wide")

# Load GeoJSON files
isochrone_files = {
    "Center 1": "scuola1.geojson",
    "Center 2": "scuola2.geojson"
}

# Dropdown for center selection
# selected_center = st.selectbox("Select a Center", list(isochrone_files.keys()))

# Sidebar for filters
# with st.sidebar:
#     selected_center = st.selectbox("Select Center", list(isochrone_files.keys()))

gdf_schools = gpd.read_file("./POI/schools.geojson").to_crs(epsg=4326)
gdf_hospitals = gpd.read_file("./POI/hospitals.geojson").to_crs(epsg=4326)

center_options = list(isochrone_files.keys())

with st.sidebar:
    selected_center = st.selectbox("Select Center", center_options)

# Load selected GeoJSON as GeoDataFrame
gdf = gpd.read_file(isochrone_files[selected_center])

with st.sidebar:
    max_minutes = int(gdf["contour"].max())
    selected_minutes = st.slider("Show areas up to X minutes", 1, max_minutes, value=max_minutes)

show_schools = st.sidebar.checkbox("Show Schools", value=False)
show_hospitals = st.sidebar.checkbox("Show Hospitals", value=False)

# Get start point (center of smallest contour)
start_point = gdf[gdf["contour"] == gdf["contour"].min()].geometry.centroid.iloc[0]

# Get centroid of polygons to center the map
# map_center = gdf.geometry.centroid.iloc[0].coords[0][::-1]  # (lat, lon)

# Create a Folium map
m = folium.Map(location=[start_point.y, start_point.x], zoom_start=12, tiles=None)

folium.TileLayer(
    tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
    name='CARTO Positron',
    control=False
).add_to(m)

# Create a colormap
contours = sorted(gdf["contour"].unique())
colormap = cm.linear.Spectral_08.scale(min(contours), max(contours))

filtered_gdf = gdf[gdf["contour"] <= selected_minutes]
# Add polygons with color
for _, row in filtered_gdf.iloc[::-1].iterrows():
    color = colormap(row["contour"])
    geojson = folium.GeoJson(
        row["geometry"],
        style_function=lambda feature, color=color: {
            "fillColor": color,
            "color": color,
            "weight": 1,
            "fillOpacity": 0.4,
            "opacity": 0.9,
        }
    )
    popup = folium.Popup(f"{int(row['contour'])} min", max_width=150)
    popup.add_to(geojson)
    geojson.add_to(m)

# Add starting point marker
folium.Marker(
    location=[start_point.y, start_point.x],
    icon=BeautifyIcon(
        icon="car",
        icon_shape="marker",
        background_color="white",
        text_color="black",
        border_color="black"
    )
).add_to(m)

# Add school markers
if show_schools:
    for _, row in gdf_schools.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon=folium.Icon(icon="graduation-cap", prefix="fa", color="blue"),
            popup=row.get("name", "School")
        ).add_to(m)

# Add hospital markers
if show_hospitals:
    for _, row in gdf_hospitals.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon=folium.Icon(icon="plus-square", prefix="fa", color="red"),
            popup=row.get("name", "Hospital")
        ).add_to(m)


# Add legend
colormap.caption = 'Minutes from Origin'
colormap.add_to(m)


# # Add polygons to the map
# folium.GeoJson(gdf).add_to(m)

# Display the map
st_folium(m, use_container_width=True, height=600, key="iso_map")