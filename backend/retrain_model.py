import sys, os
sys.path.insert(0, '.')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

import warnings
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings('ignore', category=InconsistentVersionWarning)

import csv, json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import joblib
from collections import Counter

# Inline the curated dataset (same as main.py but standalone for retraining)
CURATED_DATASET = [
    # REAL NEWS baseline
    {"text": "The global semiconductor supply chain is showing signs of recovery as production capacity increases in key Asian hubs.", "label": 0},
    {"text": "NASA's James Webb Space Telescope has captured new high-resolution images of a distant star cluster.", "label": 0},
    {"text": "The European Union has announced a new regulatory framework targeting carbon emissions in industrial manufacturing sectors by the year 2030.", "label": 0},
    {"text": "Major tech firms have agreed to standard ethical protocols for deploying large language models in public-facing customer support systems.", "label": 0},
    {"text": "International energy agencies report a significant rise in global renewable capacity, led by wind and solar installations.", "label": 0},
    {"text": "The national highway authority is launching a major infrastructure upgrade program to replace aging bridges and transit nodes.", "label": 0},
    {"text": "Medical researchers have published promising phase-2 clinical trial results for a new antibody treatment targeting neurodegenerative symptoms.", "label": 0},
    {"text": "The central labor board has approved the arbitration agreement between the cargo transport union and port operations.", "label": 0},
    {"text": "A recent census report indicates that urban outward migration has stabilized, with suburban growth rates matching pre-decade averages.", "label": 0},
    {"text": "Global markets remained stable following the trade coordination meeting between maritime commerce representatives.", "label": 0},
    # Scientific Real
    {"text": "Physicists at the high-energy collider have successfully recorded the decay channels of the Higgs Boson particle.", "label": 0},
    {"text": "Biologists have mapped the complete genomic sequence of an ancient deep-sea organism.", "label": 0},
    {"text": "Astronomers have identified three new Earth-sized exoplanets orbiting a red dwarf star within the habitable zone.", "label": 0},
    {"text": "A new research paper in the journal Nature details the synthesis of a highly stable superconducting material.", "label": 0},
    # Sports / Entertainment Real
    {"text": "Underdog team clinches historic championship victory with a stunning three-point shot in the final two seconds.", "label": 0},
    {"text": "The acclaimed director's new cinematic epic shattered weekend box office records.", "label": 0},
    {"text": "Elite marathon runner sets a new course record at the annual athletic summit, finishing in under two hours.", "label": 0},
    {"text": "The national arts foundation has announced the recipients of this year's creative grants for contemporary theatrical design.", "label": 0},
    # Simple factual Real - CRITICAL for preventing misclassification of basic facts
    {"text": "There are 7 continents in the planet Earth.", "label": 0},
    {"text": "The seven continents are Africa, Antarctica, Asia, Australia, Europe, North America, and South America.", "label": 0},
    {"text": "The Earth orbits the Sun once every 365 days.", "label": 0},
    {"text": "Water is composed of two hydrogen atoms and one oxygen atom, known as H2O.", "label": 0},
    {"text": "The speed of light in a vacuum is approximately 300,000 kilometers per second.", "label": 0},
    {"text": "Humans have 206 bones in the adult human body.", "label": 0},
    {"text": "The Great Wall of China stretches thousands of miles across northern China.", "label": 0},
    {"text": "Mount Everest is the highest mountain on Earth above sea level.", "label": 0},
    {"text": "The Amazon River is the largest river in the world by water discharge volume.", "label": 0},
    {"text": "The capital city of France is Paris.", "label": 0},
    {"text": "The Pacific Ocean is the largest and deepest ocean on Earth.", "label": 0},
    {"text": "Photosynthesis is the process by which plants convert sunlight and carbon dioxide into food.", "label": 0},
    {"text": "The human heart has four chambers: two atria and two ventricles.", "label": 0},
    {"text": "The chemical symbol for gold is Au, derived from the Latin word aurum.", "label": 0},
    {"text": "The Moon is Earth's only natural satellite and orbits the Earth.", "label": 0},
    {"text": "Gravity is the force that attracts two bodies with mass toward each other.", "label": 0},
    {"text": "The United States declared independence from Britain in the year 1776.", "label": 0},
    {"text": "DNA carries the genetic instructions for the development and function of living organisms.", "label": 0},
    {"text": "The average human body temperature is approximately 37 degrees Celsius or 98.6 degrees Fahrenheit.", "label": 0},
    {"text": "The Sun is a star located at the center of our solar system and provides light and heat to Earth.", "label": 0},
    # FAKE NEWS baseline
    {"text": "SHOCKING PROOF: Secret underground tunnels beneath major cities are being used to transport extinct dinosaurs!", "label": 1},
    {"text": "URGENT ALARM: Eating raw broccoli makes you completely immune to gravity within three days!", "label": 1},
    {"text": "CONFIRMED: The ocean water is slowly being replaced with thick gelatin by covert billionaires!", "label": 1},
    {"text": "LEAKED: Top military generals confirm a massive cloud of sleeping gas will be released tomorrow at midnight!", "label": 1},
    {"text": "NASA INSIDER EXPOSES: The sun is actually a giant projection light bulb and engineers plan a global black-out!", "label": 1},
    {"text": "MIRACLE TREATMENT: A secret herb completely cures every human disease instantly, but doctors hide it!", "label": 1},
    {"text": "CAUTION: Alien transmissions reveal extraterrestrials are planning to turn the moon into a giant disco ball!", "label": 1},
    {"text": "ALERT: Leaked secret files reveal streetlights are high-intensity neural beams designed to erase your memory!", "label": 1},
    {"text": "BREAKING: Scientists secretly created a portal to a parallel universe where gold grows on trees!", "label": 1},
    {"text": "CONFIRMED: A massive magnetic wave will permanently turn all plastics back into crude oil by next Friday!", "label": 1},
    # Satire / Parody Fake
    {"text": "Satire: Local cat successfully negotiates union contract for three extra hours of daily naps and premium salmon treats.", "label": 1},
    {"text": "ABSURD: Nationwide study reveals that looking at pictures of puppies for ten minutes counts as a full cardio workout!", "label": 1},
    {"text": "HUMOR: City council approves plan to replace all asphalt roads with giant bubble wrap to reduce traffic stress.", "label": 1},
    {"text": "PARODY: Tech company launches smart fork that locks itself if you try to eat dessert before dinner.", "label": 1},
    # Fabricated testimonies Fake
    {"text": "EXCLUSIVE: Tech CEO claims in private email that his company's new smartphones will automatically double as personal time machines!", "label": 1},
    {"text": "LEAKED TRANSCRIPT: World leaders secretly agree to replace all paper currency with sea shells by next month!", "label": 1},
    {"text": "CONFIRMED: Prime Minister declares in secret interview that gravity will be temporarily turned down on Wednesday for routine maintenance.", "label": 1},
    {"text": "ALERT: Famous actor reveals he discovered a secret code in cereal boxes that predicts the future!", "label": 1},
]

