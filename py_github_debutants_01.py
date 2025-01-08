import streamlit as st
import pandas as pd
import gdown
from datetime import datetime

# ====================================================================================
# 1) PAGE CONFIG
#    Must be the first Streamlit command (besides imports) to avoid SetPageConfig error
# ====================================================================================
st.set_page_config(layout="wide")

# ====================================================================================
# 2) SESSION STATE INIT
# ====================================================================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'run_clicked' not in st.session_state:
    st.session_state['run_clicked'] = False

# ====================================================================================
# 3) AUTHENTICATION HELPERS
# ====================================================================================
def authenticate(username, password):
    """
    Check if the given username/password match what's in st.secrets.
    If you don't have credentials in secrets, adapt or remove.
    """
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

# ====================================================================================
# 4) DATA DOWNLOAD & LOAD
# ====================================================================================
@st.cache_data
def download_and_load_data(file_url, data_version):
    """
    Download an Excel file from Google Drive via gdown, then read into a DataFrame.
    """
    xlsx_file = f'/tmp/debut02_{data_version}.xlsx'
    try:
        # Download from Google Drive
        gdown.download(url=file_url, output=xlsx_file, quiet=False, fuzzy=True)
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None

    try:
        data = pd.read_excel(xlsx_file, sheet_name='Sheet1')
        # Rename columns to standardized names
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

        # Rename "Bundesliga" -> "1. Bundesliga" if country is Germany
        data.loc[
            (data['Competition'] == 'Bundesliga') & (data['Country'] == 'Germany'),
            'Competition'
        ] = '1. Bundesliga'

        # Create a filter-friendly column (Competition||Country)
        data['CompCountryID'] = data['Competition'] + "||" + data['Country'].fillna('')
        # Also create a display-friendly column (Competition (Country))
        data['Competition (Country)'] = data['Competition'] + " (" + data['Country'].fillna('') + ")"

        return data
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

# ====================================================================================
# 5) CALLBACKS
# ====================================================================================
def run_callback():
    st.session_state['run_clicked'] = True

def clear_callback():
    """
    Clears all session_state items except for authentication-related ones,
    so the dashboard reverts to the 'just logged in' state.
    """
    keys_to_preserve = {'authenticated', 'login_username', 'login_password'}
    for key in list(st.session_state.keys()):
        if key not in keys_to_preserve:
            del st.session_state[key]
    st.experimental_rerun()

# ====================================================================================
# 6) HIGHLIGHT FUNCTION
#    Now with both green and red highlighting logic
# ====================================================================================
def highlight_mv(df):
    """
    If Current Market Value is higher than Value at Debut => green.
    If Current Market Value is lower => red.
    """
    styles = pd.DataFrame('', index=df.index, columns=df.columns)

    if 'Value at Debut' in df.columns and 'Current Market Value' in df.columns:
        mask_up = df['Current Market Value'] > df['Value at Debut']
        mask_down = df['Current Market Value'] < df['Value at Debut']

        styles.loc[mask_up, 'Current Market Value'] = 'background-color: #c6f6d5'   # light green
        styles.loc[mask_down, 'Current Market Value'] = 'background-color: #feb2b2' # light red
    return styles

# ====================================================================================
# 7) PERCENT CHANGE FUNCTION
# ====================================================================================
def calc_percent_change(row):
    """
    Calculate percentage = ((Current - Debut) / Debut) * 100
    If Debut is zero or NaN, return None.
    """
    debut_val = row.get('Value at Debut')
    curr_val = row.get('Current Market Value')
    if pd.isna(debut_val) or pd.isna(curr_val) or debut_val == 0:
        return None  # can't calculate
    return (curr_val - debut_val) / debut_val * 100

# ====================================================================================
# 8) MAIN LOGIC
# ====================================================================================
if not st.session_state['authenticated']:
    # Show login form until user is authenticated
    login()
