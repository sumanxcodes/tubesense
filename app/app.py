import re
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Configuration
API_URL = "http://localhost:8000/analyze"


st.set_page_config(
    page_title="TubeSense Analytics",
    page_icon="youtube_searched_for",
    layout="wide"
)

# Inject Custom CSS, Google Fonts, and Material Icons
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons+Round');

/* Global Font */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Premium Metric Cards */
div[data-testid="metric-container"] {
    background: linear-gradient(145deg, #1e1e24 0%, #15151a 100%);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid #2a2a35;
    box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    transition: transform 0.2s ease;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    border-color: #4a4a65;
}

/* Label & Value colors */
div[data-testid="stMetricLabel"] {
    font-weight: 600 !important;
    color: #9ba1a6 !important;
}
div[data-testid="stMetricValue"] {
    font-weight: 700 !important;
    color: #ffffff !important;
}

/* Helper class for Material Icons */
.m-icon {
    font-family: 'Material Icons Round';
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    -webkit-font-feature-settings: 'liga';
    -webkit-font-smoothing: antialiased;
    vertical-align: middle;
    margin-right: 8px;
    color: #ff4b4b;
}

/* Stylish Headers */
h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
}
</style>
''', unsafe_allow_html=True)


st.markdown("<h1><span class=\"m-icon\">troubleshoot</span> TubeSense Analytics</h1>", unsafe_allow_html=True)
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
    # --- EXECUTIVE SUMMARY ---
    st.divider()
    st.markdown("<h3><span class=\"m-icon\">lightbulb</span> Executive Summary</h3>", unsafe_allow_html=True)
    
    comments = data.get("enriched_comments", [])
    cdf = pd.DataFrame(comments)
    if not cdf.empty and "published_at" in cdf.columns:
        cdf['published_at'] = pd.to_datetime(cdf['published_at'])
        
    # Calculate KPIs
    total = data.get("total_analyzed", 0)
    sentiment_dict = data.get("sentiment_distribution", {})
    pos_count = sentiment_dict.get("Positive", 0)
    pos_ratio = (pos_count / total * 100) if total > 0 else 0
    
    topic_dict = data.get("topic_clusters", {})
    top_topic = "None"
    if topic_dict:
        # Filter out 'Uncategorized' if possible for the top topic metric
        filtered_topics = {k: v for k, v in topic_dict.items() if k != "Uncategorized"}
        if filtered_topics:
            top_topic = max(filtered_topics, key=filtered_topics.get)
            
    # Calculate Like-Weighted Sentiment
    if not cdf.empty and "like_count" in cdf.columns:
        total_likes = cdf['like_count'].sum()
        if total_likes > 0:
            pos_likes = cdf[cdf['sentiment_label'] == 'Positive']['like_count'].sum()
            like_weighted_pos_ratio = (pos_likes / total_likes) * 100
        else:
            like_weighted_pos_ratio = pos_ratio
    else:
        like_weighted_pos_ratio = pos_ratio

    # Generate heuristic summary
    overall_vibe = "positive" if pos_ratio > 50 else ("negative" if sentiment_dict.get("Negative", 0) > pos_count else "mixed")
    weighted_vibe = "higher" if like_weighted_pos_ratio > pos_ratio else "lower"
    
    st.info(f"The overall sentiment of this video is **{overall_vibe}**, with **{pos_ratio:.1f}%** of comments being positive. "
            f"The most discussed topic among the audience is **'{top_topic}'**. "
            f"Interestingly, when weighting by comment likes, the positive sentiment is **{weighted_vibe}** at **{like_weighted_pos_ratio:.1f}%**, "
            f"indicating that the 'loudest' opinions {'lean positive' if weighted_vibe == 'higher' else 'lean negative'}.")
    
    st.divider()
    
    # --- KPI METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Comments Analyzed", f"{total:,}")
    m2.metric("Raw Positive Sentiment", f"{pos_ratio:.1f}%")
    m3.metric("Like-Weighted Positive", f"{like_weighted_pos_ratio:.1f}%")
    m4.metric("Dominant Topic", top_topic)
    
    st.divider()
    
    # --- CHARTS ROW 1 ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Sentiment Distribution (Raw)")
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
            

    st.divider()
    st.markdown("<h3><span class=\"m-icon\">analytics</span> Advanced Analytics</h3>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Time Series", "Aspect-Based Sentiment", "Controversy & Engagement"])
    
    with tab1:
        # --- CHARTS ROW 2 (Time Series) ---
        if not cdf.empty and "published_at" in cdf.columns:
            cdf['date'] = cdf['published_at'].dt.date
            time_df = cdf.groupby(['date', 'sentiment_label']).size().reset_index(name='count')
            fig_time = px.line(
                time_df, 
                x="date", 
                y="count", 
                color="sentiment_label",
                color_discrete_map={"Positive": "#2ca02c", "Negative": "#d62728", "Neutral": "#7f7f7f"},
                markers=True,
                title="Sentiment Trend Over Time"
            )
            st.plotly_chart(fig_time, use_container_width=True)

    with tab2:
        # --- ASPECT-BASED SENTIMENT MATRIX ---
        if not cdf.empty and "topic_name" in cdf.columns:
            # Filter out Uncategorized for a cleaner chart
            topic_cdf = cdf[cdf['topic_name'] != "Uncategorized"]
            if not topic_cdf.empty:
                fig_absa = px.histogram(
                    topic_cdf, 
                    x="topic_name", 
                    color="sentiment_label",
                    barmode="stack",
                    histnorm="percent",
                    color_discrete_map={"Positive": "#2ca02c", "Negative": "#d62728", "Neutral": "#7f7f7f"},
                    title="Sentiment Breakdown by Topic (100% Stacked)",
                    labels={"topic_name": "Topic", "sentiment_label": "Sentiment"}
                )
                fig_absa.update_layout(yaxis_title="Percentage (%)")
                st.plotly_chart(fig_absa, use_container_width=True)
            else:
                st.info("Not enough categorized topics to generate ABSA Matrix.")
                
    with tab3:
        # --- CONTROVERSY SCATTER PLOT ---
        if not cdf.empty and "published_at" in cdf.columns and "like_count" in cdf.columns:
            fig_scatter = px.scatter(
                cdf,
                x="published_at",
                y="like_count",
                color="sentiment_label",
                hover_data=["clean_text", "topic_name"],
                color_discrete_map={"Positive": "#2ca02c", "Negative": "#d62728", "Neutral": "#7f7f7f"},
                title="Comment Velocity & Controversy (Likes vs Time)",
                labels={"published_at": "Publish Date", "like_count": "Likes"}
            )
            fig_scatter.update_traces(marker=dict(size=10, opacity=0.7))
            st.plotly_chart(fig_scatter, use_container_width=True)

    # --- ENTITY RADAR ---
    st.divider()
    st.markdown("<h3><span class=\"m-icon\">radar</span> Brand & Entity Radar</h3>", unsafe_allow_html=True)
    if not cdf.empty and "entities" in cdf.columns:
        # Flatten entities
        all_entities = []
        for index, row in cdf.iterrows():
            # If it's a list, extend. If it's a string representation of list, eval it.
            ents = row.get("entities", [])
            if isinstance(ents, list):
                for e in ents:
                    all_entities.append({"Entity": e, "Sentiment": row["sentiment_label"]})
                    
        if all_entities:
            ent_df = pd.DataFrame(all_entities)
            ent_counts = ent_df["Entity"].value_counts().reset_index()
            ent_counts.columns = ["Entity", "Mentions"]
            # Get top 15 entities
            top_ents = ent_counts.head(15)["Entity"].tolist()
            
            top_ent_df = ent_df[ent_df["Entity"].isin(top_ents)]
            
            fig_ents = px.histogram(
                top_ent_df,
                y="Entity",
                color="Sentiment",
                barmode="stack",
                orientation="h",
                color_discrete_map={"Positive": "#2ca02c", "Negative": "#d62728", "Neutral": "#7f7f7f"},
                title="Top Mentioned Brands/Entities & Their Sentiment",
            ).update_layout(yaxis={'categoryorder':'total ascending'})
            
            st.plotly_chart(fig_ents, use_container_width=True)
        else:
            st.info("No notable brands or entities detected in this comment section.")

    # --- ACTION ITEMS ---
    st.divider()
    st.markdown("<h3><span class=\"m-icon\">fact_check</span> Creator Action Items</h3>", unsafe_allow_html=True)
    st.markdown("We've automatically routed comments that require your attention (Questions & Feedback) so you don't have to read through the noise.")
    
    if not cdf.empty and "intent" in cdf.columns:
        action_df = cdf[cdf['intent'].isin(["Question", "Feedback/Request"])]
        if not action_df.empty:
            st.dataframe(
                action_df[["intent", "clean_text", "like_count", "published_at"]].sort_values("like_count", ascending=False),
                use_container_width=True,
                column_config={
                    "clean_text": st.column_config.TextColumn("Comment", width="large"),
                    "intent": "Intent",
                    "like_count": "Likes",
                    "published_at": "Date"
                }
            )
        else:
            st.success("No pressing questions or feedback requests found!")


    # --- INTERACTIVE DATA EXPLORER ---
    st.divider()
    st.markdown("<h3><span class=\"m-icon\">manage_search</span> Data Explorer (Cross-Filtering)</h3>", unsafe_allow_html=True)
    
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
            
        # Add CSV Download Button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"tubesense_export_{data.get('video_id', 'video')}.csv",
            mime="text/csv",
        )
        
        # Display dataframe
        display_df = filtered_df[["published_at", "sentiment_label", "sentiment_confidence", "topic_name", "like_count", "intent", "entities", "clean_text"]]
        
        # Format confidence as percentage string for display
        display_df['sentiment_confidence'] = display_df['sentiment_confidence'].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "N/A")
        
        
        # Convert entities list to comma separated string for display
        if 'entities' in display_df.columns:
            display_df['entities'] = display_df['entities'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            
        display_df.columns = ["Date", "Sentiment", "AI Confidence", "Assigned Topic", "Likes", "Intent", "Entities", "Clean Text"]
        
        event = st.dataframe(
            display_df, 
            use_container_width=True, 
            height=400,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Clean Text": st.column_config.TextColumn(
                    "Clean Text",
                    width="large"
                ),
                "Assigned Topic": st.column_config.TextColumn(
                    "Assigned Topic",
                    width="medium"
                )
            }
        )
        
        # Reading Pane for Full Comment
        if event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_row = display_df.iloc[selected_idx]
            st.markdown("### 💬 Selected Comment Details")
            st.info(f"**Full Text:** {selected_row['Clean Text']}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.caption(f"**Topic:** {selected_row['Assigned Topic']}")
            c2.caption(f"**Sentiment:** {selected_row['Sentiment']} ({selected_row['AI Confidence']})")
            c3.caption(f"**Likes:** {selected_row['Likes']}")
            c4.caption(f"**Date:** {selected_row['Date']}")
