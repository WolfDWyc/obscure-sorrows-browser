"""Migrate ratings from old system (-1/0/1) to new system (1-5 stars with types)."""
from sqlalchemy import inspect, text
from database import engine, SessionLocal, Rating, Base
import os

def check_schema_version():
    """Check if schema has been migrated to new rating system."""
    inspector = inspect(engine)
    if 'ratings' not in inspector.get_table_names():
        return False
    
    columns = {col['name']: col for col in inspector.get_columns('ratings')}
    
    # New schema has rating_type column
    return 'rating_type' in columns

def migrate_ratings():
    """Migrate old ratings to new system."""
    if check_schema_version():
        print("Schema already migrated. Skipping migration.")
        return
    
    print("Migrating ratings schema...")
    db = SessionLocal()
    
    try:
        # Add rating_type column if it doesn't exist
        # SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS, so we check first
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('ratings')}
        
        if 'rating_type' not in columns:
            print("Adding rating_type column...")
            db.execute(text("ALTER TABLE ratings ADD COLUMN rating_type VARCHAR DEFAULT 'overall'"))
            db.commit()
        
        # Migrate existing ratings: -1 -> 1 star, 0 -> 3 stars, 1 -> 5 stars
        print("Migrating existing ratings...")
        old_ratings = db.query(Rating).filter(Rating.rating.in_([-1, 0, 1])).all()
        
        migrated_count = 0
        for rating in old_ratings:
            # Convert old rating to new system
            if rating.rating == -1:
                new_rating = 1  # 1 star
            elif rating.rating == 0:
                new_rating = 3  # 3 stars
            elif rating.rating == 1:
                new_rating = 5  # 5 stars
            else:
                continue  # Skip if already migrated
            
            rating.rating = new_rating
            rating.rating_type = 'overall'  # Set type to overall for migrated ratings
            migrated_count += 1
        
        db.commit()
        print(f"Migrated {migrated_count} ratings to new system.")
        
        # Update any ratings that are already 1-5 but don't have rating_type
        print("Updating ratings without rating_type...")
        from sqlalchemy import or_, and_
        # Check if rating_type column exists and handle None values
        ratings_without_type = db.query(Rating).filter(
            and_(
                Rating.rating.between(1, 5),
                or_(
                    Rating.rating_type == None,
                    Rating.rating_type == '',
                    Rating.rating_type.is_(None)
                )
            )
        ).all()
        
        for rating in ratings_without_type:
            rating.rating_type = 'overall'
        
        db.commit()
        print(f"Updated {len(ratings_without_type)} ratings with rating_type.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_ratings()

