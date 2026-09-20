import streamlit as st
import requests

st.title("TubeSense: YouTube Sentiment & Topic Analytics")

video_url = st.text_input("Enter YouTube Video URL")

if st.button("Analyze"):
    if video_url:
        st.write(f"Analyzing {video_url}...")
        # TODO: Parse Video ID and send to FastAPI Backend
    else:
        st.warning("Please enter a valid URL.")
