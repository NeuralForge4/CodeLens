
import argparse
from pathlib import Path

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Train an ML code defect classifier."
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="CSV file containing code and label columns."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum number of dataset rows to use."
    )
    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit must be greater than zero.")

    dataset_path = Path(args.csv)

    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    if not {"code", "label"}.issubset(df.columns):
        raise SystemExit("CSV must contain columns named code and label.")

    df = df.dropna(subset=["code", "label"]).head(args.limit).copy()
    df["code"] = df["code"].astype(str).str.strip()

    df = df[df["code"] != ""]

    try:
        df["label"] = pd.to_numeric(df["label"], errors="raise").astype(int)
    except (ValueError, TypeError):
        raise SystemExit("Labels must be integers: 0 or 1.")

    if not set(df["label"].unique()).issubset({0, 1}):
        raise SystemExit("Labels must be 0 (non-defective) or 1 (defective).")

    if df["label"].nunique() != 2:
        raise SystemExit("Dataset must contain both label classes.")

    counts = df["label"].value_counts()

    if counts.min() < 5:
        raise SystemExit(
            "Please provide at least 5 examples for each class."
        )

    X = df["code"]
    y = df["label"]

    print(f"Total code samples: {len(df)}")
    print(f"Non-defective samples: {counts.get(0, 0)}")
    print(f"Defective samples: {counts.get(1, 0)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                analyzer="char",
                ngram_range=(2, 5),
                max_features=30000,
                sublinear_tf=True
            )
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced"
            )
        )
    ])

    print("\nTraining ML classifier...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 
        list(model.classes_).index(1)
    ]

    print("\nAccuracy:", round(accuracy_score(y_test, predictions), 4))
    print("\nClassification report:")
    print(classification_report(y_test, predictions, zero_division=0))

    print("ROC-AUC:", round(roc_auc_score(y_test, probabilities), 4))

    output_dir = Path(__file__).parent / "artifacts"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "defect_classifier.joblib"
    joblib.dump(model, output_file)

    print(f"\nModel saved successfully: {output_file}")


if __name__ == "__main__":
    main()
