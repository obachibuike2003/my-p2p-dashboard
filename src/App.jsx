import React, { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import './index.css'; // Global CSS for main layout

// Define the API_BASE_URL using the environment variable at the top level
// This is the correct way for Vite. If using Create React App, it's process.env.REACT_APP_BACKEND_URL
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';


// Dynamically import page components
const Login = lazy(() => import('./Login.jsx'));
const Dashboard = lazy(() => import('./Dashboard.jsx'));
const Settings = lazy(() => import('./Settings.jsx'));
const Clients = lazy(() => import('./Clients.jsx'));
const Orders = lazy(() => import('./Orders.jsx'));
const Payments = lazy(() => import('./Payments.jsx'));
const Logs = lazy(() => import('./Logs.jsx'));

const App = () => {
  const [currentPage, setCurrentPage] = useState('Login');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loadingApp, setLoadingApp] = useState(true); // Loading state for initial auth check

  // Function to check authentication status on app load
  const checkAuthStatus = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        // *** MODIFIED LINE HERE ***
        const response = await fetch(`${API_BASE_URL}/api/status`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          setIsAuthenticated(true);
          setCurrentPage('Dashboard'); // Default page if authenticated
        } else {
          localStorage.removeItem('token'); // Token might be expired or invalid
          setIsAuthenticated(false);
          setCurrentPage('Login');
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        // If backend is unreachable, keep showing login or specific error
        setIsAuthenticated(false);
        setCurrentPage('Login');
      }
    } else {
      setIsAuthenticated(false);
      setCurrentPage('Login');
    }
    setLoadingApp(false);
  }, []);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const handleLoginSuccess = (token) => {
    localStorage.setItem('token', token);
    setIsAuthenticated(true);
    setCurrentPage('Dashboard');
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        // *** MODIFIED LINE HERE ***
        await fetch(`${API_BASE_URL}/api/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        setCurrentPage('Login');
      } catch (error) {
        console.error('Logout failed:', error);
        // Even if logout fails on the backend, clear local state for UX
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        setCurrentPage('Login');
      }
    } else {
      localStorage.removeItem('token');
      setIsAuthenticated(false);
      setCurrentPage('Login');
    }
  };


  // Helper to render the current page component
  const renderPage = () => {
    if (loadingApp) {
      return <div>Loading application...</div>;
    }

    if (!isAuthenticated) {
      return (
        <Suspense fallback={<div>Loading Login...</div>}>
          <Login onLoginSuccess={handleLoginSuccess} />
        </Suspense>
      );
    }

    switch (currentPage) {
      case 'Dashboard':
        return (
          <Suspense fallback={<div>Loading Dashboard...</div>}>
            <Dashboard onLogout={handleLogout} />
          </Suspense>
        );
      case 'Settings':
        return (
          <Suspense fallback={<div>Loading Settings...</div>}>
            <Settings onLogout={handleLogout} />
          </Suspense>
        );
      case 'Clients':
        return (
          <Suspense fallback={<div>Loading Clients...</div>}>
            <Clients onLogout={handleLogout} />
          </Suspense>
        );
      case 'Orders':
        return (
          <Suspense fallback={<div>Loading Orders...</div>}>
            <Orders onLogout={handleLogout} />
          </Suspense>
        );
      case 'Payments':
        return (
          <Suspense fallback={<div>Loading Payments...</div>}>
            <Payments onLogout={handleLogout} />
          </Suspense>
        );
      case 'Logs':
        return (
          <Suspense fallback={<div>Loading Logs...</div>}>
            <Logs onLogout={handleLogout} />
          </Suspense>
        );
      default:
        return (
          <Suspense fallback={<div>Loading Dashboard...</div>}>
            <Dashboard onLogout={handleLogout} />
          </Suspense>
        );
    }
  };

  return (
    <div className="App-container">
      {isAuthenticated && (
        <nav className="App-nav">
          <button onClick={() => setCurrentPage('Dashboard')}>Dashboard</button>
          <button onClick={() => setCurrentPage('Settings')}>Settings</button>
          <button onClick={() => setCurrentPage('Clients')}>Clients</button>
          <button onClick={() => setCurrentPage('Orders')}>Orders</button>
          <button onClick={() => setCurrentPage('Payments')}>Payments</button>
          <button onClick={() => setCurrentPage('Logs')}>Logs</button>
          <button onClick={handleLogout} className="App-logout-button">Logout</button>
        </nav>
      )}
      <main className="App-main-content">
        {renderPage()}
      </main>
    </div>
  );
};

export default App;