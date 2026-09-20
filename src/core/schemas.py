from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class VideoRequest(BaseModel):
    video_id: str
    max_comments: int = 2000

class RawComment(BaseModel):
    comment_id: str
    author: str
    text_display: str
    like_count: int
    published_at: datetime

class CleanedComment(BaseModel):
    comment_id: str
    clean_text: str 
    is_valid_for_topic_modeling: bool 

class SentimentOutput(BaseModel):
    comment_id: str
    sentiment_label: str 
    confidence_score: float

class TopicOutput(BaseModel):
    comment_id: str
    topic_id: int
    topic_name: str 

class EnrichedComment(BaseModel):
    comment_id: str
    clean_text: str
    sentiment_label: str
    topic_name: str

class FinalResponse(BaseModel):
    video_id: str
    total_analyzed: int
    sentiment_distribution: Dict[str, Any]
    topic_clusters: Dict[str, Any]
    enriched_comments: List[EnrichedComment]
