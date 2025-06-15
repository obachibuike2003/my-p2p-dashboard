import React, { useState, useEffect, useCallback } from 'react';
import Card from './components/card'; // Use the new Card component

// Define the API_BASE_URL using the environment variable at the top level
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

const Payments = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPayments = useCallback(async () => {
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      setLoading(false);
      return;
    }

    try {
      // *** MODIFIED LINE HERE: Using API_BASE_URL and corrected endpoint for payments ***
      const response = await fetch(`${API_BASE_URL}/api/payments`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setPayments(data);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to fetch payments.');
      }
    } catch (err) {
      console.error('Error fetching payments:', err);
      setError('Network error or server unreachable. Could not load payments.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPayments();
    const interval = setInterval(fetchPayments, 10000); // Refresh payments every 10 seconds
    return () => clearInterval(interval);
  }, [fetchPayments]);

  return (
    <div className="payments-page">
      <Card title="All Payments">
        {loading ? (
          <div className="loading-spinner">Loading payments...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : payments.length === 0 ? (
          <p>No payments recorded yet.</p>
        ) : (
          <div className="responsive-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Payment ID</th>
                  <th>Client</th>
                  <th>Amount (NGN)</th>
                  <th>Bank Code</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{payment.id}</td>
                    <td>{payment.clientName}</td>
                    <td>{payment.amount.toLocaleString('en-NG', { style: 'currency', currency: 'NGN' })}</td>
                    <td>{payment.bank || 'N/A'}</td>
                    <td>{payment.status}</td>
                    <td>{new Date(payment.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Payments;