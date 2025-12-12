import React from 'react';
import ReactDOM from 'react-dom/client';
import App from 'frontend/src/App';
import './index.css'; // Make sure this imports Tailwind directives

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);