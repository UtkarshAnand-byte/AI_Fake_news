import os
import io
import warnings
import uvicorn
import csv
import joblib
import json
import html as html_lib
import xml.etree.ElementTree as ET
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from contextlib import asynccontextmanager
import re
import urllib.request
import urllib.parse
import asyncio
import time
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import httpx

# Absolute path configurations for the cache and history CSVs
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BACKEND_DIR, "fake_news_dataset.csv")
HISTORY_PATH = os.path.join(BACKEND_DIR, "user_history.csv")


# Load sensitive environment variables from .env
load_dotenv()

# Suppress sklearn version mismatch warnings for clean console outputs
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from utils.analyzer import FakeNewsAnalyzer, TEXT_CLF_MODEL_PATH
from utils.dataset import CURATED_DATASET
from utils.database import (
    init_db, insert_analysis, get_recent_analyses, clear_all_analyses,
    update_analysis_feedback, get_feedback_training_data
)
from services.gemini_service import GeminiService

def load_csv_training_data(csv_path: str) -> list:
    """
    Loads training data from a CSV file and maps labels to binary format.
    Supports label values: FAKE/SATIRE (-> 1), REAL (-> 0)
    """
    training_data = []
    try:
        if not os.path.exists(csv_path):
            print(f"[CSV Loader] Training CSV file not found at {csv_path}")
            return training_data
            
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"[CSV Loader] CSV file is empty or invalid: {csv_path}")
                return training_data
                
            # Find headline/text column and label column
            headline_col = None
            label_col = None
            
            for col in reader.fieldnames:
                col_lower = col.lower().strip()
                if col_lower in ('headline', 'text', 'article', 'content', 'news', 'body_text'):
                    headline_col = col
                elif col_lower in ('label', 'class', 'category', 'target'):
                    label_col = col
            
            if not headline_col or not label_col:
                print(f"[CSV Loader] Could not find headline/text and label columns in {csv_path}")
                return training_data
            
            for row in reader:
                text_val = row.get(headline_col, "").strip()
                label_val = row.get(label_col, "").strip().upper()
                
                if not text_val:
                    continue
                
                # Map label to binary format: FAKE/SATIRE -> 1, REAL -> 0
                if label_val in ('FAKE', 'SATIRE', '1'):
                    label = 1
                elif label_val in ('REAL', '0'):
                    label = 0
                else:
                    continue  # Skip unparseable labels
                
                training_data.append({
                    "text": text_val,
                    "label": label
                })
        
        print(f"[CSV Loader] Successfully loaded {len(training_data)} training samples from {csv_path}")
        return training_data
    except Exception as e:
        print(f"[CSV Loader Error] Failed to load CSV training data: {e}")
        return training_data

# Curated, highly representative baseline training dataset for the linguistic engine
# Copy the imported dataset to a local list to allow dynamic extension during lifespan startup without modifying the imported module's state
CURATED_DATASET = list(CURATED_DATASET)

# Initialize global analyzer instance
analyzer = FakeNewsAnalyzer()

# Lifespan manager replaces the deprecated @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connection pools and auto-migrate tables
    init_db()
    
    # Load CSV training data and merge with curated dataset
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(backend_dir, "fake_news_training_data.csv")
    csv_training_data = load_csv_training_data(csv_path)
    
    # Merge CSV data with curated dataset for enhanced training
    if csv_training_data:
        CURATED_DATASET.extend(csv_training_data)
        print(f"[Lifespan Startup] Enhanced CURATED_DATASET with {len(csv_training_data)} CSV samples. Total: {len(CURATED_DATASET)} samples")
    
    # Proactively create the initial trained_texts.json if not present using the CURATED_DATASET
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    trained_texts_path = os.path.join(model_dir, "trained_texts.json")
    if not os.path.exists(trained_texts_path):
        os.makedirs(model_dir, exist_ok=True)
        initial_texts = [item["text"] for item in CURATED_DATASET]
        try:
            with open(trained_texts_path, "w", encoding="utf-8") as f:
                json.dump(initial_texts, f, ensure_ascii=False, indent=2)
            print("[Lifespan Startup] Successfully initialized trained_texts.json corpus cache.")
        except Exception as e:
            print(f"[Lifespan Startup Warning] Failed to write initial trained_texts.json: {e}")
            
    yield
    # Shutdown cleanups can be added here if needed

# Initialize FastAPI App with lifespan context
app = FastAPI(
    title="VeracitySuite API",
    description="Futuristic fake news detection API engine with database persistence.",
    version="1.2.0",
    lifespan=lifespan
)

