from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

from src.core.schemas import CleanedComment, TopicOutput

# 1. FIX: Instantiate heavy models globally. 
# This prevents a massive memory leak and slow API responses
# by loading the 90MB PyTorch model into RAM exactly once at startup.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def run_topic_modeling(comments: list[CleanedComment]) -> list[TopicOutput]:
    """
    Discovers latent themes within the comment section dynamically using BERTopic.
    Converts text into vector embeddings, runs UMAP/HDBSCAN clustering, and 
    extracts top representation words to auto-generate topic names.
    Outliers and invalid comments are assigned to 'Uncategorized'.
    """

    # Filter valid comments for modeling
    valid_comments = [c for c in comments if c.is_valid_for_topic_modeling]
    invalid_comments = [c for c in comments if not c.is_valid_for_topic_modeling]
    
    topic_outputs: list[TopicOutput] = []
    
    # Fast path if there are not enough comments to cluster
    if len(valid_comments) < 15:
        for c in comments:
            topic_outputs.append(
                TopicOutput(
                    comment_id=c.comment_id,
                    topic_id=-1,
                    topic_name="Uncategorized"
                )
            )
        return topic_outputs

    texts = [c.clean_text for c in valid_comments]
    
    # 2. FIX: Tune UMAP for smaller YouTube-scale datasets (500-2000 comments)
    # n_neighbors=10 (down from 15) preserves local micro-topics better
    umap_model = UMAP(n_neighbors=10, n_components=5, min_dist=0.0, metric='cosine', random_state=42)
    
    # 3. FIX: Add N-grams (1, 2) to capture context like "bad camera" instead of just "bad"
    vectorizer_model = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    
    # Initialize BERTopic
    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        vectorizer_model=vectorizer_model,
        min_topic_size=max(5, len(texts) // 50) 
    )
    
    # Fit Model
    topics, _probs = topic_model.fit_transform(texts)
    
    # Generate Topic Names
    topic_info = topic_model.get_topic_info()
    
    # Create a mapping of topic_id -> topic_name
    topic_mapping = {}
    for _, row in topic_info.iterrows():
        t_id = row['Topic']
        if t_id == -1:
            topic_mapping[t_id] = "Uncategorized"
        else:
            # Extract top words (capturing bigrams makes it more descriptive)
            words = [word for word, _ in topic_model.get_topic(t_id)[:3]]
            topic_mapping[t_id] = ", ".join(words).title()

    # Map results back to valid comments
    for comment, t_id in zip(valid_comments, topics):
        topic_outputs.append(
            TopicOutput(
                comment_id=comment.comment_id,
                topic_id=t_id,
                topic_name=topic_mapping.get(t_id, "Uncategorized")
            )
        )
        
    # Assign invalid comments to Uncategorized
    for comment in invalid_comments:
        topic_outputs.append(
            TopicOutput(
                comment_id=comment.comment_id,
                topic_id=-1,
                topic_name="Uncategorized"
            )
        )
        
    return topic_outputs
