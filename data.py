import os
import re
import pandas as pd
import numpy as np


# HELPER VARIABLES
folder_path = 'exports'

film_data = pd.DataFrame()
tv_data = pd.DataFrame()
engagement_data = pd.DataFrame()

group_title_exceptions = {
    "Bright: Samurai Soul // ブライト: サムライソウル": "Bright: Samurai Soul",
    "Pokémon the Movie: Secrets of the Jungle": "Pokémon",
    "Rebel Moon": "Rebel Moon"
}

licensed_exceptions = {
    "Arrested Development": "Licensed"
}


# HELPER FUNCTIONS
def extract_dates_from_filename(filename):
    """Extract start and end dates from file name."""
    match = re.search(r'(\d{4})(Jan-Jun|Jul-Dec)', filename)
    if match:
        year, period = match.groups()
        return (f"{year}-01-01", f"{year}-06-30") if period == 'Jan-Jun' else (f"{year}-07-01", f"{year}-12-31")
    raise ValueError(f"Incorrect filename format: {filename}")


def get_group_title(title):
    """Get group title based on exceptions or title structure."""
    group_title = group_title_exceptions.get(title)
    if group_title:
        return group_title

    title = re.sub(r'\s\d$', '', title)

    return re.split(':|//', title)[0]


def convert_runtime_to_minutes(runtime):
    """Convert runtime from HH:MM format to minutes."""
    if pd.isna(runtime) or not runtime:
        return np.nan
    try:
        hours, minutes = map(int, runtime.split(':'))
        return hours * 60 + minutes
    except ValueError:
        return np.nan


def calculate_runtime(row):
    """Calculate runtime in minutes based on given runtime or by dividing hours viewed by views."""
    if row['Runtime'] == "*":
        hours_viewed, views = row['Hours Viewed'], row['Views']
        return round((hours_viewed / views) * 60) if pd.notna(hours_viewed) and pd.notna(
            views) and views != 0 else np.nan
    return convert_runtime_to_minutes(row['Runtime'])


def determine_ownership(title, release_date):
    """Check if title is licensed based on exceptions or release date."""
    return licensed_exceptions.get(title, "Licensed" if pd.isnull(release_date) else "Original")


# DATA PROCESSING FUNCTIONS
def process_sheet(file_path, sheet_name, start_date, end_date):
    """Read and process Film, TV, or Engagement sheet."""
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
        print(f"Error processing {sheet_name} sheet in {file_path}: {e}")
        return pd.DataFrame()


def process_files_in_folder(folder_path):
    """Process all Excel files in the given folder."""
    global film_data, tv_data, engagement_data
    for filename in os.listdir(folder_path):
        if filename.endswith('.xlsx') and not filename.startswith('~$'):
            file_path = os.path.join(folder_path, filename)
            start_date, end_date = extract_dates_from_filename(filename)

            if "2023Jan-Jun" in filename:
                engagement_df = process_sheet(file_path, "Engagement", start_date, end_date)
                engagement_data = pd.concat([engagement_data, engagement_df], ignore_index=True)
            else:
                film_df = process_sheet(file_path, "Film", start_date, end_date)
                tv_df = process_sheet(file_path, "TV", start_date, end_date)

                film_data = pd.concat([film_data, film_df], ignore_index=True)
                tv_data = pd.concat([tv_data, tv_df], ignore_index=True)


def clean_initial_publish(initial_publish, helper_data):
    """Clean engagement data by filling missing media and runtime values."""
    helper_data = helper_data.drop_duplicates(['Title'])
    print(helper_data)
    initial_publish = initial_publish.merge(helper_data[['Title', 'Media', 'Runtime in Minutes']], on='Title',
                                            how='left')


    # Fill missing 'Media' based on 'Title'
    initial_publish['Media'] = initial_publish.apply(
        lambda row: 'TV' if pd.isnull(row['Media']) and 'Season' in row['Title'] else
        'Film' if pd.isnull(row['Media']) else row['Media'],
        axis=1
    )

    # Fill missing 'Runtime in Minutes' with the average runtime for each 'Media'
    avg_runtimes = helper_data.groupby('Media')['Runtime in Minutes'].mean()
    initial_publish['Runtime in Minutes'] = initial_publish.apply(
        lambda row: avg_runtimes.get(row['Media'], np.nan) if pd.isnull(row['Runtime in Minutes']) else row[
            'Runtime in Minutes'],
        axis=1
    )

    return initial_publish


def add_media_to_initial_publish(initial_publish):
    """Split engagement data by media type and append to film_data and tv_data."""
    global film_data, tv_data
    film_data = pd.concat([film_data, initial_publish[initial_publish['Media'] == 'Film']], ignore_index=True)
    tv_data = pd.concat([tv_data, initial_publish[initial_publish['Media'] == 'TV']], ignore_index=True)


def convert_columns_to_datetime(df, columns):
    """Convert specified columns in dataframe to datetime format, with error handling."""
    for col in columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date if df[col].dtype == 'datetime64[ns]' else df[col]


# Execute the processing
process_files_in_folder(folder_path)

# Combine film and TV data to merge with engagement data
combined_helper = pd.concat([film_data, tv_data], ignore_index=True)

# Clean engagement data
engagement_data = clean_initial_publish(engagement_data, combined_helper)

# Append engagement data to film_data and tv_data
add_media_to_initial_publish(engagement_data)

# Convert columns to datetime
convert_columns_to_datetime(film_data, ['Start Date', 'End Date', 'Release Date'])
convert_columns_to_datetime(tv_data, ['Start Date', 'End Date', 'Release Date'])