# Configure CORS to allow any local frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_on_google(headline: str, query_text: str = None) -> dict:
    """
    Verifies a news headline using live Google News RSS feeds and DuckDuckGo search indexes.
    Extracts top search articles, publishers, and snippets asynchronously to serve as grounding context.
    """
    try:
        REPUTABLE_MAPPING = {
            "reuters": "REUTERS",
            "apnews": "AP NEWS",
            "ap news": "AP NEWS",
            "associated press": "AP NEWS",
            "bbc": "BBC NEWS",
            "nytimes": "NEW YORK TIMES",
            "new york times": "NEW YORK TIMES",
            "bloomberg": "BLOOMBERG",
            "wsj": "WALL STREET JOURNAL",
            "wall street journal": "WALL STREET JOURNAL",
            "npr": "NPR",
            "theguardian": "THE GUARDIAN",
            "the guardian": "THE GUARDIAN",
            "guardian": "THE GUARDIAN",
            "cnn": "CNN",
            "washingtonpost": "WASHINGTON POST",
            "washington post": "WASHINGTON POST",
            "afp": "AFP",
            "dw.com": "DEUTSCHE WELLE",
            "dw news": "DEUTSCHE WELLE",
            "deutsche welle": "DEUTSCHE WELLE",
            "aljazeera": "AL JAZEERA",
            "al jazeera": "AL JAZEERA",
            "cnbc": "CNBC",
            "cbs": "CBS NEWS",
            "nbc": "NBC NEWS",
            "abc news": "ABC NEWS",
            "abcnews": "ABC NEWS",
            "fox news": "FOX NEWS",
            "foxnews": "FOX NEWS",
            "forbes": "FORBES",
            "time.com": "TIME",
            "economist": "THE ECONOMIST",
            "politico": "POLITICO",
            "hill": "THE HILL",
            "the hindu": "THE HINDU",
            "thehindu": "THE HINDU",
            "times of india": "TIMES OF INDIA",
            "timesofindia": "TIMES OF INDIA",
            "indian express": "INDIAN EXPRESS",
            "indianexpress": "INDIAN EXPRESS",
            "hindustan times": "HINDUSTAN TIMES",
            "hindustantimes": "HINDUSTAN TIMES",
            "ndtv": "NDTV",
            "livemint": "LIVEMINT",
            "economic times": "ECONOMIC TIMES",
            "economictimes": "ECONOMIC TIMES",
            "press trust of india": "PTI",
            "dd news": "DD NEWS",
            "ddnews": "DD NEWS",
        }
        
        # Clean headline or query text for searching
        if query_text:
            query_text = query_text.strip()
            
        if not query_text:
            cleaned_hl = re.sub(r'[^a-zA-Z0-9\s]', '', headline)
            words = cleaned_hl.split()
            # Keep first 12 words to avoid search query length limits
            query_text = " ".join(words[:12])
        
        if not query_text.strip():
            return {
                "search_performed": False,
                "verification_score": 0.0,
                "status": "Headline empty or contained only special characters.",
                "outlets_found": [],
                "query_url": "",
                "search_results": []
            }
            
        query = urllib.parse.quote_plus(query_text)
        search_engine_used = "Google News + DuckDuckGo"
        query_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        ddg_url = f"https://html.duckduckgo.com/html/?q={query}"
        search_results = []
        found_outlets = []
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        # Perform asynchronous network queries concurrently
        async with httpx.AsyncClient(headers=headers, timeout=3.0, follow_redirects=True) as client:
            tasks = [
                client.get(query_url),
                client.get(ddg_url)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
        # 1. Parse Google News RSS Feed (Response 0)
        google_res = responses[0]
        if isinstance(google_res, httpx.Response) and google_res.status_code == 200:
            try:
                xml_content = google_res.content
                root = ET.fromstring(xml_content)
                items = root.findall('.//item')
                
                for item in items[:4]:
                    title_el  = item.find('title');  title  = (title_el.text  or "") if title_el  is not None else ""
                    link_el   = item.find('link');   link   = (link_el.text   or "") if link_el   is not None else ""
                    source_el = item.find('source'); source = (source_el.text or "") if source_el is not None else ""
                    
                    # Identify reputable publishers directly using REPUTABLE_MAPPING with boundary check
                    source_lower = source.lower()
                    for keyword, clean_name in REPUTABLE_MAPPING.items():
                        if keyword in source_lower:
                            if len(keyword) <= 3:
                                pattern = r'\b' + re.escape(keyword) + r'\b'
                                if not re.search(pattern, source_lower):
                                    continue
                            if clean_name not in found_outlets:
                                found_outlets.append(clean_name)
                    
                    # Extract actual snippet from <description> tag
                    desc_el = item.find('description')
                    desc_html = (desc_el.text or "") if desc_el is not None else ""
                    desc_text = re.sub(r'<.*?>', '', desc_html).strip()
                    desc_text = re.sub(r'\s+', ' ', desc_text)
                    
                    # Filter out useless RSS feed footers
                    if "Google News" in desc_text and len(desc_text) < 40:
                        desc_text = ""
                        
                    snippet = desc_text if len(desc_text) > 10 else f"Verified news coverage reported by {source} on Google News RSS index."
                                
                    # Push to search results
                    search_results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": link,
                        "engine": "Google News"
                    })
            except Exception as e:
                print(f"[Google Verification Warning] Google News RSS parse failed: {e}")
        elif isinstance(google_res, Exception):
            print(f"[Google Verification Warning] Google News RSS query failed: {google_res}")
            
        # 2. Parse DuckDuckGo Web Feed (Response 1)
        ddg_res = responses[1]
        if isinstance(ddg_res, httpx.Response) and ddg_res.status_code == 200:
            try:
                ddg_html = ddg_res.text
                
                # Extract top DuckDuckGo search result links, titles, and snippets
                titles_matches = re.findall(r'<a[^>]*class=["\']result__a["\'][^>]*>(.*?)</a>', ddg_html, re.DOTALL)
                snippets_matches = re.findall(r'<a[^>]*class=["\']result__snippet["\'][^>]*>(.*?)</a>', ddg_html, re.DOTALL)
                if not snippets_matches:
                    snippets_matches = re.findall(r'<td[^>]*class=["\']result-snippet["\'][^>]*>(.*?)</td>', ddg_html, re.DOTALL)
                    
                # Extract URLs
                urls_matches = []
                for a_tag in re.findall(r'<a[^>]*class=["\']result__a["\'][^>]*>', ddg_html):
                    url_match = re.search(r'uddg=(https?%3A%2F%2F[^&"\'>\s]+)', a_tag)
                    if url_match:
                        decoded_url = urllib.parse.unquote(url_match.group(1))
                        urls_matches.append(decoded_url)
                    else:
                        urls_matches.append("")
                
                # Parse DDG items
                for i in range(min(4, len(titles_matches))):
                    title = re.sub(r'<.*?>', '', titles_matches[i]).strip()
                    snippet = ""
                    if i < len(snippets_matches):
                        snippet = re.sub(r'<.*?>', '', snippets_matches[i]).strip()
                    url = ""
                    if i < len(urls_matches):
                        url = urls_matches[i]
                        
                    # Collect domain for reputable outlet verification using REPUTABLE_MAPPING
                    if url:
                        domain_match = re.search(r'https?://([^/]+)', url)
                        if domain_match:
                            domain = domain_match.group(1).lower().replace("www.", "")
                            for keyword, clean_name in REPUTABLE_MAPPING.items():
                                if keyword.replace(" ", "") in domain.replace(".", ""):
                                    if clean_name not in found_outlets:
                                        found_outlets.append(clean_name)
                                        
                    # Unescape HTML entities
                    title = html_lib.unescape(title)
                    snippet = html_lib.unescape(snippet)
                    for old, new in [("&quot;", '"'), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&#39;", "'")]:
                        title = title.replace(old, new)
                        snippet = snippet.replace(old, new)
                        
                    # Append to search_results if we don't already have too many
                    if len(search_results) < 8:
                        search_results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": url,
                            "engine": "DuckDuckGo Web"
                        })
            except Exception as e:
                print(f"[Google Verification Warning] DuckDuckGo parse failed: {e}")
        elif isinstance(ddg_res, Exception):
            print(f"[Google Verification Warning] DuckDuckGo fallback query failed: {ddg_res}")
            
        # 3. ADVANCED VERIFICATION SCORING ENGINE
        total_results = len(search_results)
        if total_results == 0:
            score = 25.0
            status = "No reputable cross-references found on live Google News or Web search indexes."
        else:
            # A. Calculate term overlap between query and result titles (excluding common stop words)
            query_words = set(query_text.lower().split())
            STOP_WORDS = {
                "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be", "been", "being",
                "to", "of", "in", "for", "on", "with", "at", "by", "from", "up", "about", "into", "over", "after"
            }
            query_words = query_words.difference(STOP_WORDS)
            
            title_similarities = []
            for res in search_results:
                title_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', res['title'].lower()).split()).difference(STOP_WORDS)
                if query_words and title_words:
                    overlap = len(query_words.intersection(title_words)) / len(query_words)
                    title_similarities.append(overlap)
            
            avg_similarity = sum(title_similarities) / len(title_similarities) if title_similarities else 0.0
            
            # B. Weighted scoring components
            presence_score = min(40.0, total_results * 8.0)     # Up to 40% for 5+ search results
            relevance_score = min(40.0, avg_similarity * 60.0)  # Up to 40% for high term match overlap
            outlet_bonus = min(20.0, len(found_outlets) * 10.0) # Up to 20% for 2+ reputable publishers
            
            score = min(99.0, 20.0 + presence_score + relevance_score + outlet_bonus)
            
            # C. Formulate descriptive status
            if len(found_outlets) >= 2:
                status = f"High Verification: Verified news coverage confirmed by {', '.join(found_outlets[:2])}."
            elif len(found_outlets) == 1:
                status = f"Verified Coverage: Cross-referenced by {found_outlets[0]}."
            elif score >= 70.0:
                status = "Indexed Coverage: Multiple matching news reports indexed across public feeds."
            else:
                status = "Unverified Search Presence: Low relevance match on public search indexes."
            
        return {
            "search_performed": True,
            "verification_score": round(score, 1),
            "status": status,
            "outlets_found": found_outlets[:4],
            "query_url": query_url,
            "search_results": search_results
        }
        
    except Exception as e:
        print(f"[Google Verification Warning] Query failed: {e}")
        return {
            "search_performed": False,
            "verification_score": 0.0,
            "status": "Verification search indexes unreachable.",
            "outlets_found": [],
            "query_url": "",
            "search_results": []
        }

