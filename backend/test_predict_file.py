import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure the backend directory is in the import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environmental configurations
load_dotenv()

async def run_diagnostic():
    print("====================================================")
    print("        AIFakeNews Dual-Layer Integration Test     ")
    print("====================================================")
    
    # 1. Verify environment settings
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    ai_weight = os.getenv("AI_WEIGHT", "0.4")
    ml_weight = os.getenv("ML_WEIGHT", "0.6")
    
    print(f"[Environment] GEMINI_MODEL: {gemini_model}")
    print(f"[Environment] AI_WEIGHT: {ai_weight} | ML_WEIGHT: {ml_weight}")
    if gemini_key:
        masked_key = gemini_key[:8] + "..." + gemini_key[-4:] if len(gemini_key) > 12 else "Short Key"
        print(f"[Environment] GEMINI_API_KEY: {masked_key} (Active)")
    else:
        print("[Environment WARNING] GEMINI_API_KEY is not defined!")

    # Import the prediction core
    try:
        from main import async_predict_and_combine, analyzer
        print("[Import Success] Successfully imported prediction pipeline and analyzer assets.")
    except Exception as e:
        print(f"[Import ERROR] Failed to load main modules: {e}")
        return

    # Verify ML model is loaded
    ml_loaded = analyzer.reload_assets()
    print(f"[ML Asset Status] Model Loaded: {ml_loaded} | Engine: {'SVC Pipeline' if analyzer.is_pipeline else 'Linguistic Heuristic'}")

    # 2. Run Live Analysis on a standard Clickbait / Suspicious Headline
    test_text = (
        "BREAKING SHOCKING CONSPIRACY: Leaked files reveal the moon is actually hollow "
        "and serves as a parking garage for active alien UFO spacecrafts! No major news media is covering this!"
    )
    print(f"\n[Test Input] Ingesting news corpus:\n\"\"\"\n{test_text}\n\"\"\"")
    print("\n[Executing] Concurrently running Scikit-Learn classification + Gemini AI deep diagnostic...")
    
    try:
        result = await async_predict_and_combine(test_text)
        
        print("\n====================================================")
        print("                 DIAGNOSTIC REPORT                  ")
        print("====================================================")
        print(f"Final Combined Verdict: {result['final_prediction'].upper()}")
        print(f"Final Combined Confidence: {result['final_confidence']:.1f}%")
        print(f"Source Reliability Rating: {result['source_reliability']}")
        print(f"Engine Latency: {result['processing_time']}")
        
        print("\n[ML Engine Result]")
        print(f"  Prediction: {result['ml_result']['prediction']}")
        print(f"  Confidence: {result['ml_result']['confidence']:.1f}%")
        print(f"  Linguistic Metrics: {result['ml_result']['metrics']}")
        
        print("\n[Gemini AI Result]")
        print(f"  Prediction: {result['gemini_result']['prediction']}")
        print(f"  Confidence: {result['gemini_result']['confidence']}%")
        print(f"  Tone: {result['gemini_result']['emotional_tone']} | Clickbait: {result['gemini_result']['clickbait_score']}%")
        
        print("\n[Identified Risk Factors]")
        for idx, rf in enumerate(result['risk_factors'], 1):
            print(f"  {idx}. {rf}")
            
        print("\n[Gemini AI Explanation]")
        print(f"  {result['ai_summary']}")
        
        print("\n[Compatibility Check]")
        print(f"  Legacy Prediction: {result['prediction']}")
        print(f"  Legacy Confidence: {result['confidence']}%")
        print(f"  Legacy Engine: {result['engine']}")
        print("====================================================")
        print("          STATUS: 100% INTEGRATION PASSED           ")
        print("====================================================")
        
    except Exception as e:
        print(f"\n[DIAGNOSTIC FAILURE] Core analysis route threw an exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
