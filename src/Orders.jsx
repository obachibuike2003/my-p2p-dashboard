import React, { useState, useEffect, useCallback } from 'react';
import Card from './components/card'; // Use the new Card component

// Define the API_BASE_URL using the environment variable at the top level
const API_BASE_URL = import.meta.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      setLoading(false);
      return;
    }

    try {
      // *** MODIFIED LINE HERE: Using API_BASE_URL and corrected endpoint for orders ***
      // Changed from /api/status to /api/orders (most likely correct endpoint)
      const response = await fetch(`${API_BASE_URL}/api/orders`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setOrders(data); // Assuming 'data' directly contains the array of orders
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to fetch orders.');
      }
    } catch (err) {
      console.error('Error fetching orders:', err);
      setError('Network error or server unreachable. Could not load orders.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 10000); // Refresh orders every 10 seconds
    return () => clearInterval(interval);
  }, [fetchOrders]);

  return (
    <div className="orders-page">
      <Card title="All Orders">
        {loading ? (
          <div className="loading-spinner">Loading orders...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : orders.length === 0 ? (
          <p>No orders recorded yet.</p>
        ) : (
          <div className="responsive-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Bybit ID</th>
                  <th>Client</th>
                  <th>Fiat Amount (NGN)</th>
                  <th>Crypto Amount</th>
                  <th>Seller Nickname</th>
                  <th>Paystack TX ID</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td>{order.id}</td>
                    <td>{order.bybitOrderId || 'N/A'}</td>
                    <td>{order.clientName}</td>
                    <td>{order.amountFiat.toLocaleString('en-NG', { style: 'currency', currency: 'NGN' })}</td>
                    <td>{order.amountCrypto ? order.amountCrypto.toFixed(4) : 'N/A'} USDT</td>
                    <td>{order.sellerNickname || 'N/A'}</td>
                    <td>{order.paystackTxId || 'N/A'}</td>
                    <td>{order.status}</td>
                    <td>{new Date(order.timestamp).toLocaleString()}</td>
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

export default Orders;