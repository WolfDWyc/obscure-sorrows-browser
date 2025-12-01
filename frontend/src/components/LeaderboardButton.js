import React from 'react';
import './LeaderboardButton.css';

const RankingIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="12" width="4" height="8" rx="1" />
    <rect x="10" y="8" width="4" height="12" rx="1" />
    <rect x="17" y="4" width="4" height="16" rx="1" />
  </svg>
);

const LeaderboardButton = ({ onClick }) => {
  return (
    <button
      className="leaderboard-button"
      onClick={onClick}
      aria-label="Show leaderboard"
    >
      <RankingIcon />
    </button>
  );
};

export default LeaderboardButton;

