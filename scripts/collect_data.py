from pathlib import Path

import pandas as pd
from tranco import Tranco


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

BENIGN_LIMIT = 10000


def collect_tranco():
    print("Downloading benign domains from Tranco...")

    tranco = Tranco(
        cache=True,
        cache_dir=str(BASE_DIR / ".tranco")
    )

    latest_list = tranco.list()

    domains = latest_list.top(BENIGN_LIMIT)

    df = pd.DataFrame({
        "url": domains,
        "label": 0,
        "source": "tranco"
    })

    output_file = RAW_DIR / "tranco_benign.csv"

    df.to_csv(output_file, index=False)

    print(f"Saved {len(df)} benign domains.")
    print(f"File: {output_file}")


if __name__ == "__main__":
    collect_tranco()