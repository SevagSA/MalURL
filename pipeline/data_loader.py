import os
import shutil
import kagglehub
import pandas as pd

from utils import clean_url

dir_path = "data/"
raw_file_path = "data/raw_malicious_phish.csv"


def _load_data_from_kaggle():
    os.makedirs(dir_path, exist_ok=True)
    download_path = kagglehub.dataset_download("sid321axn/malicious-urls-dataset")

    files = os.listdir(download_path)
    if not files:
        raise FileNotFoundError("No files found in the downloaded dataset path.")

    source_file = os.path.join(download_path, files[0])

    shutil.copy2(source_file, raw_file_path)
    print(f"Dataset saved to: {raw_file_path}")


def load_and_clean_dataset(clean_data_path):
    _load_data_from_kaggle()
    df = pd.read_csv(raw_file_path)

    initial_count = len(df)
    df = df.drop_duplicates(subset=["url"])
    print(f"Removed {initial_count - len(df)} duplicates. Shape: {df.shape}")

    class_counts = df["type"].value_counts()
    print("Class Counts:")
    print(class_counts)

    print("\nPercentage breakdown:")
    print((class_counts / len(df)) * 100)

    benign_urls = df[df["type"] == "benign"]["url"]
    malware_urls = df[df["type"] == "malware"]["url"]
    benign_has_http = benign_urls.str.startswith(("http://", "https://")).mean() * 100
    malware_has_http = malware_urls.str.startswith(("http://", "https://")).mean() * 100

    print(f"\nBenign URLs starting with http:// or https://: {benign_has_http:.1f}%")
    print(f"Malware URLs starting with http:// or https://: {malware_has_http:.1f}%")
    print("""
        A small percentage of URLs that don't have http nor https are benign.
        If left uncleaned, a naive model would "cheat" by learning that a
        lack of protocol = benign and presence of protocol = malware. So we have to
        clean the urls by removing the protocol."
        """
    )
    df['url'] = df['url'].apply(clean_url)

    df.to_csv(clean_data_path)
    print(f"Data loaded and cleaned: {df}")
