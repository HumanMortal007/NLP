import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';

const RealTimeAnalysis = ({ onComplete, onReset }) => {
  const [status, setStatus] = useState({
    status: 'idle',
    progress: 0,
    current_step: '',
    message: 'Waiting to start...',
  });
  const [ws, setWs] = useState(null);
  const [hasCompleted, setHasCompleted] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const pollingIntervalRef = useRef(null);

  // Fallback polling function in case WebSocket disconnects
  const pollDashboardStatus = useCallback(async () => {
    console.log('🔍 Polling dashboard... hasCompleted:', hasCompleted);
    
    if (hasCompleted) {
      console.log('⚠️ Already completed, stopping poll');
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      return;
    }

    try {
      console.log('📡 Fetching dashboard data...');
      const response = await axios.get('http://localhost:8001/api/dashboard-data');
      console.log('✅ Got 200 OK! Response:', response.data);
      
      if (response.data && response.data.overview) {
        console.log('🎉 DASHBOARD READY! Redirecting...');
        
        setStatus({
          status: 'completed',
          progress: 100,
          current_step: 'finalization',
          message: 'Analysis completed successfully!',
          data: {
            total_comments: response.data.overview.total_comments,
            sentiment_summary: response.data.sentiment_distribution
          }
        });
        
        setHasCompleted(true);
        
        // Stop polling
        if (pollingIntervalRef.current) {
          console.log('⏹️ Stopping polling interval');
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        
        // Navigate to dashboard
        console.log('⏰ Setting 2s timeout before calling onComplete');
        setTimeout(() => {
          console.log('🚀 Calling onComplete to redirect to dashboard');
          if (onComplete) {
            onComplete();
          } else {
            console.error('❌ onComplete is undefined!');
          }
        }, 2000);
      } else {
        console.warn('⚠️ Got 200 but no overview data:', response.data);
      }
    } catch (error) {
      // Dashboard not ready yet (404 is normal during analysis)
      if (error.response?.status === 404) {
        console.log('⏳ 404 - Still processing...');
        setStatus(prev => ({
          ...prev,
          message: 'Processing batches with Gemini AI... (this may take a few minutes)',
          status: 'running',
          progress: Math.min(prev.progress + 1, 95) // Increment progress slightly
        }));
      } else {
        console.error('❌ Unexpected error:', error);
      }
    }
  }, [hasCompleted, onComplete]);

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8001/ws/analysis');

    websocket.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received status:', data);
      setStatus(data);
      
      // Check if analysis is complete
      if (data.status === 'completed') {
        setHasCompleted(true);
        console.log('Analysis completed! Transitioning to dashboard in 3 seconds...');
        // Stop polling since we got completion via WebSocket
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        // Wait 3 seconds to show completion, then navigate to dashboard
        setTimeout(() => {
          if (onComplete) {
            onComplete();
          }
        }, 3000);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected - switching to polling mode');
      setWsConnected(false);
      
      // Start polling as fallback (check every 3 seconds)
      if (!pollingIntervalRef.current) {
        console.log('Starting fallback polling...');
        pollingIntervalRef.current = setInterval(pollDashboardStatus, 3000);
      }
    };

    setWs(websocket);

    // Cleanup on unmount
    return () => {
      if (websocket) {
        websocket.close();
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [pollDashboardStatus, onComplete]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStepIcon = (step) => {
    const steps = {
      initialization: '🔧',
      extraction: '📥',
      batching: '📦',
      llm_analysis: '🤖',
      sentiment: '😊',
      visualization: '📊',
      finalization: '✅',
    };
    return steps[step] || '⏳';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Real-Time Analysis Progress
        </h2>
        <p className="text-gray-600">
          Monitor your YouTube comment analysis in real-time
        </p>
      </div>

      {/* Status Card */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">{getStepIcon(status.current_step)}</span>
            <div>
              <h3 className={`text-xl font-semibold ${getStatusColor(status.status)}`}>
                {(status.status || 'idle').toUpperCase()}
              </h3>
              <p className="text-gray-700">{(status.current_step || '').replace(/_/g, ' ').toUpperCase()}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-indigo-600">{status.progress}%</p>
            {!wsConnected && status.status !== 'completed' && (
              <p className="text-xs text-orange-600 mt-1">📡 Polling mode</p>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-indigo-600 h-4 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${status.progress}%` }}
          ></div>
        </div>

        {/* Status Message */}
        <div className="mt-4 p-3 bg-white bg-opacity-70 rounded-lg">
          <p className="text-gray-700 font-medium">{status.message}</p>
        </div>
      </div>

      {/* Pipeline Steps */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { step: 'extraction', label: 'Extract Comments', icon: '📥' },
          { step: 'batching', label: 'Create Batches', icon: '📦' },
          { step: 'llm_analysis', label: 'LLM Analysis', icon: '🤖' },
          { step: 'sentiment', label: 'Sentiment Scoring', icon: '😊' },
          { step: 'visualization', label: 'Generate Visuals', icon: '📊' },
          { step: 'finalization', label: 'Finalize', icon: '✅' },
        ].map((item) => {
          const isActive = status.current_step === item.step;
          const isCompleted = 
            ['extraction', 'batching', 'llm_analysis', 'sentiment', 'visualization'].indexOf(item.step) <
            ['extraction', 'batching', 'llm_analysis', 'sentiment', 'visualization'].indexOf(status.current_step);

          return (
            <div
              key={item.step}
              className={`p-4 rounded-lg border-2 transition-all ${
                isActive
                  ? 'border-blue-500 bg-blue-50'
                  : isCompleted
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 bg-gray-50'
              }`}
            >
              <div className="text-2xl text-center mb-2">{item.icon}</div>
              <p className="text-sm font-medium text-center text-gray-700">
                {item.label}
              </p>
              {isCompleted && (
                <div className="text-center mt-1">
                  <span className="text-green-600 text-xl">✓</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Results Summary (shown when completed) */}
      {status.status === 'completed' && status.data && (
        <div className="mt-6 p-6 bg-green-50 border-2 border-green-500 rounded-lg">
          <h3 className="text-xl font-bold text-green-800 mb-4 flex items-center justify-center">
            <span className="text-2xl mr-2">🎉</span>
            Analysis Complete!
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white p-3 rounded-lg">
              <p className="text-gray-600 text-sm">Total Comments</p>
              <p className="text-2xl font-bold text-gray-800">
                {status.data.total_comments}
              </p>
            </div>
            <div className="bg-white p-3 rounded-lg">
              <p className="text-gray-600 text-sm">Positive</p>
              <p className="text-2xl font-bold text-green-600">
                {status.data.sentiment_summary?.positive || 0}
              </p>
            </div>
            <div className="bg-white p-3 rounded-lg">
              <p className="text-gray-600 text-sm">Neutral</p>
              <p className="text-2xl font-bold text-yellow-600">
                {status.data.sentiment_summary?.neutral || 0}
              </p>
            </div>
            <div className="bg-white p-3 rounded-lg">
              <p className="text-gray-600 text-sm">Negative</p>
              <p className="text-2xl font-bold text-red-600">
                {status.data.sentiment_summary?.negative || 0}
              </p>
            </div>
          </div>
          <div className="mt-4 text-center space-y-3">
            <button
              onClick={() => {
                console.log('🔘 Manual dashboard button clicked');
                if (onComplete) {
                  onComplete();
                }
              }}
              className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg text-lg shadow-lg transform hover:scale-105 transition-all"
            >
              📊 View Dashboard Now
            </button>
            <p className="text-sm text-green-700">
              Auto-redirecting in 2 seconds... or click button above
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {status.status === 'failed' && (
        <div className="mt-6 p-6 bg-red-50 border-2 border-red-500 rounded-lg">
          <h3 className="text-xl font-bold text-red-800 mb-4 flex items-center">
            <span className="text-2xl mr-2">❌</span>
            Analysis Failed
          </h3>
          <p className="text-red-700 mb-4">{status.message}</p>
          <button
            onClick={onReset}
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default RealTimeAnalysis;
