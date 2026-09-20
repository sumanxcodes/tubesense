import re

import pandas as pd

from src.core.schemas import CleanedComment, RawComment


def clean_text_string(text: str) -> str:
    """Removes HTML tags and URLs from a string, and strips whitespace."""
    # Remove HTML tags (e.g., <br>, <b>)
    text = re.sub(r'<[^>]*>', ' ', text)
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    # Replace multiple spaces with a single space and strip
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_preprocessing(comments: list[RawComment]) -> list[CleanedComment]:
    """
    Cleans raw comments and evaluates them for topic modeling.
    Uses pandas for efficient vectorized text processing if the dataset is large,
    but falls back to standard Python iteration for simplicity of mapping to Pydantic.
    """
    if not comments:
        return []

    # Convert to DataFrame for potential bulk text cleaning using pandas
    # (Adhering to PRD tech stack requirement: pandas, re)
    df = pd.DataFrame([c.model_dump() for c in comments])
    
    # Vectorized cleaning
    df['clean_text'] = df['text_display'].apply(lambda x: clean_text_string(str(x)))
    
    # Evaluate length (word count >= 3)
    # This prevents BERTopic from crashing on very short or empty strings
    df['word_count'] = df['clean_text'].apply(lambda x: len(x.split()))
    df['is_valid_for_topic_modeling'] = df['word_count'] >= 3

    # Map back to Pydantic CleanedComment schema
    cleaned_comments = []
    for _, row in df.iterrows():
        cleaned_comments.append(
            CleanedComment(
                comment_id=row['comment_id'],
                clean_text=row['clean_text'],
                is_valid_for_topic_modeling=row['is_valid_for_topic_modeling'],
                published_at=row['published_at'],
                like_count=row['like_count']
            )
        )
        
    return cleaned_comments
