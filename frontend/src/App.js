import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import Header from './components/Header';
import WordCard from './components/WordCard';
import NavigationButtons from './components/NavigationButtons';
import StarRating from './components/StarRating';
import LeaderboardButton from './components/LeaderboardButton';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';
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
    setShowDetailedRatings(false); // Reset detailed ratings when word changes
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

  const [showDetailedRatings, setShowDetailedRatings] = useState(false);

  const handleRate = async (ratingType, rating) => {
    if (!currentWord) return;
    
    try {
      if (rating === null) {
        // Unrate - delete the rating
        await axios.delete(
          `${API_BASE}/rate/${currentWord.id}?rating_type=${ratingType}`,
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
            rating: rating,
            rating_type: ratingType
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
              <WordCard 
                word={currentWord}
              />
            </div>
            <div className="bottom-actions">
              <div className="star-rating-wrapper">
                <StarRating
                  rating={currentWord.rating_stats?.overall?.user_rating}
                  average={currentWord.rating_stats?.overall?.average || 0}
                  total={currentWord.rating_stats?.overall?.total || 0}
                  onRate={(rating) => handleRate('overall', rating)}
                  size="normal"
                  showAverage={true}
                  averageLabel="Average"
                />
                {currentWord.rating_stats?.overall?.user_rating !== null && 
                 currentWord.rating_stats?.overall?.user_rating !== undefined && (
                  <button 
                    className="detailed-rating-link"
                    onClick={() => setShowDetailedRatings(!showDetailedRatings)}
                  >
                    Detailed ratings
                    {showDetailedRatings ? <FiChevronUp /> : <FiChevronDown />}
                  </button>
                )}
                {showDetailedRatings && currentWord.rating_stats?.overall?.user_rating !== null && 
                 currentWord.rating_stats?.overall?.user_rating !== undefined && (
                  <div className="detailed-ratings-expanded">
                    <div className="detailed-rating-sub-item">
                      <div className="detailed-rating-label">Relatability</div>
                      <StarRating
                        rating={currentWord.rating_stats?.relatability?.user_rating}
                        average={currentWord.rating_stats?.relatability?.average || 0}
                        total={currentWord.rating_stats?.relatability?.total || 0}
                        onRate={(rating) => handleRate('relatability', rating)}
                        size="small"
                        showAverage={true}
                      />
                    </div>
                    <div className="detailed-rating-sub-item">
                      <div className="detailed-rating-label">Usefulness</div>
                      <StarRating
                        rating={currentWord.rating_stats?.usefulness?.user_rating}
                        average={currentWord.rating_stats?.usefulness?.average || 0}
                        total={currentWord.rating_stats?.usefulness?.total || 0}
                        onRate={(rating) => handleRate('usefulness', rating)}
                        size="small"
                        showAverage={true}
                      />
                    </div>
                    <div className="detailed-rating-sub-item">
                      <div className="detailed-rating-label">Name</div>
                      <StarRating
                        rating={currentWord.rating_stats?.name?.user_rating}
                        average={currentWord.rating_stats?.name?.average || 0}
                        total={currentWord.rating_stats?.name?.total || 0}
                        onRate={(rating) => handleRate('name', rating)}
                        size="small"
                        showAverage={true}
                      />
                    </div>
                  </div>
                )}
              </div>
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

