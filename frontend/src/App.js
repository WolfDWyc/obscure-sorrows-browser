import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Header from './components/Header';
import WordCard from './components/WordCard';
import NavigationButtons from './components/NavigationButtons';
import RatingButtons from './components/RatingButtons';

const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api';

function App() {
  const [currentWord, setCurrentWord] = useState(null);
  const [wordHistory, setWordHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load initial random word
  useEffect(() => {
    loadRandomWord();
  }, []);

  const loadRandomWord = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/random-word`, {
        withCredentials: true
      });
      const word = response.data;
      setCurrentWord(word);
      // Add to history, maintaining previous history
      setWordHistory(prev => {
        const exists = prev.some(w => w.id === word.id);
        if (exists) {
          const index = prev.findIndex(w => w.id === word.id);
          setHistoryIndex(index);
          return prev;
        }
        const newHistory = [...prev, word];
        setHistoryIndex(newHistory.length - 1);
        return newHistory;
      });
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
    // Load a random unrated word instead of sequential
    await loadRandomWord();
  };

  const handlePrev = async () => {
    if (historyIndex > 0) {
      const prevWord = wordHistory[historyIndex - 1];
      setCurrentWord(prevWord);
      setHistoryIndex(historyIndex - 1);
    } else if (historyIndex === 0 && wordHistory.length > 1) {
      // Load previous word from API
      const response = await axios.get(`${API_BASE}/prev-word-id/${currentWord.id}`, {
        withCredentials: true
      });
      const prevWordId = response.data.word_id;
      const prevWord = await loadWordById(prevWordId);
      
      if (prevWord) {
        const newHistory = [prevWord, ...wordHistory];
        setWordHistory(newHistory);
        setHistoryIndex(0);
        setCurrentWord(prevWord);
      }
    }
  };

  const handleRate = async (rating) => {
    if (!currentWord || currentWord.user_rating !== null) return;
    
    try {
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
      
      // Reload word to get updated stats
      const updatedWord = await loadWordById(currentWord.id);
      if (updatedWord) {
        setCurrentWord(updatedWord);
        // Update in history
        const newHistory = [...wordHistory];
        newHistory[historyIndex] = updatedWord;
        setWordHistory(newHistory);
      }
    } catch (err) {
      console.error('Error rating word:', err);
      if (err.response?.status === 400 && err.response?.data?.detail === 'Word already rated') {
        // Word was already rated, reload it
        const updatedWord = await loadWordById(currentWord.id);
        if (updatedWord) {
          setCurrentWord(updatedWord);
        }
      }
    }
  };

  if (loading && !currentWord) {
    return (
      <div className="app-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  if (error && !currentWord) {
    return (
      <div className="app-container">
        <div className="error">{error}</div>
        <button onClick={loadRandomWord} className="retry-button">Try Again</button>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header />
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
              onPrev={handlePrev}
              canGoPrev={historyIndex > 0}
              loading={loading}
            />
          </div>
        </>
      )}
    </div>
  );
}

export default App;

