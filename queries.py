import pandas as pd
import altair as alt
import streamlit as st
import os
import numpy as np
import re
import time


folder_path = 'exports'

# FILE UPLOAD
@st.cache_data(show_spinner='Loading...')
def load_excel_files():
    excel_files = [file for file in os.listdir(folder_path) if file.endswith('.xlsx')]
    excel_files.sort(reverse=True)
    return pd.DataFrame(excel_files, columns=['Excel Files In Use'])

def validate_file(uploaded_file):
    try:
        xlsx = pd.ExcelFile(uploaded_file)

        required_sheets = ['Film', 'TV']
        missing_sheets = [sheet for sheet in required_sheets if sheet not in xlsx.sheet_names]

        if missing_sheets:
            return False, f'Missing sheets: {', '.join(missing_sheets)}'

        df = pd.read_excel(uploaded_file, sheet_name=required_sheets[0], skiprows=5)

        required_columns = ['Title', 'Release Date', 'Runtime', 'Hours Viewed', 'Views', 'Available Globally?']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return False, f'Missing columns: {', '.join(missing_columns)}'

        return True, 'File is valid.'

    except Exception as e:
        return False, f'Error validating file: {e}'

def is_file_name_valid(file_name):
    """Check if the file name contains '_YYYYJan-Jun' or '_YYYYJul-Dec' anywhere in the name."""
    pattern = r'_\d{4}(Jan-Jun|Jul-Dec)'
    return bool(re.search(pattern, file_name))


def has_required_columns(file):
    """Check if the uploaded file has the required columns."""
    columns = ['Title', 'Release Date', 'Runtime', 'Hours Viewed', 'Views', 'Available Globally?']
    try:
        df = pd.read_excel(file, skiprows=5)
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            return False, f'Missing columns: {', '.join(missing_columns)}'
        return True, ""
    except Exception as e:
        return False, f'Error reading file: {e}'

def process_uploaded_file(uploaded_file, folder_path):
    """Handle the file upload, validation, and saving process."""
    is_valid_file, message = validate_file(uploaded_file)
    file_name = uploaded_file.name

    if not is_file_name_valid(file_name):
        st.error('Invalid file name format. The file name must end with "_YYYYJan-Jun" or "_YYYYJul-Dec".')
        return

    if not is_valid_file:
        st.error(message)
        return

    has_columns, column_message = has_required_columns(uploaded_file)
    if not has_columns:
        st.error(f'File {file_name} is missing required columns. {column_message}')
        return

    file_path = os.path.join(folder_path, file_name)
    if os.path.exists(file_path):
        st.warning(f'The file {file_name} is already included in the dashboard.')
    else:
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        st.success(f'File {file_name} has been uploaded successfully!')
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()


# VISUALIZATION #1
def combine_windows(df):
    """Aggregate data for films or TV shows."""
    aggregated = df.groupby(
        ['Group Title', 'Title', 'Release Date', 'Runtime in Minutes'],
        as_index=False).agg({'Hours Viewed': 'sum', 'Start Date': 'min', 'End Date': 'max'})

    aggregated['Views'] = (aggregated['Hours Viewed'] / (aggregated['Runtime in Minutes'] / 60)).round()
    return aggregated

def group_and_aggregate(df):
    """Group by 'Group Title' and aggregate values."""
    return df.groupby(['Group Title'], as_index=False).agg(
        {
            'Views': 'sum',
            'Hours Viewed': 'sum',
            'Title': 'nunique',
            'Runtime in Minutes': 'mean'
        }
    )

def rename_columns(df, media_type):
    """Rename columns based on media type ('Film' or 'TV')."""
    if media_type == 'Film':
        return df.rename(columns={
            'Group Title': 'Title',
            'Runtime in Minutes': 'Avg Runtime (min)',
            'Title': '# of Films'
        })
    elif media_type == 'TV':
        return df.rename(columns={
            'Group Title': 'Series Title',
            'Runtime in Minutes': 'Avg Runtime (min)',
            'Title': '# of Seasons'
        })


