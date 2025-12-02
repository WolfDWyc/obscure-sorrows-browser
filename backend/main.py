"""FastAPI backend for Dictionary of Obscure Sorrows."""
from fastapi import FastAPI, Depends, HTTPException, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional, List
import uuid
import os
from pathlib import Path

from database import get_db, Word, Rating, init_db
from pydantic import BaseModel
import os

# Initialize database
init_db()

# Migrate ratings schema if needed
def migrate_ratings_schema():
    """Migrate ratings from old system to new system if needed."""
    try:
        print("Checking rating schema...")
        import migrate_ratings
        migrate_ratings.migrate_ratings()
        print("Rating schema check complete.")
    except Exception as e:
        print(f"Error checking rating schema: {e}")
        import traceback
        traceback.print_exc()

# Migrate ratings on startup
migrate_ratings_schema()

# Reload word data from dictionary.json on every startup
def sync_word_data():
    """Reload word data from dictionary.json, preserving user ratings."""
    from sqlalchemy.orm import Session
    from database import SessionLocal
    import traceback
    
    try:
        print("Syncing word data from dictionary.json...")
        import migrate_data
        migrate_data.migrate_data()
        print("Word data sync complete.")
    except Exception as e:
        print(f"Error syncing word data: {e}")
        traceback.print_exc()

# Sync word data on startup (preserves user ratings)
sync_word_data()

