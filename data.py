import os
import re
import pandas as pd
import numpy as np


# Helper Variables
group_title_exceptions = {
    'Bright: Samurai Soul // ブライト: サムライソウル': 'Bright: Samurai Soul',
    'Pokémon the Movie: Secrets of the Jungle': 'Pokémon',
    'Rebel Moon': 'Rebel Moon'
}

licensed_exceptions = {
    'Arrested Development': 'Licensed'
}


# Helper Functions
def extract_dates_from_filename(filename):
    match = re.search(r'(\d{4})(Jan-Jun|Jul-Dec)', filename)
    if match:
        year, period = match.groups()
        return (f'{year}-01-01', f'{year}-06-30') if period == 'Jan-Jun' else (f'{year}-07-01', f'{year}-12-31')
    raise ValueError(f'Incorrect filename format: {filename}')

def get_group_title(title):
    group_title = group_title_exceptions.get(title)
    if group_title:
        return group_title
    title = re.sub(r'\s\d$', '', title)
    return re.split(':|//', title)[0]

def convert_runtime_to_minutes(runtime):
    if pd.isna(runtime) or not runtime:
        return np.nan
    try:
        hours, minutes = map(int, runtime.split(':'))
        return hours * 60 + minutes
    except ValueError:
        return np.nan

def calculate_runtime(row):
    if row['Runtime'] == '*':
        hours_viewed, views = row['Hours Viewed'], row['Views']
        return round((hours_viewed / views) * 60) if pd.notna(hours_viewed) and pd.notna(views) and views != 0 else np.nan
    return convert_runtime_to_minutes(row['Runtime'])

def determine_ownership(title, release_date):
    return licensed_exceptions.get(title, 'Licensed' if pd.isnull(release_date) else 'Original')


# Data Processing Functions
def process_sheet(file_path, sheet_name, start_date, end_date):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=5).iloc[:, 1:]
        df['Start Date'], df['End Date'] = start_date, end_date
        df['Group Title'] = df['Title'].apply(get_group_title)
        df['Ownership'] = df.apply(lambda row: determine_ownership(row['Title'], row['Release Date']), axis=1)
        if sheet_name in ['Film', 'TV']:
            df['Media'] = sheet_name
            df['Runtime in Minutes'] = df.apply(calculate_runtime, axis=1)
        return df
    except Exception as e:
        print(f'Error processing {sheet_name} sheet in {file_path}: {e}')
        return pd.DataFrame()

def clean_initial_publish(initial_publish, helper_data):
    helper_data = helper_data.drop_duplicates(['Title'])
    initial_publish = initial_publish.merge(helper_data[['Title', 'Media', 'Runtime in Minutes']], on='Title', how='left')
    initial_publish['Media'] = initial_publish.apply(
        lambda row: 'TV' if pd.isnull(row['Media']) and 'Season' in row['Title'] else
        'Film' if pd.isnull(row['Media']) else row['Media'],
        axis=1
    )
    avg_runtimes = helper_data.groupby('Media')['Runtime in Minutes'].mean()
    initial_publish['Runtime in Minutes'] = initial_publish.apply(
        lambda row: avg_runtimes.get(row['Media'], np.nan) if pd.isnull(row['Runtime in Minutes']) else row['Runtime in Minutes'],
        axis=1
    )
    return initial_publish

def add_media_to_initial_publish(initial_publish, film_data, tv_data):
    film_data = pd.concat([film_data, initial_publish[initial_publish['Media'] == 'Film']], ignore_index=True)
    tv_data = pd.concat([tv_data, initial_publish[initial_publish['Media'] == 'TV']], ignore_index=True)
    return film_data, tv_data

def convert_columns_to_datetime(df, columns):
    for col in columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date if df[col].dtype == 'datetime64[ns]' else df[col]


# Main Data Processing
def process_data():
    film_data, tv_data, engagement_data = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    for filename in os.listdir('exports'):
        if filename.endswith('.xlsx') and not filename.startswith('~$'):
            file_path = os.path.join('exports', filename)
            start_date, end_date = extract_dates_from_filename(filename)

            # Process Engagement Data
            if '2023Jan-Jun' in filename:
                engagement_df = process_sheet(file_path, 'Engagement', start_date, end_date)
                engagement_data = pd.concat([engagement_data, engagement_df], ignore_index=True)
            else:
                # Process Film and TV Data
                film_df = process_sheet(file_path, 'Film', start_date, end_date)
                tv_df = process_sheet(file_path, 'TV', start_date, end_date)
                film_data = pd.concat([film_data, film_df], ignore_index=True)
                tv_data = pd.concat([tv_data, tv_df], ignore_index=True)

    # Combine Film and TV Data
    combined_helper = pd.concat([film_data, tv_data], ignore_index=True)

    # Clean Engagement Data
    engagement_data = clean_initial_publish(engagement_data, combined_helper)

    # Add Media Columns
    film_data, tv_data = add_media_to_initial_publish(engagement_data, film_data, tv_data)

    # Convert Date Columns
    convert_columns_to_datetime(film_data, ['Start Date', 'End Date', 'Release Date'])
    convert_columns_to_datetime(tv_data, ['Start Date', 'End Date', 'Release Date'])

    return film_data, tv_data