class PredictionRequest(BaseModel):
    text: str
    source: Optional[str] = ""
    category: Optional[str] = "other"

class PredictionResponse(BaseModel):
    # Compatibility fields to ensure no legacy frontend breaks
    prediction: str
    confidence: float
    engine: str
    metrics: dict
    explanation: list
    google_verification: Optional[dict] = None
    
    # Advanced Gemini integration fields
    final_prediction: str
    final_confidence: float
    ml_result: dict
    gemini_result: dict
    ai_summary: str
    risk_factors: list
    source_reliability: str
    processing_time: str
    
    # Caching status
    status: Optional[str] = None

def sanitize_record(record: dict) -> dict:
    """
    Recursively strips AI-related labels and traces from string values,
    leaving internal dictionary structures and keys fully backwards compatible.
    """
    if not record:
        return record
    
    def recursive_sanitize(obj):
        if isinstance(obj, str):
            s = obj
            # Remove specific brands or references
            s = re.sub(r'(?i)\b(gemini|google|generative\s+ai)\b', 'Cognitive Engine', s)
            # Remove Powered by AI Analysis / AI Analysis
            s = re.sub(r'(?i)\bpowered\s+by\s+ai\s+analysis\b', 'Powered by Cognitive Analysis', s)
            s = re.sub(r'(?i)\bai\s+analysis\b', 'Cognitive Analysis', s)
            # Remove Cognitive AI
            s = re.sub(r'(?i)\bcognitive\s+ai\b', 'Cognitive Engine', s)
            # Remove Machine Learning / Neural references
            s = re.sub(r'(?i)\bsvc\s+neural\s+pipeline\b', 'Linguistic Pipeline', s)
            s = re.sub(r'(?i)\bneural\s+network\b', 'Decision Network', s)
            s = re.sub(r'(?i)\bmachine\s+learning\b', 'Advanced Analytics', s)
            s = re.sub(r'(?i)\bml\s+predictor\b', 'Linguistic Predictor', s)
            s = re.sub(r'(?i)\bml\s+engine\b', 'Linguistic Engine', s)
            s = re.sub(r'(?i)\bml\b', 'Linguistic', s)
            # Remove generic AI/AIFakeNews
            s = re.sub(r'(?i)\baifakenews\b', 'VeracitySuite', s)
            s = re.sub(r'(?i)\bai\b', 'Cognitive Engine', s)
            return s
        elif isinstance(obj, list):
            return [recursive_sanitize(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: recursive_sanitize(value) for key, value in obj.items()}
        return obj

    return recursive_sanitize(record)

def is_in_training_corpus(text: str) -> bool:
    """
    Checks if the given text is an EXACT match in the training corpus.
    Only returns True for very high-confidence exact or near-exact matches (>90% overlap).
    We no longer use loose substring matching since that was bypassing Gemini too aggressively.
    """
    if not text:
        return False
    
    # Normalize input text
    def normalize(s: str) -> str:
        s = s.lower()
        s = re.sub(r'[^a-z0-9]', '', s)
        return s.strip()
        
    normalized_input = normalize(text)
    if not normalized_input or len(normalized_input) < 10:
        return False
        
    # 1. Try reading from trained_texts.json - EXACT matches only
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    trained_texts_path = os.path.join(model_dir, "trained_texts.json")
    if os.path.exists(trained_texts_path):
        try:
            with open(trained_texts_path, "r", encoding="utf-8") as f:
                trained_texts = json.load(f)
            for t in trained_texts:
                norm_t = normalize(t)
                # Only match if texts are nearly identical (exact same normalized string)
                if norm_t == normalized_input:
                    return True
                # High-overlap check: only if one is 95%+ contained in the other AND very long
                if len(norm_t) > 80 and len(normalized_input) > 80:
                    shorter, longer = sorted([norm_t, normalized_input], key=len)
                    if len(shorter) / len(longer) > 0.95 and shorter in longer:
                        return True
        except Exception as e:
            print(f"[Corpus Check Warning] Failed to read trained_texts.json: {e}")
            
    # 2. Fallback to Curated Dataset - EXACT matches only
    for item in CURATED_DATASET:
        norm_t = normalize(item.get("text", ""))
        if norm_t == normalized_input:
            return True
        if len(norm_t) > 80 and len(normalized_input) > 80:
            shorter, longer = sorted([norm_t, normalized_input], key=len)
            if len(shorter) / len(longer) > 0.95 and shorter in longer:
                return True
            
    return False

async def async_predict_and_combine(text: str) -> dict:
    """
    Executes the dual-intelligence pipeline:
    1. Gemini AI is ALWAYS the primary decision engine (never skipped).
    2. ML model runs in parallel as a supplementary signal.
    3. Google search grounding provides live fact-checking context to Gemini.
    4. ML fallback only activates if Gemini fails after exhausting all model retries.
    """
    start_time = time.time()
    
    # 1. Run local lexical metrics and ML prediction in parallel (supplementary signal)
    lex_stats = analyzer.analyze_lexical(text)
    ml_res = analyzer.predict(text)
    
    # 2. Execute Search Verification to scrape live grounding snippets for Gemini context
    google_res = {
        "search_performed": False,
        "verification_score": 0.0,
        "status": "Search verification offline.",
        "outlets_found": [],
        "query_url": "",
        "search_results": []
    }
    
    # Try generating a high-relevance search query using Gemini first
    search_query = None
    try:
        search_query = await GeminiService.generate_search_query(text)
        print(f"[Search Engine] Extracted query: '{search_query}'")
    except Exception as e:
        print(f"[Search Engine Warning] Failed to generate query via Gemini: {e}")
        
    try:
        # Pass both text[:200] (as headline fallback) and the extracted search_query asynchronously
        google_res = await verify_on_google(text[:200], search_query)
    except Exception as e:
        print(f"[Search Engine Warning] Google verification failed: {e}")
        
    search_results = google_res.get("search_results", [])
    
    # 3. Retrieve user correction feedback loop for Gemini active-learning context
    feedback_samples = []
    try:
        feedback_samples = get_feedback_training_data()
    except Exception as e:
        print(f"[Feedback Warning] Failed to fetch dynamic active-learning corrections: {e}")
        
    # 4. ALWAYS call Gemini first — it is the primary verdict engine
    cognitive_result = None
    cognitive_error = None
    gemini_was_used = False
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        try:
            cognitive_result = await GeminiService.analyze_article(
                text, 
                search_results=search_results, 
                feedback_samples=feedback_samples
            )
            gemini_was_used = True
        except Exception as e:
            print(f"[Cognitive Service Warning] Prediction failed: {e}")
            cognitive_error = str(e)
    else:
        cognitive_error = "API credentials not configured in environment secrets."

    # 5. Only fall back to ML if Gemini completely failed (all models exhausted)
    if cognitive_result is None:
        print(f"[Fallback] Gemini unavailable — using ML fallback. Error: {cognitive_error}")
        cognitive_result = {
            "prediction": ml_res["prediction"],
            "confidence": int(ml_res["confidence"]),
            "bias_detected": lex_stats["bias_score"] > 0.35,
            "clickbait_score": int(lex_stats["sensational_density"] * 100),
            "emotional_tone": "Neutral (AI offline)",
            "risk_factors": ["Cognitive service unavailable — using linguistic fallback"],
            "explanation": f"Cognitive service was offline: {cognitive_error or 'Connection timeout'}. Using linguistic model as fallback."
        }
        gemini_was_used = False
        
    # Verdict Decision is powered by the deep Cognitive Engine for maximum accuracy!
    final_prediction = cognitive_result["prediction"]
    final_confidence = float(cognitive_result["confidence"])
    
    # Measure processing time
    elapsed = time.time() - start_time
    processing_time_str = f"{elapsed:.2f}s"
    
    # Synthesize risk factors
    combined_risk_factors = []
    if ml_res["metrics"]["sensationalism"] > 55.0:
        combined_risk_factors.append("Sensationalist lexical triggers found")
    if ml_res["metrics"]["emotional_bias"] > 50.0:
        combined_risk_factors.append("Subjective sentiment density")
        
    for rf in cognitive_result.get("risk_factors", []):
        if rf not in combined_risk_factors:
            combined_risk_factors.append(rf)
            
    # Source Reliability
    google_score = google_res.get("verification_score", 0.0)
    if google_score >= 85:
        source_reliability = "High (Confirmed by multiple major outlets)"
    elif google_score >= 70:
        source_reliability = "Moderate (Indexed coverage found)"
    elif google_score > 25:
        source_reliability = "Low (Minimal search presence)"
    elif final_prediction == "Fake":
        source_reliability = "Low (Highly suspicious content indicators)"
    else:
        source_reliability = "Unverified (No searchable headlines)"
        
    # Standard dynamic explanation lines
    combined_explanation = [
        f"Verdict engine: Powered strictly by Cognitive Context Engine.",
        f"Linguistic Metrics - Sensationalism: {ml_res['metrics']['sensationalism']}% | Bias: {ml_res['metrics']['emotional_bias']}%",
        google_res.get("status", "Source lookup not indexed.")
    ]
    if cognitive_result.get("explanation"):
        combined_explanation.append(f"Context: {cognitive_result['explanation']}")

    # Formulate metrics block - pack all new fields so they automatically serialize to Neon JSONB!
    packed_metrics = {
        "sensationalism": ml_res["metrics"]["sensationalism"],
        "emotional_bias": ml_res["metrics"]["emotional_bias"],
        "formatting_style": ml_res["metrics"]["formatting_style"],
        "lexical_complexity": ml_res["metrics"]["lexical_complexity"],
        "google_verification": google_res,
        "ml_result": ml_res,
        "final_prediction": final_prediction,
        "final_confidence": round(final_confidence, 1),
        "ai_summary": f"Primary decision is powered strictly by the Cognitive Context Engine. The cognitive analyzer classified this news report as {final_prediction.upper()} with {final_confidence:.0f}% confidence.",
        "risk_factors": combined_risk_factors,
        "source_reliability": source_reliability,
        "processing_time": processing_time_str
    }

    return {
        # Compatibility fields
        "prediction": final_prediction,
        "confidence": round(final_confidence, 1),
        "engine": "Cognitive Context Engine",
        "metrics": packed_metrics,
        "explanation": combined_explanation,
        "google_verification": google_res,
        
        # Upgraded custom response fields
        "final_prediction": final_prediction,
        "final_confidence": round(final_confidence, 1),
        "ml_result": ml_res,
        "gemini_result": cognitive_result,
        "ai_summary": f"Primary decision is powered strictly by the Cognitive Context Engine. The cognitive analyzer classified this news report as {final_prediction.upper()} with {final_confidence:.0f}% confidence. {cognitive_result.get('explanation', '')}".strip(),
        "risk_factors": combined_risk_factors,
        "source_reliability": source_reliability,
        "processing_time": processing_time_str
    }

async def log_to_history(text: str, label: str, status: str, source: str, category: str):
    try:
        hist = pd.read_csv(HISTORY_PATH)
    except FileNotFoundError:
        hist = pd.DataFrame(columns=["text", "label", "status", "source", "category", "timestamp"])
    new = {
        "text": text,
        "label": label,
        "status": status,
        "source": source,
        "category": category,
        "timestamp": datetime.now().isoformat()
    }
    hist = pd.concat([hist, pd.DataFrame([new])], ignore_index=True)
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    hist.to_csv(HISTORY_PATH, index=False)

async def check_and_store(user_input: str, source: str = "", category: str = "other") -> tuple[dict, str]:
    # Load CSV
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["text", "label", "category", "source", "date"])

    # Search for match (fuzzy or exact)
    match = df[df["text"].str.lower().str.contains(user_input[:50].lower(), regex=False, na=False)]

    if not match.empty:
        label = match.iloc[0]["label"]
        # Standardize label output format
        if str(label) == "1" or str(label).upper() in ("FAKE", "SATIRE"):
            label = "Fake"
        elif str(label) == "0" or str(label).upper() == "REAL":
            label = "Real"
            
        status = "FOUND_IN_CSV"
        
        # Build simulated prediction metrics
        lex_stats = analyzer.analyze_lexical(user_input)
        ml_res = analyzer.predict(user_input)
        
        combined_risk_factors = ["Retrieved from local fake news dataset CSV cache"]
        if ml_res["metrics"]["sensationalism"] > 55.0:
            combined_risk_factors.append("Sensationalist lexical triggers found")
        if ml_res["metrics"]["emotional_bias"] > 50.0:
            combined_risk_factors.append("Subjective sentiment density")
            
        packed_metrics = {
            "sensationalism": ml_res["metrics"]["sensationalism"],
            "emotional_bias": ml_res["metrics"]["emotional_bias"],
            "formatting_style": ml_res["metrics"]["formatting_style"],
            "lexical_complexity": ml_res["metrics"]["lexical_complexity"],
            "google_verification": {
                "search_performed": True,
                "verification_score": 99.0 if label == "Real" else 25.0,
                "status": "Verification loaded from historical local cache.",
                "outlets_found": ["LOCAL_DATASET"],
                "query_url": "",
                "search_results": []
            },
            "ml_result": ml_res,
            "final_prediction": label,
            "final_confidence": 99.0,
            "ai_summary": f"Primary decision is powered strictly by the Cognitive Context Engine. This news report was retrieved from the local fake news dataset CSV cache as {label.upper()}.",
            "risk_factors": combined_risk_factors,
            "source_reliability": "Verified (Local Cache)" if label == "Real" else "Low (Local Cache)",
            "processing_time": "0.00s (Cache Hit)"
        }
        
        result = {
            "prediction": label,
            "confidence": 99.0,
            "engine": "Cognitive Context Engine (CSV Cache)",
            "metrics": packed_metrics,
            "explanation": [
                "Verdict engine: Loaded from local dataset cache.",
                f"Linguistic Metrics - Sensationalism: {ml_res['metrics']['sensationalism']}% | Bias: {ml_res['metrics']['emotional_bias']}%",
                "Source status: Verified in local historical dataset."
            ],
            "google_verification": {
                "search_performed": True,
                "verification_score": 99.0 if label == "Real" else 25.0,
                "status": "Verification loaded from historical local cache.",
                "outlets_found": ["LOCAL_DATASET"],
                "query_url": "",
                "search_results": []
            },
            "final_prediction": label,
            "final_confidence": 99.0,
            "ml_result": ml_res,
            "gemini_result": {
                "prediction": label,
                "confidence": 99,
                "bias_detected": ml_res["metrics"]["emotional_bias"] > 50.0,
                "clickbait_score": int(ml_res["metrics"]["sensationalism"]),
                "emotional_tone": "Sensational" if ml_res["metrics"]["sensationalism"] > 50.0 else "Neutral",
                "risk_factors": combined_risk_factors,
                "explanation": "Cached entry found in fake_news_dataset.csv."
            },
            "ai_summary": f"Primary decision is powered strictly by the Cognitive Context Engine. This news report was retrieved from the local fake news dataset CSV cache as {label.upper()}.",
            "risk_factors": combined_risk_factors,
            "source_reliability": "Verified (Local Cache)" if label == "Real" else "Low (Local Cache)",
            "processing_time": "0.00s (Cache Hit)",
            "status": status
        }
    else:
        # Run normal dual-layer prediction flow
        result = await async_predict_and_combine(user_input)
        label = result["final_prediction"]
        
        # Save new row to the dataset CSV
        new_row = {
            "text": user_input,
            "label": label,
            "category": category,
            "source": source,
            "date": datetime.now().isoformat()
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        df.to_csv(CSV_PATH, index=False)
        status = "AUTO_SAVED"
        result["status"] = status

    # Always log to history CSV
    await log_to_history(user_input, label, status, source, category)
    return result, status

@app.get("/api/health")
def health_check():
    """Health check endpoint and engine status report."""
    ml_loaded = analyzer.reload_assets()  # Check for changes
    return {
        "status": "online",
        "engine": "Advanced Linguistic Pipeline" if (ml_loaded and analyzer.is_pipeline) else ("Standard Linguistic Engine" if ml_loaded else "Heuristic Linguistics Fallback"),
        "model_loaded": ml_loaded,
        "api_version": "1.2.0"
    }

@app.get("/api/history")
def fetch_history(limit: int = 10):
    """
    Fetches recent news analysis history from Neon PostgreSQL database.
    """
    try:
        records = get_recent_analyses(limit)
        return [sanitize_record(r) for r in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history logs: {str(e)}")

@app.delete("/api/history")
def clear_history():
    """
    Clears analysis history logs.
    """
    try:
        success = clear_all_analyses()
        if not success:
            raise HTTPException(status_code=500, detail="Database truncate request failed.")
        return {"status": "success", "message": "History logs database successfully cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")

@app.post("/api/predict", response_model=PredictionResponse)
async def predict_news(request: PredictionRequest):
    """
    Predict whether a given text news headline or article is Fake or Real.
    """
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Input news text cannot be empty.")
    
    try:
        # Run the check_and_store caching/history logging flow
        result, status = await check_and_store(
            request.text,
            source=request.source or "",
            category=request.category or "other"
        )
        
        # Build Title excerpt
        clean_excerpt = request.text.strip().replace("\n", " ")
        title = clean_excerpt[:50] + "..." if len(clean_excerpt) > 50 else clean_excerpt
        
        # Persist results in Neon database - saves all combined details inside the JSONB blocks!
        insert_analysis(
            title=title,
            text=request.text,
            prediction=result["final_prediction"],
            confidence=result["final_confidence"],
            engine=result["engine"],
            metrics=result["metrics"],
            explanation=result["explanation"]
        )
        
        return sanitize_record(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/api/predict-file", response_model=PredictionResponse)
async def predict_news_file(file: UploadFile = File(...)):
    """
    Upload a .txt or .pdf file, extract its text content, and analyze for fake news patterns.
    """
    filename = (file.filename or "").lower()
    text_content = ""

    # Check file size (cap at 5MB for analysis)
    try:
        contents = file.file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds the 5MB limit.")
        
        if filename.endswith('.txt'):
            try:
                text_content = contents.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1
                text_content = contents.decode("latin-1")
        elif filename.endswith('.pdf'):
            try:
                pdf_file = io.BytesIO(contents)
                reader = PdfReader(pdf_file)
                pages_text = []
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                
                text_content = "\n".join(pages_text)
                if not text_content.strip():
                    raise HTTPException(
                        status_code=400, 
                        detail="PDF file does not contain any indexable or readable text content."
                    )
            except Exception as pdf_error:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Could not parse the PDF file: {str(pdf_error)}"
                )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Please upload a .txt or .pdf file."
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    finally:
        file.file.close()

    if not text_content or len(text_content.strip()) < 10:
        raise HTTPException(
            status_code=400, 
            detail="Extracted text is too short or empty. Please supply a more descriptive news report."
        )

    try:
        # Run the check_and_store caching/history logging flow
        result, status = await check_and_store(
            text_content,
            source=f"file:{file.filename}",
            category="other"
        )
        
        # Build Title excerpt from filename
        title = f"[File: {file.filename}]"
        
        # Persist results in Neon database
        insert_analysis(
            title=title,
            text=text_content,
            prediction=result["final_prediction"],
            confidence=result["final_confidence"],
            engine=result["engine"],
            metrics=result["metrics"],
            explanation=result["explanation"]
        )
        
        return sanitize_record(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error during file analysis: {str(e)}")

class FeedbackRequest(BaseModel):
    id: int
    feedback: str

@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest):
    """
    Logs user feedback ('correct' or 'incorrect') for a past prediction.
    """
    try:
        if request.feedback not in ("correct", "incorrect"):
            raise HTTPException(status_code=400, detail="Feedback must be either 'correct' or 'incorrect'.")
        success = update_analysis_feedback(request.id, request.feedback)
        if not success:
            raise HTTPException(status_code=404, detail="Analysis history record not found.")
        return {"status": "success", "message": "Feedback recorded successfully."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

@app.post("/api/train")
async def train_model(
    use_feedback: bool = True,
    file: UploadFile = File(None)
):
    """
    Retrains the Fake News detection classifier.
    Combines the rich curated dataset (including CSV data), user feedback history logs, and optional uploaded CSV files.
    """
    try:
        training_data = []
        
        # 1. Load curated dataset (includes CSV data merged during startup)
        training_data.extend(CURATED_DATASET)
        
        # 2. Also explicitly load CSV data if available and not already in CURATED_DATASET
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(backend_dir, "fake_news_training_data.csv")
        csv_data = load_csv_training_data(csv_path)
        csv_count = len(csv_data)
        
        # Add CSV data only for items that are not already present in training_data
        if csv_data:
            existing_texts = {item["text"].strip().lower() for item in training_data}
            new_csv_items = [
                item for item in csv_data 
                if item["text"].strip().lower() not in existing_texts
            ]
            training_data.extend(new_csv_items)
        
        # 3. Add database feedback data
        feedback_samples_count = 0
        if use_feedback:
            fb_data = get_feedback_training_data()
            training_data.extend(fb_data)
            feedback_samples_count = len(fb_data)
            
        # 4. Handle optional custom CSV upload
        custom_samples_count = 0
        if file:
            filename = file.filename.lower()
            if not filename.endswith('.csv'):
                raise HTTPException(status_code=400, detail="Only CSV files are supported for training data.")
            try:
                contents = await file.read()
                csv_str = contents.decode("utf-8")
                csv_file = io.StringIO(csv_str)
                reader = csv.DictReader(csv_file)
                
                # Identify columns
                fieldnames = reader.fieldnames
                if not fieldnames:
                    raise HTTPException(status_code=400, detail="CSV file is empty.")
                    
                text_col = None
                label_col = None
                
                # Find closest matching column names
                for col in fieldnames:
                    col_lower = col.lower().strip()
                    if col_lower in ('text', 'headline', 'article', 'content', 'news'):
                        text_col = col
                    elif col_lower in ('label', 'class', 'category', 'target', 'fake'):
                        label_col = col
                        
                # Fallbacks
                if not text_col and len(fieldnames) > 0:
                    text_col = fieldnames[0]
                if not label_col and len(fieldnames) > 1:
                    label_col = fieldnames[1]
                    
                if not text_col or not label_col:
                    raise HTTPException(status_code=400, detail="CSV must contain at least a text column and a label column.")
                    
                for row in reader:
                    text_val = row.get(text_col)
                    label_val = row.get(label_col)
                    if text_val and label_val is not None:
                        # Map label to 0 or 1
                        lbl_str = str(label_val).lower().strip()
                        if lbl_str in ('1', 'fake', 'true_fake', 'yes', 'y'):
                            label = 1
                        elif lbl_str in ('0', 'real', 'true_real', 'no', 'n'):
                            label = 0
                        else:
                            continue # Skip unparseable labels
                        training_data.append({"text": text_val, "label": label})
                        custom_samples_count += 1
            except HTTPException as he:
                raise he
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse training CSV: {str(e)}")
                
        # Check if we have enough training samples
        if len(training_data) < 10:
            raise HTTPException(status_code=400, detail="Insufficient training data. Minimum 10 samples required.")
            
        # Extract text and labels
        X = [item["text"] for item in training_data]
        y = [item["label"] for item in training_data]
        
        # 4. Train/Test split for metric reporting
        # If dataset is too small, use full training set for evaluation to avoid empty test sets.
        # Also skip stratification if any class has < 2 samples to prevent ValueError.
        if len(X) >= 20:
            from collections import Counter
            label_counts = Counter(y)
            use_stratify = all(count >= 2 for count in label_counts.values())
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.20, random_state=42,
                stratify=y if use_stratify else None
            )
        else:
            X_train, X_test, y_train, y_test = X, X, y, y
            
        # Create pipeline: TF-IDF Vectorizer + Logistic Regression
        # solver='liblinear' is the most robust choice for text classification with small-medium datasets.
        pipeline = Pipeline([
            ('vectorizer', TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=15000,
                lowercase=True
            )),
            ('clf', LogisticRegression(
                C=2.5,
                max_iter=1000,
                solver='liblinear',
                random_state=42
            ))
        ])
        
        # Fit on training partition
        pipeline.fit(X_train, y_train)
        
        # Predict on test partition to calculate robust evaluation metrics
        y_pred = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Calculate Precision, Recall, F1
        # Use average='weighted' instead of 'binary' to handle cases where y_test has only one class
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )
        
        # Fit final model on ALL data for maximum production accuracy!
        final_pipeline = Pipeline([
            ('vectorizer', TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=15000,
                lowercase=True
            )),
            ('clf', LogisticRegression(
                C=2.5,
                max_iter=1000,
                solver='liblinear',
                random_state=42
            ))
        ])
        final_pipeline.fit(X, y)
        
        # Save pipeline to text_clf_model.pkl
        model_dir = os.path.dirname(TEXT_CLF_MODEL_PATH)
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(final_pipeline, TEXT_CLF_MODEL_PATH)
        
        # Save all trained texts to a json file for corpus lookup
        trained_texts_path = os.path.join(model_dir, "trained_texts.json")
        all_texts = [item["text"] for item in training_data]
        try:
            with open(trained_texts_path, "w", encoding="utf-8") as f:
                json.dump(all_texts, f, ensure_ascii=False, indent=2)
            print("[Retraining API] Successfully updated trained_texts.json corpus cache.")
        except Exception as e:
            print(f"[Retraining API Warning] Failed to update trained_texts.json: {e}")
        
        # Hot-reload model inside the global analyzer instance!
        reload_success = analyzer.reload_assets()
        
        return {
            "status": "success",
            "message": "Engine successfully retrained and hot-swapped in-memory!",
            "reload_success": reload_success,
            "metrics": {
                "accuracy": round(float(accuracy) * 100, 1),
                "precision": round(float(precision) * 100, 1),
                "recall": round(float(recall) * 100, 1),
                "f1_score": round(float(f1) * 100, 1),
                "total_samples": len(X),
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "csv_samples": csv_count,
                "feedback_samples": feedback_samples_count,
                "custom_samples": custom_samples_count
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

# Startup entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
