import pytest
from unittest.mock import patch
from src.core.schemas import CleanedComment
from src.agents.sentiment import run_sentiment_analysis

@patch("src.agents.sentiment.sentiment_pipeline")
def test_run_sentiment_analysis(mock_pipeline):
    # Setup mock return value
    mock_pipeline.return_value = [
        {"label": "positive", "score": 0.99},
        {"label": "negative", "score": 0.85},
        {"label": "neutral", "score": 0.60}
    ]
    
    comments = [
        CleanedComment(comment_id="1", clean_text="I love this video!", is_valid_for_topic_modeling=True),
        CleanedComment(comment_id="2", clean_text="This is terrible.", is_valid_for_topic_modeling=True),
        CleanedComment(comment_id="3", clean_text="It is okay.", is_valid_for_topic_modeling=True)
    ]
    
    results = run_sentiment_analysis(comments)
    
    assert len(results) == 3
    
    assert results[0].comment_id == "1"
    assert results[0].sentiment_label == "Positive"
    assert results[0].confidence_score == 0.99
    
    assert results[1].sentiment_label == "Negative"
    
    assert results[2].sentiment_label == "Neutral"

def test_run_sentiment_analysis_empty():
    assert run_sentiment_analysis([]) == []
    
    comments = [
        CleanedComment(comment_id="1", clean_text="   ", is_valid_for_topic_modeling=False)
    ]
    assert run_sentiment_analysis(comments) == []
