from fastapi import FastAPI
from src.core.schemas import VideoRequest, FinalResponse

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
    # TODO: Orchestrator Logic (Agent 1)
    # 1. Ingestion (Agent 2)
    # 2. Preprocessing (Agent 3)
    # 3. Sentiment Analysis (Agent 4) & Topic Modeling (Agent 5)
    # 4. Join and Return
    
    return FinalResponse(
        video_id=request.video_id,
        total_analyzed=0,
        sentiment_distribution={},
        topic_clusters={},
        enriched_comments=[]
    )
