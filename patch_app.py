import re
with open("app/app.py", "r") as f:
    app_code = f.read()

# Replace the "CHARTS ROW 2 (Time Series)" section with a TABS approach for Advanced Analytics

tabs_code = """
    st.divider()
    st.subheader("📊 Advanced Analytics")
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
    st.subheader("🏷️ Brand & Entity Radar")
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
    st.subheader("🚀 Creator Action Items")
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
"""

old_time_series = """    # --- CHARTS ROW 2 (Time Series) ---
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
        st.plotly_chart(fig_time, use_container_width=True)"""

app_code = app_code.replace(old_time_series, tabs_code)

# Add intent and entities to Data Explorer dataframe
old_df_cols = """        display_df = filtered_df[["published_at", "sentiment_label", "sentiment_confidence", "topic_name", "like_count", "clean_text"]]"""
new_df_cols = """        display_df = filtered_df[["published_at", "sentiment_label", "sentiment_confidence", "topic_name", "like_count", "intent", "entities", "clean_text"]]"""
app_code = app_code.replace(old_df_cols, new_df_cols)

old_df_display_cols = """        display_df.columns = ["Date", "Sentiment", "AI Confidence", "Assigned Topic", "Likes", "Clean Text"]"""
new_df_display_cols = """        
        # Convert entities list to comma separated string for display
        if 'entities' in display_df.columns:
            display_df['entities'] = display_df['entities'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            
        display_df.columns = ["Date", "Sentiment", "AI Confidence", "Assigned Topic", "Likes", "Intent", "Entities", "Clean Text"]"""
app_code = app_code.replace(old_df_display_cols, new_df_display_cols)


with open("app/app.py", "w") as f:
    f.write(app_code)
