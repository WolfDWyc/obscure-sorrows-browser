#!/usr/bin/env python3
"""
Script to format definitions in the Dictionary of Obscure Sorrows JSON.
Uses OpenAI API to intelligently add newlines to definitions for better readability.
Preserves exact text content, only adding line breaks.
Saves progress incrementally and skips words that already have formatted definitions.
"""

import json
import os
import re
import time
from openai import OpenAI
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
INPUT_JSON = 'dictionary.json'
OUTPUT_JSON = 'dictionary_formatted.json'  # New file, not in-place
BACKUP_JSON = 'dictionary_backup.json'
MODEL = 'gpt-4o'  # Use gpt-4o for better understanding

def load_json(filename: str) -> List[Dict]:
    """Load JSON file and return as list of dictionaries."""
    json_path = Path(filename)
    if not json_path.exists():
        # Try backend directory
        json_path = Path("backend") / filename
    if not json_path.exists():
        print(f"Error: {filename} not found!")
        return []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    return words

def save_json(words: List[Dict], filename: str):
    """Save words to JSON file."""
    if not words:
        return
    
    json_path = Path(filename)
    if not json_path.exists():
        json_path = Path("backend") / filename
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    
    print(f"  Saved progress to {json_path}")

def normalize_text(text: str) -> str:
    """Normalize text for comparison (replace newlines and punctuation with spaces)."""
    # Replace literal \n with spaces
    text = text.replace('\\n', ' ')
    # Replace actual newlines with spaces
    text = re.sub(r'\n', ' ', text)
    # Replace punctuation with spaces (preserves word boundaries)
    text = re.sub(r'[^\w\s]', ' ', text)
    # Normalize all whitespace to single spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def verify_text_unchanged(original: str, formatted: str) -> bool:
    """Fuzzy vibe check - ensure the text is roughly the same, allowing for minor differences."""
    original_norm = normalize_text(original)
    formatted_norm = normalize_text(formatted)
    
    # Extract just the words (no punctuation, no spaces)
    original_words = re.findall(r'\w+', original_norm)
    formatted_words = re.findall(r'\w+', formatted_norm)
    
    # Must have roughly the same number of words (within 5% difference)
    word_count_diff = abs(len(original_words) - len(formatted_words))
    if word_count_diff > max(2, len(original_words) * 0.05):
        return False
    
    # Check that most words are the same (at least 90% match)
    # Create sets for comparison
    original_set = set(original_words)
    formatted_set = set(formatted_words)
    
    # Calculate similarity
    common_words = original_set & formatted_set
    total_unique_words = len(original_set | formatted_set)
    
    if total_unique_words == 0:
        return True
    
    similarity = len(common_words) / total_unique_words
    
    # Allow if similarity is at least 90%
    return similarity >= 0.90

