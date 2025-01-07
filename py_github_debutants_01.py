import streamlit as st
import pandas as pd
from datetime import datetime
import gdown

st.set_page_config(layout="wide")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_clicked' not in st.session_state:
    st.session_state['run_clicked'] = False

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
    xlsx_file = f'/tmp/debut01_{data_version}.xlsx'
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
            },
            inplace=True
        )

        # Date conversion
        data['Debut Date'] = pd.to_datetime(data['Debut Date'], errors='coerce')
        if 'Debut Date' in data.columns:
            data['Debut Year'] = data['Debut Date'].dt.year

        # Rename "Bundesliga" to "1. Bundesliga" if country is Germany
        data.loc[
            (data['Competition'] == 'Bundesliga') & (data['Country'] == 'Germany'),
            'Competition'
        ] = '1. Bundesliga'

        # For filter display
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

def highlight_cmv(row, vad_col, cmv_col):
    """Row-based highlight function.
    If CMV > VAD, we color the 'Current Market Value' cell."""
    styles = [''] * len(row)
    if row[cmv_col] > row[vad_col]:
        idx = row.index.get_loc(cmv_col)
        styles[idx] = 'background-color: #c6f6d5'  # Light green
    return styles

if not st.session_state['authenticated']:
    login()
else:
    st.image('logo.png', use_container_width=True, width=800)
    st.write("Welcome! You are logged in.")

    file_url = 'https://drive.google.com/uc?id=15BbDQuW_ZJbIUIV_g7YOjoqrr8k4ZPF_'
    data_version = 'v1'
    data = download_and_load_data(file_url, data_version)

    if data is None:
        st.error("Failed to load data.")
        st.stop()
    else:
        st.write("Data successfully loaded!")

        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

            # Competition
            if 'Competition (Country)' in data.columns and 'CompCountryID' in data.columns:
                all_comps = sorted(data['Competition (Country)'].dropna().unique())
                comp_options = ["All"] + all_comps
                selected_comp = col1.multiselect("Select Competition", comp_options, default=[])
            else:
                col1.warning("No Competition/Country columns in data.")
                selected_comp = []

            # Debut Month
            if 'Debut Month' in data.columns:
                all_months = sorted(data['Debut Month'].dropna().unique())
                month_options = ["All"] + all_months
                debut_month = col2.multiselect("Select Debut Month", month_options, default=[])
            else:
                col2.warning("No 'Debut Month' column in data.")
                debut_month = []

            # Debut Year
            if 'Debut Year' in data.columns:
                all_years = sorted(data['Debut Year'].dropna().unique())
                year_options = ["All"] + [str(yr) for yr in all_years]
                selected_years = col3.multiselect("Select Debut Year", year_options, default=[])
            else:
                col3.warning("No 'Debut Year' column in data.")
                selected_years = []

            # Age range
            if 'Age at Debut' in data.columns:
                min_age = int(data['Age at Debut'].min())
                max_age = int(data['Age at Debut'].max())
                age_range = col4.slider("Select Age Range", min_age, max_age, (min_age, max_age))
            else:
                col4.warning("No 'Age at Debut' column in data.")
                age_range = (0, 100)

            # Minutes
            if 'Minutes Played' in data.columns:
                max_minutes = int(data['Minutes Played'].max())
                min_minutes = col5.slider("Minimum Minutes Played", 0, max_minutes, 0)
            else:
                col5.warning("No 'Minutes Played' column in data.")
                min_minutes = 0

        st.button("Run", on_click=run_callback)

        if st.session_state['run_clicked']:
            filtered_data = data.copy()

            # Competition
            if selected_comp and "All" not in selected_comp:
                selected_ids = [item.replace(" (", "||").replace(")", "") for item in selected_comp]
                filtered_data = filtered_data[filtered_data['CompCountryID'].isin(selected_ids)]

            # Debut Month
            if debut_month and "All" not in debut_month:
                filtered_data = filtered_data[filtered_data['Debut Month'].isin(debut_month)]

            # Debut Year
            if selected_years and "All" not in selected_years:
                valid_years = [int(y) for y in selected_years if y.isdigit()]
                filtered_data = filtered_data[filtered_data['Debut Year'].isin(valid_years)]

            # Age range
            if 'Age at Debut' in filtered_data.columns:
                filtered_data = filtered_data[
                    (filtered_data['Age at Debut'] >= age_range[0]) &
                    (filtered_data['Age at Debut'] <= age_range[1])
                ]

            # Minutes
            if 'Minutes Played' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Minutes Played'] >= min_minutes]

            # Format Debut Date
            if not filtered_data.empty and 'Debut Date' in filtered_data.columns:
                filtered_data['Debut Date'] = filtered_data['Debut Date'].dt.strftime('%d.%m.%Y')

            # Columns to display
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

            st.title("Debütanten")
            st.write(f"{len(filtered_data)} Debütanten")

            final_df = filtered_data[display_columns].reset_index(drop=True)

            # Calculate percentage changes in a separate column
            # (CMV - VAD)/VAD * 100
            final_df["% Change"] = None
            mask_vad_nonzero = (final_df["Value at Debut"] != 0) & (~final_df["Value at Debut"].isna())
            final_df.loc[mask_vad_nonzero, "% Change"] = (
                (final_df.loc[mask_vad_nonzero, "Current Market Value"]
                 - final_df.loc[mask_vad_nonzero, "Value at Debut"])
                / final_df.loc[mask_vad_nonzero, "Value at Debut"]
                * 100
            )

            # Place "% Change" column right after "Current Market Value"
            if "% Change" in final_df.columns:
                cols_order = []
                for col in final_df.columns:
                    cols_order.append(col)
                    if col == "Current Market Value":
                        cols_order.append("% Change")
                final_df = final_df[cols_order]

            # Create a row-based Styler
            def row_styler(row):
                return highlight_cmv(row, "Value at Debut", "Current Market Value")

            styler = final_df.style.apply(row_styler, axis=1)

            # Format money
            def money_format(val):
                if pd.isna(val) or val <= 0:
                    return "€0"
                return f"€{val:,.0f}"

            # Format all money columns
            styler = styler.format(
                subset=["Value at Debut", "Current Market Value"],
                formatter=money_format
            )

            # Format the % Change column
            if "% Change" in final_df.columns:
                styler = styler.format(
                    subset=["% Change"],
                    formatter=lambda x: f"{x:+.1f}%"
                )

            st.dataframe(styler, use_container_width=True)

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
