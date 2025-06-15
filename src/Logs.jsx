import React, { useState, useEffect, useCallback, useRef } from 'react';
import Card from './components/card'; // Use the new Card component

// Define the API_BASE_URL using the environment variable at the top level
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

const Logs = () => {
  const [logMessages, setLogMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const logViewerRef = useRef(null); // Ref to scroll to bottom

  const fetchBotLogs = useCallback(async () => {
    setError('');
    setLoading(true); // Ensure loading is true when starting fetch
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      setLoading(false);
      return;
    }

    try {
      // *** MODIFIED LINE HERE: Using API_BASE_URL and correct endpoint for logs ***
      // Changed from /api/status to /api/logs, which is the more likely endpoint for logs.
      const response = await fetch(`${API_BASE_URL}/api/logs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        // Assuming your /api/logs endpoint returns an array of log messages
        setLogMessages(data);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to fetch logs.');
      }
    } catch (err) {
      console.error('Error fetching bot logs:', err);
      setError('Network error or server unreachable. Could not load logs.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBotLogs();
    const interval = setInterval(fetchBotLogs, 2000); // Refresh logs every 2 seconds
    return () => clearInterval(interval);
  }, [fetchBotLogs]);

  // Scroll to bottom of logs when messages update
  useEffect(() => {
    if (logViewerRef.current) {
      logViewerRef.current.scrollTop = logViewerRef.current.scrollHeight;
    }
  }, [logMessages]);

  return (
    <div className="logs-page">
      <Card title="Detailed Bot Logs">
        {loading ? (
          <div className="loading-spinner">Loading logs...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : logMessages.length === 0 ? (
          <p>No logs available.</p>
        ) : (
          <div className="log-viewer" ref={logViewerRef}>
            {logMessages.map((log, index) => (
              <p key={index} className="log-entry">{log}</p>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default Logs;