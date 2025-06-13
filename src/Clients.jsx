import React, { useState, useEffect, useCallback } from 'react';
import Card from './components/card'; // Use the new Card component
const Clients = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const [newClient, setNewClient] = useState({
    name: '',
    account: '',
    bank: '', // This will store the bank code
    amount: ''
  });

  const fetchClients = useCallback(async () => {
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('https://my-p2p-dashboard.onrender.com/api/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setClients(data);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to fetch clients.');
      }
    } catch (err) {
      console.error('Error fetching clients:', err);
      setError('Network error or server unreachable. Could not load clients.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewClient((prev) => ({ ...prev, [name]: value }));
  };

  const handleAddClient = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/api/add-client', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newClient),
      });

      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        setNewClient({ name: '', account: '', bank: '', amount: '' }); // Clear form
        fetchClients(); // Refresh client list
      } else {
        setError(data.message || 'Failed to add client.');
      }
    } catch (err) {
      console.error('Error adding client:', err);
      setError('Network error or server unreachable. Could not add client.');
    }
  };

  const handleRemoveClient = async (clientId) => {
    if (!window.confirm(`Are you sure you want to remove client ${clientId}?`)) {
      return;
    }
    setMessage('');
    setError('');
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/api/remove-client/${clientId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        fetchClients(); // Refresh client list
      } else {
        setError(data.message || 'Failed to remove client.');
      }
    } catch (err) {
      console.error('Error removing client:', err);
      setError('Network error or server unreachable. Could not remove client.');
    }
  };

  return (
    <div className="clients-page">
      <Card title="Add New Client">
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleAddClient} className="form-section">
          <div className="form-group">
            <label htmlFor="clientName">Client Name:</label>
            <input
              type="text"
              id="clientName"
              name="name"
              value={newClient.name}
              onChange={handleInputChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="accountNumber">Account Number:</label>
            <input
              type="text"
              id="accountNumber"
              name="account"
              value={newClient.account}
              onChange={handleInputChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="bankCode">Bank Code:</label>
            <input
              type="text"
              id="bankCode"
              name="bank"
              value={newClient.bank}
              onChange={handleInputChange}
              placeholder="e.g., 058 for GTB, 50211 for Kuda"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="amount">Amount (NGN):</label>
            <input
              type="number"
              id="amount"
              name="amount"
              value={newClient.amount}
              onChange={handleInputChange}
              step="0.01"
              required
            />
          </div>
          <button type="submit" className="btn btn-success">Add Client</button>
        </form>
      </Card>

      <Card title="Manage Clients">
        {loading ? (
          <div className="loading-spinner">Loading clients...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : clients.length === 0 ? (
          <p>No clients added yet.</p>
        ) : (
          <div className="responsive-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Account No.</th>
                  <th>Bank Code</th>
                  <th>Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr key={client.id}>
                    <td>{client.id}</td>
                    <td>{client.name}</td>
                    <td>{client.account}</td>
                    <td>{client.bank}</td>
                    <td>{client.amount.toLocaleString('en-NG', { style: 'currency', currency: 'NGN' })}</td>
                    <td>
                      <button
                        onClick={() => handleRemoveClient(client.id)}
                        className="btn btn-danger"
                      >
                        Remove
                      </button>
                    </td>
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

export default Clients;
