import os
import shutil
import unittest
import pandas as pd
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Adjust import path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app, CSV_PATH, HISTORY_PATH

class TestCSVCacheIntegration(unittest.TestCase):
    def setUp(self):
        # Backup existing CSV files if any
        self.csv_backup = CSV_PATH + ".bak"
        self.history_backup = HISTORY_PATH + ".bak"
        
        if os.path.exists(CSV_PATH):
            shutil.copyfile(CSV_PATH, self.csv_backup)
            os.remove(CSV_PATH)
        if os.path.exists(HISTORY_PATH):
            shutil.copyfile(HISTORY_PATH, self.history_backup)
            os.remove(HISTORY_PATH)
            
        self.client = TestClient(app)

    def tearDown(self):
        # Clean up temporary test files
        if os.path.exists(CSV_PATH):
            os.remove(CSV_PATH)
        if os.path.exists(HISTORY_PATH):
            os.remove(HISTORY_PATH)
            
        # Restore backups
        if os.path.exists(self.csv_backup):
            shutil.move(self.csv_backup, CSV_PATH)
        if os.path.exists(self.history_backup):
            shutil.move(self.history_backup, HISTORY_PATH)

    @patch("main.async_predict_and_combine")
    def test_cache_miss_and_cache_hit_flow(self, mock_predict):
        # Define mock prediction result
        mock_result = {
            "prediction": "Fake",
            "confidence": 92.0,
            "engine": "Cognitive Context Engine",
            "metrics": {
                "sensationalism": 75.0,
                "emotional_bias": 65.0,
                "formatting_style": 40.0,
                "lexical_complexity": 50.0,
                "google_verification": {
                    "search_performed": False,
                    "verification_score": 0.0,
                    "status": "Search offline.",
                    "outlets_found": [],
                    "query_url": "",
                    "search_results": []
                },
                "ml_result": {"prediction": "Fake", "confidence": 90.0, "metrics": {}},
                "final_prediction": "Fake",
                "final_confidence": 92.0,
                "ai_summary": "AI predicted this as fake.",
                "risk_factors": ["Suspicious trigger words"],
                "source_reliability": "Low",
                "processing_time": "0.10s"
            },
            "explanation": ["Primary AI Engine verdict is Fake."],
            "google_verification": None,
            "final_prediction": "Fake",
            "final_confidence": 92.0,
            "ml_result": {},
            "gemini_result": {},
            "ai_summary": "AI predicted this as fake.",
            "risk_factors": ["Suspicious trigger words"],
            "source_reliability": "Low",
            "processing_time": "0.10s"
        }
        
        mock_predict.return_value = mock_result

        test_headline = "EXCLUSIVE: Aliens spotted drinking warm tea under the Eiffel Tower!"
        
        # 1. Send first prediction (Cache Miss -> should trigger AUTO_SAVED)
        payload = {
            "text": test_headline,
            "source": "Test Runner",
            "category": "Satire"
        }
        response = self.client.post("/api/predict", json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "AUTO_SAVED")
        self.assertEqual(data["final_prediction"], "Fake")
        
        # Verify that CSV_PATH has been created and populated
        self.assertTrue(os.path.exists(CSV_PATH))
        df = pd.read_csv(CSV_PATH)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["text"], test_headline)
        self.assertEqual(df.iloc[0]["label"], "Fake")
        self.assertEqual(df.iloc[0]["category"], "Satire")
        self.assertEqual(df.iloc[0]["source"], "Test Runner")
        
        # Verify HISTORY_PATH logging
        self.assertTrue(os.path.exists(HISTORY_PATH))
        hist_df = pd.read_csv(HISTORY_PATH)
        self.assertEqual(len(hist_df), 1)
        self.assertEqual(hist_df.iloc[0]["text"], test_headline)
        self.assertEqual(hist_df.iloc[0]["status"], "AUTO_SAVED")
        
        # Reset mock call count to verify it isn't called on cache hit
        mock_predict.reset_mock()
        
        # 2. Send second prediction with same/fuzzy text (Cache Hit -> should trigger FOUND_IN_CSV)
        fuzzy_headline = "EXCLUSIVE: Aliens spotted drinking warm tea under the Eiffel" # first 50 chars match
        payload_hit = {
            "text": fuzzy_headline,
            "source": "Test Hit",
            "category": "Satire"
        }
        
        response_hit = self.client.post("/api/predict", json=payload_hit)
        self.assertEqual(response_hit.status_code, 200)
        data_hit = response_hit.json()
        
        # Should be a cache hit, so mock_predict should NOT have been called
        mock_predict.assert_not_called()
        self.assertEqual(data_hit["status"], "FOUND_IN_CSV")
        self.assertEqual(data_hit["final_prediction"], "Fake")
        
        # Verify HISTORY_PATH was appended with the cache hit log
        hist_df_2 = pd.read_csv(HISTORY_PATH)
        self.assertEqual(len(hist_df_2), 2)
        self.assertEqual(hist_df_2.iloc[1]["text"], fuzzy_headline)
        self.assertEqual(hist_df_2.iloc[1]["status"], "FOUND_IN_CSV")
        self.assertEqual(hist_df_2.iloc[1]["source"], "Test Hit")

if __name__ == "__main__":
    unittest.main()
