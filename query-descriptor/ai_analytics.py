import pandas as pd
import streamlit as st

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


MODEL_NAME = "all-MiniLM-L6-v2"


@st.cache_resource
def load_model():
    return SentenceTransformer(MODEL_NAME)


def get_cluster_keywords(texts, top_n=5):
    """
    Extract the most important words from a group of queries.
    """

    if not texts:
        return []

    texts = [str(text) for text in texts if str(text).strip()]

    if not texts:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=1000,
        ngram_range=(1, 2)
    )

    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []

    scores = matrix.mean(axis=0).A1
    words = vectorizer.get_feature_names_out()

    ranked = scores.argsort()[::-1]

    keywords = []

    for index in ranked:
        word = words[index]

        if word not in keywords:
            keywords.append(word)

        if len(keywords) >= top_n:
            break

    return keywords


def create_cluster_name(keywords):
    """
    Convert keywords into a human-readable cluster title.
    """

    if not keywords:
        return "General Queries"

    formatted = [
        word.title()
        for word in keywords[:3]
    ]

    return " & ".join(formatted)


def analyze_queries(records, n_clusters=4):

    df = pd.DataFrame(records)

    if df.empty:
        return df

    # Clean text
    df["title"] = df["title"].fillna("").astype(str)
    df["description"] = df["description"].fillna("").astype(str)

    df["text"] = (
        df["title"] + ". " + df["description"]
    ).str.strip()

    # Remove completely empty queries
    df = df[df["text"].str.strip().ne("")].copy()

    if len(df) < 2:
        return df

    # Don't create more clusters than queries
    n_clusters = min(n_clusters, len(df))

    # Load pretrained Sentence Transformer
    model = load_model()

    # Generate semantic embeddings
    embeddings = model.encode(
        df["text"].tolist(),
        show_progress_bar=False,
        normalize_embeddings=True
    )

    # K-Means clustering
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    df["cluster"] = kmeans.fit_predict(embeddings)

    # Generate readable information for every cluster
    cluster_info = {}

    for cluster_id in sorted(df["cluster"].unique()):

        cluster_df = df[df["cluster"] == cluster_id]

        cluster_texts = cluster_df["text"].tolist()

        keywords = get_cluster_keywords(
            cluster_texts,
            top_n=5
        )

        cluster_name = create_cluster_name(keywords)

        cluster_info[cluster_id] = {
            "name": cluster_name,
            "keywords": keywords,
            "count": len(cluster_df)
        }

    # Add readable names to dataframe
    df["cluster_name"] = df["cluster"].map(
        lambda x: cluster_info[x]["name"]
    )

    df["cluster_keywords"] = df["cluster"].map(
        lambda x: ", ".join(cluster_info[x]["keywords"])
    )

    return df
