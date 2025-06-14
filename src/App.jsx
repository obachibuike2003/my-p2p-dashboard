import React, { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import './index.css'; // Global CSS for main layout
// Card component is imported in the pages themselves if they use it

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
        const response = await fetch('https://my-p2p-dashboard.onrender.com/api/status', {
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
        await fetch('http://localhost:5000/api/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (error) {
        console.error('Logout API call failed:', error);
      }
    }
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setCurrentPage('Login');
  };

  // This function renders the appropriate page component based on `currentPage` state
  const renderPage = () => {
    switch (currentPage) {
      case 'Login':
        return <Login onLoginSuccess={handleLoginSuccess} />;
      case 'Dashboard':
        return <Dashboard setCurrentPage={setCurrentPage} />; // Pass setCurrentPage for navigation
      case 'Settings':
        return <Settings />;
      case 'Clients':
        return <Clients />;
      case 'Orders':
        return <Orders />;
      case 'Payments':
        return <Payments />;
      case 'Logs':
        return <Logs />;
      default:
        return <p>Page not found.</p>;
    }
  };

  return (
    <div className="app-container">
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-brand">P2P Bot Dashboard</div>
        {isAuthenticated && (
          <ul className="navbar-nav">
            <li className="nav-item">
              <button onClick={() => setCurrentPage('Dashboard')} className={currentPage === 'Dashboard' ? 'nav-link active' : 'nav-link'}>Dashboard</button>
            </li>
            <li className="nav-item">
              <button onClick={() => setCurrentPage('Orders')} className={currentPage === 'Orders' ? 'nav-link active' : 'nav-link'}>Orders</button>
            </li>
            <li className="nav-item">
              <button onClick={() => setCurrentPage('Payments')} className={currentPage === 'Payments' ? 'nav-link active' : 'nav-link'}>Payments</button>
            </li>
            <li className="nav-item">
              <button onClick={() => setCurrentPage('Clients')} className={currentPage === 'Clients' ? 'nav-link active' : 'nav-link'}>Clients</button>
            </li>
            <li className="nav-item">
              <button onClick={() => setCurrentPage('Settings')} className={currentPage === 'Settings' ? 'nav-link active' : 'nav-link'}>Settings</button>
            </li>
            <li className="nav-item">
              <button onClick={() => setCurrentPage('Logs')} className={currentPage === 'Logs' ? 'nav-link active' : 'nav-link'}>Logs</button>
            </li>
            <li className="nav-item">
              <button onClick={handleLogout} className="nav-link logout-btn">Logout</button>
            </li>
          </ul>
        )}
      </nav>

      {/* Main Content Area */}
      <main className="main-content">
        {loadingApp ? (
          <div className="loading-spinner">Loading application...</div>
        ) : (
          <Suspense fallback={<div className="loading-spinner">Loading page...</div>}>
            {renderPage()}
          </Suspense>
        )}
      </main>
    </div>
  );
};

export default App;
