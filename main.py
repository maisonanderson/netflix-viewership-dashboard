import streamlit as st

import data
import queries
from datetime import datetime
import os


# HEADER
st.set_page_config(page_title='Netflix Viewership Dashboard', layout='wide')

st.title('Netflix Viewership Dashboard')
st.markdown('<strong>Created by:</strong> [Maison Anderson](https://www.linkedin.com/in/maisonanderson/)', unsafe_allow_html=True)

st.markdown(
    f"""
    On December 12, 2023, Netflix made history as the first streaming service to release comprehensive viewership data 
    for its entire catalog. This dashboard provides high-level insights into Netflix’s viewership trends since the 
    initial publication. For more details on updating the data source, please refer to the Info section at the bottom 
    of this page, which also includes a list of the key assumptions made during data processing.
    """
)

st.write('')
st.write('')


# VISUALIZATION #1 - Most Viewed Films and TV Shows
col1, col2 = st.columns(2)

with col1:
    st.markdown('### Most Viewed Films 📽️')
    col_a, col_b, _ = st.columns([2, 2, 2])

    with col_a:
        top_films_choice = st.selectbox(
            'Choose a metric:',
            options=['Views', 'Hours Viewed'],
            key='top_films_choice'
        )

    with col_b:
        max_films = queries.film_data_grouped['# of Films'].max()
        min_films = queries.film_data_grouped['# of Films'].min()
        films_filter = st.select_slider(
            'Filter by # of Films:',
            options=list(range(min_films, int(max_films) + 1)),
            value=(min_films, max_films),  # Default to the full range
            key='films_filter'
        )

    filtered_films = queries.film_data_grouped[queries.film_data_grouped['# of Films'].between(films_filter[0], films_filter[1])]
    st.dataframe(queries.get_top_n_titles(filtered_films, 10, top_films_choice))

with col2:
    st.markdown('### Most Viewed TV Shows 📺')
    col_a, col_b, _ = st.columns([2, 2, 2])

    with col_a:
        top_tv_choice = st.selectbox(
            'Choose a metric:',
            options=['Views', 'Hours Viewed'],
            key='top_tv_choice'
        )

    with col_b:
        max_seasons = queries.tv_data_grouped['# of Seasons'].max()
        min_seasons = queries.tv_data_grouped['# of Seasons'].min()
        seasons_filter = st.select_slider(
            'Filter by # of Seasons:',
            options=list(range(min_seasons, int(max_seasons) + 1)),
            value=(min_seasons, max_seasons),  # Default to the full range
            key='seasons_filter'
        )

    filtered_tv = queries.tv_data_grouped[queries.tv_data_grouped['# of Seasons'].between(seasons_filter[0], seasons_filter[1])]
    st.dataframe(queries.get_top_n_titles(filtered_tv, 10, top_tv_choice))

st.write('')
st.write('')

# VISUALIZATION #2 - Total Views by Fiscal Half
st.header('Total Views by Fiscal Half')
col1, col2 = st.columns([1, 4])

with col1:
    column_choice = st.selectbox(
        'Choose a grouping:',
        options=['Media', 'Ownership']
    )

# Function to fetch the latest file modification timestamp from the 'exports' folder
def get_latest_file_timestamp():
    latest_time = datetime.min
    for file_name in os.listdir(data.folder_path):
        file_path = os.path.join(data.folder_path, file_name)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time > latest_time:
                latest_time = file_time
    return latest_time

# Check if the 'exports' folder has a new file added
latest_publish_time = get_latest_file_timestamp()

# Create fiscal half chart (without caching)
with st.spinner("Loading..."):
    date_range_chart = queries.create_fiscal_half_chart(column_choice)

st.altair_chart(date_range_chart, use_container_width=True)

st.write('')


# INFO SECTION
st.header('Info')

if not os.path.exists(data.folder_path):
    os.makedirs(data.folder_path)

col1, _ = st.columns([3, 2])

with col1:
    st.markdown(
        """
        **Data Sources:**
        
        Check for new Netflix viewership reports in 
        the [Netflix Newsroom](https://about.netflix.com/en/newsroom?search=what%20we%20watched), 
        then add them to the dashboard below.
        """
    )

    st.dataframe(queries.excel_files_df, hide_index=True)

    with st.expander("Expand to add new Netflix data"):
        uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_path = os.path.join(data.folder_path, file_name)

            if os.path.exists(file_path):
                st.warning(f"The file {file_name} already exists in the 'exports' folder.")
            else:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"File {file_name} has been uploaded successfully!")

    st.write('')
    st.write('')

    st.markdown(""" 
    **Data Processing Assumptions:**
    - **Ownership:** Netflix describes "Release Date" as "the premiere date for any Netflix TV series or film." 
    Therefore, titles with a blank "Release Date" are assumed to be licensed content in this dashboard.
    - **Title:** A new column is created to group related seasons and films under a unified title, enabling higher-
    level insights. Titles are grouped using the following criteria:
        - Titles containing a colon (e.g., *Bridgerton: Season 3*)
        - Titles with "//" as a delimiter (e.g., *The Seven Deadly Sins // 七つの大罪*)
        - Titles ending with a single-digit number (e.g., *Despicable Me 2*)
    - **Media:** The H1 2023 dataset did not categorize content between "Film" and "TV." This dashboard categorizes 
    each title based on classifications found in later datasets. If a title's classification is missing, it defaults 
    to "TV" if the title contains the word "season"; otherwise, it is set to "Film."
    - **Runtime:** The H1 2023 dataset excluded "Runtime." This dashboard fills in missing runtime values by matching 
    titles with later datasets; if unavailable, the runtime is set to the average within the Media classification 
    ("Film" or "TV").
    """)
