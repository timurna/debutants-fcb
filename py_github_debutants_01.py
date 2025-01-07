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

        # Create a column for filter display: e.g. "1. Bundesliga (Germany)"
        data['CompCountryID'] = data['Competition'] + "||" + data['Country'].fillna('')
        data['Competition (Country)'] = data['Competition'] + " (" + data['Country'].fillna('') + ")"

        return data
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

def reset_run():
    st.session_state['run_clicked'] = False

def run_callback():
    st.session_state['run_clicked'] = True

# Highlight Current Market Value if it's higher than Value at Debut
def highlight_mv(df):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    if 'Value at Debut' in df.columns and 'Current Market Value' in df.columns:
        mask = df['Current Market Value'] > df['Value at Debut']
        styles.loc[mask, 'Current Market Value'] = 'background-color: #c6f6d5'  # light green
    return styles

if not st.session_state['authenticated']:
    # Prompt for login
    login()
else:
    # Once authenticated, show the main content
    st.image('logo.png', use_container_width=True, width=800)
    st.write("Welcome! You are logged in.")

    # Download/Load Data
    file_url = 'https://drive.google.com/uc?id=15BbDQuW_ZJbIUIV_g7YOjoqrr8k4ZPF_'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    if data is None:
        st.error("Failed to load data.")
        st.stop()
    else:
        st.write("Data successfully loaded!")

        # Prepare filter columns
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

            # 1) Competition (Country) filter with "All"
            with col1:
                if 'Competition (Country)' in data.columns and 'CompCountryID' in data.columns:
                    all_comps = sorted(data['Competition (Country)'].dropna().unique())
                    comp_options = ["All"] + all_comps
                    selected_comp = st.multiselect("Select Competition",
                                                   comp_options,
                                                   default=[])  # no preselection
                else:
                    st.warning("No Competition/Country columns in data.")
                    selected_comp = []

            # 2) Debut Month filter with "All"
            with col2:
                if 'Debut Month' in data.columns:
                    all_months = sorted(data['Debut Month'].dropna().unique())
                    month_options = ["All"] + all_months
                    debut_month = st.multiselect("Select Debut Month",
                                                 month_options,
                                                 default=[])  # no preselection
                else:
                    st.warning("No 'Debut Month' column in data.")
                    debut_month = []

            # 3) Debut Year filter with "All"
            with col3:
                if 'Debut Year' in data.columns:
                    all_years = sorted(data['Debut Year'].dropna().unique())
                    year_options = ["All"] + [str(yr) for yr in all_years]  # convert to string for consistency
                    selected_years = st.multiselect("Select Debut Year",
                                                    year_options,
                                                    default=[])  # no preselection
                else:
                    st.warning("No 'Debut Year' column in data.")
                    selected_years = []

            # 4) Age range filter
            with col4:
                if 'Age at Debut' in data.columns:
                    min_age = int(data['Age at Debut'].min())
                    max_age = int(data['Age at Debut'].max())
                    age_range = st.slider("Select Age Range",
                                          min_age, max_age,
                                          (min_age, max_age))
                else:
                    st.warning("No 'Age at Debut' column in data.")
                    age_range = (0, 100)

            # 5) Minimum minutes played filter
            with col5:
                if 'Minutes Played' in data.columns:
                    max_minutes = int(data['Minutes Played'].max())
                    min_minutes = st.slider("Minimum Minutes Played",
                                            0, max_minutes, 0)
                else:
                    st.warning("No 'Minutes Played' column in data.")
                    min_minutes = 0

        # Run Button
        st.button("Run", on_click=run_callback)

        if st.session_state['run_clicked']:
            filtered_data = data.copy()

            # 1) Competition + Country filter
            if selected_comp and "All" not in selected_comp:
                # Convert user selection: e.g. "1. Bundesliga (Germany)" -> "1. Bundesliga||Germany"
                selected_ids = [
                    item.replace(" (", "||").replace(")", "")
                    for item in selected_comp
                ]
                filtered_data = filtered_data[filtered_data['CompCountryID'].isin(selected_ids)]

            # 2) Debut Month filter
            if debut_month and "All" not in debut_month:
                filtered_data = filtered_data[filtered_data['Debut Month'].isin(debut_month)]

            # 3) Debut Year filter
            if selected_years and "All" not in selected_years:
                # Convert strings back to int
                valid_years = [int(y) for y in selected_years if y.isdigit()]
                filtered_data = filtered_data[filtered_data['Debut Year'].isin(valid_years)]

            # 4) Age range filter
            if 'Age at Debut' in filtered_data.columns:
                filtered_data = filtered_data[
                    (filtered_data['Age at Debut'] >= age_range[0]) &
                    (filtered_data['Age at Debut'] <= age_range[1])
                ]

            # 5) Minimum minutes filter
            if 'Minutes Played' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Minutes Played'] >= min_minutes]

            # Format Debut Date -> DD.MM.YYYY
            if not filtered_data.empty and 'Debut Date' in filtered_data.columns:
                filtered_data['Debut Date'] = filtered_data['Debut Date'].dt.strftime('%d.%m.%Y')

            # Display columns
            display_columns = [
                'Competition',
                'Player Name',
                'Position',
                'Nationality',
                'Debut Club',
                'Opponent',
                'Debut Date',
                'Age at Debut',
                'Goals For',
                'Goals Against',
                'Appearances',
                'Goals',
                'Minutes Played',
                'Value at Debut',
                'Current Market Value',
            ]
            display_columns = [c for c in display_columns if c in filtered_data.columns]

            # Headline
            st.title("Debütanten")
            st.write(f"{len(filtered_data)} Debütanten")

            final_df = filtered_data[display_columns].reset_index(drop=True)

            # 1) We apply the highlight function
            styled_table = final_df.style.apply(highlight_mv, axis=None)

            # 2) Then format the numeric columns for money
            #    We'll do comma-separated, no decimals, and a leading "€"
            def money_format(x):
                if pd.isna(x):
                    return "€0"
                return f"€{x:,.0f}"

            styled_table = styled_table.format(
                subset=["Value at Debut", "Current Market Value"],
                formatter=money_format
            )

            # Show the styled DataFrame
            st.dataframe(styled_table, use_container_width=True)

            # Download button
            if not final_df.empty:
                # For the Excel file, let's keep numeric columns numeric:
                # We'll do a copy that doesn't have the styling for the file
                download_df = final_df.copy()
                
                # If you want to keep them numeric, do nothing.
                # If you want to keep them as text with "€", then convert them:
                # But typically you'd keep them numeric so they can be manipulated.
                
                tmp_path = '/tmp/filtered_data.xlsx'
                download_df.to_excel(tmp_path, index=False)

                with open(tmp_path, 'rb') as f:
                    st.download_button(
                        label="Download Filtered Data as Excel",
                        data=f,
                        file_name="filtered_debutants.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.write("Please set your filters and click **Run** to see results.")
