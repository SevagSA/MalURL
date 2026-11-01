import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit
from pipeline.features import split_url

def train_and_evaluate(clean_data_path, X_tabular_path, X_ngram_path):
    print("\n--- Starting Model Training & Evaluation ---")
    df = pd.read_csv(clean_data_path)

    text = df["url"]
    labels = df["type"].values

    sites = [split_url(u)[0] for u in df["url"]]
    train_idx, test_idx = next(
        GroupShuffleSplit(test_size=0.2, random_state=42).split(text, labels, groups=sites)
    )

    # MODEL A: Main Model (N-grams + Logistic Regression)
    print("\nTraining Main Model (Character N-grams + Logistic Regression)...")

    vectorizer = joblib.load(X_ngram_path)
    X_ngram_all = vectorizer.fit_transform(text)

    X_train_ng = X_ngram_all[train_idx]
    X_test_ng = X_ngram_all[test_idx]

    lr_model = LogisticRegression(max_iter=2000, C=5)
    lr_model.fit(X_train_ng, labels[train_idx])

    print("\n--- Logistic Regression (N-grams) Results ---")
    preds_lr = lr_model.predict(X_test_ng)
    print(classification_report(labels[test_idx], preds_lr, digits=3))

    # Save trained model
    joblib.dump(lr_model, "env/logistic_regression_ngram.pkl")

    # MODEL B: Baseline Model (Random Forest on Tabular)
    print("\nTraining Baseline Model (Random Forest on Tabular Features)...")
    X_tabular_all = pd.read_csv(X_tabular_path)

    X_train_tab = X_tabular_all.iloc[train_idx]
    X_test_tab = X_tabular_all.iloc[test_idx]

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train_tab, labels[train_idx])

    print("\n--- Random Forest Baseline Results ---")
    preds_rf = rf_model.predict(X_test_tab)
    print(classification_report(labels[test_idx], preds_rf, digits=3))

    joblib.dump(rf_model, "env/random_forest_baseline.pkl")
    print("\n✅ Training complete! All models saved to env/")
