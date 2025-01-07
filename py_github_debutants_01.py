import streamlit as st
import pandas as pd
import gdown
from datetime import datetime

# ------------------------------------------------------------------------------------
# PAGE CONFIG: Must be the very first Streamlit command
# ------------------------------------------------------------------------------------
st.set_page_config(layout="wide")

# Ensure 'authenticated' is initialized
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Ensure 'run_clicked' is initialized
if 'run_clicked' not in st.session_state:
    st.session_state['run_clicked'] = False

# ------------------------------------------------------------------------------------
# AUTHENTICATION HELPERS
# ------------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------------
# DATA DOWNLOAD & LOAD
# ------------------------------------------------------------------------------------
@st.cache_data
def download_and_load_data(file_url, data_version):
    """
    Download the Excel file from Google Drive and load it into a DataFrame.
    """
    xlsx_file = f'/tmp/debut01_{data_version}.xlsx'
    try:
        gdown.download(url=file_url, output=xlsx_file, quiet=False, fuzzy=True)
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None

    try:
        data = pd.read_excel(xlsx_file, sheet_name='Sheet1')
        # Rename columns
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
                'opponent': 'Opponent',
            },
            inplace=True
        )

        # Convert Debut Date to datetime
        data['Debut Date'] = pd.to_datetime(data['Debut Date'], errors='coerce')

        # Create Debut Year column
        if 'Debut Date' in data.columns:
            data['Debut Year'] = data['Debut Date'].dt.year

        # Rename "Bundesliga" to "1. Bundesliga" if country is Germany
        data.loc[
            (data['Competition'] == 'Bundesliga') & (data['Country'] == 'Germany'),
            'Competition'
        ] = '1. Bundesliga'

        # Create Competition (Country) columns for filtering
        data['CompCountryID'] = data['Competition'] + "||" + data['Country'].fillna('')
        data['Competition (Country)'] = data['Competition'] + " (" + data['Country'].fillna('') + ")"

        return data

    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

# ------------------------------------------------------------------------------------
# CALLBACK
# ------------------------------------------------------------------------------------
def run_callback():
    st.session_state['run_clicked'] = True

# ------------------------------------------------------------------------------------
# STYLING AND FORMAT FUNCTIONS
# ------------------------------------------------------------------------------------
def highlight_mv(df):
    """
    Highlight the 'Current Market Value' cell if the numeric current MV
    is higher than the numeric debut MV.
    """
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    if 'Value at Debut (Numeric)' in df.columns and 'Current Market Value (Numeric)' in df.columns:
        mask = df['Current Market Value (Numeric)'] > df['Value at Debut (Numeric)']
        styles.loc[mask, 'Current Market Value'] = 'background-color: #c6f6d5'
    return styles

def format_cmv_with_change(row):
    """
    Return a string: e.g. '€1,000,000 (+50.0%)' if there's an increase.
    Handles missing/zero values gracefully.
    """
    debut_val = row.get('Value at Debut (Numeric)')
    curr_val = row.get('Current Market Value (Numeric)')

    if pd.isna(curr_val):
        return "€0"

    base_str = f"€{curr_val:,.0f}"

    if pd.isna(debut_val) or debut_val == 0:
        # Can't calculate percentage if debut is missing/zero
        return base_str

    pct_change = (curr_val - debut_val) / debut_val * 100
    if pct_change == 0:
        return base_str
    return f"{base_str} ({pct_change:+.1f}%)"

# ------------------------------------------------------------------------------------
# MAIN APP LOGIC
# ------------------------------------------------------------------------------------
if not st.session_state['authenticated']:
    # Show login interface
    login()