print(f'Total training samples: {len(CURATED_DATASET)}')
label_counts = Counter(item["label"] for item in CURATED_DATASET)
print(f'Label distribution: Real={label_counts[0]}, Fake={label_counts[1]}')

X = [item["text"] for item in CURATED_DATASET]
y = [item["label"] for item in CURATED_DATASET]

pipeline = Pipeline([
    ('vectorizer', TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=15000, lowercase=True)),
    ('clf', LogisticRegression(C=2.5, max_iter=1000, solver='liblinear', random_state=42))
])
pipeline.fit(X, y)

# Test specific cases
test_cases = [
    ('there are 7 continents in the planet earth', 0),
    ('water is H2O', 0),
    ('The earth orbits the sun', 0),
    ('The capital of France is Paris', 0),
    ('SHOCKING: Aliens are replacing politicians with robots!!!', 1),
    ('The Federal Reserve kept interest rates steady.', 0),
    ('LEAKED: Secret government plan to replace all mayors with androids!', 1),
]
print()
print('--- Test Cases ---')
all_ok = True
for text, expected in test_cases:
    pred = int(pipeline.predict([text])[0])
    prob = pipeline.predict_proba([text])[0]
    pred_name = 'Fake' if pred == 1 else 'Real'
    expected_name = 'Fake' if expected == 1 else 'Real'
    ok = pred == expected
    if not ok:
        all_ok = False
    status = 'OK' if ok else 'FAIL'
    print(f'  [{status}] "{text[:55]}" -> {pred_name} ({max(prob)*100:.1f}%) [expected {expected_name}]')

# Save model
model_dir = os.path.join('..', 'models')
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, 'text_clf_model.pkl')
joblib.dump(pipeline, model_path)

# Save trained texts
texts_path = os.path.join(model_dir, 'trained_texts.json')
with open(texts_path, 'w', encoding='utf-8') as f:
    json.dump(X, f, ensure_ascii=False, indent=2)

print()
print(f'Model saved to: {model_path}')
print(f'All tests passed: {all_ok}')
