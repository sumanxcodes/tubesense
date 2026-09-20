import re


def extract_intent_and_entities(text: str) -> tuple[str, list[str]]:
    """
    Heuristic-based Intent Classification and Entity Extraction.
    Extremely fast and uses 0 memory compared to LLM/Transformers.
    """
    # 1. Intent Classification
    intent = "Comment"
    lower_text = text.lower()
    
    if "?" in text:
        intent = "Question"
    elif re.search(r'\b(wish|hope|fix|issue|bug|add|make|create|should|sucks|broken|fail)\b', lower_text):
        intent = "Feedback/Request"
    elif re.search(r'\b(love|amazing|great|awesome|perfect|thank|thanks)\b', lower_text):
        intent = "Praise"

    # 2. Entity Extraction (Simple Proper Noun heuristic + Known Tech Brands)
    # Match capitalized words that are > 2 chars, ignoring starting word of sentence
    # This is a rudimentary NER without needing heavy SpaCy/NLTK models
    entities = []
    
    # Known tech domain entities for high accuracy
    known_brands = ['Apple', 'Samsung', 'Google', 'Sony', 'Canon', 'Nikon', 'M1', 'M2', 'M3', 'M4', 'iPhone', 'iPad', 'MacBook', 'Android', 'Windows', 'Tesla', 'DJI']
    
    for brand in known_brands:
        if re.search(rf'\b{brand}\b', text, re.IGNORECASE) and brand not in entities:
            # Normalize to the correct capitalization
            entities.append(brand)
                
    # Also grab other capitalized words (Potential entities)
    # Match words starting with Capital letter, preceded by space (not start of string)
    words = re.findall(r'(?<=\s)[A-Z][a-z]+', text)
    stop_words = {'The', 'This', 'That', 'It', 'He', 'She', 'They', 'We', 'And', 'But', 'Or', 'So', 'If', 'I', 'You'}
    
    for word in words:
        # We don't add too many random capitalized words, let's limit to 3 unknown entities to avoid noise
        if word not in stop_words and word not in entities and len(word) > 2 and len(entities) < 3:
            entities.append(word)

    return intent, entities
