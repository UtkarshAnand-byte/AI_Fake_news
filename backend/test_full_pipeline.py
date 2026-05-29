"""
End-to-end test: runs the full async_predict_and_combine function for 'there are 7 continents in the planet earth'
"""
import sys, os, asyncio
sys.path.insert(0, '.')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

import warnings
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings('ignore', category=InconsistentVersionWarning)

# Import the gemini service directly
from services.gemini_service import GeminiService

async def main():
    test_inputs = [
        "there are 7 continents in the planet earth",
        "SHOCKING PROOF: Secret underground tunnels discovered beneath major cities are being used by military bunkers to transport extinct dinosaurs!",
        "The Federal Reserve decided to keep its benchmark interest rates steady during its recent meeting.",
    ]

    for text in test_inputs:
        print(f"\nTesting: \"{text[:70]}\"")
        try:
            result = await GeminiService.analyze_article(text)
            print(f"  Prediction: {result['prediction']}")
            print(f"  Confidence: {result['confidence']}%")
            print(f"  Explanation: {result['explanation'][:150]}")
        except Exception as e:
            print(f"  ERROR: {e}")

asyncio.run(main())
