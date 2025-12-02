import React, { useState } from 'react';
import { FiInfo, FiX } from 'react-icons/fi';
import './WordCard.css';

const WordCard = ({ word }) => {
  const [showEtymology, setShowEtymology] = useState(false);

  if (!word) return null;

  const tags = word.tags ? word.tags.split(';').map(t => t.trim()).filter(Boolean) : [];
  const sentences = word.example_sentences
    ? word.example_sentences.split(';').map(s => s.trim()).filter(Boolean)
    : [];

  return (
    <div className="word-card">
      <div className="word-header">
        <h1 className="word-name">{word.word}</h1>
        {(word.etymology || word.part_of_speech || word.chapter || word.concept) && (
          <button
            className="etymology-btn"
            onClick={() => setShowEtymology(!showEtymology)}
            aria-label="Show etymology and metadata"
          >
            <FiInfo />
          </button>
        )}
      </div>

      <div className="word-definition">
        {word.definition.split('\n').filter(part => part.trim() !== '').map((part, index, array) => (
          <React.Fragment key={index}>
            <span className={index === 0 ? 'definition-main' : 'definition-secondary'}>
              {part.trim()}
            </span>
            {index < array.length - 1 && ' '}
          </React.Fragment>
        ))}
      </div>

      {showEtymology && (word.etymology || word.part_of_speech || word.chapter || word.concept) && (
        <div className="etymology-modal" onClick={() => setShowEtymology(false)}>
          <div className="etymology-content" onClick={(e) => e.stopPropagation()}>
            <button className="etymology-close" onClick={() => setShowEtymology(false)} aria-label="Close">
              <FiX />
            </button>
            <h3>Details</h3>
            {word.part_of_speech && (
              <div className="etymology-pos">{word.part_of_speech}</div>
            )}
            {word.etymology && (
              <p>{word.etymology}</p>
            )}
            {(word.chapter || word.concept) && (
              <div className="etymology-meta">
                {word.chapter && (
                  <div className="etymology-meta-item">
                    <span className="etymology-meta-label">Chapter:</span>
                    <span className="etymology-meta-value">{word.chapter}</span>
                  </div>
                )}
                {word.concept && (
                  <div className="etymology-meta-item">
                    <span className="etymology-meta-label">Concept:</span>
                    <span className="etymology-meta-value">{word.concept}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {sentences.length > 0 && (
        <div className="example-sentences">
          <h3>Example Sentences</h3>
          <ul>
            {sentences.map((sentence, idx) => (
              <li key={idx}>{sentence}</li>
            ))}
          </ul>
        </div>
      )}

      {tags.length > 0 && (
        <div className="word-tags">
          {tags.map((tag, idx) => (
            <span key={idx} className="tag">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
};

export default WordCard;

