import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import folium_static
import os
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(page_title="Green Current Dashboard", layout="wide")

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
    """Displays a Folium map with detailed charging station information."""
    m = folium.Map(location=location, zoom_start=zoom_start)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in data.iterrows():
        popup_content = (
            f"<b>Station:</b> {row['Connector Name']}<br>"
            f"<b>Status:</b> {row['Status']}<br>"
            f"<b>Connector Type:</b> {row['Connector Type']}<br>"
            f"<b>Availability:</b> {row['Charger Availability']}<br>"
            f"<b>Address:</b> {row['Address']}"
        )
        color = "green" if row["Status"] == "Operational" else "orange"
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            popup=popup_content,
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

# --- Information for Environmental Impact ---
def client_environmental_impact():
    st.markdown("### Key Considerations for EV Placement Companies")
    st.markdown("""
    **Government Support and Incentives:**
    - Research incentives for EV technologies.
    - Tax breaks and exemptions on EV imports and sales.
    - Infrastructure development support for charging stations.

    **Market Potential and Demand:**
    - Compare urban vs. rural EV adoption rates.
    - Analyze target demographics for EV adoption.
    - Understand consumer preferences regarding EV models, range, and charging needs.

    **Benefits of EV Placement in Rwanda:**
    - Reduced greenhouse gas emissions.
    - Job creation in the EV sector.
    - Association with sustainable, innovative solutions.
    """)

def ev_user_environmental_impact():
    st.markdown("### How Much Emissions Can You Save with an EV?")
    st.markdown("""
    **Zero Tailpipe Emissions:** EVs produce no tailpipe emissions, significantly reducing air pollution.
    
    **Reduced Lifecycle Emissions:** While EV production generates emissions, their overall lifecycle emissions are much lower compared to traditional vehicles, especially when using renewable energy.

    **Emission Savings:** EVs can drastically reduce emissions depending on your electricity mix and driving habits.
    """)

    st.markdown("### Benefits of Owning an EV")
    st.markdown("""
    - **Lower Operating Costs:** Electricity is cheaper than gasoline or diesel.
    - **Reduced Maintenance Costs:** EVs have fewer moving parts.
    - **Quiet and Smooth Ride:** EVs offer a superior driving experience.
    - **Government Incentives:** Tax breaks and subsidies may reduce costs.
    - **Positive Environmental Impact:** Contribute to a cleaner environment.
    """)

# --- Data Loading ---
# File paths
emissions_data_path = (r"emmissions .xlsx")
charging_data_path = (r"Charging_Stations.xlsx")
population_data_path = (r"young_pop.xlsx")

# Loading data with required columns
emissions_data = load_data(emissions_data_path, ["latitude", "longitude", "CarbonMonoxide_H2O_column_number_density"])
charging_data = load_data(charging_data_path, [
    "Latitude", "Longitude", "Status", "Connector Name", "Address",
    "Connector Type", "City/Suburb/Town", "Sales Revenue (RWF)", "Charger Availability"
])
population_data = load_data(population_data_path, ["Latitude", "Longitude", "Total_Young_Population"])

# --- Authentication ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_type = None

if not st.session_state.logged_in:
    st.title("Welcome to Green Current!")
    st.markdown("""
        Green Current is your hub for EV station insights and management.
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

    st.title("⚡ Green Current Dashboard")
    st.markdown(f"Welcome, **{user_role}**! Explore tailored insights.")

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["🌍 Environmental Impact", "⚡ EV Charging Stations", "📊 Population Data"])

    # --- Environmental Impact ---
    with tab1:
        st.header("Environmental Impact")
        if user_role == "Client":
            client_environmental_impact()
        elif user_role == "EV User":
            ev_user_environmental_impact()
        if emissions_data.empty:
            st.error("Emissions data not found.")
        else:
            st.write("### Emissions Heatmap")
            display_emission_heatmap(emissions_data)

    # --- EV Charging Stations ---
    with tab2:
        st.header("EV Charging Stations")
        if charging_data.empty:
            st.error("Charging station data not found.")
        else:
            if user_role == "Client":
                st.write("Filter stations by status:")
                status_filter = st.selectbox("Station Status", ["All", "Operational", "Under Construction","Planned","Awaiting Contract","Pending Site Visit"])
                filtered_data = charging_data if status_filter == "All" else charging_data[charging_data["Status"] == status_filter]
                st.write(filtered_data[["Connector Name", "Status", "Latitude", "Longitude", "Sales Revenue (RWF)"]])
                display_station_map(filtered_data)
            elif user_role == "EV User":
                town = st.text_input("Enter your town to locate nearby stations:")
                if town:
                    stations_in_town = charging_data[charging_data["City/Suburb/Town"].str.contains(town, case=False, na=False)]
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
                    st.success(f"Nearest Station: {nearest_station['Connector Name']} ({nearest_station['Status']})")
                    st.write(nearest_station[["Connector Name", "Address", "Latitude", "Longitude"]])
                    display_station_map(charging_data[charging_data["Connector Name"] == nearest_station["Connector Name"]])

    # --- Population Data ---
    with tab3:
        st.header("Population Data Insights")
        if population_data.empty:
            st.error("Population data not found.")
        else:
            st.write("Population Overview:")
            st.write(population_data.head())
            st.bar_chart(population_data["Total_Young_Population"])
