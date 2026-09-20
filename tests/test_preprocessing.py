import pytest
from datetime import datetime
from src.core.schemas import RawComment
from src.agents.preprocessing import run_preprocessing, clean_text_string

def test_clean_text_string():
    # Test HTML removal
    assert clean_text_string("Hello <b>world</b><br>") == "Hello world"
    # Test URL removal
    assert clean_text_string("Check this out: https://youtube.com/watch?v=123") == "Check this out:"
    # Test combination
    assert clean_text_string("Wow <a href='http://link.com'>link</a>") == "Wow link"

def test_run_preprocessing_valid_topic():
    raw_comments = [
        RawComment(
            comment_id="1",
            author="User1",
            text_display="This is a perfectly valid long comment.",
            like_count=0,
            published_at=datetime.now()
        )
    ]
    
    cleaned = run_preprocessing(raw_comments)
    assert len(cleaned) == 1
    assert cleaned[0].clean_text == "This is a perfectly valid long comment."
    assert cleaned[0].is_valid_for_topic_modeling is True

def test_run_preprocessing_invalid_topic():
    raw_comments = [
        RawComment(
            comment_id="2",
            author="User2",
            text_display="Too short",
            like_count=0,
            published_at=datetime.now()
        )
    ]
    
    cleaned = run_preprocessing(raw_comments)
    assert len(cleaned) == 1
    assert cleaned[0].clean_text == "Too short"
    assert cleaned[0].is_valid_for_topic_modeling is False

def test_run_preprocessing_empty_after_clean():
    raw_comments = [
        RawComment(
            comment_id="3",
            author="User3",
            text_display="<br> https://spam.com",
            like_count=0,
            published_at=datetime.now()
        )
    ]
    
    cleaned = run_preprocessing(raw_comments)
    assert len(cleaned) == 1
    assert cleaned[0].clean_text == ""
    assert cleaned[0].is_valid_for_topic_modeling is False