@st.cache_data()
def prepare_top_n_data(film_df, tv_df):
    """Prepare aggregated and grouped data for both films and TV shows."""
    combined_window_films = combine_windows(film_df)
    combined_window_tv = combine_windows(tv_df)

    film_data_grouped = group_and_aggregate(combined_window_films)
    film_data_grouped = rename_columns(film_data_grouped, 'Film')

    tv_data_grouped = group_and_aggregate(combined_window_tv)
    tv_data_grouped = rename_columns(tv_data_grouped, 'TV')

    return film_data_grouped, tv_data_grouped


@st.cache_data()
def get_top_n_titles(df, n, metric='Views', filter_by_count=None):
    """Get and format the top N titles based on the chosen filters."""
    if filter_by_count is not None:
        column_name = '# of Films' if 'Films' in df.columns else '# of Seasons'
        df = df[df[column_name] <= filter_by_count]

    top_titles = df.nlargest(n, metric)
    top_titles[metric] = top_titles[metric].round(-5)
    top_titles['Avg Runtime (min)'] = top_titles['Avg Runtime (min)'].round(0)
    top_titles.reset_index(drop=True, inplace=True)
    top_titles.index += 1
    return top_titles


# VISUALIZATION #2
def get_fiscal_half(start_date, end_date):
    """Create a Fiscal Half column in the format H1 YYYY or H2 YYYY."""
    start_year = start_date.year
    if 1 <= start_date.month <= 6:
        return f'H1 {start_year}'
    else:
        return f'H2 {start_year}'


def add_new_columns(df, media_type):
    """Add Media, Fiscal Half columns and calculate Views based on Hours Viewed and Runtime."""
    df['Media'] = media_type
    df['Fiscal Half'] = df.apply(
        lambda row: get_fiscal_half(pd.to_datetime(row['Start Date']), pd.to_datetime(row['End Date'])),
        axis=1
    )
    df['Views'] = (df['Hours Viewed'] / (df['Runtime in Minutes'] / 60)).round()
    df['Availability'] = np.where(df['Available Globally?'] == 'Yes', 'Global', 'Domestic')
    return df


@st.cache_data(show_spinner='Loading...')
def create_fiscal_half_df(film_df, tv_df, column_choice):
    """Create and return the fiscal half summary DataFrame."""
    film_data_with_fiscal_half = add_new_columns(film_df, 'Film')
    tv_data_with_fiscal_half = add_new_columns(tv_df, 'TV')

    combined_data = pd.concat([film_data_with_fiscal_half, tv_data_with_fiscal_half])

    fiscal_half_summary = combined_data.groupby([column_choice, 'Fiscal Half', 'Start Date'], as_index=False)[
        'Views'].sum()

    fiscal_half_summary = fiscal_half_summary.sort_values(by='Start Date').reset_index()
    fiscal_half_summary['Views in Billions'] = fiscal_half_summary['Views'] / 1_000_000_000
    fiscal_half_summary['Text Label'] = (fiscal_half_summary['Views in Billions'].round(2).astype(str) + 'B')

    return fiscal_half_summary


def create_fiscal_half_chart(df, column_choice):
    """Generate and return the fiscal half chart from the summary DataFrame."""
    # Chart settings
    sort_order = df[['Fiscal Half', 'Start Date']].drop_duplicates().sort_values('Start Date').drop(
        columns='Start Date').values.flatten().tolist()

    if column_choice == 'Media':
        domain = ['Film', 'TV']
        range_ = ['#db0000', '#000000']
    elif column_choice == 'Availability':
        domain = ['Domestic', 'Global']
        range_ = ['#ba0c0c', '#6D6D6D']
    elif column_choice == 'Ownership':
        domain = ['Original', 'Licensed']
        range_ = ['#780909', '#564d4d']

    color_scale = alt.Scale(domain=domain, range=range_)

    fiscal_half_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Fiscal Half:N', axis=alt.Axis(labelAngle=0), sort=sort_order),
        y='Views:Q',
        xOffset=f'{column_choice}:N',
        color=alt.Color(f'{column_choice}:N', scale=color_scale)
    )

    text_labels = fiscal_half_chart.mark_text(
        baseline='middle',
        dy=-10,
        fontSize=14
    ).encode(
        text='Text Label:N'
    )

    # Final chart configuration
    fiscal_half_chart = (fiscal_half_chart + text_labels).configure_mark(
        opacity=0.8
    ).configure_axis(
        labelFontSize=16,
        titleFontSize=0,
        grid=False
    ).configure_axisY(
        labelFontSize=0
    )

    return fiscal_half_chart