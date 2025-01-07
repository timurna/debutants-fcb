import streamlit as st
import pandas as pd
from datetime import datetime
import gdown

# Set the page to wide layout
st.set_page_config(layout="wide")

# Ensure 'authenticated' is initialized
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Ensure 'run_clicked' is initialized
if 'run_clicked' not in st.session_state:
    st.session_state['run_clicked'] = False

# Authentication helper
def authenticate(username, password):
    try:
        stored_username = st.secrets["credentials"]["username"]
        stored_password = st.secrets["credentials"]["password"]
    except KeyError:
        st.error("Credentials not found in Streamlit secrets.")
        return False
    return (username == stored_username) and (password == stored_password)

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
    """Download the Excel file from Google Drive and load it into a DataFrame."""
    xlsx_file = f'/tmp/debut01_{data_version}.xlsx'
    try:
        gdown.download(url=file_url, output=xlsx_file, quiet=False, fuzzy=True)
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None

    try:
        data = pd.read_excel(xlsx_file, sheet_name='Sheet1')
        # Rename columns to what we need
        data.rename(
            columns={
                'comp_name': 'Competition',
                'country': 'Country',
                'player_name': 'Player Name',
                'position': 'Position',
                'nationality': 'Nationality',
                'second_nationality': 'Second Nationality',
                'debut_for': 'Debut Club',
                'debut_date': 'Debut Date',
                'age_debut': 'Age at Debut',
                'debut_month': 'Debut Month',
                'goals_for': 'Goals For',
                'goals_against': 'Goals Against',
                'value_at_debut': 'Value at Debut',
                'player_market_value': 'Current Market Value',
                'appearances': 'Appearances',
                'goals': 'Goals',
                'minutes_played': 'Minutes Played',
                'debut_type': 'Debut Type',
            },
            inplace=True
        )
        # Convert Debut Date to a proper datetime
        data['Debut Date'] = pd.to_datetime(data['Debut Date'], errors='coerce')

        # Create a Debut Year column
        if 'Debut Date' in data.columns:
            data['Debut Year'] = data['Debut Date'].dt.year

        return data
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

def reset_run():
    st.session_state['run_clicked'] = False

def run_callback():
    st.session_state['run_clicked'] = True

# -----------------------------
# Main App Logic
# -----------------------------
if not st.session_state['authenticated']:
    # Prompt for login
    login()
else:
    # Once authenticated, show the main content

    # 1) Show the Logo
    # Make sure 'logo.png' is in the same directory or update the path
    st.image('logo.png', use_container_width=True, width=800)

    st.write("Welcome! You are logged in.")

    # 2) Download/Load Data
    file_url = 'https://drive.google.com/uc?id=15BbDQuW_ZJbIUIV_g7YOjoqrr8k4ZPF_'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    if data is None:
        st.error("Failed to load data.")
        st.stop()
    else:
        st.write("Data successfully loaded!")

        # 3) Build Filters in a Single Row
        #    We'll use st.columns(...) so the filters appear horizontally.
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

            with col1:
                # Competition filter
                if 'Competition' in data.columns:
                    all_competitions = sorted(data['Competition'].dropna().unique())
                    competition = st.multiselect("Select Competition",
                                                 all_competitions,
                                                 default=all_competitions)
                else:
                    st.warning("No 'Competition' column in data.")
                    competition = []

            with col2:
                # Debut Month filter
                if 'Debut Month' in data.columns:
                    all_months = sorted(data['Debut Month'].dropna().unique())
                    debut_month = st.multiselect("Select Debut Month",
                                                 all_months,
                                                 default=all_months)
                else:
                    st.warning("No 'Debut Month' column in data.")
                    debut_month = []

            with col3:
                # Debut Year filter
                if 'Debut Year' in data.columns:
                    all_years = sorted(data['Debut Year'].dropna().unique())
                    debut_year = st.multiselect("Select Debut Year",
                                                all_years,
                                                default=all_years)
                else:
                    st.warning("No 'Debut Year' column in data.")
                    debut_year = []

            with col4:
                # Age range filter
                if 'Age at Debut' in data.columns:
                    min_age = int(data['Age at Debut'].min())
                    max_age = int(data['Age at Debut'].max())
                    age_range = st.slider("Select Age Range",
                                          min_age, max_age,
                                          (min_age, max_age))
                else:
                    st.warning("No 'Age at Debut' column in data.")
                    age_range = (0, 100)

        # 4) Run Button
        st.button("Run", on_click=run_callback)

        # 5) Once run is clicked, filter and display
        if st.session_state['run_clicked']:
            # Filter the data
            filtered_data = data.copy()

            # Competition filter
            if 'Competition' in filtered_data.columns and competition:
                filtered_data = filtered_data[filtered_data['Competition'].isin(competition)]

            # Debut Month filter
            if 'Debut Month' in filtered_data.columns and debut_month:
                filtered_data = filtered_data[filtered_data['Debut Month'].isin(debut_month)]

            # Debut Year filter
            if 'Debut Year' in filtered_data.columns and debut_year:
                filtered_data = filtered_data[filtered_data['Debut Year'].isin(debut_year)]

            # Age range filter
            if 'Age at Debut' in filtered_data.columns:
                filtered_data = filtered_data[
                    (filtered_data['Age at Debut'] >= age_range[0]) &
                    (filtered_data['Age at Debut'] <= age_range[1])
                ]

            # Choose which columns we want to display
            display_columns = [
                'Competition',
                'Country',
                'Player Name',
                'Position',
                'Nationality',
                'Second Nationality',
                'Debut Club',
                'Debut Date',
                'Debut Month',
                'Age at Debut',
                'Goals For',
                'Goals Against',
                'Appearances',
                'Goals',
                'Minutes Played',
                'Value at Debut',
                'Current Market Value'
            ]
            # Only keep columns that actually exist in filtered_data
            display_columns = [c for c in display_columns if c in filtered_data.columns]

            # Title & row count
            st.title("Football Debutants Explorer")
            st.write(f"Showing {len(filtered_data)} debutants based on filters")

            # 6) Display the table *only with the chosen columns*
            st.dataframe(filtered_data[display_columns].reset_index(drop=True))

            # 7) Download button
            if not filtered_data.empty:
                tmp_path = '/tmp/filtered_data.xlsx'
                filtered_data[display_columns].to_excel(tmp_path, index=False)

                with open(tmp_path, 'rb') as f:
                    st.download_button(
                        label="Download Filtered Data as Excel",
                        data=f,
                        file_name="filtered_debutants.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.write("Please set your filters and click **Run** to see results.")
