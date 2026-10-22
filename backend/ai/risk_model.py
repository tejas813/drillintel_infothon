import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline


DATA_FILE = "data/processed/risk_features.csv"

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

print("=" * 70)
print("eRTMAC-NWIS | SIMPLE RISK PREDICTION MODEL")
print("=" * 70)

df = pd.read_csv(DATA_FILE)

print("\nDataset:", df.shape)

X = df[FEATURES].copy()
y = df["risk_label"]

# Replace infinite values
X = X.replace([np.inf, -np.inf], np.nan)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples :", len(X_test))

# Simple ML pipeline
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

print("\nTraining Random Forest...")

model.fit(X_train, y_train)

print("Training complete.")

# Prediction
y_pred = model.predict(X_test)

print("\n" + "=" * 70)
print("MODEL RESULTS")
print("=" * 70)

print("\nAccuracy:")
print(accuracy_score(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)

# Feature importance
rf = model.named_steps["classifier"]

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": rf.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\nFeature Importance:")
print(importance.to_string(index=False))

# Save importance
importance.to_csv(
    "data/processed/risk_feature_importance.csv",
    index=False
)

print("\nSaved:")
print("data/processed/risk_feature_importance.csv")
