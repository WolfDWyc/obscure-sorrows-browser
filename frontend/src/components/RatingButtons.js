import React from 'react';
import { FiThumbsDown, FiThumbsUp, FiMinus } from 'react-icons/fi';
import './RatingButtons.css';

const RatingButtons = ({ word, onRate, gap }) => {
  if (!word) return null;

  const currentRating = word.user_rating;
  const stats = word.rating_stats || {};
  const hasStats = stats.total > 0;

  const gapStyle = gap !== undefined ? { gap: `${gap}rem` } : {};

  return (
    <div className="rating-container">
      <div className="rating-unified" style={gapStyle}>
        <button
          className={`rating-item thumbs-down ${currentRating === -1 ? 'active' : ''}`}
          onClick={() => onRate(-1)}
          aria-label="Thumbs down"
        >
          <span className="rating-icon">
            <FiThumbsDown />
          </span>
          {hasStats && (
            <>
              <span className="rating-percentage">{stats.percentages?.thumbs_down || 0}%</span>
              <span className="rating-count">({stats.thumbs_down || 0})</span>
            </>
          )}
          {currentRating === -1 && <span className="your-rating-badge">Your rating</span>}
        </button>
        <button
          className={`rating-item hyphen ${currentRating === 0 ? 'active' : ''}`}
          onClick={() => onRate(0)}
          aria-label="Indifferent"
        >
          <span className="rating-icon">
            <FiMinus />
          </span>
          {hasStats && (
            <>
              <span className="rating-percentage">{stats.percentages?.hyphen || 0}%</span>
              <span className="rating-count">({stats.hyphen || 0})</span>
            </>
          )}
          {currentRating === 0 && <span className="your-rating-badge">Your rating</span>}
        </button>
        <button
          className={`rating-item thumbs-up ${currentRating === 1 ? 'active' : ''}`}
          onClick={() => onRate(1)}
          aria-label="Thumbs up"
        >
          <span className="rating-icon">
            <FiThumbsUp />
          </span>
          {hasStats && (
            <>
              <span className="rating-percentage">{stats.percentages?.thumbs_up || 0}%</span>
              <span className="rating-count">({stats.thumbs_up || 0})</span>
            </>
          )}
          {currentRating === 1 && <span className="your-rating-badge">Your rating</span>}
        </button>
      </div>
    </div>
  );
};

export default RatingButtons;

