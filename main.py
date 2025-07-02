import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# Load Data with caching
@st.cache_data
def load_data():
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
                with open(os.path.join(json_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    dataframes.append(pd.DataFrame(data))
            except Exception as e:
                st.warning(f"Error loading {file}: {str(e)}")
    
    if not dataframes:
        st.error("No valid data loaded")
        st.stop()
    
    df = pd.concat(dataframes, ignore_index=True)
    df['ts'] = pd.to_datetime(df['ts'])
    df['hours_played'] = df['ms_played'] / 3600000
    return df

df = load_data()

# Streamlit App
st.title("🎵 Spotify Streaming History Dashboard (2013-2023)")
st.sidebar.header("Filters")

# Filter by Year
years = sorted(df['ts'].dt.year.unique(), reverse=True)
year_filter = st.sidebar.multiselect(
    "Select Year(s)", 
    years,
    default=years
)
df_filtered = df[df['ts'].dt.year.isin(year_filter)]

# Add number of artists selector
num_artists = st.sidebar.slider(
    "Number of Artists to Display",
    min_value=5,
    max_value=500,
    value=25,
    step=5
)

# Top Artists Analysis
st.subheader(f"Top Artists Analysis ({min(num_artists, len(df_filtered))} shown)")

# Clean and prepare data
df_filtered = df_filtered.dropna(subset=['master_metadata_album_artist_name'])
top_artists = (df_filtered
               .groupby("master_metadata_album_artist_name")['hours_played']
               .sum()
               .nlargest(num_artists)
               .reset_index()
               .sort_values('hours_played', ascending=True))  # Sort ascending for proper chart order

# Add rank column (1st, 2nd, 3rd...)
top_artists['rank'] = range(1, len(top_artists) + 1)

# Create interactive plot with ranking
fig = px.bar(
    top_artists, 
    x='hours_played', 
    y='master_metadata_album_artist_name',
    orientation='h',
    title=f"Top {len(top_artists)} Artists by Total Hours Played",
    labels={
        'master_metadata_album_artist_name': 'Artist',
        'hours_played': 'Hours Played',
        'rank': 'Rank'
    },
    hover_data={'rank': True, 'hours_played': ':.1f'},
    height=max(600, 30 * len(top_artists)),
    color='hours_played',
    color_continuous_scale='viridis'
)

# Format y-axis labels to show rankings
fig.update_yaxes(
    ticktext=[f"#{i} - {artist}" for i, artist in 
             zip(top_artists['rank'], top_artists['master_metadata_album_artist_name'])],
    tickvals=top_artists['master_metadata_album_artist_name'],
    title=None
)

# Improve tooltips
fig.update_traces(
    hovertemplate="<b>%{y}</b><br>Rank: #%{customdata[0]}<br>Hours Played: %{x:.1f}<extra></extra>"
)

# Enhanced layout
fig.update_layout(
    margin=dict(l=180, r=50, t=80, b=50),  # Increased left margin for longer labels
    yaxis={'categoryorder': 'total ascending'},
    hovermode='y',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis_title="Hours Played"
)

# Add some metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Artists", df['master_metadata_album_artist_name'].nunique())
col2.metric("Total Plays", len(df))
col3.metric("Total Hours", f"{df['hours_played'].sum():.1f}")

st.plotly_chart(fig, use_container_width=True)

# Listening Patterns Heatmap
st.subheader("Listening Patterns Heatmap")

# Prepare heatmap data
df_filtered['hour'] = df_filtered['ts'].dt.hour
df_filtered['day_of_week'] = df_filtered['ts'].dt.day_name()
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df_filtered['day_of_week'] = pd.Categorical(df_filtered['day_of_week'], categories=day_order, ordered=True)

heatmap_data = df_filtered.pivot_table(
    index='day_of_week', 
    columns='hour', 
    values='hours_played', 
    aggfunc='sum',
    fill_value=0
)

# Create interactive heatmap
heatmap_fig = px.imshow(
    heatmap_data,
    color_continuous_scale='viridis',
    labels={'x': 'Hour of Day', 'y': 'Day of Week', 'color': 'Hours Played'},
    title='Listening Activity by Day and Hour',
    aspect='auto'
)

heatmap_fig.update_layout(
    xaxis_title="Hour of Day (0-23)",
    yaxis_title="Day of Week"
)

st.plotly_chart(heatmap_fig, use_container_width=True)

# Enhanced Top Tracks Analysis
st.subheader(f"Top Tracks Analysis (Top {min(100, len(df_filtered))} Tracks)")

# Get top tracks with ranking
top_tracks = (df_filtered
              .dropna(subset=['master_metadata_track_name', 'master_metadata_album_artist_name'])
              .groupby(['master_metadata_track_name', 'master_metadata_album_artist_name'])['hours_played']
              .sum()
              .nlargest(100)
              .reset_index()
              .sort_values('hours_played', ascending=True))

# Add rank column
top_tracks.insert(0, 'Rank', range(1, len(top_tracks) + 1))

# Format the display
st.dataframe(
    top_tracks.style.format({
        'Hours Played': '{:.2f}',
        'Rank': '{:.0f}'
    }).bar(subset=['Hours Played'], color='#5fba7d'),
    column_config={
        'Rank': st.column_config.NumberColumn("Rank", width="small"),
        'master_metadata_track_name': "Track Name",
        'master_metadata_album_artist_name': "Artist",
        'hours_played': st.column_config.NumberColumn("Hours Played", format="%.2f")
    },
    hide_index=True,
    use_container_width=True,
    height=min(800, 35 * len(top_tracks))  # Dynamic height

# Add download button
csv = top_tracks.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Top Tracks Data",
    data=csv,
    file_name='spotify_top_tracks.csv',
    mime='text/csv'
)

# Raw data explorer
with st.expander("Explore Raw Data"):
    st.dataframe(df_filtered.sort_values('ts', ascending=False), use_container_width=True)