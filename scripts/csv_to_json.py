#!/usr/bin/env python3
"""
Convert the existing CSV with sentences to JSON format.
"""

import csv
import json
import sys
from pathlib import Path

def csv_to_json(csv_file: str, json_file: str = None) -> None:
    """Convert CSV to JSON format."""
    if json_file is None:
        json_file = csv_file.replace('.csv', '.json')
    
    print(f"Reading CSV from {csv_file}...")
    
    words = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            words.append(row)
    
    print(f"Loaded {len(words)} words")
    
    print(f"Writing JSON to {json_file}...")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully converted to {json_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python csv_to_json.py <input_csv> [output_json]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    csv_to_json(csv_file, json_file)

