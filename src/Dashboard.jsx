import React, { useState, useEffect, useCallback } from 'react';
import Card from './components/card'; // Use the new Card component

// Define the API_BASE_URL using the environment variable at the top level
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

// Removed onLogout prop from function signature as it's no longer passed from App.jsx
// setCurrentPage is still needed for navigation to Logs page.
const Dashboard = ({ setCurrentPage }) => {
  const [botStatus, setBotStatus] = useState('Loading...');
  const [lastRunTime, setLastRunTime] = useState('N/A');
  const [numOrders, setNumOrders] = useState(0);
  const [numPayments, setNumPayments] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [logMessages, setLogMessages] = useState([]);

  const fetchBotStatus = useCallback(async () => {
    // Removed authentication token check
    // const token = localStorage.getItem('token');
    // if (!token) {
    //   // If authentication was required, App.jsx would handle redirect.
    //   // Now, we proceed without a token.
    //   return;
    // }
    try {
      // API call no longer requires Authorization header
      const response = await fetch(`${API_BASE_URL}/api/status`, {
        // Removed headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBotStatus(data.status);
        setLastRunTime(data.lastRunTime || 'N/A');
        setNumOrders(data.numOrders);
        setNumPayments(data.numPayments);
      } else {
        console.error('Failed to fetch bot status:', response.statusText);
        setBotStatus('Error (API)');
      }
    } catch (error) {
      console.error('Error fetching bot status:', error);
      setBotStatus('Error (Network)');
    }
  }, []); // Dependency array changed, token removed

  const fetchBotLogs = useCallback(async () => {
    // Removed authentication token check
    // const token = localStorage.getItem('token');
    // if (!token) return; // Proceed without token
    try {
      // API call no longer requires Authorization header
      const response = await fetch(`${API_BASE_URL}/api/logs`, {
        // Removed headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setLogMessages(data);
      } else {
        console.error('Failed to fetch bot logs:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching bot logs:', error);
    }
  }, []); // Dependency array changed, token removed

  useEffect(() => {
    fetchBotStatus();
    fetchBotLogs();

    const statusInterval = setInterval(fetchBotStatus, 5000); // Poll status every 5 seconds
    const logInterval = setInterval(fetchBotLogs, 2000); // Poll logs every 2 seconds

    return () => {
      clearInterval(statusInterval);
      clearInterval(logInterval);
    };
  }, [fetchBotStatus, fetchBotLogs]);

  const handleRunBot = async () => {
    setLoading(true);
    setMessage('');
    // Removed authentication token check
    // const token = localStorage.getItem('token');
    try {
      // API call no longer requires Authorization header
      const response = await fetch(`${API_BASE_URL}/api/trigger-bot-run`, {
        method: 'POST',
        // Removed headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setMessage(data.message);
      if (response.ok) {
        fetchBotStatus(); // Update status immediately
      }
    } catch (error) {
      console.error('Error running bot:', error);
      setMessage('Failed to trigger bot run. Network error or server unreachable.');
    } finally {
      setLoading(false);
    }
  };

  const handleStopBot = async () => {
    setLoading(true);
    setMessage('');
    // Removed authentication token check
    // const token = localStorage.getItem('token');
    try {
      // API call no longer requires Authorization header
      const response = await fetch(`${API_BASE_URL}/api/stop-bot`, {
        method: 'POST',
        // Removed headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setMessage(data.message);
      if (response.ok) {
        fetchBotStatus(); // Update status immediately
      }
    } catch (error) {
      console.error('Error stopping bot:', error);
      setMessage('Failed to send stop signal. Network error or server unreachable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="button-controls">
        <button className="btn btn-success" onClick={handleRunBot} disabled={loading || botStatus.startsWith('Running')}>
          Run Bot
        </button>
        <button className="btn btn-danger" onClick={handleStopBot} disabled={loading || botStatus.startsWith('Stopped') || botStatus.startsWith('Idle')}>
          Stop Bot
        </button>
      </div>

      {message && <div className="info-message">{message}</div>}

      <div className="dashboard-grid">
        <Card title="Bot Status">
          <p>Status: <strong>{botStatus}</strong></p>
          <p>Last Run: {lastRunTime}</p>
        </Card>
        <Card title="Orders & Payments Summary">
          <p>Total Orders: {numOrders}</p>
          <p>Total Payments: {numPayments}</p>
        </Card>
      </div>

      <Card title="Bot Logs">
        <div className="log-viewer">
          {logMessages.length > 0 ? (
            logMessages.map((log, index) => (
              <p key={index} className="log-entry">{log}</p>
            ))
          ) : (
            <p>No logs available.</p>
          )}
        </div>
        <button className="btn" onClick={() => setCurrentPage('Logs')} style={{ marginTop: '1rem' }}>View All Logs</button>
      </Card>
    </div>
  );
};

export default Dashboard;
