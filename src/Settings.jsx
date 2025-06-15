import React, { useState, useEffect, useCallback } from 'react';
import Card from './components/card'; // Note the lowercase 'c' for 'card'

// Define the API_BASE_URL using the environment variable at the top level
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
const Settings = () => {
  const [config, setConfig] = useState({
    bybitApiKey: '',
    bybitApiSecret: '',
    paystackSecretKey: '',
    runIntervalMinutes: 5,
    email_alerts_enabled: false,
    email_username: '',
    email_password: '',
    alert_recipient_email: '',
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      setLoading(false);
      return;
    }

    try {
      // *** MODIFIED LINE HERE: Using API_BASE_URL and corrected endpoint for config ***
      const response = await fetch(`${API_BASE_URL}/api/config`, { // Changed from /api/status
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setConfig(data); // Assuming 'data' directly contains the config object
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to fetch configuration.');
      }
    } catch (err) {
      console.error('Error fetching config:', err);
      setError('Network error or server unreachable. Could not load configuration.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      return;
    }

    try {
      // *** MODIFIED LINE HERE: Using API_BASE_URL for saving config ***
      const response = await fetch(`${API_BASE_URL}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(config),
      });

      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        fetchConfig(); // Refresh config to show truncated keys
      } else {
        setError(data.message || 'Failed to save configuration.');
      }
    } catch (err) {
      console.error('Error saving config:', err);
      setError('Network error or server unreachable. Could not save configuration.');
    
    }
  };

  return (
    <div className="settings-page">
      <Card title="Bot Configuration">
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}
        {loading ? (
          <div className="loading-spinner">Loading settings...</div>
        ) : (
          <form onSubmit={handleSubmit} className="form-section">
            <div className="form-group">
              <label htmlFor="bybitApiKey">Bybit API Key:</label>
              <input
                type="text"
                id="bybitApiKey"
                name="bybitApiKey"
                value={config.bybitApiKey}
                onChange={handleInputChange}
                placeholder="Enter full API key (masked after save)"
              />
            </div>
            <div className="form-group">
              <label htmlFor="bybitApiSecret">Bybit API Secret:</label>
              <input
                type="password"
                id="bybitApiSecret"
                name="bybitApiSecret"
                value={config.bybitApiSecret}
                onChange={handleInputChange}
                placeholder="Enter full API secret (masked after save)"
              />
            </div>
            <div className="form-group">
              <label htmlFor="paystackSecretKey">Paystack Secret Key:</label>
              <input
                type="password"
                id="paystackSecretKey"
                name="paystackSecretKey"
                value={config.paystackSecretKey}
                onChange={handleInputChange}
                placeholder="Enter full Paystack secret key (masked after save)"
              />
            </div>
            <div className="form-group">
              <label htmlFor="runIntervalMinutes">Run Interval (minutes):</label>
              <input
                type="number"
                id="runIntervalMinutes"
                name="runIntervalMinutes"
                value={config.runIntervalMinutes}
                onChange={handleInputChange}
                min="0.5"
                step="0.5"
                required
              />
            </div>
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="emailAlertsEnabled"
                name="email_alerts_enabled"
                checked={config.email_alerts_enabled}
                onChange={handleInputChange}
              />
              <label htmlFor="emailAlertsEnabled">Enable Email Alerts</label>
            </div>
            {config.email_alerts_enabled && (
              <>
                <div className="form-group">
                  <label htmlFor="emailUsername">Email Username (Sender):</label>
                  <input
                    type="email"
                    id="emailUsername"
                    name="email_username"
                    value={config.email_username}
                    onChange={handleInputChange}
                    placeholder="e.g., your_bot_email@gmail.com"
                    required={config.email_alerts_enabled}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="emailPassword">Email App Password (Sender):</label>
                  <input
                    type="password"
                    id="emailPassword"
                    name="email_password"
                    value={config.email_password}
                    onChange={handleInputChange}
                    placeholder="Use a Gmail App Password if 2FA is on (masked after save)"
                    required={config.email_alerts_enabled}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="alertRecipientEmail">Alert Recipient Email:</label>
                  <input
                    type="email"
                    id="alertRecipientEmail"
                    name="alert_recipient_email"
                    value={config.alert_recipient_email}
                    onChange={handleInputChange}
                    placeholder="e.g., your_personal_email@example.com"
                    required={config.email_alerts_enabled}
                  />
                </div>
              </>
            )}
            <button type="submit" className="btn btn-success">Save Configuration</button>
          </form>
        )}
      </Card>
    </div>
  );
};

export default Settings;