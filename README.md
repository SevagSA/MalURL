# MalURL Guard

Real-time malicious URL detection and traffic filtering system built with **mitmproxy**, **FastAPI**, and a **Character N-gram Machine Learning classifier**, containerized with **Docker Compose**.

---

## Repository Structure

```text
MalURL/
├── backend/                  # FastAPI analysis service
│   ├── app.py                # REST API exposing /health and /analyze
│   ├── Dockerfile            # Backend container definition (Python 3.12)
│   └── requirements.txt      # Backend Python dependencies (scikit-learn==1.9.1)
├── ml/                       # Machine Learning training & inference module
│   ├── __init__.py
│   ├── train.py              # Dataset preprocessing, training, and model export
│   ├── predict.py            # Inference logic & configurable strictness thresholds
│   └── models/
│       └── model.joblib      # Trained pipeline (gitignored — generated locally)
├── proxy/                    # Traffic interception gateway
│   └── malurl_guard.py       # mitmproxy addon forwarding URLs to the backend
├── scripts/
│   └── collect_data.py       # Data collection utilities
├── data/                     # Downloaded & cleaned datasets (gitignored)
├── data_loader.py            # Kaggle dataset downloader and URL normalizer
├── docker-compose.yml        # Multi-container lab setup (Firefox + Proxy + Backend)
└── requirements.txt          # Root Python dependencies for local training
```

> **Note on Ignored Artifacts:** Large binary files and runtime artifacts (`ml/models/model.joblib`, `data/`, `certs/`, `firefox-profile/`) are excluded via `.gitignore`. You must generate `model.joblib` locally before starting the Docker stack.

---

## Prerequisites

* **Docker** and **Docker Compose**
* **Python 3.12+** (for local model training)
* **scikit-learn `1.9.1`** (must match between local training and the Docker container to prevent `joblib` serialization mismatches)

---

## 1. Generating the ML Model (`ml/models/model.joblib`)

Because `model.joblib` is not tracked in Git, generate it once on your machine before running the containers:

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install training dependencies with the exact scikit-learn version
pip install scikit-learn==1.9.1 joblib pandas kagglehub

# 3. Download the dataset, clean URLs, train the pipeline, and export the model
python -m ml.train
```

### What `python -m ml.train` Does
1. Downloads the Malicious URLs dataset (~641k deduplicated URLs across `benign`, `phishing`, `malware`, and `defacement`) via `data_loader.py` and caches it in `data/clean_data.csv`.
2. Strips protocols (`http://`, `https://`), leading `www.`, and trailing slashes so the model cannot rely on protocol presence as a shortcut.
3. Splits train/test sets (`80/20`) using `GroupShuffleSplit` grouped by domain so URLs from the same host never leak across splits.
4. Trains a unified `scikit-learn` `Pipeline`:
   * **Vectorizer:** `TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3, max_features=300_000)`
   * **Classifier:** `LogisticRegression(max_iter=2000, C=5)`
5. Saves the fitted pipeline to `ml/models/model.joblib`.

### Verify Local Inference
```bash
python -c "from ml.predict import predict_url; print(predict_url('https://www.google.com')); print(predict_url('http://paypal-verify-login.xyz/auth'))"
```

---

## 2. Strictness Levels (Decision Thresholds)

`ml/predict.py` computes a continuous malicious probability (`0.0` to `1.0`) and classifies a URL as `"malicious"` when `probability >= threshold`. Three strictness profiles are supported without retraining the model:

| Level | Threshold | Behavior |
| :--- | :---: | :--- |
| **`high`** | `0.30` | **Strict:** Blocks suspicious URLs early; minimizes false negatives at the cost of occasional false positives. |
| **`medium`** | `0.50` | **Balanced (Default):** Standard trade-off between security and browsing experience. |
| **`low`** | `0.75` | **Permissive:** Blocks only high-confidence threats; minimizes false positives on legitimate sites. |

You can configure the strictness level in two ways:
* **Globally via environment variable:** Set `STRICTNESS_LEVEL=high` (or `medium` / `low`) under the `backend` service in `docker-compose.yml`.
* **Per request via API payload:** Pass `"strictness"` in the `POST /analyze` JSON body (overrides the environment default).

---

## 3. Running the Docker Stack

Once `ml/models/model.joblib` exists, build and start the services:

```bash
docker compose up --build
```
### MITM Proxy Test

The mitmproxy addon is located at `proxy/malurl_guard.py`.

For local browser testing, configure Firefox to use the proxy:

```text
HTTP Proxy: 127.0.0.1
Port: 8080
```

If port `8080` is already in use, start the stack with another host port:

```bash
PROXY_PORT=8082 docker compose up --build
```

Then configure Firefox to use:

```text
HTTP Proxy: 127.0.0.1
Port: 8082
```

Import `certs/mitmproxy-ca-cert.pem` into Firefox and trust it to identify websites.

To verify interception, open an HTTPS website and check the proxy logs:

```bash
docker compose logs proxy --tail=30
```

Expected output:

```text
Protocol: https
Host: example.com
URL: https://example.com/
```
### Services & Ports
* **Backend API (`http://localhost:8000`):** FastAPI service loading `/app/ml/models/model.joblib` (interactive docs at `http://localhost:8000/docs`).
* **Proxy (`localhost:8080`):** `mitmproxy` instance intercepting HTTP/HTTPS traffic and querying `http://backend:8000/analyze`.
* **User Browser (`http://localhost:5800`):** Containerized Firefox pre-routed through the proxy for live testing.

### Quick API Test
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "http://paypal-verify-login.xyz/auth", "strictness": "high"}'
```

Expected response:
```json
{
  "prediction": "malicious",
  "probability": 0.9412,
  "strictness": "high",
  "threshold": 0.3
}
```