app = FastAPI(title="Dictionary of Obscure Sorrows API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class WordResponse(BaseModel):
    id: int
    word: str
    definition: str
    part_of_speech: Optional[str]
    etymology: Optional[str]
    chapter: Optional[str]
    concept: Optional[str]
    tags: Optional[str]
    example_sentences: Optional[str]
    rating_stats: dict = {}  # Contains stats for each rating type: overall, relatability, usefulness, name

    class Config:
        from_attributes = True


class RatingRequest(BaseModel):
    word_id: int
    rating: int  # 1-5 stars
    rating_type: str = 'overall'  # 'overall', 'relatability', 'usefulness', 'name'


class RatingStats(BaseModel):
    average: float
    total: int
    user_rating: Optional[int] = None


def get_or_create_user_id(user_id: Optional[str] = Cookie(None)) -> Optional[str]:
    """Get existing user ID from cookie or return None if needs to be created."""
    if not user_id or user_id == "None":
        return None
    return user_id


def get_rating_stats(db: Session, word_id: int, rating_type: str = 'overall', user_id: Optional[str] = None) -> dict:
    """Get rating statistics for a word and rating type."""
    # Get all ratings for this word and type
    ratings_query = db.query(Rating).filter(
        Rating.word_id == word_id,
        Rating.rating_type == rating_type
    )
    
    ratings = ratings_query.all()
    total = len(ratings)
    
    if total == 0:
        return {
            "average": 0.0,
            "total": 0,
            "user_rating": None
        }
    
    # Calculate average
    total_rating = sum(r.rating for r in ratings)
    average = round(total_rating / total, 1)
    
    # Get user's rating if user_id provided
    user_rating = None
    if user_id:
        user_rating_obj = ratings_query.filter(Rating.user_id == user_id).first()
        if user_rating_obj:
            user_rating = user_rating_obj.rating
    
    return {
        "average": average,
        "total": total,
        "user_rating": user_rating
    }


@app.get("/api/random-word", response_model=WordResponse)
async def get_random_word(
    response: Response,
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Get a random word that the user hasn't rated yet."""
    user_id = get_or_create_user_id(user_id)
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="user_id", value=user_id, max_age=31536000, httponly=True, samesite="lax")
    
    # Get all rated word IDs for this user (only overall ratings count)
    rated_word_ids = {r.word_id for r in db.query(Rating.word_id).filter(
        Rating.user_id == user_id,
        Rating.rating_type == 'overall'
    ).all()}
    
    # Get a random word that hasn't been rated
    query = db.query(Word)
    if rated_word_ids:
        query = query.filter(~Word.id.in_(rated_word_ids))
    
    word = query.order_by(func.random()).first()
    
    if not word:
        # All words rated, return any random word
        word = db.query(Word).order_by(func.random()).first()
    
    if not word:
        raise HTTPException(status_code=404, detail="No words found")
    
    # Get rating stats for all types
    rating_types = ['overall', 'relatability', 'usefulness', 'name']
    stats = {}
    for rating_type in rating_types:
        stats[rating_type] = get_rating_stats(db, word.id, rating_type, user_id)
    
    response = WordResponse(
        id=word.id,
        word=word.word,
        definition=word.definition,
        part_of_speech=word.part_of_speech,
        etymology=word.etymology,
        chapter=word.chapter,
        concept=word.concept,
        tags=word.tags,
        example_sentences=word.example_sentences,
        rating_stats=stats
    )
    
    return response


@app.get("/api/word/{word_identifier}", response_model=WordResponse)
async def get_word(
    word_identifier: str,
    response: Response,
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Get a specific word by ID (integer) or name (string)."""
    user_id = get_or_create_user_id(user_id)
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="user_id", value=user_id, max_age=31536000, httponly=True, samesite="lax")
    
    # Try to parse as integer ID first
    word = None
    if word_identifier.isdigit():
        word = db.query(Word).filter(Word.id == int(word_identifier)).first()
    
    # If not found by ID, try by word name
    if not word:
        word = db.query(Word).filter(Word.word == word_identifier).first()
    
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    
    # Get rating stats for all types
    rating_types = ['overall', 'relatability', 'usefulness', 'name']
    stats = {}
    for rating_type in rating_types:
        stats[rating_type] = get_rating_stats(db, word.id, rating_type, user_id)
    
    response = WordResponse(
        id=word.id,
        word=word.word,
        definition=word.definition,
        part_of_speech=word.part_of_speech,
        etymology=word.etymology,
        chapter=word.chapter,
        concept=word.concept,
        tags=word.tags,
        example_sentences=word.example_sentences,
        rating_stats=stats
    )
    
    return response


@app.post("/api/rate")
async def rate_word(
    rating_req: RatingRequest,
    response: Response,
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Rate a word. Can update existing rating."""
    user_id = get_or_create_user_id(user_id)
    
    # Set cookie if not present
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="user_id", value=user_id, max_age=31536000, httponly=True, samesite="lax")  # 1 year
    
    # Check if word exists
    word = db.query(Word).filter(Word.id == rating_req.word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    
    # Validate rating
    if rating_req.rating not in [1, 2, 3, 4, 5]:
        raise HTTPException(status_code=400, detail="Rating must be 1-5 stars")
    
    # Validate rating type
    if rating_req.rating_type not in ['overall', 'relatability', 'usefulness', 'name']:
        raise HTTPException(status_code=400, detail="Invalid rating type")
    
    # Check if user already rated this word for this type
    existing_rating = db.query(Rating).filter(
        Rating.user_id == user_id,
        Rating.word_id == rating_req.word_id,
        Rating.rating_type == rating_req.rating_type
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_req.rating
        db.commit()
    else:
        # Create new rating
        rating = Rating(
            user_id=user_id,
            word_id=rating_req.word_id,
            rating_type=rating_req.rating_type,
            rating=rating_req.rating
        )
        db.add(rating)
        db.commit()
    
    # Return updated stats for this rating type
    stats = get_rating_stats(db, rating_req.word_id, rating_req.rating_type, user_id)
    return {"message": "Rating saved", "stats": stats}


@app.delete("/api/rate/{word_id}")
async def unrate_word(
    word_id: int,
    rating_type: str = 'overall',
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Remove rating for a word."""
    
    user_id = get_or_create_user_id(user_id)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Check if word exists
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    
    # Validate rating type
    if rating_type not in ['overall', 'relatability', 'usefulness', 'name']:
        raise HTTPException(status_code=400, detail="Invalid rating type")
    
    # Find and delete the rating
    existing_rating = db.query(Rating).filter(
        Rating.user_id == user_id,
        Rating.word_id == word_id,
        Rating.rating_type == rating_type
    ).first()
    
    if existing_rating:
        db.delete(existing_rating)
        db.commit()
    
    # Get updated stats
    stats = get_rating_stats(db, word_id, rating_type, user_id)
    
    return {"message": "Rating removed", "stats": stats}


@app.get("/api/next-word-id/{current_id}")
async def get_next_word_id(
    current_id: int,
    response: Response,
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Get the next word ID in sequence."""
    user_id = get_or_create_user_id(user_id)
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="user_id", value=user_id, max_age=31536000, httponly=True, samesite="lax")
    
    # Get next word (by ID)
    next_word = db.query(Word).filter(Word.id > current_id).order_by(Word.id).first()
    
    if not next_word:
        # Wrap around to first word
        next_word = db.query(Word).order_by(Word.id).first()
    
    if not next_word:
        raise HTTPException(status_code=404, detail="No words found")
    
    return {"word_id": next_word.id}


@app.get("/api/prev-word-id/{current_id}")
async def get_prev_word_id(
    current_id: int,
    response: Response,
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Get the previous word ID in sequence."""
    user_id = get_or_create_user_id(user_id)
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="user_id", value=user_id, max_age=31536000, httponly=True, samesite="lax")
    
    # Get previous word (by ID)
    prev_word = db.query(Word).filter(Word.id < current_id).order_by(Word.id.desc()).first()
    
    if not prev_word:
        # Wrap around to last word
        prev_word = db.query(Word).order_by(Word.id.desc()).first()
    
    if not prev_word:
        raise HTTPException(status_code=404, detail="No words found")
    
    return {"word_id": prev_word.id}


@app.get("/api/rated-words")
async def get_rated_words(
    response: Response,
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Get list of word IDs that the user has rated."""
    user_id = get_or_create_user_id(user_id)
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="user_id", value=user_id, max_age=31536000, httponly=True, samesite="lax")
    
    rated_ids = [r.word_id for r in db.query(Rating.word_id).filter(Rating.user_id == user_id).all()]
    return {"rated_word_ids": rated_ids}


class LeaderboardEntry(BaseModel):
    word_id: int
    word: str
    average: float
    total_ratings: int


@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    db: Session = Depends(get_db)
):
    """Get leaderboard of all words sorted by average rating (overall only)."""
    # Get all words with their rating stats
    words = db.query(Word).all()
    
    leaderboard = []
    for word in words:
        # Only use overall rating for leaderboard
        stats = get_rating_stats(db, word.id, 'overall')
        average = stats.get("average", 0.0)
        total = stats.get("total", 0)
        
        leaderboard.append((
            average,  # For sorting
            total,  # For tie-breaking
            LeaderboardEntry(
                word_id=word.id,
                word=word.word,
                average=average,
                total_ratings=total
            )
        ))
    
    # Sort by average (descending), then by total_ratings (descending) for ties
    leaderboard.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    # Extract just the entries (without sorting scores)
    return [entry for _, _, entry in leaderboard]


# Serve React app in production
# When running from /app/backend, go up one level to /app, then to frontend/build
frontend_build = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_build / "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for all non-API routes."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = frontend_build / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_build / "index.html")

