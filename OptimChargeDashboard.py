import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
import os

# --- Page Configuration ---
st.set_page_config(page_title="OptimCharge Dashboard", layout="wide")

# --- Custom CSS for Background Image ---
st.markdown(
    """
    <style>
        .reportview-container {
            background: url('file:///C:/Users/robyn/OneDrive/OptimCharge_Streamlit_EV_placement/EV-Charging-Station-2048x1536.jpg');
            background-size: cover;
            background-repeat: no-repeat;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Helper Functions ---
@st.cache_data
def load_emissions_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    emissions = pd.read_excel(file_path)
    return emissions.dropna(subset=['latitude', 'longitude', 'CarbonMonoxide_H2O_column_number_density'])

@st.cache_data
def load_ev_station_data(file_path, sheet_name="Sheet2"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    return data.dropna(subset=["Latitude", "Longitude"])

@st.cache_data
def load_population_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    return pd.read_excel(file_path)

def display_station_map(data, zoom_start=8, location=[-1.95, 30.06]):
    """Display a map with EV stations."""
    m = folium.Map(location=location, zoom_start=zoom_start)
    marker_cluster = MarkerCluster().add_to(m)

    for index, row in data.iterrows():
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            popup=f"Station: {row['Name']}, Status: {row['Status']}"
        ).add_to(marker_cluster)

    map_file = 'station_map.html'
    m.save(map_file)
    HtmlFile = open(map_file, 'r', encoding='utf-8')
    st.components.v1.html(HtmlFile.read(), width=700, height=500)

def display_emission_heatmap(data):
    """Display a heatmap of carbon monoxide emissions."""
    m = folium.Map(location=[-1.95, 30.06], zoom_start=7)
    heat_data = [[row['latitude'], row['longitude'], row['CarbonMonoxide_H2O_column_number_density']] 
                 for index, row in data.iterrows()]
    HeatMap(heat_data).add_to(m)
    
    map_file = 'emission_heatmap.html'
    m.save(map_file)
    HtmlFile = open(map_file, 'r', encoding='utf-8')
    st.components.v1.html(HtmlFile.read(), width=700, height=500)

# --- Data Loading ---
emissions_data = load_emissions_data(r"C:/Users/robyn/OneDrive/Rwanda Charging Stations/emmissions .xlsx")
charging_data = load_ev_station_data(r"C:/Users/robyn/OneDrive/Rwanda Charging Stations/missing addresses .xlsx")
population_data = load_population_data(r"C:/Users/robyn/OneDrive/Rwanda Charging Stations/young_pop.xlsx")

# --- User Authentication ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_type = None

if not st.session_state.logged_in:
    st.title("OptimCharge: Your EV Charging Hub")
    st.markdown("""
    **OptimCharge** is a platform designed to optimize the placement and usage of EV charging stations in Rwanda.
    Log in to access features tailored to your role.
    """)
    
    # Sidebar Login Form
    st.sidebar.header("Login")
    user_type = st.sidebar.selectbox("Select User Type", ["Client", "EV User"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")
    
    if login_button:
        if username == "optimcharge" and password == "optimcharge_password" and user_type == "Client":
            st.session_state.logged_in = True
            st.session_state.user_type = "Client"
            st.sidebar.success("Welcome OptimCharge Client!")
        elif username == "ev_user" and password == "ev_user_password" and user_type == "EV User":
            st.session_state.logged_in = True
            st.session_state.user_type = "EV User"
            st.sidebar.success("Welcome EV User!")
        else:
            st.sidebar.error("Invalid credentials.")
else:
    # --- Post Login Interface ---
    user_role = st.session_state.user_type
    
    # Sidebar Options
    st.sidebar.header("Welcome")
    st.sidebar.markdown(f"Logged in as: **{user_role}**")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.experimental_rerun()
    
    # Home Page Content
    st.title("⚡ OptimCharge Management Dashboard")
    st.markdown(f"Welcome, **{user_role}**! Explore insights tailored to your role.")
    
    # Tabs for dashboard
    tab1, tab2, tab3 = st.tabs(["🌍 Environmental Impact", "⚡ EV Charging Stations", "📊 Population Data"])

    # --- Environmental Impact Tab ---
    with tab1:
        st.header("Carbon Monoxide Emissions Heatmap")
        if emissions_data.empty:
            st.error("Emissions data not found or loaded incorrectly.")
        else:
            st.write("#### Heatmap of Carbon Monoxide Emissions")
            display_emission_heatmap(emissions_data)

    # --- EV Charging Stations Tab ---
    with tab2:
        st.header("EV Charging Stations")
        if user_role == "Client":
            status_filter = st.selectbox("Filter Stations by Status", ["All", "Operational", "Under-Construction"])
            filtered_data = charging_data if status_filter == "All" else charging_data[charging_data['Status'] == status_filter]
            st.write(filtered_data[['Name', 'Status', 'Latitude', 'Longitude']])
            display_station_map(filtered_data)
        elif user_role == "EV User":
            town = st.text_input("Enter your town")
            if town:
                stations_in_town = charging_data[charging_data['Address'].str.contains(town, case=False, na=False)]
                if stations_in_town.empty:
                    st.warning("No charging stations found in that town.")
                else:
                    st.write("Stations in your town:")
                    st.write(stations_in_town[['Name', 'Status', 'Latitude', 'Longitude']])
                    display_station_map(stations_in_town)

            start_lat = st.number_input("Enter starting latitude:", format="%.6f")
            start_lon = st.number_input("Enter starting longitude:", format="%.6f")
            if st.button("Find Closest Station"):
                if start_lat and start_lon:
                    charging_data['Distance'] = ((charging_data['Latitude'] - start_lat) ** 2 + 
                                                 (charging_data['Longitude'] - start_lon) ** 2) ** 0.5
                    closest_station = charging_data.loc[charging_data['Distance'].idxmin()]
                    st.success(f"Closest station: {closest_station['Name']} ({closest_station['Status']}).")
                    st.write(closest_station[['Name', 'Address', 'Latitude', 'Longitude']])
                    display_station_map(charging_data[charging_data['Name'] == closest_station['Name']])

            feedback = st.text_area("Leave feedback:")
            if st.button("Submit Feedback"):
                st.success("Thank you for your feedback!")

    # --- Population Data Tab ---
    with tab3:
        st.header("Population Data Analysis")
        if population_data.empty:
            st.error("Population data not found or loaded incorrectly.")
        else:
            st.write("### Population by Province")
            st.write(population_data.head())
            st.bar_chart(population_data["Total_Young_Population"])  # Replace with actual column name
