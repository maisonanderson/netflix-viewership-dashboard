# Netflix Viewership Analysis App

A Python web application for analyzing Netflix viewership data, allowing users to explore insights into Netflix's catalog. The app processes, cleans, and visualizes the data to provide valuable trends and analysis. Visit the dashboard at [netflix-viewership-dashboard.streamlit.app](https://netflix-viewership-dashboard.streamlit.app).

## Table of Contents

- [Features](#features)
- [Data Structure](#data-structure)
- [File Structure](#file-structure)
- [Future Development](#future-development)

## Features

- **Processing New Data**: 
  - Once Netflix publishes new viewership data, the user can add it to the dashboard using the file uploader at the bottom of the page.
  - Initially, this application scraped the Netflix Newsroom directly, but this led to issues after deployment.
- **Data Cleaning**: Cleans and preprocesses data with helper functions that handle exceptions, set group titles, and determine licensing.
- **Visualizations**: Interactive charts and tables, including:
  - Total views by fiscal half
  - Top 100 most viewed films and TV shows

## Data Structure

The application processes data structured as follows:

- **Title**: The title of the media.
- **Release Date**: The release date of the media.
- **Runtime**: The duration of the media in `hh:mm` format.
- **Hours Viewed**: Total hours watched.
- **Views**: Total view counts.
- **Available Globally?**: Indicates if the media is available worldwide (Y/N).

## File Structure
- main.py: Streamlit frontend for data display and visualization.
- data.py: Contains helper functions for data cleaning and processing.
- queries.py: Handles data validation and complex query operations.
- exports/: Folder for storing Netflix's viewership files.

## Future Development
- **The Movie Database (TMDB) API**
  - This would provide additional content metadata (e.g., genre) that Netflix excludes from their datasets, enabling deeper insights and more detailed analysis.
- **Additional Filters**
  - The current filtering options are limited. Expanding the available filters would allow users to explore more tailored and meaningful insights.
- **Performance Optimizations**
  - While Streamlit’s caching system is in use, further performance improvements are possible, such as optimizing data processing and reducing loading times for large datasets.


