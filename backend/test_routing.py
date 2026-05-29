import asyncio
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import async_predict_and_combine, analyzer, init_db, CURATED_DATASET

async def test():
    print("=========================================")
    print("      VeracitySuite Routing Test         ")
    print("=========================================")
    init_db()
    
    # Reload model assets
    analyzer.reload_assets()
    print("Model Loaded:", analyzer.ml_loaded)
    
    # Case 1: Headline from the CURATED_DATASET (inside text_clf_model.pkl training corpus)
    inside_text = CURATED_DATASET[0]["text"] # Semiconductor supply chain
    print(f"\n[Case 1: INSIDE CORPUS] Ingesting: '{inside_text[:60]}...'")
    
    start_time = time.time()
    res1 = await async_predict_and_combine(inside_text)
    elapsed1 = time.time() - start_time
    
    print("Combined Verdict:", res1["final_prediction"])
    print("Confidence Score:", res1["final_confidence"])
    print("Engine Used:", res1["engine"])
    print(f"Elapsed Time: {elapsed1:.4f}s")
    print("Bypassed External APIs:", res1["engine"] == "Trained ML Model File (text_clf_model.pkl)")
    
    # Case 2: Headline OUTSIDE the CURATED_DATASET
    outside_text = "This is a random new headline that has never been seen in the training dataset of the classifier."
    print(f"\n[Case 2: OUTSIDE CORPUS] Ingesting: '{outside_text}'")
    
    # Temporarily set API key blank to check online fallback or live call
    # In either case, the engine used will NOT be "Trained ML Model File (text_clf_model.pkl)"
    # It will perform search and call Gemini (or fallback due to rate limits)
    start_time = time.time()
    res2 = await async_predict_and_combine(outside_text)
    elapsed2 = time.time() - start_time
    
    print("Combined Verdict:", res2["final_prediction"])
    print("Confidence Score:", res2["final_confidence"])
    print("Engine Used:", res2["engine"])
    print(f"Elapsed Time: {elapsed2:.4f}s")
    print("Triggered Search & Cognitive:", res2["engine"] == "Cognitive Context Engine")

    # Case 3: Headline with a substring match (minor alterations to Semiconductor headline)
    inside_text_substring = "Reuters reports that " + CURATED_DATASET[0]["text"] + " in early 2026."
    print(f"\n[Case 3: SUBSTRING MATCH] Ingesting: '{inside_text_substring[:80]}...'")
    
    start_time = time.time()
    res3 = await async_predict_and_combine(inside_text_substring)
    elapsed3 = time.time() - start_time
    
    print("Combined Verdict:", res3["final_prediction"])
    print("Confidence Score:", res3["final_confidence"])
    print("Engine Used:", res3["engine"])
    print(f"Elapsed Time: {elapsed3:.4f}s")
    print("Bypassed External APIs:", res3["engine"] == "Trained ML Model File (text_clf_model.pkl)")

if __name__ == "__main__":
    asyncio.run(test())
