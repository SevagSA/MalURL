import os
import re

from pipeline.data_loader import load_and_clean_dataset
from pipeline.train_models import train_and_evaluate
from pipeline.feature_extraction import extract_features_pipeline

clean_data_path = "data/clean_data.csv"
X_tabular_path = "data/X_tabular.csv"
X_ngram_path = "data/X_ngram.csv"

if __name__ == "__main__":
    print("Running pipeline")
    if not os.path.isfile(clean_data_path):
        print("Loading and cleaning dataset")
        load_and_clean_dataset(clean_data_path)
    
    if not os.path.isfile(X_tabular_path) or not os.path.isfile(X_ngram_path):
        print("Extracting features from pipeline")
        extract_features_pipeline(
            clean_data_path, X_tabular_path, X_ngram_path
        )

    train_and_evaluate(clean_data_path, X_tabular_path, X_ngram_path)
