#!/usr/bin/env python3
"""
Fix and merge dictionary data:
- Take all fields (except Example Sentences) from the newly scraped JSON
- Take Example Sentences from the existing JSON
- If sentences are too short (< 5 words), regenerate them
- Save to dictionary.json
"""

import json
import os
import sys
from pathlib import Path

# Import the sentence generation function
sys.path.insert(0, str(Path(__file__).parent))
from add_example_sentences import get_example_sentences
from openai import OpenAI

SCRAPED_JSON = 'obscure_sorrows_dictionary.json'
EXISTING_JSON = 'obscure_sorrows_dictionary_with_sentences.json'
OUTPUT_JSON = 'dictionary.json'
MIN_SENTENCE_WORDS = 5  # Minimum words to consider sentences valid

def count_words(text: str) -> int:
    """Count words in a text string."""
    if not text or not text.strip():
        return 0
    return len(text.strip().split())

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
    print("Dictionary of Obscure Sorrows - Fix and Merge")
    print("=" * 60)
    
    # Load scraped data (correct metadata)
    print(f"\nLoading scraped data from {SCRAPED_JSON}...")
    scraped_words = load_json(SCRAPED_JSON)
    if not scraped_words:
        print("No words found in scraped JSON!")
        return
    print(f"Loaded {len(scraped_words)} words from scraped data")
    
    # Load existing data (has sentences)
    print(f"\nLoading existing data from {EXISTING_JSON}...")
    existing_words = load_json(EXISTING_JSON)
    if not existing_words:
        print("No words found in existing JSON!")
        return
    print(f"Loaded {len(existing_words)} words from existing data")
    
    # Create mapping of existing words by name
    existing_by_word = {}
    for word_data in existing_words:
        word_name = word_data.get('Word', '').strip()
        if word_name:
            sentences = word_data.get('Example Sentences', '').strip()
            existing_by_word[word_name] = sentences
    
    print(f"Found {len(existing_by_word)} words with sentences in existing data")
    
    # Check for API key (needed if we need to regenerate sentences)
    api_key = os.getenv('OPENAI_API_KEY')
    
    client = None
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            print("OpenAI client initialized")
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
            client = None
    
    # Merge data
    print(f"\nMerging data...")
    merged_words = []
    regenerated = 0
    used_existing = 0
    missing = 0
    
    for idx, scraped_word in enumerate(scraped_words, 1):
        word_name = scraped_word.get('Word', '').strip()
        if not word_name:
            continue
        
        # Get sentences from existing data
        sentences = existing_by_word.get(word_name, '').strip()
        
        # Check if sentences are valid (at least MIN_SENTENCE_WORDS words)
        word_count = count_words(sentences)
        
        if word_count < MIN_SENTENCE_WORDS:
            # Sentences are too short, regenerate them
            print(f"[{idx}/{len(scraped_words)}] {word_name}: Sentences too short ({word_count} words), regenerating...")
            
            if client:
                definition = scraped_word.get('Definition', '')
                new_sentences = get_example_sentences(client, word_name, definition, num_sentences=3)
                if new_sentences and count_words(new_sentences) >= MIN_SENTENCE_WORDS:
                    sentences = new_sentences
                    regenerated += 1
                    print(f"  ✓ Regenerated sentences ({count_words(sentences)} words)")
                else:
                    print(f"  ✗ Failed to generate valid sentences")
                    sentences = ""
                    missing += 1
            else:
                print(f"  ✗ No API key available, skipping regeneration")
                sentences = ""
                missing += 1
        else:
            # Use existing sentences
            used_existing += 1
            if idx % 50 == 0:
                print(f"[{idx}/{len(scraped_words)}] {word_name}: Using existing sentences ({word_count} words)")
        
        # Create merged word entry
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
    
    # Save merged data
    print(f"\nSaving merged data to {OUTPUT_JSON}...")
    save_json(merged_words, OUTPUT_JSON)
    
    print(f"\n{'='*60}")
    print(f"Merge complete!")
    print(f"Total words: {len(merged_words)}")
    print(f"Used existing sentences: {used_existing}")
    print(f"Regenerated sentences: {regenerated}")
    print(f"Missing sentences: {missing}")
    print(f"Output saved to: {OUTPUT_JSON}")

if __name__ == '__main__':
    main()

