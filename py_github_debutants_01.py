import streamlit as st
import pandas as pd
from datetime import datetime
import gdown

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Ensure 'authenticated' is initialized in session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

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

# Function to download and load the Excel file
@st.cache_data
def download_and_load_data(file_url, data_version):
    xlsx_file = f'/tmp/debut01_{data_version}.xlsx'
    try:
        gdown.download(url=file_url, output=xlsx_file, quiet=False, fuzzy=True)
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None

    try:
        data = pd.read_excel(xlsx_file, sheet_name='Sheet1')
        data.rename(columns={
            'comp_name': 'Competition',
            'country': 'Country',
            'player_name': 'Player Name',
            'position': 'Position',
            'debut_for': 'Debut Club',
            'debut_date': 'Debut Date',
            'age_debut': 'Age at Debut',
            'debut_month': 'Debut Month'
        }, inplace=True)
        data['Debut Date'] = pd.to_datetime(data['Debut Date'], errors='coerce')
        return data
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

if not st.session_state.authenticated:
    login()
else:
    st.write("Welcome! You are logged in.")
    file_url = 'https://drive.google.com/uc?id=15BbDQuW_ZJbIUIV_g7YOjoqrr8k4ZPF_'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    if data is None:
        st.error("Failed to load data")
        st.stop()
    else:
        st.write("Data successfully loaded!")

        # Sidebar Filters
        st.sidebar.header("Filter Options")
        competition = st.sidebar.multiselect(
            "Select Competition", data['Competition'].unique(), data['Competition'].unique()
        )
        month = st.sidebar.multiselect(
            "Select Debut Month", data['Debut Month'].unique(), data['Debut Month'].unique()
        )
        age_range = st.sidebar.slider(
            "Select Age Range",
            int(data['Age at Debut'].min()),
            int(data['Age at Debut'].max()),
            (int(data['Age at Debut'].min()), int(data['Age at Debut'].max()))
        )

        filtered_data = data[
            (data['Competition'].isin(competition)) &
            (data['Debut Month'].isin(month)) &
            (data['Age at Debut'].between(age_range[0], age_range[1]))
        ]

        st.title("Football Debutants Explorer")
        st.write(f"Showing {len(filtered_data)} debutants based on filters")
        st.dataframe(filtered_data)

        filtered_data_xlsx = filtered_data.to_excel('/tmp/filtered_data.xlsx', index=False)
        with open('/tmp/filtered_data.xlsx', 'rb') as f:
            st.download_button(
                "Download Filtered Data as Excel",
                data=f,
                file_name="filtered_debutants.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
