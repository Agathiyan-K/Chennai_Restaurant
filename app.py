# app.py

import gdown
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import ast

# --- Download the dataset from Google Drive ---
file_id = "1uZt10B_f16oTj_u_EM-VCUhI6nmGQzuG"
url = f"https://drive.google.com/uc?id={file_id}"
output_path = "zomato_chennai.csv"
gdown.download(url, output_path, quiet=False)

# --- Load and preprocess the data ---
df = pd.read_csv("zomato_chennai.csv")
df.columns = df.columns.str.strip()
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

def safe_eval(val):
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except:
            return [val]
    return val

for col in ['Cuisine', 'Top Dishes', 'Features']:
    df[col] = df[col].apply(safe_eval)

df_exploded = df.explode('Cuisine').explode('Top Dishes').explode('Features')
for col in ['Cuisine', 'Top Dishes', 'Features']:
    df_exploded[col] = df_exploded[col].astype(str).str.strip()

df = df_exploded

# --- Streamlit App Interface ---
st.set_page_config(page_title="Zomato Chennai Explorer", layout="wide")
st.title("🍽️ Zomato Chennai Restaurant Explorer")

# Filters
location = st.selectbox("Select Location", sorted(df['Location'].dropna().unique()))

filtered_df = df[df['Location'] == location]
cuisines = sorted(filtered_df['Cuisine'].dropna().unique())
cuisine = st.selectbox("Select Cuisine", cuisines)

filtered_df = filtered_df[filtered_df['Cuisine'] == cuisine]
restaurants = sorted(filtered_df['Name of Restaurant'].dropna().unique())
selected_restaurants = st.multiselect("Select Restaurant(s)", restaurants)

# If restaurants are selected
if selected_restaurants:
    display_df = filtered_df[filtered_df['Name of Restaurant'].isin(selected_restaurants)]

    grouped_df = display_df.groupby('Name of Restaurant').agg({
        'Address': 'first',
        'Top Dishes': lambda x: ', '.join(x.dropna().unique()),
        'Features': lambda x: ', '.join(x.dropna().unique()),
        'Price for 2': 'first',
        'Dining Rating': 'mean',
        'Dining Rating Count': 'sum',
        'Delivery Rating': 'mean',
        'Delivery Rating Count': 'sum'
    }).reset_index()

    st.subheader("📊 Restaurant Details")
    st.dataframe(grouped_df)

    # --- Price Bar Chart ---
    st.subheader("💸 Price for 2 Comparison")
    price_fig = px.bar(
        grouped_df,
        x='Name of Restaurant',
        y='Price for 2',
        labels={'Price for 2': 'Price for 2 (₹)'},
        title='Price for 2 Comparison'
    )
    st.plotly_chart(price_fig, use_container_width=True)

    # --- Ratings Chart ---
    st.subheader("⭐ Dining and Delivery Ratings")
    rating_fig = go.Figure()
    rating_fig.add_trace(go.Bar(
        x=grouped_df['Name of Restaurant'],
        y=grouped_df['Dining Rating'],
        name='Dining Rating',
        marker_color='blue'
    ))
    rating_fig.add_trace(go.Bar(
        x=grouped_df['Name of Restaurant'],
        y=grouped_df['Delivery Rating'],
        name='Delivery Rating',
        marker_color='orange'
    ))
    rating_fig.update_layout(
        barmode='group',
        xaxis_title='Restaurant',
        yaxis_title='Rating',
        title='Dining and Delivery Rating Comparison'
    )
    st.plotly_chart(rating_fig, use_container_width=True)

    # --- Correlation Heatmap ---
    st.subheader("🔍 Correlation Heatmap")
    corr_df = grouped_df[['Price for 2', 'Dining Rating', 'Delivery Rating']]
    corr_matrix = corr_df.corr().round(2)

    heatmap_fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu',
        zmin=-1,
        zmax=1,
        text=corr_matrix.values,
        texttemplate="%{text}",
        colorbar=dict(title="Correlation")
    ))
    heatmap_fig.update_layout(
        title='Correlation: Price, Dining & Delivery',
        height=400
    )
    st.plotly_chart(heatmap_fig, use_container_width=True)

else:
    st.info("👈 Select at least one restaurant to view analysis.")
