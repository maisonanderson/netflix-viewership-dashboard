import pandas as pd
import altair as alt
import os
import streamlit as st
import data


# FILE UPLOAD
excel_files = [file for file in os.listdir(data.folder_path) if file.endswith('.xlsx')]
excel_files.sort(reverse=True)
excel_files_df = pd.DataFrame(excel_files, columns=['Excel Files In Use'])


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


combined_window_films = combine_windows(data.film_data)
combined_window_tv = combine_windows(data.tv_data)

film_data_grouped = group_and_aggregate(combined_window_films)
film_data_grouped = rename_columns(film_data_grouped, 'Film')

tv_data_grouped = group_and_aggregate(combined_window_tv)
tv_data_grouped = rename_columns(tv_data_grouped, 'TV')

top_10_tv = get_top_n_titles(tv_data_grouped, 10)
top_10_films = get_top_n_titles(film_data_grouped, 10)


# VISUALIZATION #2
def get_fiscal_half(start_date, end_date):
    """Create a Fiscal Half column in the format H1 YYYY or H2 YYYY."""
    start_year = start_date.year
    if 1 <= start_date.month <= 6:
        return f"H1 {start_year}"
    else:
        return f"H2 {start_year}"


def get_latest_publish_time():
    """Get the latest publish time from the data to check for updates."""
    # Assuming 'data.film_data' and 'data.tv_data' have a 'Start Date' column
    latest_film_time = data.film_data['Start Date'].max()
    latest_tv_time = data.tv_data['Start Date'].max()
    return max(latest_film_time, latest_tv_time)


def add_fiscal_half_and_views(df, media_type, latest_publish_time):
    """Add Media, Fiscal Half columns and calculate Views based on Hours Viewed and Runtime."""
    df['Media'] = media_type
    df['Fiscal Half'] = df.apply(
        lambda row: get_fiscal_half(pd.to_datetime(row['Start Date']), pd.to_datetime(row['End Date'])),
        axis=1
    )
    df['Views'] = (df['Hours Viewed'] / (df['Runtime in Minutes'] / 60)).round()
    return df


def create_fiscal_half_chart(column_choice):
    """Create and return the fiscal half chart."""
    # Get latest data publish time to ensure proper cache invalidation
    latest_publish_time = get_latest_publish_time()

    # Prepare data with chosen column
    film_data_with_fiscal_half = add_fiscal_half_and_views(data.film_data, 'Film', latest_publish_time)
    tv_data_with_fiscal_half = add_fiscal_half_and_views(data.tv_data, 'TV', latest_publish_time)

    combined_data = pd.concat([film_data_with_fiscal_half, tv_data_with_fiscal_half])

    fiscal_half_summary = combined_data.groupby([column_choice, 'Fiscal Half', 'Start Date'], as_index=False)[
        'Views'].sum()

    fiscal_half_summary = fiscal_half_summary.sort_values(by='Start Date').reset_index()
    fiscal_half_summary['Views in Billions'] = fiscal_half_summary['Views'] / 1_000_000_000
    fiscal_half_summary['Text Label'] = (fiscal_half_summary['Views in Billions'].round(2).astype(str) + 'B')

    # Chart settings
    sort_order = fiscal_half_summary[['Fiscal Half', 'Start Date']].drop_duplicates().sort_values('Start Date').drop(
        columns='Start Date').values.flatten().tolist()

    if column_choice == 'Media':
        domain = ['Film', 'TV']
        range_ = ['#E50914', '#000000']
    elif column_choice == 'Ownership':
        domain = ['Original', 'Licensed']
        range_ = ['#B1060F', '#564d4d']

    color_scale = alt.Scale(domain=domain, range=range_)

    fiscal_half_chart = alt.Chart(fiscal_half_summary).mark_bar().encode(
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