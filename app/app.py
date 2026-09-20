import streamlit as st
import requests
import re
import pandas as pd
import plotly.express as px

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
    # Match standard youtube.com/watch?v= or youtu.be/ formats
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

# User Input
video_url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
max_comments = st.slider("Max Comments to Analyze", min_value=100, max_value=2000, value=500, step=100)

if st.button("Analyze Video"):
    if not video_url:
        st.warning("Please enter a valid YouTube URL.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("Could not extract a valid Video ID from the URL. Please check the format.")
        else:
            with st.spinner(f"Analyzing comments for video '{video_id}'... (This may take a minute)"):
                try:
                    response = requests.post(
                        API_URL, 
                        json={"video_id": video_id, "max_comments": max_comments},
                        timeout=300 # 5 minutes timeout for heavy ML processing
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Analysis complete! Analyzed {data['total_analyzed']} comments.")
                        
                        # Layout with columns
                        col1, col2 = st.columns(2)
                        
                        # 1. Sentiment Distribution
                        with col1:
                            st.subheader("Sentiment Distribution")
                            sentiment_dict = data.get("sentiment_distribution", {})
                            if sentiment_dict:
                                sdf = pd.DataFrame(list(sentiment_dict.items()), columns=["Sentiment", "Count"])
                                fig_sent = px.pie(
                                    sdf, 
                                    names="Sentiment", 
                                    values="Count",
                                    color="Sentiment",
                                    color_discrete_map={
                                        "Positive": "#2ca02c", 
                                        "Negative": "#d62728", 
                                        "Neutral": "#7f7f7f"
                                    },
                                    hole=0.4
                                )
                                st.plotly_chart(fig_sent, use_container_width=True)
                            else:
                                st.info("No sentiment data available.")

                        # 2. Topic Clusters
                        with col2:
                            st.subheader("Discovered Topics")
                            topic_dict = data.get("topic_clusters", {})
                            if topic_dict:
                                tdf = pd.DataFrame(list(topic_dict.items()), columns=["Topic", "Mentions"])
                                # Sort by mentions descending
                                tdf = tdf.sort_values(by="Mentions", ascending=True)
                                fig_topics = px.bar(
                                    tdf, 
                                    x="Mentions", 
                                    y="Topic", 
                                    orientation='h',
                                    color="Mentions",
                                    color_continuous_scale="Blues"
                                )
                                st.plotly_chart(fig_topics, use_container_width=True)
                            else:
                                st.info("No topic data available.")
                                
                        # 3. Data Table
                        st.subheader("Enriched Comments")
                        comments = data.get("enriched_comments", [])
                        if comments:
                            cdf = pd.DataFrame(comments)
                            # Reorder columns for better UX
                            cdf = cdf[["sentiment_label", "topic_name", "clean_text", "comment_id"]]
                            cdf.columns = ["Sentiment", "Assigned Topic", "Clean Text", "Comment ID"]
                            
                            # Add filtering
                            st.dataframe(cdf, use_container_width=True, height=400)
                            
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the backend API. Is FastAPI running? Error: {e}")
