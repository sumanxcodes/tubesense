import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.main import app
from src.core.schemas import RawComment, CleanedComment, SentimentOutput, TopicOutput
from datetime import datetime

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("src.api.main.run_topic_modeling")
@patch("src.api.main.run_sentiment_analysis")
@patch("src.api.main.run_preprocessing")
@patch("src.api.main.run_ingestion")
def test_analyze_video_success(mock_ingestion, mock_preprocessing, mock_sentiment, mock_topic):
    # Mock data
    mock_ingestion.return_value = [
        RawComment(comment_id="1", author="A", text_display="Great", like_count=1, published_at=datetime.now())
    ]
    mock_preprocessing.return_value = [
        CleanedComment(comment_id="1", clean_text="Great", is_valid_for_topic_modeling=True)
    ]
    mock_sentiment.return_value = [
        SentimentOutput(comment_id="1", sentiment_label="Positive", confidence_score=0.9)
    ]
    mock_topic.return_value = [
        TopicOutput(comment_id="1", topic_id=0, topic_name="Good")
    ]
    
    response = client.post("/analyze", json={"video_id": "test_id"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "test_id"
    assert data["total_analyzed"] == 1
    assert data["sentiment_distribution"] == {"Positive": 1}
    assert data["topic_clusters"] == {"Good": 1}
    assert len(data["enriched_comments"]) == 1
    assert data["enriched_comments"][0]["clean_text"] == "Great"

@patch("src.api.main.run_ingestion")
def test_analyze_video_no_comments(mock_ingestion):
    mock_ingestion.return_value = []
    
    response = client.post("/analyze", json={"video_id": "test_id"})
    
    assert response.status_code == 404
    assert "No comments found" in response.json()["detail"]
