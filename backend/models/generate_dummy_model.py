import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Sample training data
corpus = [
    # Fake News Headlines / Texts
    "BREAKING: Secret bunker discovered under White House containing alien spaceship!",
    "Miracle cure found: Drank lemon water and cured all diseases in 24 hours!",
    "SHOCKING! Scientists confirm the Earth is actually flat and NASA lied!",
    "Government is spraying mind-control chemicals in all commercial flights.",
    "Billionaire secretly buys all voting machines to rig the next election.",
    "Hollywood celebrities are using secret youth serum made from space rocks.",
    "Breaking News: New law makes it illegal to own dogs starting next month!",
    "Unbelievable: Local man learns to fly by eating only organic mushrooms.",
    "ALERT: Major bank freezes all accounts forever starting tonight at midnight!",
    "Proof: Ancient pyramids were actually wireless energy transmitters.",
    
    # Real News Headlines / Texts
    "Federal Reserve decides to keep interest rates steady after inflation report.",
    "New study finds exercise significantly improves cardiovascular health.",
    "Local community center opens new library wing with funding from city council.",
    "NASA Perseverance rover celebrates two years of exploring Mars surface.",
    "Global climate summit reaches agreement on carbon reduction targets.",
    "Tech company announces new open-source software library for machine learning.",
    "Scientists successfully sequence the genome of rare deep-sea coral species.",
    "Public transport system introduces hybrid electric buses to reduce emissions.",
    "National park reports record-high attendance during the summer season.",
    "University research team develops new efficient solar cell technology."
]

# Labels: 1 for Fake News, 0 for Real News
labels = [1]*10 + [0]*10

def generate_assets():
    print("Training TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
    X = vectorizer.fit_transform(corpus)
    
    print("Training Logistic Regression model...")
    model = LogisticRegression()
    model.fit(X, labels)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model.pkl")
    vectorizer_path = os.path.join(current_dir, "vectorizer.pkl")
    
    print(f"Saving model to {model_path}...")
    joblib.dump(model, model_path)
    
    print(f"Saving vectorizer to {vectorizer_path}...")
    joblib.dump(vectorizer, vectorizer_path)
    
    print("Dummy assets generated successfully!")

if __name__ == "__main__":
    generate_assets()
