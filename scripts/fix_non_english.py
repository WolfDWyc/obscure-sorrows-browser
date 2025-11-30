#!/usr/bin/env python3
"""
Fix non-English characters in example sentences.
Iterates through dictionary.json and regenerates sentences that contain non-English characters.
"""

import json
import os
import re
import sys
from pathlib import Path

# Import the sentence generation function
sys.path.insert(0, str(Path(__file__).parent))
from add_example_sentences import get_example_sentences
from openai import OpenAI

INPUT_JSON = 'dictionary.json'
OUTPUT_JSON = 'dictionary.json'

# Common non-English characters that indicate non-English text
# German: ä, ö, ü, ß
# French: é, è, ê, ë, à, â, ç, ô, ù, û, ÿ
# Spanish: á, é, í, ó, ú, ñ, ¿, ¡
# And other accented characters
NON_ENGLISH_PATTERN = re.compile(
    r'[äöüßáàâäéèêëíìîïóòôöúùûüýÿñç]|'
    r'[ÄÖÜÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜÝŸÑÇ]|'
    r'[¿¡]'
)

def has_non_english(text: str) -> bool:
    """Check if text contains non-English characters."""
    if not text:
        return False
    return bool(NON_ENGLISH_PATTERN.search(text))

def load_json(filename: str) -> list:
    """Load JSON file."""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: list, filename: str):
    """Save data to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} words to {filename}")

def main():
    print("Dictionary of Obscure Sorrows - Fix Non-English Sentences")
    print("=" * 60)
    
    # Load dictionary
    print(f"\nLoading dictionary from {INPUT_JSON}...")
    words = load_json(INPUT_JSON)
    if not words:
        print("No words found!")
        return
    print(f"Loaded {len(words)} words")
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("\nError: OPENAI_API_KEY not found!")
        print("Please set it using:")
        print("  Windows PowerShell: $env:OPENAI_API_KEY='your-api-key'")
        return
    
    try:
        client = OpenAI(api_key=api_key)
        print("OpenAI client initialized")
    except Exception as e:
        print(f"Error: Could not initialize OpenAI client: {e}")
        return
    
    # Check and fix sentences
    print(f"\nChecking for non-English characters in sentences...")
    fixed = 0
    skipped = 0
    failed = 0
    
    for idx, word in enumerate(words, 1):
        word_name = word.get('Word', '').strip()
        sentences = word.get('Example Sentences', '').strip()
        
        if not sentences:
            continue
        
        # Check if sentences contain non-English characters
        if has_non_english(sentences):
            print(f"[{idx}/{len(words)}] {word_name}: Found non-English characters, regenerating...")
            print(f"  Original: {sentences[:100]}...")
            
            definition = word.get('Definition', '')
            new_sentences = get_example_sentences(client, word_name, definition, num_sentences=3)
            
            if new_sentences and not has_non_english(new_sentences):
                word['Example Sentences'] = new_sentences
                fixed += 1
                print(f"  ✓ Fixed: {new_sentences[:100]}...")
            else:
                print(f"  ✗ Failed to generate English-only sentences")
                failed += 1
        else:
            skipped += 1
            if idx % 50 == 0:
                print(f"[{idx}/{len(words)}] {word_name}: OK")
    
    # Save fixed dictionary
    print(f"\nSaving fixed dictionary to {OUTPUT_JSON}...")
    save_json(words, OUTPUT_JSON)
    
    print(f"\n{'='*60}")
    print(f"Fix complete!")
    print(f"Total words: {len(words)}")
    print(f"Sentences checked: {skipped + fixed + failed}")
    print(f"Fixed (regenerated): {fixed}")
    print(f"Already English: {skipped}")
    print(f"Failed to fix: {failed}")
    print(f"Output saved to: {OUTPUT_JSON}")

if __name__ == '__main__':
    main()

