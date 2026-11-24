import os
import re
from urllib.parse import urlparse
import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from data_loader import load_and_clean_dataset
from ml.predict import MODEL_PATH, clean_url

assert sklearn.__version__ == "1.9.1", f"Expected scikit-learn 1.9.1, got {sklearn.__version__}"

CLEAN_DATA_PATH = "data/clean_data.csv"


def _extract_host(cleaned_url: str) -> str:
    host = re.split(r"[/?#]", cleaned_url, maxsplit=1)[0]
    return host or cleaned_url


def train():
    if os.path.isfile(CLEAN_DATA_PATH):
        df = pd.read_csv(CLEAN_DATA_PATH)
    else:
        df = load_and_clean_dataset()
        os.makedirs(os.path.dirname(CLEAN_DATA_PATH), exist_ok=True)
        df.to_csv(CLEAN_DATA_PATH, index=False)

    df = df.dropna(subset=["url", "type"]).copy()
    X = df["url"].astype(str).map(clean_url)
    y = df["type"].astype(str).values

    # Keep domains disjoint between train and test splits
    sites = [_extract_host(u) for u in X]
    train_idx, test_idx = next(
        GroupShuffleSplit(test_size=0.2, random_state=42).split(X, y, groups=sites)
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(3, 5),
                    min_df=3,
                    max_features=300_000,
                ),
            ),
            (
                "clf",
                LogisticRegression(max_iter=2000, C=5),
            ),
        ]
    )

    print("Training Character N-gram + Logistic Regression pipeline...")
    pipeline.fit(X.iloc[train_idx], y[train_idx])

    preds = pipeline.predict(X.iloc[test_idx])
    print("\n--- Evaluation Results ---")
    print(classification_report(y[test_idx], preds, digits=3))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH, compress=3)
    size_mb = MODEL_PATH.stat().st_size / (1024 * 1024)
    print(f"Saved model to {MODEL_PATH} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    train()