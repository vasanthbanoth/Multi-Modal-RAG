import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import DocumentUpload from './DocumentUpload';
import RagQuery from './RagQuery';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is logged in
    const fetchUser = async () => {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch (error) {
        // If 401, api.js might handle it, or we force redirect
        navigate('/login');
      }
    };
    fetchUser();
  }, [navigate]);

  const handleLogout = () => {
    api.logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navbar */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-indigo-600">Multi-RAG App</h1>
            </div>
            <div className="flex items-center">
              <span className="text-gray-500 text-sm mr-4">
                {user ? `Hello, ${user.email}` : 'Loading...'}
              </span>
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-red-600 text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column: Upload */}
            <div>
              <DocumentUpload />
            </div>
            
            {/* Right Column: Chat */}
            <div>
              <RagQuery />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;