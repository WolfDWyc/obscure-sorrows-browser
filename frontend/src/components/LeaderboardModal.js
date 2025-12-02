import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiX, FiStar } from 'react-icons/fi';
import './LeaderboardModal.css';
import { slugify } from '../utils/urlUtils';

const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api';

const LeaderboardModal = ({ isOpen, onClose, onWordClick }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);

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

  if (!isOpen) return null;

  return (
    <div className="leaderboard-modal-overlay" onClick={onClose}>
      <div className="leaderboard-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="leaderboard-header">
          <h2 className="leaderboard-title">Top words</h2>
          <button className="leaderboard-close" onClick={onClose} aria-label="Close">
            <FiX />
          </button>
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
                    <div className="leaderboard-rating-value">
                      <FiStar className="leaderboard-star-icon" />
                      <span>{entry.average > 0 ? entry.average.toFixed(2) : '—'}</span>
                    </div>
                    <div className="leaderboard-voters-count">
                      {entry.total_ratings} {entry.total_ratings === 1 ? 'voter' : 'voters'}
                    </div>
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

