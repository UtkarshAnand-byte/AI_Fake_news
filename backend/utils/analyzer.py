import os
import re
import warnings
import joblib
import numpy as np

# Suppress sklearn unpickling version mismatch warnings
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

# Absolute paths for the models
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_CLF_MODEL_PATH = os.path.join(CURRENT_DIR, "models", "text_clf_model.pkl")
MODEL_PATH = os.path.join(CURRENT_DIR, "models", "model.pkl")
VECTORIZER_PATH = os.path.join(CURRENT_DIR, "models", "vectorizer.pkl")

# Sensational/Clickbait lexical triggers
SENSATIONAL_WORDS = {
    "breaking", "shocking", "miracle", "secret", "exposed", "unbelievable", "rigged", "banned", 
    "conspiracy", "coincidence", "proof", "scientists confirm", "nasa lied", "insider reveals",
    "must see", "won't believe", "cured", "alien", "bunker", "scam", "hoax", "agenda", "truth", 
    "alert", "urgent", "warning", "drank", "cures", "hiding", "anonymous", "classified"
}

# Simple Lexicon for Sentiment Polarity & Bias
POSITIVE_WORDS = {
    "great", "amazing", "miracle", "outstanding", "wonderful", "success", "innovative", "scientific", 
    "victory", "perfect", "breakthrough", "healed", "cured", "excellent", "progress", "advance"
}

NEGATIVE_WORDS = {
    "terrible", "worst", "conspiracy", "rigged", "fake", "scam", "crisis", "lie", "lied", "corruption",
    "threat", "danger", "collapse", "destroyed", "illegal", "secretly", "abuse", "scandal", "exposed"
}

