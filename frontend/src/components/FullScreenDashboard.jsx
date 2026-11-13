import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import axios from 'axios';

const FullScreenDashboard = ({ onReset }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('📊 Dashboard: Component mounted, fetching data...');
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    console.log('📊 Dashboard: Starting fetch...');
    setLoading(true);
    setError(null);
    
    try {
      console.log('📊 Dashboard: Calling API...');
      const response = await axios.get('http://localhost:8001/api/dashboard-data');
      console.log('📊 Dashboard: Got response:', response.data);
      
      if (!response.data || !response.data.overview) {
        console.error('📊 Dashboard: Invalid data structure!', response.data);
        throw new Error('Invalid dashboard data received - missing overview');
      }
      
      console.log('📊 Dashboard: Data validated, setting state...');
      setDashboardData(response.data);
      setLoading(false);
      console.log('📊 Dashboard: Loading complete!');
    } catch (error) {
      console.error('📊 Dashboard: Error occurred!', error);
      console.error('📊 Dashboard: Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      setError(error.response?.data?.detail || error.message || 'Failed to load dashboard data');
      setLoading(false);
    }
  };

  if (loading) {
    console.log('📊 Dashboard: Rendering loading state...');
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">Loading dashboard...</p>
          <p className="mt-2 text-gray-500 text-sm">Fetching analysis results</p>
        </div>
      </div>
    );
  }

  if (error) {
    console.log('📊 Dashboard: Rendering error state:', error);
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md bg-white p-8 rounded-lg shadow-xl">
          <div className="text-6xl mb-4">⚠️</div>
          <p className="text-xl text-gray-800 font-bold mb-2">Error Loading Dashboard</p>
          <p className="text-gray-600 mb-4">{error}</p>
          <div className="space-x-4">
            <button
              onClick={fetchDashboardData}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded"
            >
              🔄 Retry
            </button>
            {onReset && (
              <button
                onClick={onReset}
                className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded"
              >
                🏠 New Analysis
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    console.log('📊 Dashboard: No data available');
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md bg-white p-8 rounded-lg shadow-xl">
          <div className="text-6xl mb-4">😕</div>
          <p className="text-xl text-gray-800 font-bold mb-2">No Data Available</p>
          <p className="text-gray-600 mb-4">Please run an analysis first</p>
          <div className="space-x-4">
            <button
              onClick={fetchDashboardData}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded"
            >
              🔄 Retry
            </button>
            {onReset && (
              <button
                onClick={onReset}
                className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded"
              >
                🏠 New Analysis
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  console.log('📊 Dashboard: Rendering dashboard with data:', dashboardData);

  const { overview, sentiment_distribution, trending_keywords, top_keyword_terms, batch_summaries, temporal_trends, engagement_metrics, visualizations } = dashboardData;

  // Safety checks for data
  const safeOverview = overview || {};
  const safeSentiment = sentiment_distribution || { positive: 0, neutral: 0, negative: 0, avg_score: 0 };
  const safeKeywords = trending_keywords || [];
  const safeKeywordTerms = top_keyword_terms || [];
  const safeBatchSummaries = batch_summaries || [];
  const safeTemporalTrends = temporal_trends || [];
  const safeEngagement = engagement_metrics || { total_likes: 0, avg_likes: 0 };
  const safeVisualizations = visualizations || [];

  // Prepare data for charts
  const sentimentPieData = [
    { name: 'Positive', value: safeSentiment.positive, color: '#10B981' },
    { name: 'Neutral', value: safeSentiment.neutral, color: '#F59E0B' },
    { name: 'Negative', value: safeSentiment.negative, color: '#EF4444' },
  ];

  const trendLineData = safeTemporalTrends.map(t => ({
    date: t.date,
    score: t.avg_score,
    count: t.count,
  }));

  // Handle both string arrays and object arrays for keywords
  const keywordBarData = safeKeywords.slice(0, 10).map(k => {
    if (typeof k === 'string') {
      return { word: k, count: 1 };
    } else if (k && typeof k === 'object') {
      return { 
        word: k.keyword || k.word || 'unknown', 
        count: k.count || 1 
      };
    }
    return { word: 'unknown', count: 1 };
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          YouTube Comment Analytics Dashboard
        </h1>
        <div className="flex items-center space-x-4 text-gray-600">
          <span>📺 {safeOverview.channel_name || 'N/A'}</span>
          <span>•</span>
          <span>🎬 {safeOverview.video_title || 'N/A'}</span>
          <span>•</span>
          <span>📅 {safeOverview.analysis_date ? new Date(safeOverview.analysis_date).toLocaleDateString() : 'N/A'}</span>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
          <p className="text-gray-600 text-sm font-medium">Comments Analyzed</p>
          <p className="text-4xl font-bold text-gray-800 mt-2">
            {(safeOverview.total_comments || 0).toLocaleString()}
          </p>
          <p className="text-xs text-gray-500 mt-1">of {(safeOverview.total_comments_available || 0).toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-red-500">
          <p className="text-gray-600 text-sm font-medium">Video Likes</p>
          <p className="text-4xl font-bold text-red-600 mt-2">
            {(safeOverview.video_likes || 0).toLocaleString()}
          </p>
          <p className="text-xs text-gray-500 mt-1">{(safeOverview.video_views || 0).toLocaleString()} views</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
          <p className="text-gray-600 text-sm font-medium">Avg Sentiment</p>
          <p className="text-4xl font-bold text-green-600 mt-2">
            {(safeOverview.avg_sentiment_score || 0).toFixed(1)}
          </p>
          <p className="text-xs text-gray-500 mt-1">out of 100</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
          <p className="text-gray-600 text-sm font-medium">Positive Rate</p>
          <p className="text-4xl font-bold text-purple-600 mt-2">
            {safeSentiment.positive && safeOverview.total_comments 
              ? ((safeSentiment.positive / safeOverview.total_comments) * 100).toFixed(1) 
              : '0'}%
          </p>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Sentiment Distribution Pie Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Sentiment Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentPieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(1)}%)`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {sentimentPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Keywords Bar Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-2xl mr-2">🔑</span>
            Trending Keywords
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={keywordBarData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="word" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
          {/* Keyword Tag Cloud */}
          <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
            <p className="text-sm font-semibold text-gray-700 mb-2">Top Keywords:</p>
            <div className="flex flex-wrap gap-2">
              {(safeKeywordTerms.length > 0 ? safeKeywordTerms : keywordBarData.map(k => k.word)).slice(0, 20).map((keyword, idx) => (
                <span 
                  key={idx}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium hover:bg-blue-200 transition-colors cursor-default"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Sentiment Trend Line */}
      {trendLineData.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Sentiment Trend Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendLineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="score" stroke="#3B82F6" strokeWidth={2} name="Avg Sentiment Score" />
              <Line yAxisId="right" type="monotone" dataKey="count" stroke="#F59E0B" strokeWidth={2} name="Comment Count" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* AI-Generated Visualizations Gallery */}
      {safeVisualizations && safeVisualizations.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-2xl mr-2">📊</span>
            AI-Generated Visualizations
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {safeVisualizations.map((viz, index) => (
              <div key={index} className="border-2 border-gray-200 rounded-lg overflow-hidden hover:border-blue-500 transition-all hover:shadow-xl">
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3">
                  <h4 className="font-bold text-sm capitalize">
                    {(viz.name || 'visualization').replace(/_/g, ' ')}
                  </h4>
                </div>
                <div className="p-2 bg-gray-50">
                  <img 
                    src={viz.url} 
                    alt={viz.name}
                    className="w-full h-auto rounded shadow-md cursor-pointer hover:scale-105 transition-transform"
                    onClick={() => window.open(viz.url, '_blank')}
                  />
                </div>
                <div className="p-3 bg-white">
                  <a 
                    href={viz.url} 
                    download={viz.filename}
                    className="text-sm text-blue-600 hover:text-blue-800 font-semibold flex items-center justify-center"
                  >
                    📥 Download
                  </a>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-800">
              💡 <strong>Tip:</strong> Click on any visualization to view it full-size, or download them for your reports!
            </p>
          </div>
        </div>
      )}

      {/* Batch Summaries */}
      {safeBatchSummaries && safeBatchSummaries.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-2xl mr-2">🤖</span>
            AI Batch Analysis Insights
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {safeBatchSummaries.map((batch) => (
              <div key={batch.batch_number} className="border-2 border-purple-200 rounded-lg p-4 hover:border-purple-500 transition-colors bg-gradient-to-br from-white to-purple-50">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-bold text-purple-800">Batch {batch.batch_number}</h4>
                  <span className="bg-purple-100 text-purple-800 text-xs font-semibold px-2 py-1 rounded">
                    {batch.themes?.length || 0} themes
                  </span>
                </div>
                
                {/* Themes */}
                {batch.themes && batch.themes.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-gray-600 mb-1">🎯 Key Themes:</p>
                    <ul className="space-y-1">
                      {batch.themes.map((theme, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="text-purple-500 mr-2">•</span>
                          <span>{theme.substring(0, 80)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Suggestions */}
                {batch.suggestions && batch.suggestions.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-semibold text-gray-600 mb-1">💡 Suggestions:</p>
                    <ul className="space-y-1">
                      {batch.suggestions.map((suggestion, idx) => (
                        <li key={idx} className="text-xs text-green-700 flex items-start">
                          <span className="mr-1">✓</span>
                          <span>{suggestion.substring(0, 60)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Sentiment Summary */}
                {batch.sentiment && (
                  <div className="mt-2 pt-2 border-t border-purple-200">
                    <p className="text-xs text-gray-600">
                      <strong>Sentiment:</strong> {batch.sentiment.substring(0, 50)}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FullScreenDashboard;
