import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# Load Data
json_dir = 'data/' 
dataframes = []

# Create data directory if doesn't exist
if not os.path.exists(json_dir):
    os.makedirs(json_dir)
    st.warning(f"Created missing directory: {json_dir}")

# Check if directory is empty
if not os.listdir(json_dir):
    st.error(f"No JSON files found in {json_dir}")
    st.stop()  # Halt the app if no data

for file in os.listdir(json_dir):
    if file.endswith('.json'):
        try:
            with open(os.path.join(json_dir, file), 'r') as f:
                data = json.load(f)
                dataframes.append(pd.DataFrame(data))
        except Exception as e:
            st.warning(f"Error loading {file}: {str(e)}")

df = pd.concat(dataframes, ignore_index=True)
df['ts'] = pd.to_datetime(df['ts'])
df['hours_played'] = df['ms_played'] / 3600000

# Streamlit App
st.title("🎵 Spotify Streaming History Dashboard")
st.sidebar.header("Filters")

# Filter by Year
year_filter = st.sidebar.multiselect(
    "Select Year", 
    df['ts'].dt.year.unique(), 
    default=df['ts'].dt.year.unique()
)
df_filtered = df[df['ts'].dt.year.isin(year_filter)]

# Top Artists Chart - IMPROVED VERSION
st.subheader("Top Artists Analysis")

# First ensure we have clean data
df_filtered = df_filtered.dropna(subset=['master_metadata_album_artist_name'])

# Get top artists with better handling
top_artists = (df_filtered.groupby("master_metadata_album_artist_name", dropna=False)['hours_played']
               .sum()
               .sort_values(ascending=False)
               .reset_index())

# Show how many unique artists we actually have
st.sidebar.markdown(f"**Unique artists in selection:** {len(top_artists)}")

# Create visualization with all available artists (up to 25)
show_n = min(40, len(top_artists))  # Show 25 or whatever's available
top_artists = top_artists.head(show_n)

# Create the plot with improved layout
fig = px.bar(top_artists, 
             x='hours_played', 
             y='master_metadata_album_artist_name',
             orientation='h',
             title=f"Top {show_n} Artists (Total Hours Played)",
             labels={
                 'master_metadata_album_artist_name': 'Artist',
                 'hours_played': 'Hours Played'
             },
             height=max(600, 50 * show_n))  # Dynamic height

# Improve layout
fig.update_layout(
    margin=dict(l=150, r=50, t=50, b=50),  # Adjust margins
    yaxis={'categoryorder':'total ascending'},
    hovermode='y'
)

st.plotly_chart(fig, use_container_width=True)

# Debug info (can be commented out)
with st.expander("Data Debug Info"):
    st.write(f"Total unique artists in full dataset: {df['master_metadata_album_artist_name'].nunique()}")
    st.write(f"Filtered dataset contains {len(df_filtered)} plays")
    st.write("Sample of filtered data:", df_filtered.head(3))

# Heatmap of Listening Patterns
st.subheader("Listening Patterns Heatmap")
df_filtered['hour'] = df_filtered['ts'].dt.hour
df_filtered['day_of_week'] = df_filtered['ts'].dt.day_name()
heatmap_data = df_filtered.pivot_table(
    index='day_of_week', 
    columns='hour', 
    values='hours_played', 
    aggfunc='sum'
)

# Order days of week properly
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = heatmap_data.reindex(day_order)

st.plotly_chart(
    px.imshow(
        heatmap_data, 
        color_continuous_scale='viridis',
        labels={'color': 'Hours Played'},
        title='Listening Activity by Day and Hour'
    ),
    use_container_width=True
)