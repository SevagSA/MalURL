import pandas as pd

from pipeline.features import get_features
from sklearn.feature_extraction.text import TfidfVectorizer


def extract_features_pipeline(df_path):
    df = pd.read_csv(df_path)

    feature_list = [get_features(u) for u in df["url"]]
    X_tabular = pd.DataFrame(feature_list)

    # 3-to-5 letter character n-grams using TF-IDF
    vectorizer = TfidfVectorizer(
        analyzer="char", 
        ngram_range=(3, 5), 
        min_df=3, 
        max_features=300_000
    )
    X_ngram = vectorizer.fit_transform(df["url"])

    return X_tabular, X_ngram, df["type"].values
