import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
#to run streamlit run gapp.py
# Load Data
# My listening history from Spotify
#Wed  2 Jul 2025 11:15:37 AEST
# from Onedrive to local storage
json_dir = 'data/' 
dataframes = []

for file in os.listdir(json_dir):
    if file.endswith('.json'):
        with open(os.path.join(json_dir, file), 'r') as f:
            data = json.load(f)
            dataframes.append(pd.DataFrame(data))

df = pd.concat(dataframes, ignore_index=True)
df['ts'] = pd.to_datetime(df['ts'])
df['hours_played'] = df['ms_played'] / 3600000

# Streamlit App
st.title("🎵 Spotify Streaming History Dashboard")
st.sidebar.header("Filters")

# Filter by Year
year_filter = st.sidebar.multiselect("Select Year", df['ts'].dt.year.unique(), default=df['ts'].dt.year.unique())
df_filtered = df[df['ts'].dt.year.isin(year_filter)]

# Top Artists Chart
top_artists = df_filtered.groupby("master_metadata_album_artist_name")['hours_played'].sum().nlargest(25).reset_index()
fig = px.bar(top_artists, x='hours_played', y='master_metadata_album_artist_name', orientation='h', title="Top Artists", labels={'master_metadata_album_artist_name': 'Artist', 'hours_played': 'Hours Played'})
st.plotly_chart(fig)

# Heatmap of Listening Patterns
st.subheader("Listening Patterns Heatmap")
df_filtered['hour'] = df_filtered['ts'].dt.hour
df_filtered['day_of_week'] = df_filtered['ts'].dt.day_name()
heatmap_data = df_filtered.pivot_table(index='day_of_week', columns='hour', values='hours_played', aggfunc='sum')

st.write(px.imshow(heatmap_data, color_continuous_scale='viridis'))

