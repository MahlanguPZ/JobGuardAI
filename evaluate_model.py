import csv
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from ml_model import train

# Load the labelled dataset
dataset = Path("data/jobs.csv")

with dataset.open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))

X = [row["text"] for row in rows]
y = [int(row["fraud"]) for row in rows]

# Separate training data from testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)

# Train only on the training portion
model = train(list(zip(X_train, y_train)))

# Predict the unseen test examples
predictions = model.predict(X_test)

print("\nJOBGUARDAI MACHINE LEARNING EVALUATION")
print("-------------------------------------")
print(f"Total examples: {len(X)}")
print(f"Training examples: {len(X_train)}")
print(f"Testing examples: {len(X_test)}")

print("\nRESULTS")
print(f"Accuracy:  {accuracy_score(y_test, predictions) * 100:.2f}%")
print(f"Precision: {precision_score(y_test, predictions, zero_division=0) * 100:.2f}%")
print(f"Recall:    {recall_score(y_test, predictions, zero_division=0) * 100:.2f}%")
print(f"F1-score:  {f1_score(y_test, predictions, zero_division=0) * 100:.2f}%")

print("\nCLASSIFICATION REPORT")
print(classification_report(
    y_test,
    predictions,
    target_names=["Legitimate", "Fraudulent"],
    zero_division=0,
))

print("\nCONFUSION MATRIX")
print(confusion_matrix(y_test, predictions))