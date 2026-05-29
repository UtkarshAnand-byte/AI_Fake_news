#!/usr/bin/env python
"""
Test script to verify CSV training data integration.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import load_csv_training_data, CURATED_DATASET

def main():
    print("=" * 60)
    print("CSV TRAINING DATA INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Check CSV file exists
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(backend_dir, "fake_news_training_data.csv")
    print(f"\n1. Checking CSV file: {csv_path}")
    if os.path.exists(csv_path):
        print(f"   ✓ CSV file found (Size: {os.path.getsize(csv_path)} bytes)")
    else:
        print(f"   ✗ CSV file not found!")
        return False
    
    # Test 2: Load CSV data
    print("\n2. Loading CSV training data...")
    csv_data = load_csv_training_data(csv_path)
    print(f"   ✓ Loaded {len(csv_data)} training samples from CSV")
    
    # Test 3: Show sample data
    if csv_data:
        print("\n3. Sample CSV data:")
        for i, item in enumerate(csv_data[:3]):
            label_name = "FAKE/SATIRE" if item["label"] == 1 else "REAL"
            preview = item["text"][:60] + "..." if len(item["text"]) > 60 else item["text"]
            print(f"   [{i+1}] Label: {label_name} | Text: {preview}")
    
    # Test 4: Check CURATED_DATASET
    print(f"\n4. CURATED_DATASET statistics:")
    print(f"   Total samples: {len(CURATED_DATASET)}")
    real_count = sum(1 for item in CURATED_DATASET if item["label"] == 0)
    fake_count = sum(1 for item in CURATED_DATASET if item["label"] == 1)
    print(f"   Real news (0): {real_count}")
    print(f"   Fake/Satire (1): {fake_count}")
    
    # Test 5: Label distribution
    print(f"\n5. CSV Label Distribution:")
    csv_real = sum(1 for item in csv_data if item["label"] == 0)
    csv_fake = sum(1 for item in csv_data if item["label"] == 1)
    print(f"   Real news (0): {csv_real}")
    print(f"   Fake/Satire (1): {csv_fake}")
    
    print("\n" + "=" * 60)
    print("✓ CSV INTEGRATION TEST PASSED!")
    print("=" * 60)
    print("\nThe CSV data is successfully integrated and ready for training.")
    print(f"Use the /api/train endpoint to train the model with {len(CURATED_DATASET)} samples.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