else:
    # Show main content after successful login
    # Logo or image
    st.image('logo.png', use_container_width=True, width=800)
    st.write("Welcome! You are logged in.")

    # Download/Load Data
    file_url = 'https://drive.google.com/uc?id=15BbDQuW_ZJbIUIV_g7YOjoqrr8k4ZPF_'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    # If data fails to load, stop
    if data is None:
        st.error("Failed to load data.")
        st.stop()
    else:
        st.write("Data successfully loaded!")

        # Create numeric backup columns
        data['Value at Debut (Numeric)'] = data['Value at Debut']
        data['Current Market Value (Numeric)'] = data['Current Market Value']

        # Build the display version of Current Market Value
        data['Current Market Value'] = data.apply(format_cmv_with_change, axis=1)

        # Just to confirm environment at runtime:
        st.write("Pandas version at runtime:", pd.__version__)

        # ---------------
        # FILTER UI
        # ---------------
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

            # 1) Competition (Country) filter
            with col1:
                if 'Competition (Country)' in data.columns and 'CompCountryID' in data.columns:
                    all_comps = sorted(data['Competition (Country)'].dropna().unique())
                    comp_options = ["All"] + list(all_comps)
                    selected_comp = st.multiselect("Select Competition", comp_options, default=[])
                else:
                    st.warning("No Competition/Country columns in data.")
                    selected_comp = []

            # 2) Debut Month filter
            with col2:
                if 'Debut Month' in data.columns:
                    all_months = sorted(data['Debut Month'].dropna().unique())
                    month_options = ["All"] + list(all_months)
                    debut_month = st.multiselect("Select Debut Month", month_options, default=[])
                else:
                    st.warning("No 'Debut Month' column in data.")
                    debut_month = []

            # 3) Debut Year filter
            with col3:
                if 'Debut Year' in data.columns:
                    all_years = sorted(data['Debut Year'].dropna().unique())
                    year_options = ["All"] + [str(yr) for yr in all_years]
                    selected_years = st.multiselect("Select Debut Year", year_options, default=[])
                else:
                    st.warning("No 'Debut Year' column in data.")
                    selected_years = []

            # 4) Age range filter
            with col4:
                if 'Age at Debut' in data.columns:
                    min_age = int(data['Age at Debut'].min())
                    max_age = int(data['Age at Debut'].max())
                    age_range = st.slider("Select Age Range", min_age, max_age, (min_age, max_age))
                else:
                    st.warning("No 'Age at Debut' column in data.")
                    age_range = (0, 100)

            # 5) Minimum minutes played
            with col5:
                if 'Minutes Played' in data.columns:
                    max_minutes = int(data['Minutes Played'].max())
                    min_minutes = st.slider("Minimum Minutes Played", 0, max_minutes, 0)
                else:
                    st.warning("No 'Minutes Played' column in data.")
                    min_minutes = 0

        # ---------------
        # RUN BUTTON
        # ---------------
        st.button("Run", on_click=run_callback)

        if st.session_state['run_clicked']:
            # Make a copy for filtering
            filtered_data = data.copy()

            # 1) Competition + Country
            if selected_comp and "All" not in selected_comp:
                selected_ids = [c.replace(" (", "||").replace(")", "") for c in selected_comp]
                filtered_data = filtered_data[filtered_data['CompCountryID'].isin(selected_ids)]

            # 2) Debut Month
            if debut_month and "All" not in debut_month:
                filtered_data = filtered_data[filtered_data['Debut Month'].isin(debut_month)]

            # 3) Debut Year
            if selected_years and "All" not in selected_years:
                valid_years = [int(y) for y in selected_years if y.isdigit()]
                filtered_data = filtered_data[filtered_data['Debut Year'].isin(valid_years)]

            # 4) Age range
            if 'Age at Debut' in filtered_data.columns:
                filtered_data = filtered_data[
                    (filtered_data['Age at Debut'] >= age_range[0]) &
                    (filtered_data['Age at Debut'] <= age_range[1])
                ]

            # 5) Minimum minutes
            if 'Minutes Played' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Minutes Played'] >= min_minutes]

            # Format Debut Date -> DD.MM.YYYY
            if not filtered_data.empty and 'Debut Date' in filtered_data.columns:
                filtered_data['Debut Date'] = filtered_data['Debut Date'].dt.strftime('%d.%m.%Y')

            # ---------------
            # BUILD final_df
            # ---------------
            all_columns_we_need = [
                "Competition",
                "Player Name",
                "Position",
                "Nationality",
                "Debut Club",
                "Opponent",
                "Debut Date",
                "Age at Debut",
                "Goals For",
                "Goals Against",
                "Appearances",
                "Goals",
                "Minutes Played",
                "Value at Debut",
                "Current Market Value",
                "Value at Debut (Numeric)",
                "Current Market Value (Numeric)",
            ]
            all_columns_we_need = [c for c in all_columns_we_need if c in filtered_data.columns]
            final_df = filtered_data[all_columns_we_need].reset_index(drop=True)

            st.title("Debütanten")
            st.write(f"{len(filtered_data)} Debütanten")

            # ---------------
            # APPLY STYLING
            # ---------------
            styled_table = final_df.style.apply(highlight_mv, axis=None)

            # Format only "Value at Debut"
            def money_format(x):
                if pd.isna(x):
                    return "€0"
                return f"€{x:,.0f}"

            styled_table = styled_table.format(subset=["Value at Debut"], formatter=money_format)

            # -------------------------------------------------------------------------
            # INSTEAD OF .hide_columns(), DROP THE NUMERIC COLUMNS FROM THE STYLER DATA
            # -------------------------------------------------------------------------
            for col_to_drop in ["Value at Debut (Numeric)", "Current Market Value (Numeric)"]:
                if col_to_drop in styled_table.data.columns:
                    styled_table.data.drop(col_to_drop, axis=1, inplace=True)

            # Show the styled DataFrame
            st.dataframe(styled_table, use_container_width=True)

            # ---------------
            # DOWNLOAD BUTTON
            # ---------------
            if not final_df.empty:
                tmp_path = '/tmp/filtered_data.xlsx'
                filtered_data.to_excel(tmp_path, index=False)
                with open(tmp_path, 'rb') as f:
                    st.download_button(
                        label="Download Filtered Data as Excel",
                        data=f,
                        file_name="filtered_debutants.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.write("Please set your filters and click **Run** to see results.")
