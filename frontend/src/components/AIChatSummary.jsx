import React, { useState } from 'react';
import axios from 'axios';

const AIChatSummary = () => {
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);

  const suggestedQuestions = [
    "What are the main themes in the comments?",
    "What do viewers like most about this video?",
    "What improvements are viewers suggesting?",
    "How is the overall sentiment?",
    "What are the negative comments about?",
    "Who are the most engaged commenters?",
    "What topics should I cover in my next video?",
    "Are there any common concerns or issues?",
  ];

  const askQuestion = async (questionText) => {
    if (!questionText.trim()) return;

    setLoading(true);
    const userMessage = { type: 'user', text: questionText, timestamp: new Date() };
    setChatHistory(prev => [...prev, userMessage]);
    setQuestion('');

    try {
      const response = await axios.post('http://localhost:8001/api/chat', {
        question: questionText
      });

      const aiMessage = {
        type: 'ai',
        text: response.data.answer,
        timestamp: new Date(),
        context: response.data.context_used
      };

      setChatHistory(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        text: error.response?.data?.detail || 'Failed to get AI response. Please try again.',
        timestamp: new Date()
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedClick = (suggestion) => {
    askQuestion(suggestion);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Floating Chat Button */}
      {!showChat && (
        <button
          onClick={() => setShowChat(true)}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all transform hover:scale-110"
        >
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🤖</span>
            <span className="font-semibold">Ask AI</span>
          </div>
        </button>
      )}

      {/* Chat Window */}
      {showChat && (
        <div className="bg-white rounded-2xl shadow-2xl w-96 h-[600px] flex flex-col">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 rounded-t-2xl flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🤖</span>
              <div>
                <h3 className="font-bold">AI Comment Analyst</h3>
                <p className="text-xs opacity-90">Ask me anything about your comments</p>
              </div>
            </div>
            <button
              onClick={() => setShowChat(false)}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-1"
            >
              ✕
            </button>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {chatHistory.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">💬</div>
                <p className="text-gray-600 font-semibold mb-2">
                  Hi! I'm your AI Comment Analyst
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  Ask me anything about your video's comments!
                </p>
                
                {/* Suggested Questions */}
                <div className="text-left space-y-2">
                  <p className="text-xs text-gray-500 font-semibold mb-2">Try asking:</p>
                  {suggestedQuestions.slice(0, 4).map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestedClick(suggestion)}
                      className="w-full text-left text-sm bg-white hover:bg-purple-50 border border-purple-200 rounded-lg p-2 transition-colors"
                    >
                      💡 {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              chatHistory.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl p-3 ${
                      message.type === 'user'
                        ? 'bg-purple-600 text-white'
                        : message.type === 'error'
                        ? 'bg-red-100 text-red-800 border border-red-300'
                        : 'bg-white text-gray-800 shadow-md border border-gray-200'
                    }`}
                  >
                    {message.type === 'ai' && (
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">🤖</span>
                        <span className="text-xs font-semibold text-purple-600">AI Assistant</span>
                      </div>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                    {message.context && (
                      <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                        📊 Based on {message.context.total_comments} comments
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-white rounded-2xl p-3 shadow-md">
                  <div className="flex items-center space-x-2">
                    <div className="animate-pulse flex space-x-1">
                      <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                      <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                      <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                    </div>
                    <span className="text-sm text-gray-500">AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
            {/* Quick Suggestions */}
            {chatHistory.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-1">
                {suggestedQuestions.slice(4, 6).map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedClick(suggestion)}
                    className="text-xs bg-purple-100 hover:bg-purple-200 text-purple-700 px-2 py-1 rounded-full transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}

            <div className="flex space-x-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && askQuestion(question)}
                placeholder="Ask a question..."
                disabled={loading}
                className="flex-1 border-2 border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-purple-500 disabled:bg-gray-100"
              />
              <button
                onClick={() => askQuestion(question)}
                disabled={loading || !question.trim()}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 text-white rounded-full p-2 px-4 transition-colors"
              >
                {loading ? '⏳' : '📤'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIChatSummary;
