import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib

def train_model(csv_path: str, model_save_path: str):
    print("=" * 70)
    print("🐝 Smart Bee - Training Email Categorizer Model")
    print("=" * 70)
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV data file not found at {csv_path}")
        
    print(f"1. Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Clean text data
    df['email'] = df['email'].fillna('').astype(str)
    df['category'] = df['category'].fillna('').astype(str)
    
    print(f"   Loaded {len(df)} rows.")
    print("   Category class distribution:")
    for cat, count in df['category'].value_counts().items():
        print(f"     - {cat}: {count}")
        
    # Split train/test sets
    print("\n2. Splitting into train and test sets (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        df['email'], df['category'], test_size=0.2, random_state=42, stratify=df['category']
    )
    
    # Build text classification pipeline
    print("\n3. Building TF-IDF Vectorizer + Logistic Regression pipeline...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True
        )),
        ('clf', LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        ))
    ])
    
    # Train the pipeline
    print("4. Training model classifier...")
    pipeline.fit(X_train, y_train)
    print("   Training complete!")
    
    # Evaluate model
    print("\n5. Evaluating model on test set...")
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"   Test Accuracy: {accuracy:.4f}")
    print("\n   Detailed Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the trained model file
    print(f"\n6. Saving trained model to {model_save_path}...")
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    joblib.dump(pipeline, model_save_path)
    print("✅ Model successfully trained and saved!")
    print("=" * 70)

if __name__ == "__main__":
    # Go up 4 levels from train_category.py to reach Desktop/SmartBeee
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    csv_file = os.path.join(base_dir, "email_category.csv")
    model_file = os.path.join(os.path.dirname(__file__), "category_model.joblib")
    
    train_model(csv_file, model_file)
