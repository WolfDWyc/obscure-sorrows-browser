#!/usr/bin/env python3
"""
Script to extract all words and definitions from The Dictionary of Obscure Sorrows
and save them to a CSV file.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse

def get_word_definition(word_url, base_url):
    """
    Fetch a single word page and extract its definition and metadata.
    Returns a tuple: (word_name, definition, part_of_speech, etymology, chapter, concept, tags)
    """
    try:
        if not word_url.startswith('http'):
            word_url = urljoin(base_url, word_url)
        
        response = requests.get(word_url, timeout=10)
        response.raise_for_status()
        # Ensure proper encoding handling
        response.encoding = response.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the word name - try multiple methods
        word_name = None
        
        # Method 1: h1 with class word-h1 (might be hidden)
        word_elem = soup.find('h1', class_='word-h1')
        if word_elem:
            word_name = word_elem.get_text(strip=True)
        
        # Method 2: Extract from URL as fallback
        if not word_name:
            word_name = word_url.split('/word/')[-1].replace('-', ' ').title()
        
        # Find the definition - try multiple class names
        definition = None
        
        # Try word-definition first (most common)
        definition_elem = soup.find('div', class_='word-definition')
        if definition_elem:
            definition = definition_elem.get_text(strip=True)
        
        # Try sf-word-definition (for some pages)
        if not definition:
            definition_elem = soup.find('div', class_='sf-word-definition')
            if definition_elem:
                definition = definition_elem.get_text(strip=True)
        
        # Try word-definition-wrapper and extract just the definition part
        if not definition:
            wrapper_elem = soup.find('div', class_='word-definition-wrapper')
            if wrapper_elem:
                # The wrapper contains word name + definition, extract just definition
                full_text = wrapper_elem.get_text(strip=True)
                # Try to find the definition part (usually after "n." or similar)
                # Look for pattern like "Wordn. definition" or "Word n. definition"
                match = re.search(r'[a-z]+\.\s*(.+)', full_text, re.IGNORECASE)
                if match:
                    definition = match.group(1).strip()
                else:
                    # Fallback: take everything after first sentence that looks like part of speech
                    parts = re.split(r'\b(n|v|adj|adv)\.\s*', full_text, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) > 2:
                        definition = parts[-1].strip()
        
        # Clean up definition - remove any leading word name or artifacts
        if definition:
            # Remove part of speech markers at start (n., v., adj., adv., etc.)
            definition = re.sub(r'^[a-z]+\.\s*', '', definition, flags=re.IGNORECASE).strip()
            # Remove common leading artifacts like "he ", "e ", "t ", etc. that might be from word name
            definition = re.sub(r'^(he|e|t|th|the)\s+', '', definition, flags=re.IGNORECASE).strip()
            # Remove word name if it appears at the start (case-insensitive)
            if word_name:
                word_lower = word_name.lower()
                if definition.lower().startswith(word_lower):
                    definition = definition[len(word_name):].strip()
                    # Remove any remaining part of speech after word name
                    definition = re.sub(r'^[a-z]+\.\s*', '', definition, flags=re.IGNORECASE).strip()
        
        # Extract metadata
        # Part of speech
        part_of_speech = None
        word_part_elem = soup.find('div', class_='word-part')
        if word_part_elem:
            part_of_speech = word_part_elem.get_text(strip=True)
        
        # Etymology
        etymology = None
        etymology_elem = soup.find('div', class_='word-etymology')
        if etymology_elem:
            etymology = etymology_elem.get_text(strip=True)
            # Clean up etymology - remove extra whitespace
            etymology = ' '.join(etymology.split())
        
        # Chapter
        chapter = None
        chapter_link = soup.find('a', href=lambda x: x and x.startswith('/chapter/'))
        if chapter_link:
            chapter = chapter_link.find('div', class_='toolbar-tag')
            if chapter:
                chapter = chapter.get_text(strip=True)
        
        # Concept
        concept = None
        concept_link = soup.find('a', href=lambda x: x and x.startswith('/concept/'))
        if concept_link:
            concept = concept_link.find('div', class_='toolbar-tag')
            if concept:
                concept = concept.get_text(strip=True)
        
        # Tags (can be multiple)
        tags = []
        tag_links = soup.find_all('a', href=lambda x: x and x.startswith('/tag/'))
        for tag_link in tag_links:
            tag_elem = tag_link.find('div', class_='toolbar-tag')
            if tag_elem:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
        tags_str = '; '.join(tags) if tags else None
        
        if word_name and definition:
            return (word_name, definition, part_of_speech, etymology, chapter, concept, tags_str)
        
        return None
    except Exception as e:
        print(f"  Error fetching {word_url}: {e}")
        return None

def get_all_words():
    """
    Scrape all words and definitions from the Dictionary of Obscure Sorrows website.
    Handles pagination to get all words.
    """
    base_url = 'https://www.thedictionaryofobscuresorrows.com'
    words_url = f'{base_url}/words'
    
    all_word_links = []
    page = 1
    
    # Collect word links from all pages
    while True:
        if page == 1:
            current_url = words_url
        else:
            current_url = f"{words_url}?843c8602_page={page}"
        
        print(f"Fetching words list from page {page}...")
        
        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            # Ensure proper encoding handling
            response.encoding = response.apparent_encoding or 'utf-8'
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links to word pages (links with href starting with /word/)
        page_word_links = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            if href.startswith('/word/') and href not in [w[1] for w in all_word_links]:
                # Extract word name from link text or href
                word_text = link.get_text(strip=True)
                # Skip if it's empty or too long (likely not a word name)
                if word_text and len(word_text) < 100:
                    page_word_links.append((word_text, href))
        
        if not page_word_links:
            # No more words found, we've reached the end
            break
        
        all_word_links.extend(page_word_links)
        print(f"  Found {len(page_word_links)} words on page {page} (total: {len(all_word_links)})")
        
        # Check if there's a next page
        next_link = soup.find('a', class_='w-pagination-next')
        if not next_link or 'href' not in next_link.attrs:
            break
        
        page += 1
        time.sleep(0.5)  # Be respectful between page requests
    
    print(f"\nFound {len(all_word_links)} total word links across {page} page(s)")
    
    # Visit each word page to get the definition and metadata
    words_data = []
    print("Fetching definitions and metadata from individual word pages...")
    for i, (word_text, word_href) in enumerate(all_word_links, 1):
        print(f"  [{i}/{len(all_word_links)}] Fetching {word_href}...", end='\r')
        result = get_word_definition(word_href, base_url)
        if result:
            words_data.append(result)
        # Be respectful with rate limiting
        time.sleep(0.3)
    
    print(f"\nSuccessfully extracted {len(words_data)} words with definitions and metadata")
    return words_data

def fix_encoding_text(text: str) -> str:
    """
    Fix common encoding issues in text.
    Replaces smart quotes and apostrophes with standard ones.
    """
    if not text:
        return text
    
    # Replace smart quotes and apostrophes with standard ASCII equivalents
    replacements = {
        '\u2019': "'",  # right single quotation mark/apostrophe
        '\u2018': "'",  # left single quotation mark
        '\u201C': '"',  # left double quotation mark
        '\u201D': '"',  # right double quotation mark
        '\u2014': '—',  # em dash
        '\u2013': '–',  # en dash
        '\u2026': '…',  # ellipsis
    }
    
    fixed = text
    for unicode_char, ascii_char in replacements.items():
        fixed = fixed.replace(unicode_char, ascii_char)
    
    return fixed

def save_to_json(words_data, filename='obscure_sorrows_dictionary.json'):
    """
    Save words, definitions, and metadata to a JSON file.
    """
    if not words_data:
        print("No words found to save.")
        return
    
    words_list = []
    for word_data in words_data:
        # Unpack: (word_name, definition, part_of_speech, etymology, chapter, concept, tags_str)
        word, definition, pos, etymology, chapter, concept, tags = word_data
        
        # Clean up the text and fix encoding
        word = fix_encoding_text(word.strip() if word else '')
        definition = fix_encoding_text(definition.strip() if definition else '')
        pos = fix_encoding_text(pos.strip() if pos else '')
        etymology = fix_encoding_text(etymology.strip() if etymology else '')
        chapter = fix_encoding_text(chapter.strip() if chapter else '')
        concept = fix_encoding_text(concept.strip() if concept else '')
        tags = fix_encoding_text(tags.strip() if tags else '')
        
        # Replace newlines with spaces
        definition = ' '.join(definition.split()) if definition else ''
        etymology = ' '.join(etymology.split()) if etymology else ''
        
        word_dict = {
            'Word': word,
            'Definition': definition,
            'Part of Speech': pos,
            'Etymology': etymology,
            'Chapter': chapter,
            'Concept': concept,
            'Tags': tags,
        }
        words_list.append(word_dict)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(words_list, f, ensure_ascii=False, indent=2)
    
    print(f"\nSuccessfully saved {len(words_data)} words to {filename}")

def main():
    print("Dictionary of Obscure Sorrows - CSV Extractor")
    print("=" * 50)
    
    words_data = get_all_words()
    
    if words_data:
        save_to_json(words_data)
        print(f"\nFirst few entries:")
        for i, word_data in enumerate(words_data[:3], 1):
            word, definition, pos, etymology, chapter, concept, tags = word_data
            print(f"\n{i}. {word}")
            print(f"   Definition: {definition[:100]}...")
            if pos:
                print(f"   Part of Speech: {pos}")
            if chapter:
                print(f"   Chapter: {chapter}")
            if concept:
                print(f"   Concept: {concept}")
            if tags:
                print(f"   Tags: {tags}")
    else:
        print("\nNo words found. The website structure may have changed.")
        print("You may need to inspect the website manually and update the script.")

if __name__ == '__main__':
    main()

