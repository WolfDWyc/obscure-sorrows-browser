#!/usr/bin/env python3
"""
Refactored script to generate HTML using Jinja2 template.
This is much cleaner than building HTML strings manually.
"""

import html
import json
from pathlib import Path
from jinja2 import Template

def escape_html(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    return html.escape(str(text))

def process_words(words):
    """Process words from JSON, parsing tags and sentences."""
    processed = []
    for idx, word in enumerate(words, 1):
        word_name = word.get('Word', '')
        processed_word = {
            'index': idx,
            'word_name': escape_html(word_name),
            'word_name_lower': word_name.lower(),
            'definition': escape_html(word.get('Definition', '')),
            'part_of_speech': escape_html(word.get('Part of Speech', '')),
            'etymology': escape_html(word.get('Etymology', '')),
            'etymology_attr': escape_html(word.get('Etymology', '')).replace('"', '&quot;').replace("'", '&#39;'),
            'chapter': escape_html(word.get('Chapter', '')),
            'concept': escape_html(word.get('Concept', '')),
            'tags': [escape_html(tag.strip()) for tag in (word.get('Tags') or '').split(';') if tag.strip()],
            'sentences': [escape_html(s.strip()) for s in (word.get('Example Sentences') or '').split(';') if s.strip()],
        }
        processed.append(processed_word)
    return processed

def generate_html(json_file='dictionary.json', output_file='dictionary.html'):
    """Generate a beautiful single-page HTML website from the JSON using Jinja2 template."""
    
    # Read the JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    print(f"Loaded {len(words)} words from {json_file}")
    
    # Process words
    processed_words = process_words(words)
    
    # Create word mappings for JavaScript
    word_to_index = {word['word_name_lower']: word['index'] for word in processed_words}
    index_to_word = {word['index']: word['word_name'] for word in processed_words}
    
    # Convert to JSON strings for JavaScript (more reliable than Jinja2 loops)
    # Use custom formatting to ensure numeric keys in indexToWord
    word_to_index_js = json.dumps(word_to_index, ensure_ascii=False)
    # For indexToWord, we need numeric keys, so format manually
    # Escape quotes in word names for JavaScript
    index_to_word_items = [f'{k}: {json.dumps(v, ensure_ascii=False)}' for k, v in sorted(index_to_word.items())]
    index_to_word_js = '{\n            ' + ',\n            '.join(index_to_word_items) + '\n        }'
    
    # Load template
    template_path = Path('template.html')
    if not template_path.exists():
        print(f"Error: template.html not found. Please create it first.")
        return
    
    template_content = template_path.read_text(encoding='utf-8')
    template = Template(template_content)
    
    # Render template
    html_content = template.render(
        words=processed_words,
        total_words=len(processed_words),
        word_to_index_js=word_to_index_js,
        index_to_word_js=index_to_word_js,
    )
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated {output_file} with {len(words)} words")

if __name__ == '__main__':
    generate_html()

