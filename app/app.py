import re
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Configuration
API_URL = "http://localhost:8000/analyze"

st.set_page_config(
    page_title="TubeSense Analytics",
    page_icon="🎥",
    layout="wide"
)

st.title("🎥 TubeSense: YouTube Sentiment & Topic Analytics")
st.markdown("Analyze audience sentiment and discover latent topics in YouTube comments instantly using pre-trained NLP models.")

def extract_video_id(url: str) -> str:
    """Extracts the video ID from a standard YouTube URL."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def render_empty_state():
    st.info("👈 Enter a YouTube URL in the sidebar to begin analysis!")
    st.image("https://images.unsplash.com/photo-1611162617474-5b21e879e113?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True, caption="Analyze your audience.")

# Initialize session state for data persistence
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None

# Sidebar for controls
with st.sidebar:
    st.header("Configuration")
    video_url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
    max_comments = st.slider("Max Comments to Analyze", min_value=100, max_value=2000, value=500, step=100)
    analyze_btn = st.button("Analyze Video", type="primary", use_container_width=True)

# 1. Fetch Data on Button Click
if analyze_btn:
    if not video_url:
        st.sidebar.warning("Please enter a valid YouTube URL.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.sidebar.error("Could not extract a valid Video ID from the URL.")
        else:
            with st.spinner(f"Analyzing comments for video '{video_id}'... (This may take a minute)"):
                try:
                    response = requests.post(
                        API_URL, 
                        json={"video_id": video_id, "max_comments": max_comments},
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        # Store the result in session state so it survives reruns!
                        st.session_state.analysis_data = response.json()
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                        st.session_state.analysis_data = None
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the backend API. Is FastAPI running? Error: {e}")
                    st.session_state.analysis_data = None

# 2. Render UI from Session State
if st.session_state.analysis_data is None:
    render_empty_state()
else:
    data = st.session_state.analysis_data
    metadata = data.get("metadata", {})
    
    # --- HERO SECTION (Video Context) ---
    st.divider()
    col_img, col_info = st.columns([1, 3])
    with col_img:
        st.image(metadata.get("thumbnail_url", ""), use_container_width=True)
    with col_info:
        st.subheader(metadata.get("title", "Unknown Title"))
        st.write(f"**Channel:** {metadata.get('channel_title', 'Unknown')}")
        st.write(f"**Views:** {metadata.get('view_count', 0):,}")
        
    st.divider()
    
    # Calculate KPIs
    sentiment_dict = data.get("sentiment_distribution", {})
    total = data.get("total_analyzed", 0)
    pos_count = sentiment_dict.get("Positive", 0)
    pos_ratio = (pos_count / total * 100) if total > 0 else 0
    
    topic_dict = data.get("topic_clusters", {})
    top_topic = "None"
    if topic_dict:
        # Filter out 'Uncategorized' if possible for the top topic metric
        filtered_topics = {k: v for k, v in topic_dict.items() if k != "Uncategorized"}
        if filtered_topics:
            top_topic = max(filtered_topics, key=filtered_topics.get)
    
    # --- KPI METRICS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Comments Analyzed", f"{total:,}")
    m2.metric("Positive Sentiment", f"{pos_ratio:.1f}%")
    m3.metric("Dominant Topic", top_topic)
    
    st.divider()
    
    comments = data.get("enriched_comments", [])
    cdf = pd.DataFrame(comments)
    if not cdf.empty and "published_at" in cdf.columns:
        cdf['published_at'] = pd.to_datetime(cdf['published_at'])
    
    # --- CHARTS ROW 1 ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Sentiment Distribution")
        if sentiment_dict:
            sdf = pd.DataFrame(list(sentiment_dict.items()), columns=["Sentiment", "Count"])
            fig_sent = px.pie(
                sdf, 
                names="Sentiment", 
                values="Count",
                color="Sentiment",
                color_discrete_map={"Positive": "#2ca02c", "Negative": "#d62728", "Neutral": "#7f7f7f"},
                hole=0.4
            )
            st.plotly_chart(fig_sent, use_container_width=True)
    
    with c2:
        st.subheader("Topic Clusters")
        if topic_dict:
            tdf = pd.DataFrame(list(topic_dict.items()), columns=["Topic", "Mentions"])
            fig_topics = px.treemap(
                tdf,
                path=["Topic"],
                values="Mentions",
                color="Mentions",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig_topics, use_container_width=True)
            
    # --- CHARTS ROW 2 (Time Series) ---
    if not cdf.empty and "published_at" in cdf.columns:
        st.subheader("Sentiment Trend Over Time")
        # Group by date and sentiment
        cdf['date'] = cdf['published_at'].dt.date
        time_df = cdf.groupby(['date', 'sentiment_label']).size().reset_index(name='count')
        fig_time = px.line(
            time_df, 
            x="date", 
            y="count", 
            color="sentiment_label",
            color_discrete_map={"Positive": "#2ca02c", "Negative": "#d62728", "Neutral": "#7f7f7f"},
            markers=True
        )
        st.plotly_chart(fig_time, use_container_width=True)

    # --- INTERACTIVE DATA EXPLORER ---
    st.divider()
    st.subheader("Data Explorer (Cross-Filtering)")
    
    if not cdf.empty:
        # Filters
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            sent_filter = st.multiselect("Filter by Sentiment", options=cdf['sentiment_label'].unique())
        with f_col2:
            top_filter = st.multiselect("Filter by Topic", options=cdf['topic_name'].unique())
            
        filtered_df = cdf.copy()
        if sent_filter:
            filtered_df = filtered_df[filtered_df['sentiment_label'].isin(sent_filter)]
        if top_filter:
            filtered_df = filtered_df[filtered_df['topic_name'].isin(top_filter)]
            
        # Display dataframe
        display_df = filtered_df[["published_at", "sentiment_label", "topic_name", "clean_text", "comment_id"]]
        display_df.columns = ["Date", "Sentiment", "Assigned Topic", "Clean Text", "Comment ID"]
        st.dataframe(display_df, use_container_width=True, height=400)