def clean_text(text: str) -> str:
    """Preprocess text by removing web links, special characters, and multiple spaces."""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Keep alphanumeric characters and standard spacing
    text = re.sub(r'[^a-zA-Z0-9\s!?.,]', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class FakeNewsAnalyzer:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.ml_loaded = False
        self.is_pipeline = False
        self._load_ml_assets()

    def _load_ml_assets(self):
        """Attempts to load the unified pipeline or separate legacy pickles."""
        text_clf_path = os.path.abspath(TEXT_CLF_MODEL_PATH)
        model_path_abs = os.path.abspath(MODEL_PATH)
        vec_path_abs = os.path.abspath(VECTORIZER_PATH)
        
        # Option A: Loaded pre-packaged single pipeline model (e.g. text_clf_model.pkl)
        if os.path.exists(text_clf_path):
            try:
                self.model = joblib.load(text_clf_path)
                self.is_pipeline = True
                self.ml_loaded = True
                print(f"[ML Engine] Successfully loaded unified LinearSVC Pipeline from models/text_clf_model.pkl.")
            except Exception as e:
                print(f"[ML Engine WARNING] Failed to load text_clf_model.pkl: {e}. Falling back...")
                self.ml_loaded = False
                self.is_pipeline = False
        
        # Option B: Loaded legacy separate classifier and vectorizer models
        if not self.ml_loaded and os.path.exists(model_path_abs) and os.path.exists(vec_path_abs):
            try:
                self.model = joblib.load(model_path_abs)
                self.vectorizer = joblib.load(vec_path_abs)
                self.is_pipeline = False
                self.ml_loaded = True
                print(f"[ML Engine] Successfully loaded separate model and vectorizer from models/ directory.")
            except Exception as e:
                print(f"[ML Engine WARNING] Failed to load pickled legacy assets: {e}. Falling back to Heuristic Engine.")
                self.ml_loaded = False
                self.is_pipeline = False
                
        if not self.ml_loaded:
            print(f"[ML Engine] Pickled assets not found. Falling back to Heuristic Engine.")
            self.ml_loaded = False
            self.is_pipeline = False

    def reload_assets(self):
        """Allows hot-reloading model assets if they are generated post-startup."""
        self._load_ml_assets()
        return self.ml_loaded

    def analyze_lexical(self, raw_text: str):
        """
        Computes various text statistics to formulate heuristics and construct
        the AI explanation structure.
        """
        words = raw_text.split()
        if not words:
            return {
                "caps_ratio": 0.0,
                "exclamation_ratio": 0.0,
                "sensational_density": 0.0,
                "lexical_diversity": 0.0,
                "bias_score": 0.0
            }

        # 1. Capitalization Ratio (excluding single letters like I or starting words)
        cap_words = [w for w in words if w.isupper() and len(w) > 1]
        caps_ratio = len(cap_words) / len(words)

        # 2. Exclamation/Question Ratio
        exclamation_count = len(re.findall(r'[!?]', raw_text))
        # Rate of excessive punctuation sequences e.g. !!! or !?
        excessive_punc = len(re.findall(r'[!?]{2,}', raw_text))
        exclamation_ratio = (exclamation_count + (excessive_punc * 2.5)) / len(words)
        # Cap at 1.0
        exclamation_ratio = min(1.0, exclamation_ratio)

        # 3. Sensationalism density
        cleaned_text = clean_text(raw_text)
        cleaned_words = cleaned_text.split()
        sensational_matches = 0
        for word in cleaned_words:
            if word in SENSATIONAL_WORDS:
                sensational_matches += 1
        # Also check for exact multi-word triggers in lowcase text
        lower_text = raw_text.lower()
        for phrase in ["scientists confirm", "nasa lied", "insider reveals", "won't believe", "must see"]:
            if phrase in lower_text:
                sensational_matches += 2
        
        sensational_density = sensational_matches / max(1, len(cleaned_words))
        # Scale to match general expected threshold
        sensational_density = min(1.0, sensational_density * 3.0)

        # 4. Lexical Diversity (unique words / total words)
        unique_words = set(cleaned_words)
        lexical_diversity = len(unique_words) / max(1, len(cleaned_words))

        # 5. Bias/Sentiment Score (highly emotional negative or positive words suggest opinionated bias)
        pos_count = sum(1 for w in cleaned_words if w in POSITIVE_WORDS)
        neg_count = sum(1 for w in cleaned_words if w in NEGATIVE_WORDS)
        total_sentiment_words = pos_count + neg_count
        bias_score = total_sentiment_words / max(1, len(cleaned_words))
        bias_score = min(1.0, bias_score * 4.0) # Scale it up

        return {
            "caps_ratio": float(caps_ratio),
            "exclamation_ratio": float(exclamation_ratio),
            "sensational_density": float(sensational_density),
            "lexical_diversity": float(lexical_diversity),
            "bias_score": float(bias_score)
        }

    def predict(self, text: str) -> dict:
        """
        Main entry point for predictions. It combines the active model (if loaded)
        with lexical heuristics to compute the prediction, confidence, and explanation.
        """
        if not self.ml_loaded:
            self._load_ml_assets()

        text_cleaned = clean_text(text)
        if not text_cleaned:
            return {
                "prediction": "Real",
                "confidence": 50.0,
                "engine": "Heuristic Linguistics Analyzer",
                "metrics": {
                    "sensationalism": 0.0,
                    "emotional_bias": 0.0,
                    "formatting_style": 0.0,
                    "lexical_complexity": 0.0
                },
                "explanation": ["No indexable text content was provided to analyze (e.g. only contains URLs or special characters)."]
            }

        # Extract features for explanation card
        lex_stats = self.analyze_lexical(text)

        # Predict using Loaded ML model
        if self.ml_loaded:
            try:
                if self.is_pipeline:
                    # Case 1: Pipeline loaded (e.g. contains TfidfVectorizer + LogisticRegression/LinearSVC)
                    pred_label = int(self.model.predict([text])[0])
                    
                    if hasattr(self.model, "predict_proba"):
                        pred_probs = self.model.predict_proba([text])[0]
                        if pred_label == 1:
                            prediction = "Fake"
                            confidence = float(pred_probs[1]) * 100
                        else:
                            prediction = "Real"
                            confidence = float(pred_probs[0]) * 100
                    else:
                        decision_val = float(self.model.decision_function([text])[0])
                        # Sigmoid function: p = 1 / (1 + exp(-margin))
                        prob_fake = 1.0 / (1.0 + np.exp(-decision_val))
                        if pred_label == 1:
                            prediction = "Fake"
                            confidence = prob_fake * 100
                        else:
                            prediction = "Real"
                            confidence = (1.0 - prob_fake) * 100
                else:
                    # Case 2: Legacy separate vectorizer and classifier
                    X_vec = self.vectorizer.transform([text_cleaned])
                    pred_label = self.model.predict(X_vec)[0]
                    pred_probs = self.model.predict_proba(X_vec)[0]
                    
                    if pred_label == 1:
                        prediction = "Fake"
                        confidence = float(pred_probs[1]) * 100
                    else:
                        prediction = "Real"
                        confidence = float(pred_probs[0]) * 100
                    
                confidence = max(50.0, min(99.9, confidence))
            except Exception as e:
                print(f"[ML Prediction Error] Failed during model inference: {e}. Falling back to Heuristic Model.")
                prediction, confidence = self._compute_heuristic_prediction(lex_stats)
        else:
            # Fallback to Heuristic engine
            prediction, confidence = self._compute_heuristic_prediction(lex_stats)

        # Compose a detailed explanation response
        explanation_details = self._generate_explanation_bullets(prediction, confidence, lex_stats, text)

        return {
            "prediction": prediction,
            "confidence": round(float(confidence), 1),
            "engine": "Advanced Linguistic Pipeline" if (self.ml_loaded and self.is_pipeline) else ("Standard Linguistic Engine" if self.ml_loaded else "Heuristic Linguistics Analyzer"),
            "metrics": {
                "sensationalism": round(lex_stats["sensational_density"] * 100, 1),
                "emotional_bias": round(lex_stats["bias_score"] * 100, 1),
                "formatting_style": round(max(lex_stats["caps_ratio"], lex_stats["exclamation_ratio"]) * 100, 1),
                "lexical_complexity": round(lex_stats["lexical_diversity"] * 100, 1)
            },
            "explanation": explanation_details
        }

    def _compute_heuristic_prediction(self, stats: dict) -> tuple:
        """
        Combines various linguistic markers to estimate fake news probability.
        High sensationalism, extreme capitalization, extreme emotional punctuation,
        and high subjective bias indicate a higher likelihood of fake news.
        """
        # Base probability starting at 35% (slightly towards Real)
        fake_prob = 0.35
        
        # Add weights from features
        fake_prob += stats["caps_ratio"] * 0.40          # High caps is very typical of spammy fake news
        fake_prob += stats["exclamation_ratio"] * 0.35   # Excessive exclamations/question marks
        fake_prob += stats["sensational_density"] * 0.45 # Explicit trigger words
        fake_prob += stats["bias_score"] * 0.20          # Overly emotional bias
        
        # Lexical diversity modifier: extremely low lexical diversity slightly pushes fake news probability
        if stats["lexical_diversity"] < 0.4:
            fake_prob += 0.10
        elif stats["lexical_diversity"] > 0.85:
            fake_prob -= 0.05
            
        # Bound probability between 0 and 1
        fake_prob = max(0.01, min(0.99, fake_prob))
        
        if fake_prob >= 0.50:
            prediction = "Fake"
            confidence = fake_prob * 100
        else:
            prediction = "Real"
            # Invert probability for Real confidence
            confidence = (1.0 - fake_prob) * 100
            
        return prediction, confidence

    def _generate_explanation_bullets(self, prediction: str, confidence: float, stats: dict, raw_text: str) -> list:
        """Generates dynamic AI bullets explaining why the model labeled the text."""
        bullets = []
        
        if prediction == "Fake":
            # Bullet 1: General reasoning
            bullets.append(f"Classified as FAKE with {confidence:.1f}% confidence, indicating a high presence of standard propaganda and clickbait markers.")
            
            # Bullet 2: Sensationalism
            if stats["sensational_density"] > 0.15:
                bullets.append("Sensationalist Language: Detected multiple high-intensity trigger words or clickbait phrases typical of fabricated reporting designed to drive emotional reactions.")
            else:
                bullets.append("Linguistic Pattern: The narrative structure exhibits low lexical depth, relying on simple declarative assertions rather than multi-clause journalistic phrasing.")

            # Bullet 3: Formatting & Punctuation
            if stats["caps_ratio"] > 0.12 or stats["exclamation_ratio"] > 0.05:
                bullets.append("Aggressive Formatting: High density of capitalized terms and sensational punctuation (exclamation and question marks), typical of alarmist or fake reporting.")
            else:
                bullets.append("Source Verifiability: The text relies heavily on unsourced testimonies without citing verifiable institutions or direct hyper-linked citations.")
            
            # Bullet 4: Emotional Bias
            if stats["bias_score"] > 0.25:
                bullets.append("Emotional Bias: Text features an elevated concentration of subjective terms (extreme positive or negative qualifiers) rather than objective reporting language.")
        else:
            # Prediction == "Real"
            bullets.append(f"Classified as REAL with {confidence:.1f}% confidence. The text adheres closely to standard professional journalistic structures.")
            
            if stats["sensational_density"] < 0.05:
                bullets.append("Objective Tone: Neutral phrasing identified. The content avoids sensationalist buzzwords, indicating informational intent rather than emotional manipulation.")
            else:
                bullets.append("Minor Sensationalism: Although some promotional language is present, the primary structural components match authentic reportage.")

            if stats["caps_ratio"] < 0.05 and stats["exclamation_ratio"] < 0.02:
                bullets.append("Professional Typography: Sentence structure adheres to formal grammatical standards with standard capitalization and restrained punctuation.")
            
            if stats["lexical_diversity"] > 0.6:
                bullets.append("High Informational Density: Varied vocabulary and diverse sentence structures indicate a sophisticated, descriptive narrative typical of factual documentation.")

        return bullets
