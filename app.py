import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Texas Historic Sites Explorer", layout="wide")
st.title("🗺️ Texas Historic Sites Explorer")
st.markdown("Public markers, National Register sites, courthouses & museums from the Texas Historical Commission.")

with st.sidebar:
    st.header("Filters & Layers")
    keyword = st.text_input("Keyword Search", "")
    show_markers = st.checkbox("Historical Markers", value=True)
    show_nr_props = st.checkbox("National Register Properties", value=True)
    show_nr_dists = st.checkbox("National Register Districts", value=True)
    show_courthouses = st.checkbox("County Courthouses", value=True)
    show_museums = st.checkbox("Museums", value=True)

m = folium.Map(location=[31.0, -99.0], zoom_start=6, tiles="CartoDB positron")

def query_layer(layer_id, name, color, icon="info-sign", max_features=1500):
    # ... rest of function unchanged
    url = f"https://gis.thc.texas.gov/arcgis/rest/services/Historical/FeatureServer/{layer_id}/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
        "resultRecordCount": max_features
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        geojson = r.json()
        fg = folium.FeatureGroup(name=name)
        cluster = MarkerCluster().add_to(fg)
        
        for feature in geojson.get("features", []):
            props = feature["properties"]
            geom = feature["geometry"]
            
            if geom["type"] == "Point":
                lon, lat = geom["coordinates"]
                popup_html = f"""
                <b>{props.get('Marker_Title') or props.get('Property_Name') or props.get('Museum_Name') or props.get('Courthouse_Name') or 'Site'}</b><br>
                County: {props.get('County', 'N/A')}<br>
                <a href="https://atlas.thc.texas.gov/Details/{props.get('Atlas_Number') or props.get('NRIS_Number')}" target="_blank">View on THC Atlas</a>
                """
                folium.Marker(
                    [lat, lon],
                    popup=popup_html,
                    icon=folium.Icon(color=color, icon=icon, prefix="fa"),
                    tooltip=name
                ).add_to(cluster)
            elif geom["type"] == "Polygon" and layer_id == 4:  # NR Districts
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {"fillColor": color, "color": color, "weight": 2, "fillOpacity": 0.25},
                    tooltip=props.get("District_Name", "NR District")
                ).add_to(fg)
        return fg
    except:
        return None

# Add layers conditionally - separate if statements to avoid Streamlit parsing bug
if show_markers:
    fg_markers = query_layer(2, "Historical Markers", "blue", "bookmark")
    if fg_markers:
        fg_markers.add_to(m)

if show_nr_props:
    fg_props = query_layer(3, "NR Properties", "purple", "star")
    if fg_props:
        fg_props.add_to(m)

if show_nr_dists:
    fg_dists = query_layer(4, "NR Districts", "orange")
    if fg_dists:
        fg_dists.add_to(m)

if show_courthouses:
    fg_courts = query_layer(6, "County Courthouses", "red", "university")
    if fg_courts:
        fg_courts.add_to(m)

if show_museums:
    fg_museums = query_layer(1, "Museums", "green", "info-sign")
    if fg_museums:
        fg_museums.add_to(m)
folium.LayerControl().add_to(m)
st_folium(m, width=1200, height=650)

st.caption("Data from Texas Historical Commission • Not official • Live from public ArcGIS services")
