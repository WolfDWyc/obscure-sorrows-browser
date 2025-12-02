"""Database setup and models for the Dictionary of Obscure Sorrows."""
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Determine database path
# If DATABASE_URL is set, use it directly
# Otherwise, try to find dictionary.db in the backend directory
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
    # For SQLite, ensure the directory exists if using a file path
    if "sqlite" in DATABASE_URL.lower():
        # Extract path from sqlite:///path format
        if "///" in DATABASE_URL:
            # Absolute path (sqlite:////absolute/path)
            db_path_str = DATABASE_URL.split("///", 1)[1]
        elif ":///" in DATABASE_URL:
            # Relative path (sqlite:///relative/path)
            db_path_str = DATABASE_URL.split(":///", 1)[1]
        else:
            db_path_str = None
        
        if db_path_str:
            if db_path_str.startswith("/"):
                # Absolute path
                db_path = Path(db_path_str)
            else:
                # Relative path - resolve from backend directory
                db_path = Path(__file__).parent / db_path_str
            # Ensure parent directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)
else:
    _db_path = Path(__file__).parent / "dictionary.db"
    # Ensure parent directory exists
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{_db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Word(Base):
    """Word model."""
    __tablename__ = "words"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, index=True, nullable=False)
    definition = Column(Text, nullable=False)
    part_of_speech = Column(String)
    etymology = Column(Text)
    chapter = Column(String)
    concept = Column(String)
    tags = Column(String)
    example_sentences = Column(Text)


class Rating(Base):
    """Rating model for user ratings."""
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Cookie-based user ID
    word_id = Column(Integer, index=True, nullable=False)
    rating_type = Column(String, nullable=False, default='overall')  # 'overall', 'relatability', 'usefulness', 'name'
    rating = Column(Integer, nullable=False)  # 1-5 stars (was -1/0/1 for old system)
    
    # Ensure one rating per user per word per type
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