def format_definition(client: OpenAI, word: str, definition: str) -> str:
    """
    Use OpenAI API to format definition by adding newlines for readability.
    Returns the same definition with newlines inserted, or original if formatting fails.
    """
    prompt = f"""Analyze the following definition and add newlines (\\n) to separate the core meaning from supporting material.

CRITICAL REQUIREMENTS:
- You MUST preserve the EXACT same text - do not change, add, remove, or modify any word
- Do NOT change any punctuation, commas, dashes, or other marks, even not at the cutoff points for newlines - but have the newlines be AFTER the punctuation at the cutoff mark, if there is one
- Do NOT add the word itself to the definition - return the definition exactly as provided, only with newlines added
- The definition should start with the exact same text as the input - do not prefix it with the word
- Think semantically: What is the CORE DEFINITION vs what is ILLUSTRATION or ELABORATION?
- The core definition is the essential meaning - what the word fundamentally means
- Supporting material includes: examples, comparisons, metaphors, extended descriptions that help illustrate the concept
- Separate the core definition from supporting material with a newline
- Keep all supporting material together on the same line(s) - if it's illustrating the same concept, it belongs together
- If the definition is purely the core meaning with no illustration, you can leave it unchanged
- If there's a clear shift from "what it is" to "how to understand it" (via example/comparison), split there
- Return ONLY the formatted definition with newlines, nothing else

Word: {word}
Definition: {definition}

Identify: What is the essential definition, and what is supporting illustration? Separate them with a newline."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats text by adding newlines for readability. You never change the actual words or content, only add line breaks. Never add the word itself to the beginning of the definition."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent formatting
            max_tokens=500
        )
        
        formatted = response.choices[0].message.content.strip()
        
        # Remove any markdown formatting or quotes if present
        formatted = formatted.strip('"\'`')
        formatted = re.sub(r'^```[\w]*\n?', '', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'\n?```$', '', formatted, flags=re.MULTILINE)
        formatted = formatted.strip()
        
        # Convert literal \n strings to actual newlines if present
        formatted = formatted.replace('\\n', '\n')
        
        # Verify the text hasn't changed
        if not verify_text_unchanged(definition, formatted):
            print(f"    WARNING: Text verification failed! Returning original.")
            print(f"    Original: {definition}...")
            print(f"    Formatted: {formatted}...")
            return definition
        
        return formatted
    
    except Exception as e:
        print(f"    Error formatting definition: {e}")
        return definition

def process_words(words: List[Dict], api_key: str, output_file: str):
    """Process words and format definitions."""
    client = OpenAI(api_key=api_key)
    
    # Check if output file exists and load it to preserve progress
    existing_dict = {}
    if os.path.exists(output_file) or Path("backend") / output_file:
        json_path = Path(output_file)
        if not json_path.exists():
            json_path = Path("backend") / output_file
        if json_path.exists():
            existing_words = load_json(output_file)
            # Create a dictionary for quick lookup by word name
            existing_dict = {word.get('Word', ''): word for word in existing_words if word.get('Word')}
            print(f"Found existing file with {len(existing_words)} words. Resuming from where we left off...")
    
    # Create backup before processing
    if not Path(BACKUP_JSON).exists():
        json_path = Path(INPUT_JSON)
        if not json_path.exists():
            json_path = Path("backend") / INPUT_JSON
        if json_path.exists():
            backup_path = Path(BACKUP_JSON)
            with open(json_path, 'r', encoding='utf-8') as f_in:
                with open(backup_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(f_in.read())
            print(f"Created backup: {BACKUP_JSON}")
    
    # Process each word
    total = len(words)
    processed = 0
    skipped = 0
    formatted = 0
    unchanged = 0
    
    # Start with existing words or create new list
    all_words = []
    
    # Process each word
    for word in words:
        word_name = word.get('Word', '')
        if not word_name:
            continue
        
        definition = word.get('Definition', '')
        if not definition:
            all_words.append(word)
            continue
        
        # Check if word already has formatted definition (has newlines)
        if word_name in existing_dict:
            existing_word = existing_dict[word_name]
            existing_def = existing_word.get('Definition', '')
            # If it already has newlines, consider it formatted
            if '\n' in existing_def:
                word['Definition'] = existing_def
                all_words.append(word)
                skipped += 1
                print(f"[{len(all_words)}/{total}] Skipping {word_name} (already formatted)")
                continue
        
        # Word needs processing
        print(f"[{len(all_words) + 1}/{total}] Processing {word_name}...")
        
        # Format definition
        formatted_def = format_definition(client, word_name, definition)
        
        if formatted_def != definition:
            word['Definition'] = formatted_def
            print(f"  Formatted definition (added newlines)")
            formatted += 1
        else:
            print(f"  Definition unchanged (no formatting needed)")
            unchanged += 1
        
        # Add to all_words list
        all_words.append(word)
        processed += 1
        
        # Save progress after each word
        save_json(all_words, output_file)
        
        # Rate limiting - be respectful to the API    
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Total words: {total}")
    print(f"Processed: {processed}")
    print(f"Formatted (newlines added): {formatted}")
    print(f"Unchanged (no formatting needed): {unchanged}")
    print(f"Skipped (already formatted): {skipped}")
    print(f"Output saved to: {output_file}")

def main():
    print("Dictionary of Obscure Sorrows - Definition Formatter")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\nError: OPENAI_API_KEY not found!")
        print("Please create a .env file with: OPENAI_API_KEY=your-api-key")
        return
    
    # Load words from JSON
    print(f"\nLoading words from {INPUT_JSON}...")
    words = load_json(INPUT_JSON)
    
    if not words:
        print("No words found!")
        return
    
    print(f"Loaded {len(words)} words")
    
    # Process words
    process_words(words, api_key, OUTPUT_JSON)

if __name__ == '__main__':
    main()

