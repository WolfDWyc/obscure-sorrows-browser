import React from 'react';
import './RatingButtons.css';

const ThumbsDownIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
  </svg>
);

const HyphenIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

const ThumbsUpIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
  </svg>
);

const RatingButtons = ({ word, onRate }) => {
  if (!word) return null;

  const hasRated = word.user_rating !== null;
  const stats = word.rating_stats || {};

  return (
    <div className="rating-container">
      {!hasRated ? (
        <div className="rating-buttons">
          <button
            className="rating-btn thumbs-down"
            onClick={() => onRate(-1)}
            aria-label="Thumbs down"
          >
            <ThumbsDownIcon />
          </button>
          <button
            className="rating-btn hyphen"
            onClick={() => onRate(0)}
            aria-label="Indifferent"
          >
            <HyphenIcon />
          </button>
          <button
            className="rating-btn thumbs-up"
            onClick={() => onRate(1)}
            aria-label="Thumbs up"
          >
            <ThumbsUpIcon />
          </button>
        </div>
      ) : (
        stats.total > 0 && (
          <div className="rating-stats">
            <div className={`stat-item ${word.user_rating === -1 ? 'user-rated' : ''}`}>
              <span className="stat-icon"><ThumbsDownIcon /></span>
              <span className="stat-value">{stats.percentages?.thumbs_down || 0}%</span>
              <span className="stat-count">({stats.thumbs_down || 0})</span>
              {word.user_rating === -1 && <span className="your-rating-label">Your rating</span>}
            </div>
            <div className={`stat-item ${word.user_rating === 0 ? 'user-rated' : ''}`}>
              <span className="stat-icon"><HyphenIcon /></span>
              <span className="stat-value">{stats.percentages?.hyphen || 0}%</span>
              <span className="stat-count">({stats.hyphen || 0})</span>
              {word.user_rating === 0 && <span className="your-rating-label">Your rating</span>}
            </div>
            <div className={`stat-item ${word.user_rating === 1 ? 'user-rated' : ''}`}>
              <span className="stat-icon"><ThumbsUpIcon /></span>
              <span className="stat-value">{stats.percentages?.thumbs_up || 0}%</span>
              <span className="stat-count">({stats.thumbs_up || 0})</span>
              {word.user_rating === 1 && <span className="your-rating-label">Your rating</span>}
            </div>
          </div>
        )
      )}
    </div>
  );
};

export default RatingButtons;