else:
    # Once authenticated, show main content
    st.image('logo.png', use_container_width=True, width=800)
    st.write("Welcome! You are logged in.")

    # Download & load data
    file_url = 'https://drive.google.com/uc?id=1aeSuhDoWEiyD34PjnDIqIVtbbmL_aTRI'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    if data is None:
        st.error("Failed to load data.")
        st.stop()

    st.write("Data successfully loaded!")

    # Create our new column for % Change
    data['% Change'] = data.apply(calc_percent_change, axis=1)

    # Remove invalid negative ages
    if 'Age at Debut' in data.columns:
        data = data[data['Age at Debut'] >= 0]

    # ==================================================================================
    # 8A) FILTERS
    # ==================================================================================
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

        # 1) Competition (Country)
        with col1:
            if 'Competition (Country)' in data.columns and 'CompCountryID' in data.columns:
                all_comps = sorted(data['Competition (Country)'].dropna().unique())
                comp_options = ["All"] + all_comps
                selected_comp = st.multiselect("Select Competition", comp_options, default=[])
            else:
                st.warning("No Competition/Country columns in data.")
                selected_comp = []

        # 2) Debut Month
        with col2:
            if 'Debut Month' in data.columns:
                all_months = sorted(data['Debut Month'].dropna().unique())
                month_options = ["All"] + list(all_months)
                selected_months = st.multiselect("Select Debut Month", month_options, default=[])
            else:
                st.warning("No 'Debut Month' column in data.")
                selected_months = []

        # 3) Debut Year
        with col3:
            if 'Debut Year' in data.columns:
                all_years = sorted(data['Debut Year'].dropna().unique())
                year_options = ["All"] + [str(yr) for yr in all_years]
                selected_years = st.multiselect("Select Debut Year", year_options, default=[])
            else:
                st.warning("No 'Debut Year' column in data.")
                selected_years = []

        # 4) SINGLE SLIDER for MAX AGE
        with col4:
            if 'Age at Debut' in data.columns and not data.empty:
                min_age_actual = int(data['Age at Debut'].min())
                max_age_actual = int(data['Age at Debut'].max())

                max_age_filter = st.slider("Maximum Age at Debut",
                                           min_value=min_age_actual,
                                           max_value=max_age_actual,
                                           value=max_age_actual)
            else:
                st.warning("No 'Age at Debut' column in data or no valid ages.")
                max_age_filter = 100

        # 5) Minimum minutes played
        with col5:
            if 'Minutes Played' in data.columns and not data.empty:
                max_minutes = int(data['Minutes Played'].max())
                min_minutes = st.slider("Minimum Minutes Played", 0, max_minutes, 0)
            else:
                st.warning("No 'Minutes Played' column in data.")
                min_minutes = 0

    # RUN & CLEAR buttons side by side
    with st.container():
        run_col, clear_col = st.columns([0.2, 0.2])  # adjust widths as needed
        with run_col:
            st.button("Run", on_click=run_callback)
        with clear_col:
            st.button("Clear", on_click=clear_callback)

    # ==================================================================================
    # 8B) APPLY FILTERS
    # ==================================================================================
    if st.session_state['run_clicked']:
        filtered_data = data.copy()

        # Filter: Competition + Country
        if selected_comp and "All" not in selected_comp:
            selected_ids = [
                c.replace(" (", "||").replace(")", "")
                for c in selected_comp
            ]
            filtered_data = filtered_data[filtered_data['CompCountryID'].isin(selected_ids)]

        # Filter: Debut Month
        if selected_months and "All" not in selected_months:
            filtered_data = filtered_data[filtered_data['Debut Month'].isin(selected_months)]

        # Filter: Debut Year
        if selected_years and "All" not in selected_years:
            valid_years = [int(y) for y in selected_years if y.isdigit()]
            filtered_data = filtered_data[filtered_data['Debut Year'].isin(valid_years)]

        # Filter: Maximum Age at Debut
        if 'Age at Debut' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Age at Debut'] <= max_age_filter]

        # Filter: Minimum minutes played
        if 'Minutes Played' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Minutes Played'] >= min_minutes]

        # -----------
        # SORT BY DEBUT DATE (DESC), THEN FORMAT
        # -----------
        if not filtered_data.empty and 'Debut Date' in filtered_data.columns:
            filtered_data.sort_values('Debut Date', ascending=False, inplace=True)
            filtered_data['Debut Date'] = filtered_data['Debut Date'].dt.strftime('%d.%m.%Y')

        # ==================================================================================
        # 8C) BUILD FINAL DATAFRAME
        # ==================================================================================
        # Columns to show in final table
        display_columns = [
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
            "% Change",  # Our newly created column
        ]

        display_columns = [c for c in display_columns if c in filtered_data.columns]
        final_df = filtered_data[display_columns].reset_index(drop=True)

        st.title("Debütanten")
        st.write(f"{len(final_df)} Debütanten")

        # ==================================================================================
        # 8D) STYLING
        # ==================================================================================
        styled_table = final_df.style.apply(highlight_mv, axis=None)

        # Format money columns
        money_cols = []
        if "Value at Debut" in final_df.columns:
            money_cols.append("Value at Debut")
        if "Current Market Value" in final_df.columns:
            money_cols.append("Current Market Value")

        def money_format(x):
            if pd.isna(x):
                return "€0"
            return f"€{x:,.0f}"

        styled_table = styled_table.format(subset=money_cols, formatter=money_format)

        # Format % Change
        if "% Change" in final_df.columns:
            def pct_format(x):
                if pd.isna(x):
                    return ""
                return f"{x:+.1f}%"
            styled_table = styled_table.format(subset=["% Change"], formatter=pct_format)

        st.dataframe(styled_table, use_container_width=True)

        # ==================================================================================
        # 8E) DOWNLOAD BUTTON
        # ==================================================================================
        if not final_df.empty:
            tmp_path = '/tmp/filtered_data.xlsx'
            final_df.to_excel(tmp_path, index=False)

            with open(tmp_path, 'rb') as f:
                st.download_button(
                    label="Download Filtered Data as Excel",
                    data=f,
                    file_name="filtered_debutants.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    else:
        st.write("Please set your filters and click **Run** to see results.")
