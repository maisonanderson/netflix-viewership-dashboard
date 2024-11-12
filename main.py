import streamlit as st
import os
from data import process_data
from queries import (
    load_excel_files, prepare_top_n_data, get_top_n_titles,
    create_fiscal_half_chart, folder_path, create_fiscal_half_df,
    process_uploaded_file
)

# Set up page
st.set_page_config(page_title='Netflix Viewership Dashboard', layout='wide')
st.title('Netflix Viewership Dashboard')
st.markdown(
    '<strong>Created by:</strong> [Maison Anderson](https://www.linkedin.com/in/maisonanderson/)',
    unsafe_allow_html=True
)
st.markdown("""
    On December 12, 2023, Netflix made history as the first streaming service to release comprehensive viewership data 
    for its entire catalog. This dashboard provides high-level insights into Netflix’s viewership trends since the 
    initial publication. For more details on updating the data source, please refer to the Info section at the bottom 
    of this page, which also includes a list of the key assumptions made during data processing.
""")
st.write('')

# Load datasets
film_data, tv_data = process_data()

# Visualization 1: Top viewed content
film_data_grouped, tv_data_grouped = prepare_top_n_data(film_data, tv_data)

col1, col2 = st.columns(2)
with col1:
    st.markdown('### Most Viewed Films 📽️')
    col_a, col_b, _ = st.columns([2, 2, 2])
    with col_a:
        top_films_choice = st.selectbox(
            'Choose a metric:', options=['Views', 'Hours Viewed'], key='top_films_choice'
        )
    with col_b:
        films_filter = st.select_slider(
            'Filter by # of Films:',
            options=list(range(film_data_grouped['# of Films'].min(), int(film_data_grouped['# of Films'].max()) + 1)),
            value=(film_data_grouped['# of Films'].min(), film_data_grouped['# of Films'].max()),
            key='films_filter'
        )
    filtered_films = film_data_grouped[film_data_grouped['# of Films'].between(*films_filter)]
    st.dataframe(get_top_n_titles(filtered_films, 100, top_films_choice))

with col2:
    st.markdown('### Most Viewed TV Shows 📺')
    col_a, col_b, _ = st.columns([2, 2, 2])
    with col_a:
        top_tv_choice = st.selectbox(
            'Choose a metric:', options=['Views', 'Hours Viewed'], key='top_tv_choice'
        )
    with col_b:
        seasons_filter = st.select_slider(
            'Filter by # of Seasons:',
            options=list(range(tv_data_grouped['# of Seasons'].min(), int(tv_data_grouped['# of Seasons'].max()) + 1)),
            value=(tv_data_grouped['# of Seasons'].min(), tv_data_grouped['# of Seasons'].max()),
            key='seasons_filter'
        )
    filtered_tv = tv_data_grouped[tv_data_grouped['# of Seasons'].between(*seasons_filter)]
    st.dataframe(get_top_n_titles(filtered_tv, 100, top_tv_choice))

st.write('')

# Visualization 2: Views by Fiscal Half
st.header('Total Views by Fiscal Half')
col1, col2 = st.columns([1, 4])
with col1:
    column_choice = st.selectbox(
        'Choose a grouping:', options=['Media', 'Availability', 'Ownership']
    )

fiscal_half_df = create_fiscal_half_df(film_data, tv_data, column_choice)
fiscal_half_chart = create_fiscal_half_chart(fiscal_half_df, column_choice)
st.altair_chart(fiscal_half_chart, use_container_width=True)

st.write('')

# Info Section
st.header('Info')
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

col1, _ = st.columns([3, 2])
with col1:
    st.markdown("""
        **Data Sources:**
        Check for new Netflix viewership reports in 
        the [Netflix Newsroom](https://about.netflix.com/en/newsroom?search=what%20we%20watched), 
        then add them to the dashboard below.
    """)

    excel_files_df = load_excel_files()
    st.dataframe(excel_files_df, hide_index=True)

    with st.expander('Expand to add new Netflix data'):
        uploaded_file = st.file_uploader('Choose an Excel file', type=['xlsx'])
        if uploaded_file is not None:
            process_uploaded_file(uploaded_file, folder_path)

    st.write('')
    st.markdown(""" 
        **Data Processing Assumptions:**
        - **Ownership:** Netflix describes "Release Date" as "the premiere date for any Netflix TV series or film." 
        Titles with a blank "Release Date" are assumed to be licensed content.
        - **Title Grouping:** Titles are grouped under a unified name to allow higher-level insights. Grouping criteria:
            - Contains a colon (e.g., *Bridgerton: Season 3*)
            - Uses "//" as a delimiter (e.g., *The Seven Deadly Sins // 七つの大罪*)
            - Ends with a single-digit number (e.g., *Despicable Me 2*)
        - **Media Category:** The H1 2023 dataset lacked "Film" and "TV" categorization. Titles are categorized based 
        on later datasets, defaulting to "TV" if "season" is mentioned; otherwise, "Film."
        - **Runtime Filling:** H1 2023 excluded "Runtime." Missing values are filled by matching with later datasets 
        or set to the average within the "Film" or "TV" classification.
    """)
