# Machine Learning Models

Place your trained Fake News classifier pickle files in this directory:
- `model.pkl` - A serialized classification model (e.g. Scikit-Learn's `LogisticRegression`, `MultinomialNB`, or `RandomForestClassifier`).
- `vectorizer.pkl` - A serialized text vectorizer (e.g. Scikit-Learn's `TfidfVectorizer` or `CountVectorizer`).

## Generate a Test Model

If you do not have pre-trained models yet, we have included a script `generate_dummy_model.py` which trains a lightweight `TfidfVectorizer` and `LogisticRegression` model on a sample dataset of real/fake headlines and serializes them.

To run it, install dependencies and run the script:
```bash
pip install scikit-learn joblib
python generate_dummy_model.py
```
After executing, it will produce `model.pkl` and `vectorizer.pkl` in this directory, which the backend will load automatically!
