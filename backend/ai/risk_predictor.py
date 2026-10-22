from functools import lru_cache
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data" / "processed" / "risk_features.csv"


FEATURES = [
    "Depth",
    "BITDEP",
    "VDEPTH",
    "WOB",
    "TORQUE",
    "TQ_IN_AMPS",
    "TQ_IN_AMPS_AV",
    "FLOWIN",
    "FLOWOUT",
    "MWIN",
    "MWOUT",
    "ECDCS",
    "PUMP",
    "PUMPPOWER",
]

@lru_cache(maxsize=1)
def train_model():

    df = pd.read_csv(DATA_FILE)

    X = df[FEATURES].copy()
    y = df["risk_label"]

    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )

    model = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42,
                class_weight="balanced"
            )
        )
    ])

    model.fit(X, y)

    return model



def predict_risk(model, data):
    X = pd.DataFrame([data], columns=FEATURES)

    X = X.replace([np.inf, -np.inf], np.nan)

    # Explicitly select the probability for risk-positive class 1.
    classifier = model.named_steps["classifier"]
    classes = list(classifier.classes_)

    if 1 not in classes:
        raise ValueError(
            f"Expected risk-positive class 1; model classes are {classes}"
        )

    risk_class_index = classes.index(1)
    probability = model.predict_proba(X)[0][risk_class_index]

    # This is a model score expressed as a percentage,
    # not necessarily a calibrated incident probability.
    probability_percent = float(probability * 100)

    if probability_percent < 30:
        risk_level = "LOW"
    elif probability_percent < 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return probability_percent, risk_level



def main():

    print("=" * 70)
    print("eRTMAC-NWIS | REAL-TIME RISK PREDICTOR")
    print("=" * 70)

    print("\nTraining model...")

    model = train_model()

    print("Model trained successfully.")

    # Example current drilling condition
    sample = {
        "Depth": 1206,
        "BITDEP": 100,
        "VDEPTH": 1077,
        "WOB": 13000,
        "TORQUE": 7,
        "TQ_IN_AMPS": 0,
        "TQ_IN_AMPS_AV": 0,
        "FLOWIN": 0.05,
        "FLOWOUT": 0.0007,
        "MWIN": 1000,
        "MWOUT": 1000,
        "ECDCS": 0,
        "PUMP": 150000,
        "PUMPPOWER": 50,
    }

    probability, risk_level = predict_risk(
        model,
        sample
    )

    print("\n" + "=" * 70)
    print("RISK PREDICTION")
    print("=" * 70)

    print(
        f"\nRisk Probability : {probability:.2f}%"
    )

    print(
        f"Risk Level       : {risk_level}"
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
