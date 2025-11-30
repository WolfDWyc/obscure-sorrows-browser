import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="app-header">
      <h1 className="header-title">Obscure Sorrows Browser</h1>
      <p className="header-subtitle">
        From <a href="https://www.thedictionaryofobscuresorrows.com" target="_blank" rel="noopener noreferrer" className="header-link">The Dictionary of Obscure Sorrows</a>
      </p>
    </header>
  );
};

export default Header;

