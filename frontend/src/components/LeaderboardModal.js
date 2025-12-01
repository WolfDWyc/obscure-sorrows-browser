import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './LeaderboardModal.css';
import { slugify } from '../utils/urlUtils';
import RatingButtons from './RatingButtons';

const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api';

const LeaderboardModal = ({ isOpen, onClose, onWordClick }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadLeaderboard();
    }
  }, [isOpen]);

  const loadLeaderboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/leaderboard`, {
        withCredentials: true
      });
      setLeaderboard(response.data);
    } catch (err) {
      console.error('Error loading leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleWordClick = (word) => {
    const wordSlug = slugify(word);
    onWordClick(wordSlug);
    onClose();
  };

  // Convert leaderboard entry to word format for RatingButtons
  const entryToWord = (entry) => {
    return {
      id: entry.word_id,
      word: entry.word,
      user_rating: null, // No user rating in leaderboard context
      rating_stats: {
        thumbs_up: entry.thumbs_up,
        thumbs_down: entry.thumbs_down,
        hyphen: entry.hyphen,
        total: entry.total_ratings,
        percentages: {
          thumbs_up: entry.total_ratings > 0 ? Math.round((entry.thumbs_up / entry.total_ratings) * 100) : 0,
          thumbs_down: entry.total_ratings > 0 ? Math.round((entry.thumbs_down / entry.total_ratings) * 100) : 0,
          hyphen: entry.total_ratings > 0 ? Math.round((entry.hyphen / entry.total_ratings) * 100) : 0
        }
      }
    };
  };

  if (!isOpen) return null;

  return (
    <div className="leaderboard-modal-overlay" onClick={onClose}>
      <div className="leaderboard-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="leaderboard-header">
          <div className="leaderboard-title-container">
            <h2 className="leaderboard-title">Top words</h2>
            <button
              className="leaderboard-info-btn"
              onClick={() => setShowInfo(!showInfo)}
              aria-label="How ranking is calculated"
            >
              ℹ
            </button>
            {showInfo && (
              <div className="leaderboard-info-tooltip">
                <p>Words are ranked using a Bayesian average that balances both rating percentage and total number of ratings. This prevents words with few ratings from ranking too high while rewarding words with both good ratings and more votes.</p>
              </div>
            )}
          </div>
          <button className="leaderboard-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="leaderboard-body">
          {loading ? (
            <div className="leaderboard-loading">Loading...</div>
          ) : (
            <div className="leaderboard-list">
              {leaderboard.map((entry, index) => (
                <div
                  key={entry.word_id}
                  className="leaderboard-item"
                  onClick={() => handleWordClick(entry.word)}
                >
                  <div className="leaderboard-rank">#{index + 1}</div>
                  <div className="leaderboard-word-name">{entry.word}</div>
                  <div className="leaderboard-rating" onClick={(e) => e.stopPropagation()}>
                    <RatingButtons word={entryToWord(entry)} onRate={() => {}} gap={0.02} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LeaderboardModal;

