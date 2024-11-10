from sklearn.feature_extraction.text import TfidfVectorizer

def extract_key_concepts(text):
    """Extract key concepts from the text using TF-IDF."""
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10)
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()[0]
    key_concepts = sorted(zip(feature_names, tfidf_scores), key=lambda x: x[1], reverse=True)
    return key_concepts