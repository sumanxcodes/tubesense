from datetime import datetime, timezone

import pytest

from src.core.schemas import RawComment


def test_raw_comment_schema_valid():
    """Test valid instantiation of RawComment schema."""
    comment = RawComment(
        comment_id="Ugz12345",
        author="John Doe",
        text_display="This is a great video!",
        like_count=10,
        published_at=datetime.now(timezone.utc)
    )
    assert comment.comment_id == "Ugz12345"
    assert comment.like_count == 10

def test_raw_comment_schema_missing_fields():
    """Test that missing required fields raise validation error."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RawComment(
            comment_id="Ugz12345",
            # author missing
            text_display="This is a great video!",
            like_count=10,
            published_at=datetime.now(timezone.utc)
        )

def test_raw_comment_schema_edge_cases():
    """Test edge cases like empty strings for author or text."""
    comment = RawComment(
        comment_id="",
        author="",
        text_display="",
        like_count=0,
        published_at=datetime.now(timezone.utc)
    )
    assert comment.author == ""
    assert comment.text_display == ""
