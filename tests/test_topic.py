import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.core.schemas import CleanedComment
from src.agents.topic import run_topic_modeling

def test_run_topic_modeling_too_few_comments():
    # Less than 15 comments should fallback to Uncategorized
    comments = [
        CleanedComment(comment_id=str(i), clean_text=f"Comment {i}", is_valid_for_topic_modeling=True)
        for i in range(5)
    ]
    
    results = run_topic_modeling(comments)
    assert len(results) == 5
    for r in results:
        assert r.topic_id == -1
        assert r.topic_name == "Uncategorized"

@patch("src.agents.topic.BERTopic")
@patch("src.agents.topic.SentenceTransformer")
def test_run_topic_modeling_success(mock_st, mock_bertopic_cls):
    # Setup mock BERTopic instance
    mock_bt_instance = MagicMock()
    mock_bertopic_cls.return_value = mock_bt_instance
    
    # Mock fit_transform returns topics list and probabilities
    # Let's say we have 15 valid comments, they map to topics 0, 1, and -1
    mock_bt_instance.fit_transform.return_value = (
        [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1], 
        None
    )
    
    # Mock get_topic_info DataFrame
    df = pd.DataFrame({
        "Topic": [0, 1, -1],
        "Count": [5, 5, 5],
        "Name": ["0_apple_banana_orange", "1_car_bike_truck", "-1_noise"]
    })
    mock_bt_instance.get_topic_info.return_value = df
    
    # Mock get_topic word tuples
    def get_topic_side_effect(t_id):
        if t_id == 0:
            return [("apple", 0.9), ("banana", 0.8), ("orange", 0.7)]
        elif t_id == 1:
            return [("car", 0.9), ("bike", 0.8), ("truck", 0.7)]
        return []
    
    mock_bt_instance.get_topic.side_effect = get_topic_side_effect
    
    # Create 15 valid comments and 2 invalid comments
    comments = [
        CleanedComment(comment_id=f"v{i}", clean_text=f"Valid {i}", is_valid_for_topic_modeling=True)
        for i in range(15)
    ]
    comments.extend([
        CleanedComment(comment_id="inv1", clean_text="No", is_valid_for_topic_modeling=False),
        CleanedComment(comment_id="inv2", clean_text="Hi", is_valid_for_topic_modeling=False)
    ])
    
    results = run_topic_modeling(comments)
    
    # Total should be 17
    assert len(results) == 17
    
    # Find invalid comments and check if they are uncategorized
    invalid_results = [r for r in results if r.comment_id.startswith("inv")]
    assert len(invalid_results) == 2
    assert all(r.topic_id == -1 for r in invalid_results)
    assert all(r.topic_name == "Uncategorized" for r in invalid_results)
    
    # Find a valid comment mapped to topic 0
    topic_0_results = [r for r in results if r.topic_id == 0]
    assert len(topic_0_results) == 5
    assert topic_0_results[0].topic_name == "Apple, Banana, Orange"
