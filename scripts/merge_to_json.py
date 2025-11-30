#!/usr/bin/env python3
"""
Merge newly scraped JSON with existing CSV that has example sentences,
outputting to JSON.
"""

import json
import csv
import sys
from pathlib import Path

def merge_to_json(scraped_json: str, existing_data: str, output_json: str = None) -> None:
    """
    Merge scraped JSON data with existing data (CSV or JSON) that has example sentences.
    
    Args:
        scraped_json: Path to the newly scraped JSON (without sentences)
        existing_data: Path to the existing CSV or JSON (with sentences)
        output_json: Path to save merged JSON (defaults to existing_data name with .json)
    """
    if output_json is None:
        output_json = existing_data.replace('.csv', '.json').replace('.json', '_merged.json')
    
    print(f"Reading scraped data from {scraped_json}...")
    with open(scraped_json, 'r', encoding='utf-8') as f:
        scraped_words = json.load(f)
    
    print(f"Loaded {len(scraped_words)} words from scraped data")
    
    print(f"Reading existing data from {existing_data}...")
    # Try to read as JSON first (if it was converted from CSV)
    existing_json_path = existing_data.replace('.csv', '.json')
    if existing_json_path != existing_data and Path(existing_json_path).exists():
        print(f"Found JSON version at {existing_json_path}, using that instead...")
        with open(existing_json_path, 'r', encoding='utf-8') as f:
            existing_words = json.load(f)
    else:
        # Read as CSV - but be smarter about finding sentences
        existing_words = []
        with open(existing_data, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_words.append(row)
    
    print(f"Loaded {len(existing_words)} words from existing data")
    
    # Create a mapping by word name for existing data
    existing_by_word = {}
    for word_data in existing_words:
        word_name = word_data.get('Word', '').strip()
        if word_name:
            # Try to find sentences - check multiple possible field names
            sentences = (
                word_data.get('Example Sentences', '') or
                word_data.get('Example Sentences', '') or
                word_data.get('Sentences', '') or
                ''
            )
            existing_by_word[word_name] = sentences
    
    # Merge: use scraped data for all fields except Example Sentences
    # Match by word name first, then fall back to position
    merged_words = []
    for idx, scraped_word in enumerate(scraped_words):
        word_name = scraped_word.get('Word', '').strip()
        
        # Try to get sentences by word name
        sentences = existing_by_word.get(word_name, '')
        
        # If not found by name and we have positional data, try by index
        if not sentences and idx < len(existing_words):
            existing_word = existing_words[idx]
            sentences = (
                existing_word.get('Example Sentences', '') or
                existing_word.get('Sentences', '') or
                ''
            )
        
        merged_word = {
            'Word': scraped_word.get('Word', ''),
            'Definition': scraped_word.get('Definition', ''),
            'Part of Speech': scraped_word.get('Part of Speech', ''),
            'Etymology': scraped_word.get('Etymology', ''),
            'Chapter': scraped_word.get('Chapter', ''),
            'Concept': scraped_word.get('Concept', ''),
            'Tags': scraped_word.get('Tags', ''),
            'Example Sentences': sentences,
        }
        merged_words.append(merged_word)
    
    # Write merged data to JSON
    print(f"Writing merged data to {output_json}...")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(merged_words, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully merged {len(merged_words)} words")
    print(f"Output saved to {output_json}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python merge_to_json.py <scraped_json> <existing_csv> [output_json]")
        print("  If output_json is not specified, it will be based on existing_csv name.")
        sys.exit(1)
    
    scraped_json = sys.argv[1]
    existing_csv = sys.argv[2]
    output_json = sys.argv[3] if len(sys.argv) > 3 else None
    
    merge_to_json(scraped_json, existing_csv, output_json)

