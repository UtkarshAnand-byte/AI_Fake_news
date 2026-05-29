import asyncio
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

from main import async_predict_and_combine, init_db

async def run_test():
    print("=====================================================")
    print("     VeracitySuite AI Fact-Grounding Test            ")
    print("=====================================================")
    
    init_db()
    
    # Test input: A real claim with a lengthy introductory phrase that would fail under the old query logic
    long_article_text = (
        "According to early statements released this morning by economic policy advisers, "
        "the Federal Reserve is fully expected to hold benchmark interest rates steady in "
        "its next meeting, keeping borrowing costs at their current levels to monitor inflation."
    )
    
    print("\n--- Test Input (Full Article) ---")
    print(f"Content: \"{long_article_text}\"")
    
    start_time = time.time()
    result = await async_predict_and_combine(long_article_text)
    elapsed = time.time() - start_time
    
    print("\n--- Telemetry & Decision Results ---")
    print(f"Latency: {elapsed:.2f}s (Response measures: {result.get('processing_time', 'N/A')})")
    print(f"Final Prediction: {result.get('final_prediction')}")
    print(f"Final Confidence: {result.get('final_confidence')}%")
    print(f"Engine Used: {result.get('engine')}")
    print(f"Source Reliability: {result.get('source_reliability')}")
    
    google_res = result.get("google_verification", {})
    print(f"\n--- Google & DuckDuckGo Search Verification ---")
    print(f"Search Performed: {google_res.get('search_performed')}")
    print(f"Verification Score: {google_res.get('verification_score')}%")
    print(f"Outlets Identified: {google_res.get('outlets_found')}")
    print(f"Status Msg: {google_res.get('status')}")
    
    print(f"\n--- Top Scraped Search Snippets (First 2) ---")
    results = google_res.get("search_results", [])
    for idx, r in enumerate(results[:2]):
        print(f"Result {idx+1} [{r.get('engine')}]:")
        print(f"  Title: {r.get('title')}")
        print(f"  Snippet: {r.get('snippet')}")
        print(f"  URL: {r.get('url')}")
        
    print("\n--- AI Summary ---")
    print(result.get("ai_summary"))
    
    print("\n--- Diagnostic Bullet Logs ---")
    for b in result.get("explanation", []):
         print(f" - {b}")
         
    print("\n=====================================================")

if __name__ == "__main__":
    asyncio.run(run_test())
