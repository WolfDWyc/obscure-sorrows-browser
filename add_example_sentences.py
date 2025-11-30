#!/usr/bin/env python3
"""
Script to add example sentences to the Dictionary of Obscure Sorrows CSV.
Uses OpenAI API to generate natural example sentences for each word.
Saves progress incrementally and skips words that already have sentences.
"""

import csv
import os
import re
import time
from openai import OpenAI
from typing import List, Dict

# Configuration
INPUT_CSV = 'obscure_sorrows_dictionary.csv'
OUTPUT_CSV = 'obscure_sorrows_dictionary_with_sentences.csv'
SENTENCES_COLUMN = 'Example Sentences'
NUM_SENTENCES = 3  # Number of example sentences to generate per word
MODEL = 'gpt-5.1'

def load_csv(filename: str) -> List[Dict]:
    """Load CSV file and return as list of dictionaries."""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return []
    
    words = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            words.append(row)
    
    return words

def save_csv(words: List[Dict], filename: str):
    """Save words to CSV file."""
    if not words:
        return
    
    # Get all column names
    fieldnames = list(words[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(words)
    
    print(f"  Saved progress to {filename}")

def get_example_sentences(client: OpenAI, word: str, definition: str, num_sentences: int = 3) -> str:
    """
    Use OpenAI API to generate example sentences for a word.
    Returns a semicolon-separated string of sentences.
    """
    prompt = f"""Generate {num_sentences} natural, conversational example sentences using the word "{word}".

IMPORTANT REQUIREMENTS:
- Each sentence should be natural and could be used in real conversation
- Do NOT include the meaning or definition of the word in the sentences
- Do NOT explain what the word means - just use it naturally
- The sentences should NOT describe what the word means
- Just use the word naturally in context, as if the reader already knows what it means
- Make the sentences diverse and show different ways the word can be used
- Separate each sentence with a semicolon and space (; )
- CRITICAL: All sentences MUST be in English only. Do not use any non-English characters, words, or phrases.

Word: {word}
Definition: {definition} (provided for context only - do not include in sentences)

Generate {num_sentences} example sentences in English:"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates natural example sentences for words."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=300
        )
        
        sentences = response.choices[0].message.content.strip()
        
        # Clean up the response - remove any numbering, bullets, or extra formatting
        sentences = sentences.replace('\n', ' ')
        # Remove common prefixes like "1.", "2.", "-", etc.
        sentences = re.sub(r'^\d+[\.\)]\s*', '', sentences, flags=re.MULTILINE)
        sentences = re.sub(r'^[-•]\s*', '', sentences, flags=re.MULTILINE)
        
        # Split by semicolon if present, otherwise try other separators
        if ';' in sentences:
            sentence_list = [s.strip() for s in sentences.split(';') if s.strip()]
        else:
            # Try to split by periods or newlines
            sentence_list = [s.strip() for s in re.split(r'[\.\n]', sentences) if s.strip() and len(s.strip()) > 10]
        
        # Limit to requested number
        sentence_list = sentence_list[:num_sentences]
        
        # Join with semicolon and space
        return '; '.join(sentence_list)
    
    except Exception as e:
        print(f"    Error generating sentences: {e}")
        return ""

def process_words(words: List[Dict], api_key: str, output_file: str):
    """Process words and add example sentences."""
    client = OpenAI(api_key=api_key)
    
    # Initialize all words with empty sentences column if needed
    for word in words:
        if SENTENCES_COLUMN not in word:
            word[SENTENCES_COLUMN] = ""
    
    # Check if output file exists and load it to preserve progress
    existing_dict = {}
    if os.path.exists(output_file):
        existing_words = load_csv(output_file)
        # Create a dictionary for quick lookup by word name
        existing_dict = {word.get('Word', ''): word for word in existing_words if word.get('Word')}
        print(f"Found existing file with {len(existing_words)} words. Resuming from where we left off...")
    
    # Process each word
    total = len(words)
    processed = 0
    skipped = 0
    new = 0
    
    # Start with existing words or create new list
    all_words = []
    
    # Process each word
    for word in words:
        word_name = word.get('Word', '')
        if not word_name:
            continue
        
        # Check if word already has sentences in existing file
        if word_name in existing_dict:
            existing_word = existing_dict[word_name]
            if existing_word.get(SENTENCES_COLUMN) and existing_word[SENTENCES_COLUMN].strip():
                # Use existing word data but preserve all columns from input
                word[SENTENCES_COLUMN] = existing_word[SENTENCES_COLUMN]
                all_words.append(word)
                skipped += 1
                print(f"[{len(all_words)}/{total}] Skipping {word_name} (already has sentences)")
                continue
        
        # Word needs processing
        print(f"[{len(all_words) + 1}/{total}] Processing {word_name}...")
        
        # Get definition for context
        definition = word.get('Definition', '')
        
        # Generate example sentences
        sentences = get_example_sentences(client, word_name, definition, NUM_SENTENCES)
        
        if sentences:
            word[SENTENCES_COLUMN] = sentences
            print(f"  Generated example sentences")
            new += 1
        else:
            word[SENTENCES_COLUMN] = ""
            print(f"  Failed to generate sentences")
        
        # Add to all_words list
        all_words.append(word)
        processed += 1
        
        # Save progress after each word
        save_csv(all_words, output_file)
        
        # Rate limiting - be respectful to the API
        time.sleep(1)
    
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Total words: {total}")
    print(f"Processed: {processed}")
    print(f"New sentences added: {new}")
    print(f"Skipped (already had sentences): {skipped}")
    print(f"Output saved to: {output_file}")

def main():
    print("Dictionary of Obscure Sorrows - Example Sentences Generator")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\nError: OPENAI_API_KEY environment variable not set!")
        print("Please set it using:")
        print("  Windows PowerShell: $env:OPENAI_API_KEY='your-api-key'")
        print("  Windows CMD: set OPENAI_API_KEY=your-api-key")
        print("  Linux/Mac: export OPENAI_API_KEY='your-api-key'")
        return
    
    # Load words from CSV
    print(f"\nLoading words from {INPUT_CSV}...")
    words = load_csv(INPUT_CSV)
    
    if not words:
        print("No words found!")
        return
    
    print(f"Loaded {len(words)} words")
    
    # Process words
    process_words(words, api_key, OUTPUT_CSV)

if __name__ == '__main__':
    main()

