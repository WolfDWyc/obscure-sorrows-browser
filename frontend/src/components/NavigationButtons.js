import React from 'react';
import './NavigationButtons.css';

const NavigationButtons = ({ onNext, loading }) => {
  return (
    <div className="navigation-buttons">
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

