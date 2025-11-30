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
        # Clear existing words
        db.query(Word).delete()
        db.commit()
        
        # Insert words
        for word_data in words_data:
            word = Word(
                word=word_data.get('Word', ''),
                definition=word_data.get('Definition', ''),
                part_of_speech=word_data.get('Part of Speech', ''),
                etymology=word_data.get('Etymology', ''),
                chapter=word_data.get('Chapter', ''),
                concept=word_data.get('Concept', ''),
                tags=word_data.get('Tags', ''),
                example_sentences=word_data.get('Example Sentences', '')
            )
            db.add(word)
        
        db.commit()
        print(f"Successfully migrated {len(words_data)} words to database")
    except Exception as e:
        db.rollback()
        print(f"Error migrating data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_data()

