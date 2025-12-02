import React, { useState } from 'react';
import { FiStar } from 'react-icons/fi';
import './StarRating.css';

const StarRating = ({ 
  rating, 
  average, 
  total, 
  onRate, 
  size = 'normal',
  showAverage = true,
  disabled = false,
  averageLabel = 'Avg'
}) => {
  const [hoveredStar, setHoveredStar] = useState(null);
  
  const handleStarClick = (starValue) => {
    if (disabled) return;
    // If clicking the same rating, unrate it
    if (rating === starValue) {
      onRate(null);
      // Clear hover state when unrating
      setHoveredStar(null);
    } else {
      onRate(starValue);
    }
  };

  const handleStarHover = (starValue) => {
    if (disabled) return;
    setHoveredStar(starValue);
  };

  const handleMouseLeave = () => {
    if (disabled) return;
    setHoveredStar(null);
  };

  const sizeClass = size === 'large' ? 'large' : size === 'small' ? 'small' : 'normal';
  const hasRating = rating !== null && rating !== undefined;
  const hasStats = total > 0;

  return (
    <div className={`star-rating-container ${sizeClass}`}>
      <div 
        className="star-rating-stars"
        onMouseLeave={handleMouseLeave}
      >
        {[1, 2, 3, 4, 5].map((starValue) => {
          const isFilled = hoveredStar 
            ? starValue <= hoveredStar 
            : (hasRating && starValue <= rating);
          
          return (
            <button
              key={starValue}
              className={`star-button ${isFilled ? 'filled' : ''}`}
              onClick={() => handleStarClick(starValue)}
              onMouseEnter={() => handleStarHover(starValue)}
              disabled={disabled}
              aria-label={`Rate ${starValue} stars`}
            >
              <FiStar />
            </button>
          );
        })}
      </div>
      {showAverage && hasStats && (
        <span className="star-rating-average">
          {averageLabel}: <FiStar className="star-rating-average-icon" /> {average.toFixed(2)} <span className="star-rating-voters">({total})</span>
        </span>
      )}
    </div>
  );
};

export default StarRating;

