import React, { useState, Suspense, lazy } from 'react';
import './index.css'; // Global CSS for main layout

// Define the API_BASE_URL using the environment variable at the top level
// This is the correct way for Vite. If using Create React App, it's process.env.REACT_APP_BACKEND_URL
// The API_BASE_URL is still needed for other API calls (e.g., fetching dashboard data)
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';


// Dynamically import page components;
const Dashboard = lazy(() => import('./Dashboard.jsx'));
const Settings = lazy(() => import('./Settings.jsx'));
const Clients = lazy(() => import('./Clients.jsx'));
const Orders = lazy(() => import('./Orders.jsx'));
const Payments = lazy(() => import('./Payments.jsx'));
const Logs = lazy(() => import('./Logs.jsx'));

// Note: The Login component is no longer imported or used.

const App = () => {
  // We no longer need isAuthenticated state, as we are always "authenticated"
  // The default page is now always Dashboard
  const [currentPage, setCurrentPage] = useState('Dashboard');

  // Since there's no login, no initial authentication check is needed
  // and thus no loadingApp state for that purpose.

  // handleLoginSuccess and handleLogout are no longer needed
  // as there's no login/logout functionality.

  // Helper to render the current page component
  const renderPage = () => {
    // Application will always start on Dashboard
    switch (currentPage) {
      case 'Dashboard':
        return (
          <Suspense fallback={<div>Loading Dashboard...</div>}>
            {/* onLogout prop is no longer needed as there's no logout */}
            <Dashboard />
          </Suspense>
        );
      case 'Settings':
        return (
          <Suspense fallback={<div>Loading Settings...</div>}>
            {/* onLogout prop is no longer needed as there's no logout */}
            <Settings />
          </Suspense>
        );
      case 'Clients':
        return (
          <Suspense fallback={<div>Loading Clients...</div>}>
            {/* onLogout prop is no longer needed as there's no logout */}
            <Clients />
          </Suspense>
        );
      case 'Orders':
        return (
          <Suspense fallback={<div>Loading Orders...</div>}>
            {/* onLogout prop is no longer needed as there's no logout */}
            <Orders />
          </Suspense>
        );
      case 'Payments':
        return (
          <Suspense fallback={<div>Loading Payments...</div>}>
            {/* onLogout prop is no longer needed as there's no logout */}
            <Payments />
          </Suspense>
        );
      case 'Logs':
        return (
          <Suspense fallback={<div>Loading Logs...</div>}>
            {/* onLogout prop is no longer needed as there's no logout */}
            <Logs />
          </Suspense>
        );
      default:
        // Fallback to Dashboard if currentPage somehow gets an unknown value
        return (
          <Suspense fallback={<div>Loading Dashboard...</div>}>
            <Dashboard />
          </Suspense>
        );
    }
  };

  return (
    <div className="App-container">
      {/* Navigation is always visible now */}
      <nav className="App-nav">
        <button onClick={() => setCurrentPage('Dashboard')}>Dashboard</button>
        <button onClick={() => setCurrentPage('Settings')}>Settings</button>
        <button onClick={() => setCurrentPage('Clients')}>Clients</button>
        <button onClick={() => setCurrentPage('Orders')}>Orders</button>
        <button onClick={() => setCurrentPage('Payments')}>Payments</button>
        <button onClick={() => setCurrentPage('Logs')}>Logs</button>
        {/* Logout button is removed */}
      </nav>
      <main className="App-main-content">
        {renderPage()}
      </main>
    </div>
  );
};

export default App;
