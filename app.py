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
    "Istituto Giovanni Pascoli": "scuola_giovanni_pascoli.geojson",
    "Liceo Volta": "scuola_volta.geojson",
    "Istituto Borgovico": "istituto_borgovico.geojson",
    "Stadio Senigallia" : "stadio.geojson"
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

# Initialize default map center and zoom
if "map_center" not in st.session_state:
    st.session_state["map_center"] = [start_point.y, start_point.x]
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 12
if "prev_filters" not in st.session_state:
    st.session_state.prev_filters = {}
if "last_map_data" not in st.session_state:
    st.session_state.last_map_data = None


# === Detect filter change BEFORE map creation ===
filters_changed = (
    st.session_state.prev_filters.get("show_schools") != show_schools or
    st.session_state.prev_filters.get("show_hospitals") != show_hospitals or 
    st.session_state.prev_filters.get("selected_center") != selected_center or
    st.session_state.prev_filters.get("selected_minutes") != selected_minutes
)

if filters_changed and st.session_state.last_map_data:
    map_data = st.session_state.last_map_data
    if "center" in map_data and "zoom" in map_data:
        st.session_state.map_center = [
            map_data["center"]["lat"],
            map_data["center"]["lng"]
        ]
        st.session_state.map_zoom = map_data["zoom"]

# === Now update stored filters (for next round) ===
st.session_state.prev_filters = {
    "show_schools": show_schools,
    "show_hospitals": show_hospitals,
    "selected_center": selected_center,
    "selected_minutes": selected_minutes
}

# Create a Folium map
m = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"] , tiles=None, control_scale=True)

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


# Detect if filters changed (compared to previous state)
filter_keys = ["show_schools", "show_hospitals", "selected_center", "selected_minutes"]
if "prev_filters" not in st.session_state:
    st.session_state["prev_filters"] = {}

filters_changed = (
    st.session_state["prev_filters"].get("show_schools") != show_schools or
    st.session_state["prev_filters"].get("show_hospitals") != show_hospitals or
    st.session_state["prev_filters"].get("selected_center") != selected_center or 
    st.session_state["prev_filters"].get("selected_minutes") != selected_minutes 
)

# Save previous map view only if filters are changed
if filters_changed and "last_map_data" in st.session_state:
    map_data = st.session_state["last_map_data"]
    if map_data and "center" in map_data and "zoom" in map_data:
        st.session_state["map_center"] = [
            map_data["center"]["lat"],
            map_data["center"]["lng"]
        ]
        st.session_state["map_zoom"] = map_data["zoom"]

# Update stored filter values
st.session_state["prev_filters"] = {
    "show_schools": show_schools,
    "show_hospitals": show_hospitals,
    "selected_center": selected_center,
    "selected_minutes": selected_minutes
}

# Add legend
colormap.caption = 'Minutes from Origin'
colormap.add_to(m)


# # Add polygons to the map
# folium.GeoJson(gdf).add_to(m)

# Display the map
map_data = st_folium(m, use_container_width=True, height=650, key="iso_map", returned_objects=["last_object_clicked", "center", "zoom"])

# Save latest map state to session
st.session_state["last_map_data"] = map_data

# if map_data and "zoom" in map_data and "center" in map_data:
#     center_dict = map_data["center"]
#     center_list = [center_dict['lat'], center_dict['lng']]
#     st.session_state["map_zoom"] = map_data["zoom"]
#     st.session_state["map_center"] = center_list

# Update session_state only if user moved the map
# if map_data and "center" in map_data and "zoom" in map_data:
#     new_center = [map_data["center"]["lat"], map_data["center"]["lng"]]
#     new_zoom = map_data["zoom"]
#     print(new_center)
#     st.session_state.map_center = new_center
#     st.session_state.map_zoom = new_zoom
    
    # # Save only if it's a real change (optional)
    # if new_center != st.session_state.map_center or new_zoom != st.session_state.map_zoom:
    #     print("SALVAAA")
    #     st.session_state.map_center = new_center
    #     st.session_state.map_zoom = new_zoom




    