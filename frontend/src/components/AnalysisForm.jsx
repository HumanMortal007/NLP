import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8001';

const AnalysisForm = ({ onAnalysisStart }) => {
  const [videoId, setVideoId] = useState('');
  const [maxComments, setMaxComments] = useState(1000);
  const [batchSize, setBatchSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const extractVideoId = (input) => {
    // Extract video ID from URL or use as-is
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/,
      /^([a-zA-Z0-9_-]{11})$/
    ];

    for (const pattern of patterns) {
      const match = input.match(pattern);
      if (match) return match[1];
    }
    
    return input;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const extractedId = extractVideoId(videoId.trim());

    if (!extractedId || extractedId.length < 5) {
      setError('Please enter a valid YouTube video ID or URL');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/analyze`, {
        video_id: extractedId,
        max_comments: parseInt(maxComments),
        batch_size: parseInt(batchSize)
      });

      console.log('Analysis started:', response.data);
      onAnalysisStart(response.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">
          🎬 YouTube Comment Analyzer
        </h2>
        <p className="text-gray-600">
          Enter a YouTube video ID or URL to analyze comments with AI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Video ID Input */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            YouTube Video ID or URL *
          </label>
          <input
            type="text"
            value={videoId}
            onChange={(e) => setVideoId(e.target.value)}
            placeholder="e.g., dQw4w9WgXcQ or https://youtube.com/watch?v=dQw4w9WgXcQ"
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Paste a YouTube URL or just the 11-character video ID
          </p>
        </div>

        {/* Max Comments */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Maximum Comments to Analyze
          </label>
          <select
            value={maxComments}
            onChange={(e) => setMaxComments(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
          >
            <option value="100">100 (Quick test)</option>
            <option value="500">500 (Recommended)</option>
            <option value="1000">1000 (Standard)</option>
            <option value="2000">2000 (Extended)</option>
            <option value="5000">5000 (Maximum)</option>
          </select>
        </div>

        {/* Batch Size */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Batch Size (for AI Analysis)
          </label>
          <select
            value={batchSize}
            onChange={(e) => setBatchSize(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
          >
            <option value="25">25 (Faster, more batches)</option>
            <option value="50">50 (Recommended)</option>
            <option value="100">100 (Slower, fewer batches)</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Smaller batches = more detailed analysis but slower
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
            <p className="text-red-700 font-medium">❌ {error}</p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-4 rounded-lg font-bold text-lg transition-all ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Starting Analysis...
            </span>
          ) : (
            '🚀 Start Analysis'
          )}
        </button>
      </form>

      {/* Info Cards */}
      <div className="mt-8 grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <div className="text-2xl mb-1">📥</div>
          <div className="text-xs font-semibold text-gray-700">YouTube Extraction</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 text-center">
          <div className="text-2xl mb-1">🤖</div>
          <div className="text-xs font-semibold text-gray-700">Gemini AI Analysis</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4 text-center">
          <div className="text-2xl mb-1">😊</div>
          <div className="text-xs font-semibold text-gray-700">Sentiment Scoring</div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisForm;
