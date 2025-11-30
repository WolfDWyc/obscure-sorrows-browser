# Dictionary of Obscure Sorrows - Web Application

A modern web application for exploring "The Dictionary of Obscure Sorrows" with rating and navigation features.

## Tech Stack

- **Frontend**: React 18 with modern components
- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Containerization**: Docker

## Features

- **Random Word Display**: Shows a random unrated word on entry
- **Rating System**: Thumbs up/down/hyphen ratings (one-time, server-side)
- **Rating Statistics**: See percentage breakdown of all user ratings
- **Navigation**: Next/Previous word buttons
- **Cookie-based User Tracking**: Automatic user identification
- **Dark Mode**: Beautiful dark theme with Merriweather/Playfair Display fonts
- **Mobile-First**: Responsive design optimized for mobile devices

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python migrate_data.py  # Migrates dictionary.json to SQLite
python run.py  # Starts FastAPI server on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm start  # Starts React dev server on http://localhost:3000
```

The frontend is configured to proxy API requests to `http://localhost:8000` during development.

## Production Deployment

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t obscure-sorrows .
docker run -p 8000:8000 obscure-sorrows
```

The application will be available at `http://localhost:8000`.

### Manual Production Build

```bash
# Build React app
cd frontend
npm run build

# Run FastAPI (serves both API and React build)
cd ../backend
python run.py
```

## API Endpoints

- `GET /api/random-word` - Get a random unrated word
- `GET /api/word/{word_id}` - Get a specific word by ID
- `POST /api/rate` - Rate a word (body: `{word_id: int, rating: int}` where rating is -1, 0, or 1)
- `GET /api/next-word-id/{current_id}` - Get next word ID
- `GET /api/prev-word-id/{current_id}` - Get previous word ID
- `GET /api/rated-words` - Get list of rated word IDs for current user

## Project Structure

```
.
├── backend/
│   ├── main.py           # FastAPI application
│   ├── database.py       # SQLAlchemy models
│   ├── migrate_data.py   # JSON to SQLite migration
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   ├── components/   # React components
│   │   └── index.css     # Global styles
│   └── package.json      # Node dependencies
├── dictionary.json       # Source data (274 words)
├── Dockerfile            # Docker build configuration
└── docker-compose.yml    # Docker Compose configuration
```

## Notes

- User identification is cookie-based (UUID stored in cookie)
- Ratings are permanent (cannot change rating once set)
- Words are filtered to exclude already-rated words when possible
- All ratings are stored server-side with statistics
