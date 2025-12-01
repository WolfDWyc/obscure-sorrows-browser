import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import Header from './components/Header';
import WordCard from './components/WordCard';
import NavigationButtons from './components/NavigationButtons';
import RatingButtons from './components/RatingButtons';
import LeaderboardButton from './components/LeaderboardButton';
import LeaderboardModal from './components/LeaderboardModal';
import { slugify } from './utils/urlUtils';

const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api';

function WordPage() {
  const { wordSlug } = useParams();
  const navigate = useNavigate();
  const [currentWord, setCurrentWord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLeaderboard, setShowLeaderboard] = useState(false);

  useEffect(() => {
    loadWordFromSlug(wordSlug);
  }, [wordSlug]);

  const loadWordFromSlug = async (slug) => {
    try {
      setLoading(true);
      setError(null);
      
      // React Router already decodes the URL parameter, so we have the word name
      // Axios will automatically encode it when making the request
      const wordName = slug;
      
      // Load word by name (API accepts both ID and name)
      const response = await axios.get(`${API_BASE}/word/${wordName}`, {
        withCredentials: true
      });
      const word = response.data;
      setCurrentWord(word);
    } catch (err) {
      console.error('Error loading word:', err);
      if (err.response?.status === 404) {
        setError('Word not found');
      } else {
        setError('Failed to load word. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadRandomWord = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/random-word`, {
        withCredentials: true
      });
      const word = response.data;
      
      // Update URL to the new word
      const wordSlug = slugify(word.word);
      navigate(`/word/${wordSlug}`, { replace: false });
    } catch (err) {
      console.error('Error loading word:', err);
      setError('Failed to load word. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadWordById = async (wordId) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/word/${wordId}`, {
        withCredentials: true
      });
      return response.data;
    } catch (err) {
      console.error('Error loading word:', err);
      setError('Failed to load word. Please try again.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    // Load a random unrated word and update URL
    await loadRandomWord();
  };

  const handleRate = async (rating) => {
    if (!currentWord) return;
    
    // If clicking the same rating, unrate it
    if (currentWord.user_rating === rating) {
      rating = null;
    }
    
    try {
      if (rating === null) {
        // Unrate - delete the rating
        await axios.delete(
          `${API_BASE}/rate/${currentWord.id}`,
          {
            withCredentials: true
          }
        );
      } else {
        // Rate or update rating
        await axios.post(
          `${API_BASE}/rate`,
          {
            word_id: currentWord.id,
            rating: rating
          },
          {
            withCredentials: true
          }
        );
      }
      
      // Reload word to get updated stats
      const updatedWord = await loadWordById(currentWord.id);
      if (updatedWord) {
        setCurrentWord(updatedWord);
      }
    } catch (err) {
      console.error('Error rating word:', err);
    }
  };

  if (loading && !currentWord) {
    return (
      <div className="app-container">
        <Header />
        <div className="app-content-wrapper">
          <div className="loading">Loading...</div>
        </div>
      </div>
    );
  }

  if (error && !currentWord) {
    return (
      <div className="app-container">
        <Header />
        <div className="app-content-wrapper">
          <div className="error">{error}</div>
          <button onClick={loadRandomWord} className="retry-button">Try Again</button>
        </div>
      </div>
    );
  }

  const handleWordClick = (wordSlug) => {
    navigate(`/word/${wordSlug}`);
  };

  return (
    <div className="app-container">
      <Header />
      <div className="app-content-wrapper">
        {currentWord && (
          <>
            <div className="word-content">
              <WordCard word={currentWord} />
            </div>
            <div className="bottom-actions">
              <RatingButtons
                word={currentWord}
                onRate={handleRate}
              />
              <NavigationButtons
                onNext={handleNext}
                loading={loading}
              />
            </div>
          </>
        )}
      </div>
      <LeaderboardButton onClick={() => setShowLeaderboard(true)} />
      <LeaderboardModal
        isOpen={showLeaderboard}
        onClose={() => setShowLeaderboard(false)}
        onWordClick={handleWordClick}
      />
    </div>
  );
}

function HomePage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to a random word on initial load
    const loadRandomAndRedirect = async () => {
      try {
        const response = await axios.get(`${API_BASE}/random-word`, {
          withCredentials: true
        });
        const word = response.data;
        const wordSlug = slugify(word.word);
        navigate(`/word/${wordSlug}`, { replace: true });
      } catch (err) {
        console.error('Error loading random word:', err);
      }
    };
    loadRandomAndRedirect();
  }, [navigate]);

  return (
    <div className="app-container">
      <Header />
      <div className="app-content-wrapper">
        <div className="loading">Loading...</div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/word/:wordSlug" element={<WordPage />} />
    </Routes>
  );
}

export default App;

