import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/lib/auth.jsx';
import Layout from '@/components/Layout';
import Dashboard from '@/components/Dashboard';
import LoginForm from '@/components/LoginForm';
import './App.css';

// Main App Content (after authentication)
function AppContent() {
  const { isAuthenticated, loading, user } = useAuth();
  const [currentPage, setCurrentPage] = useState('dashboard');

  // Handle page navigation (in a real app, you'd use React Router)
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (hash) {
        setCurrentPage(hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange(); // Check initial hash

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Mass Tracking System...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm onSuccess={() => window.location.reload()} />;
  }

  // Render different pages based on currentPage
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'celebrations':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-4">Mass Celebrations</h2>
            <p className="text-gray-600">Mass celebrations management coming soon...</p>
          </div>
        );
      case 'bulk-intentions':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-4">Bulk Intentions</h2>
            <p className="text-gray-600">Bulk intentions management coming soon...</p>
          </div>
        );
      case 'statistics':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-4">Statistics</h2>
            <p className="text-gray-600">Detailed statistics coming soon...</p>
          </div>
        );
      case 'import':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-4">Excel Import</h2>
            <p className="text-gray-600">Excel import functionality coming soon...</p>
          </div>
        );
      case 'notifications':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-4">Notifications</h2>
            <p className="text-gray-600">Notifications management coming soon...</p>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout currentPage={currentPage}>
      {renderPage()}
    </Layout>
  );
}

// Main App Component
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
