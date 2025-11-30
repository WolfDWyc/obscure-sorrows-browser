import React from 'react';
import './NavigationButtons.css';

const NavigationButtons = ({ onNext, onPrev, canGoPrev, loading }) => {
  return (
    <div className="navigation-buttons">
      {canGoPrev && (
        <button
          className="nav-btn prev-btn"
          onClick={onPrev}
          disabled={loading}
          aria-label="Previous word"
        >
          Previous
        </button>
      )}
      <button
        className="nav-btn next-btn main-btn"
        onClick={onNext}
        disabled={loading}
        aria-label="Random word"
      >
        Random Word
      </button>
    </div>
  );
};

export default NavigationButtons;

