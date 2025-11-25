import React, { useState, useEffect } from 'react';
import AnalysisForm from './components/AnalysisForm';
import RealTimeAnalysis from './components/RealTimeAnalysis';
import FullScreenDashboard from './components/FullScreenDashboard';
import AIChatSummary from './components/AIChatSummary';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('form'); // 'form', 'analysis', 'dashboard'
  const [analysisData, setAnalysisData] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);

  const handleAnalysisStart = (data) => {
    console.log('📝 App: Analysis started with data:', data);
    setAnalysisData(data);
    setCurrentView('analysis');
    console.log('📝 App: Switched to analysis view');
  };

  const handleAnalysisComplete = () => {
    console.log('✅ App: Analysis completed! Switching to dashboard...');
    // Fetch dashboard data after analysis completes
    setCurrentView('dashboard');
    console.log('✅ App: Current view is now:', 'dashboard');
  };

  const handleReset = () => {
    console.log('🔄 App: Resetting to form view');
    setCurrentView('form');
    setAnalysisData(null);
    setDashboardData(null);
  };

  // Debug: Log view changes
  useEffect(() => {
    console.log('👁️ App: Current view changed to:', currentView);
  }, [currentView]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">🎯</div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  CreatorGPT
                </h1>
                <p className="text-sm text-gray-600">
                  YouTube Comment Sentiment Intelligence
                </p>
              </div>
            </div>
            
            {currentView !== 'form' && (
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-semibold text-gray-700 transition-colors"
              >
                🏠 New Analysis
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {currentView === 'form' && (
          <div className="py-12">
            <AnalysisForm onAnalysisStart={handleAnalysisStart} />
          </div>
        )}

        {currentView === 'analysis' && (
          <ErrorBoundary>
            <RealTimeAnalysis 
              onComplete={handleAnalysisComplete}
              onReset={handleReset}
            />
          </ErrorBoundary>
        )}

        {currentView === 'dashboard' && (
          <ErrorBoundary>
            <FullScreenDashboard onReset={handleReset} />
          </ErrorBoundary>
        )}
      </main>

      {/* AI Chat Assistant - Only show after analysis is complete */}
      {currentView === 'dashboard' && (
        <ErrorBoundary>
          <AIChatSummary />
        </ErrorBoundary>
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-gray-600">
            <p>
              Powered by{' '}
              <span className="font-semibold text-blue-600">YouTube API</span> +{' '}
              <span className="font-semibold text-purple-600">Google Gemini</span> +{' '}
              <span className="font-semibold text-green-600">Transformers</span>
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Real-time sentiment analysis with AI-powered insights
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
