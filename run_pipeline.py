import os
import re

from pipeline.data_loader import load_and_clean_dataset
from pipeline.feature_extraction import extract_features_pipeline

clean_data_path = "data/clean_data.csv"

if __name__ == "__main__":
    if not os.path.isfile(clean_data_path):
        load_and_clean_dataset(clean_data_path)

    X_tab, X_ng, labels = extract_features_pipeline(clean_data_path)
    print(X_tab, X_ng, labels)
