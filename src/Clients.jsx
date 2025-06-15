import React, { useState, useEffect, useCallback } from 'react';
import Card from './components/card'; // Use the new Card component

// Define the API_BASE_URL using the environment variable at the top level
// This is crucial for both local development and deployed environments.
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

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

  // Removed onLogout prop from function signature as it's no longer passed from App.jsx

  const fetchClients = useCallback(async () => {
    setLoading(true);
    setError('');
    // Removed authentication token check
    // const token = localStorage.getItem('token');
    // if (!token) {
    //   setError('Authentication token missing. Please log in again.');
    //   setLoading(false);
    //   return;
    // }

    try {
      // API call no longer requires Authorization header
      const response = await fetch(`${API_BASE_URL}/api/clients`, { // Changed from /api/status
        // Removed headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setClients(data); // Assuming 'data' directly contains the array of clients
      } else {
        const errorData = await response.json();
        // Updated error message to reflect no login
        setError(errorData.message || 'Failed to fetch clients (no authentication required).');
      }
    } catch (err) {
      console.error('Error fetching clients:', err);
      setError('Network error or server unreachable. Could not load clients.');
    } finally {
      setLoading(false);
    }
  }, []); // Dependency array changed, token removed

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
    // Removed authentication token check
    // const token = localStorage.getItem('token');
    // if (!token) {
    //   setError('Authentication token missing. Please log in again.');
    //   return;
    // }

    try {
      // API call no longer requires Authorization header
      const response = await fetch(`${API_BASE_URL}/api/add-client`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Removed 'Authorization': `Bearer ${token}`
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
    // Replaced window.confirm with a custom message box for better UI/UX
    // (This is a general best practice, not strictly related to login removal)
    const confirmed = await new Promise((resolve) => {
      const CustomConfirm = ({ message, onConfirm, onCancel }) => (
        <div style={{
          position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          backgroundColor: '#333', color: 'white', padding: '20px', borderRadius: '8px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.2)', zIndex: 1000, textAlign: 'center'
        }}>
          <p>{message}</p>
          <button onClick={() => { onConfirm(); document.body.removeChild(dialogDiv); }} style={{ margin: '5px', padding: '8px 15px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Yes</button>
          <button onClick={() => { onCancel(); document.body.removeChild(dialogDiv); }} style={{ margin: '5px', padding: '8px 15px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>No</button>
        </div>
      );

      const dialogDiv = document.createElement('div');
      document.body.appendChild(dialogDiv);
      ReactDOM.render(
        <CustomConfirm
          message={`Are you sure you want to remove client ${clientId}?`}
          onConfirm={() => resolve(true)}
          onCancel={() => resolve(false)}
        />,
        dialogDiv
      );
    });

    if (!confirmed) {
      return;
    }

    setMessage('');
    setError('');
    // Removed authentication token check
    // const token = localStorage.getItem('token');
    // if (!token) {
    //   setError('Authentication token missing. Please log in again.');
    //   return;
    // }

    try {
      // API call no longer requires Authorization header
      const response = await fetch(`${API_BASE_URL}/api/remove-client/${clientId}`, {
        method: 'DELETE',
        // Removed headers: { 'Authorization': `Bearer ${token}` }
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
