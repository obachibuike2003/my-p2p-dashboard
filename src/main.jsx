import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css'; // This line needs to correctly point to your index.css
import App from './App.jsx';

// Get the root element from your HTML (typically public/index.html)
const container = document.getElementById('root');
const root = createRoot(container); // Create a root.

// Render your App component into the root
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
