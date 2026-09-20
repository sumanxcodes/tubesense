import asyncio
from collections import Counter

from fastapi import FastAPI, HTTPException

from src.agents.ingestion import run_ingestion
from src.agents.preprocessing import run_preprocessing
from src.agents.sentiment import run_sentiment_analysis
from src.agents.topic import run_topic_modeling
from src.core.schemas import EnrichedComment, FinalResponse, VideoRequest

app = FastAPI(
    title="TubeSense API",
    description="Automated analytics tool for YouTube video comments (Sentiment & Topic Modeling).",
    version="0.1.0"
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/analyze", response_model=FinalResponse)
async def analyze_video(request: VideoRequest):
    try:
        # Agent 2: Ingestion
        # Offload to thread since it makes synchronous HTTP requests
        raw_comments = await asyncio.to_thread(
            run_ingestion, 
            request.video_id, 
            request.max_comments
        )
        
        if not raw_comments:
            raise HTTPException(status_code=404, detail="No comments found or comments are disabled.")

        # Agent 3: Preprocessing
        cleaned_comments = await asyncio.to_thread(
            run_preprocessing, 
            raw_comments
        )

        # Agent 4 & 5: Parallel Execution
        # We run Sentiment and Topic Modeling concurrently
        sentiment_task = asyncio.to_thread(run_sentiment_analysis, cleaned_comments)
        topic_task = asyncio.to_thread(run_topic_modeling, cleaned_comments)
        
        # Wait for both NLP models to finish
        sentiment_outputs, topic_outputs = await asyncio.gather(sentiment_task, topic_task)
        
        # Join data arrays on comment_id
        # We use a dictionary for O(1) lookups
        sentiment_map = {s.comment_id: s.sentiment_label for s in sentiment_outputs}
        topic_map = {t.comment_id: t.topic_name for t in topic_outputs}
        
        enriched_comments = []
        sentiment_counter = Counter()
        topic_counter = Counter()

        for comment in cleaned_comments:
            # Skip completely empty comments from final output
            if not comment.clean_text.strip():
                continue
                
            s_label = sentiment_map.get(comment.comment_id, "Neutral")
            t_name = topic_map.get(comment.comment_id, "Uncategorized")
            
            enriched = EnrichedComment(
                comment_id=comment.comment_id,
                clean_text=comment.clean_text,
                sentiment_label=s_label,
                topic_name=t_name
            )
            enriched_comments.append(enriched)
            
            # Aggregate stats
            sentiment_counter[s_label] += 1
            topic_counter[t_name] += 1

        # Agent 1 Synthesis
        return FinalResponse(
            video_id=request.video_id,
            total_analyzed=len(enriched_comments),
            sentiment_distribution=dict(sentiment_counter),
            topic_clusters=dict(topic_counter),
            enriched_comments=enriched_comments
        )
        
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        # Catch unexpected errors and return as 500
        raise HTTPException(status_code=500, detail=str(e))
