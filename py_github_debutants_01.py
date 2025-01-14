import streamlit as st
import pandas as pd
import gdown
from datetime import datetime

# ====================================================================================
# 1) PAGE CONFIG
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
            st.session_state['authenticated'] = True
            st.success("Login successful!")
        else:
            st.error("Invalid username or password")

    st.button("Login", on_click=authenticate_and_login)

# ====================================================================================
# 4) DATA DOWNLOAD & LOAD
# ====================================================================================
@st.cache_data
def download_and_load_data(file_url, data_version):
    xlsx_file = f'/tmp/debut02_{data_version}.xlsx'
    try:
        gdown.download(url=file_url, output=xlsx_file, quiet=False, fuzzy=True)
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None

    try:
        data = pd.read_excel(xlsx_file, sheet_name='Sheet1')
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
                'player_url': 'player_url'  # Ensure 'player_url' is included
            },
            inplace=True
        )

        # Standardize 'Debut Month' format to three-letter abbreviations
        if 'Debut Month' in data.columns:
            data['Debut Month'] = data['Debut Month'].str.strip().str.title()

        data['Debut Date'] = pd.to_datetime(data['Debut Date'], errors='coerce')
        if 'Debut Date' in data.columns:
            data['Debut Year'] = data['Debut Date'].dt.year

        data.loc[
            (data['Competition'] == 'Bundesliga') & (data['Country'] == 'Germany'),
            'Competition'
        ] = '1. Bundesliga'

        data['CompCountryID'] = data['Competition'] + "||" + data['Country'].fillna('')
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
    Clears session state except for authentication keys.
    Does NOT force rerun (since rerun is unavailable).
    User can refresh the page or just see fresh filters when they next click 'Run'.
    """
    keys_to_preserve = {'authenticated', 'login_username', 'login_password'}
    for key in list(st.session_state.keys()):
        if key not in keys_to_preserve:
            del st.session_state[key]

    st.info("All filters cleared! Please refresh your page or click 'Run' again.")

# ====================================================================================
# 6) HIGHLIGHT FUNCTION
# ====================================================================================
def highlight_mv(df):
    """
    Applies conditional styling:
    - Green background for 'Current Market Value' > 'Value at Debut'
    - Red background for 'Current Market Value' < 'Value at Debut'
    - Green background for '% Change' > 0
    - Red background for '% Change' < 0
    - No background for '% Change' = 0 or NaN
    """
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    
    # Style 'Current Market Value'
    if 'Value at Debut' in df.columns and 'Current Market Value' in df.columns:
        mask_up = df['Current Market Value'] > df['Value at Debut']
        mask_down = df['Current Market Value'] < df['Value at Debut']
        styles.loc[mask_up, 'Current Market Value'] = 'background-color: #c6f6d5'   # light green
        styles.loc[mask_down, 'Current Market Value'] = 'background-color: #feb2b2' # light red
    
    # Style '% Change'
    if '% Change' in df.columns:
        mask_change_up = df['% Change'] > 0
        mask_change_down = df['% Change'] < 0
        styles.loc[mask_change_up, '% Change'] = 'background-color: #c6f6d5'        # light green
        styles.loc[mask_change_down, '% Change'] = 'background-color: #feb2b2'      # light red
    
    return styles

# ====================================================================================
# 7) PERCENT CHANGE FUNCTION
# ====================================================================================
def calc_percent_change(row):
    debut_val = row.get('Value at Debut')
    curr_val = row.get('Current Market Value')
    if pd.isna(debut_val) or pd.isna(curr_val) or debut_val == 0:
        return None
    return (curr_val - debut_val) / debut_val * 100

# ====================================================================================
# 8) MAIN LOGIC
# ====================================================================================
if not st.session_state['authenticated']:
    login()
else:
    st.image('logo.png', use_container_width=True, width=800)
    st.write("Welcome! You are logged in.")

    file_url = 'https://drive.google.com/uc?id=1vYmV_BcpYhudGJ4Ogboi_ENCHPbmaW6a'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    if data is None:
        st.error("Failed to load data.")
        st.stop()

    st.write("Data successfully loaded!")
    data['% Change'] = data.apply(calc_percent_change, axis=1)

    if 'Age at Debut' in data.columns:
        data = data[data['Age at Debut'] >= 0]

    # ----------------------------------------------------------------------------------
    # FILTER UI
    # ----------------------------------------------------------------------------------
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

        # 1) Competition
        with col1:
            if 'Competition (Country)' in data.columns and 'CompCountryID' in data.columns:
                all_comps = sorted(data['Competition (Country)'].dropna().unique())
                comp_options = ["All"] + all_comps
                selected_comp = st.multiselect("Select Competition", comp_options, default=["All"])
            else:
                st.warning("No Competition/Country columns in data.")
                selected_comp = []

        # 2) Debut Month
        with col2:
            if 'Debut Month' in data.columns:
                # Define the chronological order of months using abbreviations
                months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                # Extract unique months from the data and sort them chronologically
                available_months = data['Debut Month'].dropna().unique()
                sorted_months = [month for month in months_order if month in available_months]
                
                # Create the filter options with "All" as the first option
                month_options = ["All"] + sorted_months
                
                # Multiselect widget for selecting debut months
                selected_months = st.multiselect("Select Debut Month", month_options, default=["All"])
            else:
                st.warning("No 'Debut Month' column in data.")
                selected_months = []

        # 3) Debut Year
        with col3:
            if 'Debut Year' in data.columns:
                all_years = sorted(data['Debut Year'].dropna().unique())
                year_options = ["All"] + [str(yr) for yr in all_years]
                selected_years = st.multiselect("Select Debut Year", year_options, default=["All"])
            else:
                st.warning("No 'Debut Year' column in data.")
                selected_years = []

        # 4) Single slider for max age
        with col4:
            if 'Age at Debut' in data.columns and not data.empty:
                min_age_actual = int(data['Age at Debut'].min())
                max_age_actual = int(data['Age at Debut'].max())
                max_age_filter = st.slider("Maximum Age at Debut",
                                           min_value=min_age_actual,
                                           max_value=max_age_actual,
                                           value=max_age_actual)
            else:
                st.warning("No 'Age at Debut' column or no valid ages.")
                max_age_filter = 100

        # 5) Minimum minutes played
        with col5:
            if 'Minutes Played' in data.columns and not data.empty:
                max_minutes = int(data['Minutes Played'].max())
                min_minutes = st.slider("Minimum Minutes Played", 0, max_minutes, 0)
            else:
                st.warning("No 'Minutes Played' column in data.")
                min_minutes = 0

    # ----------------------------------------------------------------------------------
    # RUN & CLEAR
    # ----------------------------------------------------------------------------------
    with st.container():
        run_col, clear_col = st.columns([0.2, 0.2])
        with run_col:
            st.button("Run", on_click=run_callback)
        with clear_col:
            st.button("Clear", on_click=clear_callback)

    # ----------------------------------------------------------------------------------
    # APPLY FILTERS & DISPLAY
    # ----------------------------------------------------------------------------------
    if st.session_state['run_clicked']:
        filtered_data = data.copy()

        # 1) Competition
        if selected_comp and "All" not in selected_comp:
            selected_ids = [c.replace(" (", "||").replace(")", "") for c in selected_comp]
            filtered_data = filtered_data[filtered_data['CompCountryID'].isin(selected_ids)]

        # 2) Debut Month
        if selected_months and "All" not in selected_months:
            filtered_data = filtered_data[filtered_data['Debut Month'].isin(selected_months)]

        # 3) Debut Year
        if selected_years and "All" not in selected_years:
            valid_years = [int(y) for y in selected_years if y.isdigit()]
            filtered_data = filtered_data[filtered_data['Debut Year'].isin(valid_years)]

        # 4) Max Age
        if 'Age at Debut' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Age at Debut'] <= max_age_filter]

        # 5) Min minutes
        if 'Minutes Played' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Minutes Played'] >= min_minutes]

        # Sort by Debut Date desc, then format
        if not filtered_data.empty and 'Debut Date' in filtered_data.columns:
            filtered_data.sort_values('Debut Date', ascending=False, inplace=True)
            filtered_data['Debut Date'] = filtered_data['Debut Date'].dt.strftime('%d.%m.%Y')

        # Create 'Player Link' column with clickable links
        def sanitize_url(url):
            import re
            # Simple URL validation
            regex = re.compile(
                r'^(?:http|ftp)s?://'  # http:// or https://
                r'(?:\S+(?::\S*)?@)?'  # user:pass@
                r'(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])'  # IP
                r'(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}'
                r'(?:\.(?:[0-9]{1,3}))|'
                r'(?:(?:[a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))'  # Domain
                r'(?::\d{2,5})?'  # Port
                r'(?:/\S*)?$',
                re.IGNORECASE
            )
            return re.match(regex, url) is not None

        filtered_data['Player'] = filtered_data.apply(
            lambda row: f'<a href="{row["player_url"]}" target="_blank">{row["Player Name"]}</a>' 
                        if pd.notna(row['player_url']) and isinstance(row['player_url'], str) and sanitize_url(row['player_url']) 
                        else row['Player Name'],
            axis=1
        )

        # Define the columns to display, replacing 'Player Name' with 'Player Link'
        display_columns = [
            "Competition",
            "Player",  # Use the new link column
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
            "% Change"
        ]
        # Ensure that all display columns exist in the filtered data
        display_columns = [c for c in display_columns if c in filtered_data.columns]
        final_df = filtered_data[display_columns].reset_index(drop=True)

        st.title("Debütanten")
        st.write(f"{len(final_df)} Debütanten")

        # Apply conditional styling
        styled_table = final_df.style.apply(highlight_mv, axis=None)

        # Set font size to 12px and define table layout for even column distribution
        styled_table = styled_table.set_table_styles(
            [
                # Set table width to 100% and layout to fixed for even column distribution
                {'selector': 'table',
                 'props': [('width', '100%'), ('table-layout', 'fixed')]},
                
                # Set font size and padding for headers and cells
                {'selector': 'th, td',
                 'props': [('font-size', '14px'), ('padding', '5px')]}
            ]
        )

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

        # Format integer columns
        integer_cols = ["Goals For", "Goals Against"]

        def integer_format(x):
            if pd.isna(x):
                return "0"
            return f"{int(x)}"

        styled_table = styled_table.format(subset=integer_cols, formatter=integer_format)

        # Format % Change
        if "% Change" in final_df.columns:
            def pct_format(x):
                if pd.isna(x):
                    return ""
                return f"{x:+.1f}%"
            styled_table = styled_table.format(subset=["% Change"], formatter=pct_format)

        # Additional table styling for responsiveness and horizontal scrolling (optional)
        styled_table = styled_table.set_table_styles(
            [
                {'selector': 'table',
                 'props': [('width', '100%'), ('table-layout', 'fixed'), ('overflow-x', 'auto')]}
            ],
            overwrite=False  # Prevent overwriting previous styles
        )

        # Render the styled table as HTML
        try:
            html_table = styled_table.to_html(escape=False)
        except AttributeError:
            st.error("The 'to_html()' method is not available in your Pandas version. Please update Pandas to use this feature.")
            st.stop()

        st.markdown(html_table, unsafe_allow_html=True)

        # Download
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
