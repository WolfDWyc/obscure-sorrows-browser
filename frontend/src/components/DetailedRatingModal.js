import React from 'react';
import { FiX } from 'react-icons/fi';
import StarRating from './StarRating';
import './DetailedRatingModal.css';

const DetailedRatingModal = ({ isOpen, onClose, word, onRate }) => {
  if (!isOpen || !word) return null;

  const ratingStats = word.rating_stats || {};
  const overallStats = ratingStats.overall || {};
  const relatabilityStats = ratingStats.relatability || {};
  const usefulnessStats = ratingStats.usefulness || {};
  const nameStats = ratingStats.name || {};

  const handleRate = (ratingType) => (rating) => {
    onRate(ratingType, rating);
  };

  return (
    <div className="detailed-rating-modal-overlay" onClick={onClose}>
      <div className="detailed-rating-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="detailed-rating-close" onClick={onClose} aria-label="Close">
          <FiX />
        </button>
        
        <h2 className="detailed-rating-word-name">{word.word}</h2>
        
        <div className="detailed-rating-main">
          <StarRating
            rating={overallStats.user_rating}
            average={overallStats.average || 0}
            total={overallStats.total || 0}
            onRate={handleRate('overall')}
            size="large"
            showAverage={true}
          />
        </div>

        <div className="detailed-rating-sub-ratings">
          <div className="detailed-rating-sub-item">
            <div className="detailed-rating-label">Relatability</div>
            <StarRating
              rating={relatabilityStats.user_rating}
              average={relatabilityStats.average || 0}
              total={relatabilityStats.total || 0}
              onRate={handleRate('relatability')}
              size="small"
              showAverage={true}
            />
          </div>

          <div className="detailed-rating-sub-item">
            <div className="detailed-rating-label">Usefulness</div>
            <StarRating
              rating={usefulnessStats.user_rating}
              average={usefulnessStats.average || 0}
              total={usefulnessStats.total || 0}
              onRate={handleRate('usefulness')}
              size="small"
              showAverage={true}
            />
          </div>

          <div className="detailed-rating-sub-item">
            <div className="detailed-rating-label">Name</div>
            <StarRating
              rating={nameStats.user_rating}
              average={nameStats.average || 0}
              total={nameStats.total || 0}
              onRate={handleRate('name')}
              size="small"
              showAverage={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailedRatingModal;

