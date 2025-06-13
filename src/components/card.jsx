import React from 'react';
import './card.css'; // Import Card-specific CSS

const Card = ({ title, children, className = '' }) => {
  return (
    <div className={`card ${className}`}>
      {title && <div className="card-header">{title}</div>}
      <div className="card-content">
        {children}
      </div>
    </div>
  );
};

export default Card;
