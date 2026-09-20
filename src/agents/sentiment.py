
import torch
from transformers import pipeline

from src.core.schemas import CleanedComment, SentimentOutput

# Load the model specified in the PRD.
# We initialize it outside the function so it only loads into memory once when the module is imported.
# It automatically uses the GPU (mps on Mac, cuda on Nvidia) if available.
device = 0 if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else -1)

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
    device=device
)

# Model outputs are typically LABEL_0 (Negative), LABEL_1 (Neutral), LABEL_2 (Positive)
# We will dynamically map them based on the model's config, or hardcode the RoBERTa mappings.
LABEL_MAPPING = {
    "negative": "Negative",
    "neutral": "Neutral",
    "positive": "Positive",
    # Fallbacks for standard label naming
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

def run_sentiment_analysis(comments: list[CleanedComment]) -> list[SentimentOutput]:
    """
    Processes a batch of clean text through the RoBERTa pipeline.
    Maps tensor logits to human-readable string labels with confidence scores.
    """
    if not comments:
        return []

    # Filter out empty texts that might crash the pipeline (just in case)
    # The pipeline accepts a list of strings for batch processing.
    valid_comments = [c for c in comments if c.clean_text.strip()]
    if not valid_comments:
        return []
        
    texts = [c.clean_text for c in valid_comments]
    
    # Run pipeline in batch
    # truncation=True ensures we don't crash on comments exceeding 512 tokens.
    results = sentiment_pipeline(texts, truncation=True, max_length=512)
    
    sentiment_outputs = []
    for comment, result in zip(valid_comments, results):
        raw_label = result['label'].lower()
        mapped_label = LABEL_MAPPING.get(raw_label, "Neutral") # Default to Neutral if unknown
        
        sentiment_outputs.append(
            SentimentOutput(
                comment_id=comment.comment_id,
                sentiment_label=mapped_label,
                confidence_score=float(result['score'])
            )
        )
        
    return sentiment_outputs
