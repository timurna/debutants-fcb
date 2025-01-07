import streamlit as st
import pandas as pd
from datetime import datetime
import gdown

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Ensure 'authenticated' is initialized in session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Ensure 'run_clicked' is also initialized
if 'run_clicked' not in st.session_state:
    st.session_state['run_clicked'] = False

# Authentication
def authenticate(username, password):
    try:
        stored_username = st.secrets["credentials"]["username"]
        stored_password = st.secrets["credentials"]["password"]
    except KeyError:
        st.error("Credentials not found in Streamlit secrets.")
        return False
    return username == stored_username and password == stored_password

def login():
    st.text_input("Username", key="login_username")
    st.text_input("Password", type="password", key="login_password")

    def authenticate_and_login():
        username = st.session_state.login_username
        password = st.session_state.login_password
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.success("Login successful!")
        else:
            st.error("Invalid username or password")

    st.button("Login", on_click=authenticate_and_login)

# Download and load data
@st.cache_data
def download_and_load_data(file_url, data_version):
    """Download Excel from Google Drive (using gdown) and load it."""
    xlsx_file = f'/tmp/debut01_{data_version}.xlsx'
    try:
        gdown.download(url=file_url, output=xlsx_file, quiet=False, fuzzy=True)
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None

    try:
        data = pd.read_excel(xlsx_file, sheet_name='Sheet1')
        # Rename columns to match what we use in filters and displays
        data.rename(
            columns={
                'comp_name': 'Competition',
                'country': 'Country',
                'comp_url': 'Competition URL',
                'player_name': 'Player Name',
                'player_url': 'Player URL',
                'position': 'Position',
                'nationality': 'Nationality',
                'second_nationality': 'Second Nationality',
                'debut_for': 'Debut Club',
                'debut_date': 'Debut Date',
                'goals_for': 'Goals For',
                'goals_against': 'Goals Against',
                'age_debut': 'Age at Debut',
                'value_at_debut': 'Value at Debut',
                'player_market_value': 'Current Market Value',
                'appearances': 'Appearances',
                'goals': 'Goals',
                'minutes_played': 'Minutes Played',
                'debut_type': 'Debut Type',
                'debut_month': 'Debut Month'
            },
            inplace=True
        )
        # Convert Debut Date to datetime
        data['Debut Date'] = pd.to_datetime(data['Debut Date'], errors='coerce')
        return data
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

# Reset run state
def reset_run():
    st.session_state['run_clicked'] = False

def run_callback():
    st.session_state['run_clicked'] = True

# Main app flow
if not st.session_state.authenticated:
    # Show login if user is not authenticated
    login()
else:
    # User is authenticated, show main app
    st.image('logo.png', use_container_width=True, width=800)
    st.write("Welcome! You are logged in.")

    # Download/Load data
    file_url = 'https://drive.google.com/uc?id=15BbDQuW_ZJbIUIV_g7YOjoqrr8k4ZPF_'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    if data is None:
        st.error("Failed to load data")
        st.stop()
    else:
        st.write("Data successfully loaded!")

        # Create filters
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

            # Competition filter
            with col1:
                # Display all unique competitions as default
                all_competitions = data['Competition'].dropna().unique()
                competition = st.multiselect(
                    "Select Competition",
                    all_competitions,
                    default=all_competitions
                )

            # Debut year filter
            with col2:
                # Create a Debut Year column for filtering
                data['Debut Year'] = data['Debut Date'].dt.year
                all_years = data['Debut Year'].dropna().unique()
                debut_year = st.multiselect(
                    "Select Debut Year",
                    all_years,
                    default=all_years
                )

            # Debut month filter
            with col3:
                all_months = data['Debut Month'].dropna().unique()
                month = st.multiselect(
                    "Select Debut Month",
                    all_months,
                    default=all_months
                )

            # Age range filter
            with col4:
                min_age = int(data['Age at Debut'].min())
                max_age = int(data['Age at Debut'].max())
                age_range = st.slider(
                    "Select Age Range",
                    min_age,
                    max_age,
                    (min_age, max_age)
                )

        # "Run" button
        st.button("Run", on_click=run_callback)

        # Only apply filters after user clicks "Run"
        if st.session_state['run_clicked']:
            # Filter the data
            filtered_data = data[
                (data['Competition'].isin(competition)) &
                (data['Debut Year'].isin(debut_year)) &
                (data['Debut Month'].isin(month)) &
                (data['Age at Debut'].between(age_range[0], age_range[1]))
            ]

            # Define which columns to display in final table
            display_columns = [
                'Competition', 'Country', 'Player Name', 'Position', 'Nationality',
                'Second Nationality', 'Debut Club', 'Debut Type', 'Debut Date',
                'Debut Month', 'Age at Debut', 'Goals For', 'Goals Against',
                'Appearances', 'Goals', 'Minutes Played', 'Value at Debut',
                'Current Market Value'
            ]

            # Filter to only those columns that actually exist
            display_columns = [col for col in display_columns if col in filtered_data.columns]

            # Show results
            st.title("Football Debutants Explorer")
            st.write(f"Showing {len(filtered_data)} debutants based on filters:")
            st.dataframe(filtered_data[display_columns].reset_index(drop=True))

            # Export to Excel
            filtered_xlsx = filtered_data[display_columns].to_excel('/tmp/filtered_data.xlsx', index=False)
            with open('/tmp/filtered_data.xlsx', 'rb') as f:
                st.download_button(
                    "Download Filtered Data as Excel",
                    data=f,
                    file_name="filtered_debutants.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.write("Set your filters and click **Run** to see results.")
