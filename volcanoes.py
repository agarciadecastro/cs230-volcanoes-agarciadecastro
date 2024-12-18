"""
Name:       Álvaro García de Castro
CS230:      Section 5 (Asynchronous)
Data:       Volcanoes Dataset
URL:        

Description:
This program explores the Volcanoes dataset with interactive visualizations. Users can explore queries about volcanic regions, eruption dates, volcano types, and rock types through charts, graphs, and maps.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Volcanoes Explorer", page_icon="🌋", layout="wide")

# [DA1] Clean the data
@st.cache_data
def load_and_clean_data(data_path):
    data = pd.read_csv(data_path, encoding='latin1', skiprows=1)
    data.columns = [
        "Volcano Number", "Volcano Name", "Country", "Volcanic Region", "Volcanic Province",
        "Volcano Landform", "Primary Volcano Type", "Activity Evidence", "Last Known Eruption",
        "Latitude", "Longitude", "Elevation (m)", "Tectonic Setting", "Dominant Rock Type"
    ]
    data = data.dropna(subset=["Latitude", "Longitude", "Elevation (m)"])
    data["Latitude"] = pd.to_numeric(data["Latitude"], errors='coerce')
    data["Longitude"] = pd.to_numeric(data["Longitude"], errors='coerce')
    data["Elevation (m)"] = pd.to_numeric(data["Elevation (m)"], errors='coerce')
    data["Negative Elevation"] = -data["Elevation (m)"]  # Precompute for undersea maps
    return data

# [PY1] Function with parameters and a default value
@st.cache_data
def filter_data(data, column, value, exact_match=True):
    if exact_match:
        return data[data[column] == value]
    else:
        return data[data[column].str.contains(value, na=False)]

# Load and clean data
try:
    data_path = "volcanoes.csv"
    data = load_and_clean_data(data_path)
except FileNotFoundError:
    st.error("File not found. Please upload the dataset.")

# Custom styling for a more user-friendly and prettier interface
st.markdown("""
    <style>
    .main {background-color: #f5f7fa;}
    h1 {color: #ff6347; text-align: center; font-family: Arial, sans-serif;}
    h3 {color: #444;}
    .stButton > button {background-color: #ff6347; color: white; border-radius: 8px; border: none;}
    .stButton > button:hover {background-color: #ff4500;}
    </style>
    """, unsafe_allow_html=True)

# Header with style and description
st.markdown("""
# 🌋 Global Volcanoes Map Explorer
Welcome to the interactive web application that visualizes volcano locations worldwide. Use the map below to explore volcanoes around the globe!
""", unsafe_allow_html=True)

# Sidebar Navigation for Options
st.sidebar.title("Volcano Data Explorer")
st.sidebar.markdown("Use this sidebar to explore the data and visualizations.")
option = st.sidebar.radio("Select an Option:", [
    "World Map of Volcanoes",
    "Top 5 Countries by Region",
    "Map of Overseas Volcanoes",
    "Map of Undersea Volcanoes",
    "Volcano Types by Tectonic Setting"
])

if option == "World Map of Volcanoes":
    st.title("🔍 Explore Volcanoes Worldwide")
    st.subheader("Pinpointing volcano locations with latitude and longitude coordinates")

    # [DA2] Sort data
    map_data = data.sort_values(by="Latitude")

    # [PY4] Lambda function to assign colors based on elevation
    map_data["Color"] = map_data["Elevation (m)"].apply(lambda x: [255, 99, 71, 160] if x > 0 else [71, 99, 255, 160])

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/outdoors-v11",
        initial_view_state=pdk.ViewState(
            latitude=map_data["Latitude"].mean(),
            longitude=map_data["Longitude"].mean(),
            zoom=2,
            pitch=50
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position="[Longitude, Latitude]",
                get_radius=40000,
                get_color="Color",
                pickable=True
            )
        ]
    ))
    st.text("Zoom and pan the map to explore volcanoes across different regions of the world.")

# Query 2: Top 5 Countries by Region
elif option == "Top 5 Countries by Region":
    st.title("Top 5 Countries by Volcanic Region")
    region = st.selectbox("Select a Region:", data["Volcanic Region"].unique())
    filtered_data = data[data["Volcanic Region"] == region]
    top_countries = filtered_data["Country"].value_counts().head(5).reset_index()
    top_countries.columns = ["Country", "Volcano Count"]

    st.subheader(f"Top 5 Countries in {region}")
    st.bar_chart(top_countries.set_index("Country"))

    st.subheader("Country, Province, and Volcano Count")
    country_province_count = filtered_data.groupby(["Volcanic Province", "Country"]).size().reset_index(name="Count")

    # Format table to avoid repeating province names
    formatted_table = []
    for province, group in country_province_count.groupby("Volcanic Province"):
        first_row = {"Province": province, "Country": group.iloc[0]["Country"], "Count": group.iloc[0]["Count"]}
        formatted_table.append(first_row)
        for _, row in group.iloc[1:].iterrows():
            additional_row = {"Province": "", "Country": row["Country"], "Count": row["Count"]}
            formatted_table.append(additional_row)

    # Convert formatted data to DataFrame
    formatted_df = pd.DataFrame(formatted_table)
    formatted_df.index = ["" for _ in range(len(formatted_df))]  # Remove the index completely
    st.table(formatted_df)

# Query 3.1: Map of Overseas Volcanoes
elif option == "Map of Overseas Volcanoes":
    st.title("Map of Overseas Volcanoes")
    overseas_data = data[data["Elevation (m)"] > 0]

    if not overseas_data.empty:
        fig = px.scatter_mapbox(
            overseas_data,
            lat="Latitude",
            lon="Longitude",
            size="Elevation (m)",  # Tower height based on elevation
            color="Elevation (m)",  # Color scale for elevation
            color_continuous_scale="Reds",
            size_max=20,
            zoom=1,
            height=700
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_zoom=2,
            mapbox_center={"lat": overseas_data["Latitude"].mean(), "lon": overseas_data["Longitude"].mean()},
            coloraxis_colorbar=dict(title="Elevation (m)"),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for overseas volcanoes.")

# Query 3.2: 3D Map of Undersea Volcanoes
elif option == "Map of Undersea Volcanoes":
    st.title("Map of Undersea Volcanoes")
    undersea_data = data[data["Elevation (m)"] < 0]

    if not undersea_data.empty:
        fig = px.scatter_mapbox(
            undersea_data,
            lat="Latitude",
            lon="Longitude",
            size=-undersea_data["Elevation (m)"],  # Tower height based on depth
            color=-undersea_data["Elevation (m)"],  # Color scale for depth
            color_continuous_scale="Blues",
            size_max=20,
            zoom=1,
            height=700
        )
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox_zoom=2,
            mapbox_center={"lat": undersea_data["Latitude"].mean(), "lon": undersea_data["Longitude"].mean()},
            coloraxis_colorbar=dict(title="Depth (m)"),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for undersea volcanoes.")

# Query 4: Volcano Types by Tectonic Setting
elif option == "Volcano Types by Tectonic Setting":
    st.title("Volcano Types by Tectonic Setting")
    tectonic_settings = st.multiselect("Select Tectonic Settings:", data["Tectonic Setting"].dropna().unique())

    if tectonic_settings:
        filtered_data = data[data["Tectonic Setting"].isin(tectonic_settings)]
        if not filtered_data.empty:
            chart_data = filtered_data.groupby(["Tectonic Setting", "Primary Volcano Type"]).size().unstack()
            st.bar_chart(chart_data)
            st.text("This chart shows the distribution of volcano types across selected tectonic settings.")
        else:
            st.warning("No data available for the selected tectonic settings.")
    else:
        st.warning("Please select at least one tectonic setting.")

# Footer with styling
st.markdown("---")
st.markdown("**🔗 Developed by Álvaro | CS230 Final Project**")
