import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import folium_static
import os

# --- Page Configuration ---
st.set_page_config(page_title="OptimCharge Dashboard", layout="wide")

# --- Helper Functions ---
@st.cache_data
def load_data(file_path, required_columns=None):
    """Loads data from an Excel file and checks required columns."""
    if not os.path.exists(file_path):
        st.error(f"File not found: {file_path}")
        return pd.DataFrame()
    try:
        data = pd.read_excel(file_path)
        if required_columns:
            missing_cols = [col for col in required_columns if col not in data.columns]
            if missing_cols:
                st.error(f"Missing columns in {file_path}: {', '.join(missing_cols)}")
                return pd.DataFrame()
            data = data.dropna(subset=required_columns)
        return data
    except Exception as e:
        st.error(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()

def display_station_map(data, location=[-1.95, 30.06], zoom_start=8):
    """Displays a Folium map with charging stations."""
    m = folium.Map(location=location, zoom_start=zoom_start)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in data.iterrows():
        color = "green" if row["Status"] == "Operational" else "orange"
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            popup=f"Station: {row['Name']}<br>Status: {row['Status']}",
            icon=folium.Icon(color=color)
        ).add_to(marker_cluster)

    folium_static(m, width=800, height=500)

def display_emission_heatmap(data):
    """Displays a heatmap of emissions."""
    m = folium.Map(location=[-1.95, 30.06], zoom_start=7)
    heat_data = [
        [row['latitude'], row['longitude'], row['CarbonMonoxide_H2O_column_number_density']]
        for _, row in data.iterrows()
    ]
    HeatMap(heat_data).add_to(m)
    folium_static(m, width=800, height=500)

# --- Data Loading ---
# File paths
emissions_data_path = r"C:/Users/robyn/OneDrive/Rwanda Charging Stations/emmissions .xlsx"
charging_data_path = r"C:/Users/robyn/OneDrive/Rwanda Charging Stations/missing addresses .xlsx"
population_data_path = r"C:/Users/robyn/OneDrive/Rwanda Charging Stations/young_pop.xlsx"

# Loading data with required columns
emissions_data = load_data(emissions_data_path, ["latitude", "longitude", "CarbonMonoxide_H2O_column_number_density"])
charging_data = load_data(charging_data_path, ["Latitude", "Longitude", "Status", "Name", "Address"])
population_data = load_data(population_data_path, ["Latitude", "Longitude", "Total_Young_Population"])

# --- Authentication ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_type = None

if not st.session_state.logged_in:
    st.title("Welcome to OptimCharge!")
    st.markdown("""
        OptimCharge is your hub for EV station insights and management.
        Log in to access tailored features.
    """)
    st.sidebar.header("Login")
    user_type = st.sidebar.selectbox("Select User Type", ["Client", "EV User"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")

    if login_button:
        if username == "client" and password == "client123" and user_type == "Client":
            st.session_state.logged_in = True
            st.session_state.user_type = "Client"
            st.sidebar.success("Welcome, Client!")
        elif username == "evuser" and password == "evuser123" and user_type == "EV User":
            st.session_state.logged_in = True
            st.session_state.user_type = "EV User"
            st.sidebar.success("Welcome, EV User!")
        else:
            st.sidebar.error("Invalid credentials.")
else:
    # --- Main Dashboard ---
    user_role = st.session_state.user_type
    st.sidebar.header("Welcome")
    st.sidebar.markdown(f"Logged in as: **{user_role}**")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.experimental_rerun()

    st.title("⚡ OptimCharge Dashboard")
    st.markdown(f"Welcome, **{user_role}**! Explore tailored insights.")

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["🌍 Environmental Impact", "⚡ EV Charging Stations", "📊 Population Data"])

    # --- Environmental Impact ---
    with tab1:
        st.header("Carbon Monoxide Emissions Heatmap")
        if emissions_data.empty:
            st.error("Emissions data not found.")
        else:
            st.write("### Visualizing Carbon Monoxide Emissions")
            display_emission_heatmap(emissions_data)

    # --- EV Charging Stations ---
    with tab2:
        st.header("EV Charging Stations")
        if charging_data.empty:
            st.error("Charging station data not found.")
        else:
            if user_role == "Client":
                st.write("Filter stations by status:")
                status_filter = st.selectbox("Station Status", ["All", "Operational", "Under Construction"])
                filtered_data = charging_data if status_filter == "All" else charging_data[charging_data["Status"] == status_filter]
                st.write(filtered_data[["Name", "Status", "Latitude", "Longitude"]])
                display_station_map(filtered_data)
            elif user_role == "EV User":
                town = st.text_input("Enter your town to locate nearby stations:")
                if town:
                    stations_in_town = charging_data[charging_data["Address"].str.contains(town, case=False, na=False)]
                    if stations_in_town.empty:
                        st.warning("No charging stations found in your town.")
                    else:
                        st.write("Stations in your town:")
                        display_station_map(stations_in_town)

                start_lat = st.number_input("Enter your latitude:", format="%.6f")
                start_lon = st.number_input("Enter your longitude:", format="%.6f")
                if st.button("Find Nearest Station"):
                    charging_data["Distance"] = ((charging_data["Latitude"] - start_lat) ** 2 + 
                                                 (charging_data["Longitude"] - start_lon) ** 2) ** 0.5
                    nearest_station = charging_data.loc[charging_data["Distance"].idxmin()]
                    st.success(f"Nearest Station: {nearest_station['Name']} ({nearest_station['Status']})")
                    st.write(nearest_station[["Name", "Address", "Latitude", "Longitude"]])
                    display_station_map(charging_data[charging_data["Name"] == nearest_station["Name"]])

    # --- Population Data ---
    with tab3:
        st.header("Population Data Insights")
        if population_data.empty:
            st.error("Population data not found.")
        else:
            st.write("Population Overview:")
            st.write(population_data.head())
            st.bar_chart(population_data["Total_Young_Population"])
