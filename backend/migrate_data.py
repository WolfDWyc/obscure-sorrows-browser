"""Migrate dictionary.json to SQLite database."""
import json
import sys
from pathlib import Path
from database import SessionLocal, Word, init_db

def migrate_data(json_file: str = "dictionary.json"):
    """Load words from JSON and insert into database."""
    # Try current directory first (for Docker)
    json_path = Path(__file__).parent / json_file
    if not json_path.exists():
        # Try parent directory (for local dev)
        json_path = Path(__file__).parent.parent / json_file
    if not json_path.exists():
        print(f"Error: {json_path} not found!")
        return
    
    print(f"Loading data from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)
    
    print(f"Found {len(words_data)} words")
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        # Upsert words (update existing or insert new)
        # This preserves user ratings while updating word data
        updated_count = 0
        inserted_count = 0
        
        for word_data in words_data:
            word_name = word_data.get('Word', '')
            if not word_name:
                continue
            
            # Check if word already exists
            existing_word = db.query(Word).filter(Word.word == word_name).first()
            
            if existing_word:
                # Update existing word
                existing_word.definition = word_data.get('Definition', '')
                existing_word.part_of_speech = word_data.get('Part of Speech', '')
                existing_word.etymology = word_data.get('Etymology', '')
                existing_word.chapter = word_data.get('Chapter', '')
                existing_word.concept = word_data.get('Concept', '')
                existing_word.tags = word_data.get('Tags', '')
                existing_word.example_sentences = word_data.get('Example Sentences', '')
                updated_count += 1
            else:
                # Insert new word
                word = Word(
                    word=word_name,
                    definition=word_data.get('Definition', ''),
                    part_of_speech=word_data.get('Part of Speech', ''),
                    etymology=word_data.get('Etymology', ''),
                    chapter=word_data.get('Chapter', ''),
                    concept=word_data.get('Concept', ''),
                    tags=word_data.get('Tags', ''),
                    example_sentences=word_data.get('Example Sentences', '')
                )
                db.add(word)
                inserted_count += 1
        
        db.commit()
        print(f"Successfully synced {len(words_data)} words: {updated_count} updated, {inserted_count} inserted")
    except Exception as e:
        db.rollback()
        print(f"Error migrating data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_data()

