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

# Auto-migrate data if database is empty (first run only)
def check_and_migrate_data():
    """Check if database needs migration and run it if empty."""
    from sqlalchemy.orm import Session
    from database import SessionLocal
    import traceback
    
    try:
        db = SessionLocal()
        try:
            word_count = db.query(Word).count()
            if word_count == 0:
                # Database is empty, run migration
                print("Database is empty, running initial migration...")
                import migrate_data
                migrate_data.migrate_data()
                print("Migration complete.")
            else:
                print(f"Database already has {word_count} words, skipping migration.")
        finally:
            db.close()
    except Exception as e:
        print(f"Error checking/migrating database: {e}")
        traceback.print_exc()

# Run migration check on startup (only if database is empty)
check_and_migrate_data()

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
    user_rating: Optional[int] = None
    rating_stats: dict = {}

    class Config:
        from_attributes = True


class RatingRequest(BaseModel):
    word_id: int
    rating: int  # -1, 0, or 1


class RatingStats(BaseModel):
    thumbs_down: int
    hyphen: int
    thumbs_up: int
    total: int
    percentages: dict


def get_or_create_user_id(user_id: Optional[str] = Cookie(None)) -> Optional[str]:
    """Get existing user ID from cookie or return None if needs to be created."""
    if not user_id or user_id == "None":
        return None
    return user_id


def get_rating_stats(db: Session, word_id: int) -> dict:
    """Get rating statistics for a word."""
    stats = db.query(
        func.sum(case((Rating.rating == -1, 1), else_=0)).label('thumbs_down'),
        func.sum(case((Rating.rating == 0, 1), else_=0)).label('hyphen'),
        func.sum(case((Rating.rating == 1, 1), else_=0)).label('thumbs_up'),
        func.count(Rating.id).label('total')
    ).filter(Rating.word_id == word_id).first()
    
    if not stats or stats.total == 0:
        return {
            "thumbs_down": 0,
            "hyphen": 0,
            "thumbs_up": 0,
            "total": 0,
            "percentages": {
                "thumbs_down": 0,
                "hyphen": 0,
                "thumbs_up": 0
            }
        }
    
    total = stats.total or 0
    thumbs_down = stats.thumbs_down or 0
    hyphen = stats.hyphen or 0
    thumbs_up = stats.thumbs_up or 0
    
    return {
        "thumbs_down": thumbs_down,
        "hyphen": hyphen,
        "thumbs_up": thumbs_up,
        "total": total,
        "percentages": {
            "thumbs_down": round((thumbs_down / total * 100) if total > 0 else 0, 1),
            "hyphen": round((hyphen / total * 100) if total > 0 else 0, 1),
            "thumbs_up": round((thumbs_up / total * 100) if total > 0 else 0, 1)
        }
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
    
    # Get all rated word IDs for this user
    rated_word_ids = {r.word_id for r in db.query(Rating.word_id).filter(Rating.user_id == user_id).all()}
    
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
    
    # Get user's rating for this word
    user_rating = db.query(Rating).filter(
        Rating.user_id == user_id,
        Rating.word_id == word.id
    ).first()
    
    rating_value = user_rating.rating if user_rating else None
    
    # Get rating stats
    stats = get_rating_stats(db, word.id)
    
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
        user_rating=rating_value,
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
    
    # Get user's rating
    user_rating = db.query(Rating).filter(
        Rating.user_id == user_id,
        Rating.word_id == word.id
    ).first()
    
    rating_value = user_rating.rating if user_rating else None
    
    # Get rating stats
    stats = get_rating_stats(db, word.id)
    
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
        user_rating=rating_value,
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
    if rating_req.rating not in [-1, 0, 1]:
        raise HTTPException(status_code=400, detail="Rating must be -1, 0, or 1")
    
    # Check if user already rated this word
    existing_rating = db.query(Rating).filter(
        Rating.user_id == user_id,
        Rating.word_id == rating_req.word_id
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
            rating=rating_req.rating
        )
        db.add(rating)
        db.commit()
    
    # Return updated stats
    stats = get_rating_stats(db, rating_req.word_id)
    return {"message": "Rating saved", "stats": stats}


@app.delete("/api/rate/{word_id}")
async def unrate_word(
    word_id: int,
    response: Response,
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
    
    # Find and delete the rating
    existing_rating = db.query(Rating).filter(
        Rating.user_id == user_id,
        Rating.word_id == word_id
    ).first()
    
    if existing_rating:
        db.delete(existing_rating)
        db.commit()
    
    # Get updated stats
    stats = get_rating_stats(db, word_id)
    
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
    score: int  # likes - dislikes (net score)
    thumbs_up: int
    thumbs_down: int
    hyphen: int
    total_ratings: int


@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    db: Session = Depends(get_db)
):
    """Get leaderboard of all words sorted by Bayesian average score."""
    # Get all words with their rating stats
    words = db.query(Word).all()
    
    # Calculate global average for Bayesian prior
    all_stats = [get_rating_stats(db, word.id) for word in words]
    total_all_ratings = sum(s.get("total", 0) for s in all_stats)
    total_all_net = sum(s.get("thumbs_up", 0) - s.get("thumbs_down", 0) for s in all_stats)
    
    # Prior: average net score across all words (or 0 if no ratings)
    prior_rating = (total_all_net / total_all_ratings) if total_all_ratings > 0 else 0.0
    prior_weight = 10  # Minimum number of ratings to reach prior confidence
    
    leaderboard = []
    for word in words:
        stats = get_rating_stats(db, word.id)
        thumbs_up = stats.get("thumbs_up", 0)
        thumbs_down = stats.get("thumbs_down", 0)
        total = stats.get("total", 0)
        
        # Calculate Bayesian average score
        if total > 0:
            # Net score normalized: (thumbs_up - thumbs_down) / total
            average_rating = (thumbs_up - thumbs_down) / total
            # Bayesian average: weighted average between word's average and prior
            bayesian_score = (total * average_rating + prior_weight * prior_rating) / (total + prior_weight)
        else:
            # No ratings: use a very low score so words with any ratings rank higher
            bayesian_score = -1000.0
        
        # Store original net score for display, but use Bayesian score for sorting
        net_score = thumbs_up - thumbs_down
        
        # Store as tuple with Bayesian score for sorting
        leaderboard.append((
            bayesian_score,  # For sorting
            LeaderboardEntry(
                word_id=word.id,
                word=word.word,
                score=net_score,
                thumbs_up=thumbs_up,
                thumbs_down=thumbs_down,
                hyphen=stats.get("hyphen", 0),
                total_ratings=total
            )
        ))
    
    # Sort by Bayesian score (descending), then by total_ratings (descending) for ties
    leaderboard.sort(key=lambda x: (x[0], x[1].total_ratings), reverse=True)
    
    # Extract just the entries (without Bayesian scores)
    return [entry for _, entry in leaderboard]
    
    return leaderboard


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

