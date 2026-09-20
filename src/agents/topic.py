from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

from src.core.schemas import CleanedComment, TopicOutput


# Lazy load BERTopic to prevent slow startup times if only other agents are needed.
# Since it loads heavy dependencies, it's better instantiated inside the function
# or loaded at the top if we strictly follow the singleton pattern.
# For API usage, a global instance is preferred if we reuse it, but BERTopic needs to 
# fit dynamically on the specific video's comments every time.
def run_topic_modeling(comments: list[CleanedComment]) -> list[TopicOutput]:
    """
    Discovers latent themes within the comment section dynamically using BERTopic.
    Converts text into vector embeddings, runs UMAP/HDBSCAN clustering, and 
    extracts top representation words to auto-generate topic names.
    Outliers and invalid comments are assigned to 'Uncategorized'.
    """

    # 1. Filter valid comments for modeling
    
    # 1. Filter valid comments for modeling
    valid_comments = [c for c in comments if c.is_valid_for_topic_modeling]
    invalid_comments = [c for c in comments if not c.is_valid_for_topic_modeling]
    
    topic_outputs: list[TopicOutput] = []
    
    # Fast path if there are not enough comments to cluster
    # HDBSCAN typically needs at least a few dozen data points. 
    # If we have very few comments, BERTopic will fail to cluster.
    if len(valid_comments) < 15:
        # Fallback: everything is uncategorized
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
    
    # 2. Initialize Model
    # all-MiniLM-L6-v2 is specifically requested in the PRD for speed & performance
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Use CountVectorizer to remove common English stop words ("the", "and", "your")
    from sklearn.feature_extraction.text import CountVectorizer
    vectorizer_model = CountVectorizer(stop_words="english")
    
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        # We can tune min_topic_size depending on max_comments, but default is usually fine
        min_topic_size=max(5, len(texts) // 50) 
    )
    
    # 3. Fit Model
    topics, _probs = topic_model.fit_transform(texts)
    
    # 4. Generate Topic Names (top 3 words)
    topic_info = topic_model.get_topic_info()
    
    # Create a mapping of topic_id -> topic_name
    topic_mapping = {}
    for _, row in topic_info.iterrows():
        t_id = row['Topic']
        if t_id == -1:
            topic_mapping[t_id] = "Uncategorized"
        else:
            # Extract top words. Name column looks like: "0_word1_word2_word3"
            # We can also get it explicitly from topic_model.get_topic(t_id)
            words = [word for word, _ in topic_model.get_topic(t_id)[:3]]
            topic_mapping[t_id] = ", ".join(words).title()

    # 5. Map results back to valid comments
    for comment, t_id in zip(valid_comments, topics):
        topic_outputs.append(
            TopicOutput(
                comment_id=comment.comment_id,
                topic_id=t_id,
                topic_name=topic_mapping.get(t_id, "Uncategorized")
            )
        )
        
    # 6. Assign invalid comments to Uncategorized
    for comment in invalid_comments:
        topic_outputs.append(
            TopicOutput(
                comment_id=comment.comment_id,
                topic_id=-1,
                topic_name="Uncategorized"
            )
        )
        
    return topic_outputs
