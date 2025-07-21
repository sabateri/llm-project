import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Get API URL from environment variable or default to localhost
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [queryHistory, setQueryHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // Configure axios to handle CORS
  const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds timeout for RAG queries
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Check if backend is healthy on component mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      await apiClient.get('/api/health');
      console.log('Backend is healthy');
    } catch (err) {
      console.error('Backend health check failed:', err);
      setError('Unable to connect to backend service');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError('');
    setAnswer('');

    try {
      const response = await apiClient.post('/api/query', {
        query: query.trim()
      });

      if (response.data.success) {
        setAnswer(response.data.answer);
        // Clear query after successful submission
        setQuery('');
        // Refresh history if it's showing
        if (showHistory) {
          fetchQueryHistory();
        }
      } else {
        setError(response.data.error || 'Unknown error occurred');
      }
    } catch (err) {
      console.error('Query error:', err);
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timed out. Please try again.');
      } else if (err.response?.status === 0) {
        setError('Unable to connect to server. Please check if the backend is running.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchQueryHistory = async () => {
    try {
      const response = await apiClient.get('/api/queries?limit=10');
      setQueryHistory(response.data.queries || []);
    } catch (err) {
      console.error('Failed to fetch query history:', err);
    }
  };

  const toggleHistory = () => {
    setShowHistory(!showHistory);
    if (!showHistory) {
      fetchQueryHistory();
    }
  };

  const clearAnswer = () => {
    setAnswer('');
    setError('');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>ArXiv LLM Research Asisstant</h1>
        <p>Harness the power of AI to explore cutting-edge research papers and get intelligent insights from the arxiv repository</p>
        <small>Connected to: {API_BASE_URL}</small>
      </header>

      <main className="App-main">
        <div className="query-section">
          <form onSubmit={handleSubmit} className="query-form">
            <div className="form-group">
              <label htmlFor="query">Your Question:</label>
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your query here... (e.g., 'What is machine learning?')"
                rows={4}
                disabled={loading}
                className="query-input"
              />
            </div>
            
            <div className="form-actions">
              <button 
                type="submit" 
                disabled={loading || !query.trim()}
                className="submit-button"
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Processing...
                  </>
                ) : (
                  'Submit Query'
                )}
              </button>
              
              {(answer || error) && (
                <button 
                  type="button" 
                  onClick={clearAnswer}
                  className="clear-button"
                >
                  Clear
                </button>
              )}
            </div>
          </form>
        </div>

        {error && (
          <div className="error-section">
            <h3>❌ Error</h3>
            <p>{error}</p>
          </div>
        )}

        {answer && (
          <div className="answer-section">
            <h3>✅ Answer</h3>
            <div className="answer-content">
              {answer.split('\n').map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          </div>
        )}

        <div className="history-section">
          <button 
            onClick={toggleHistory}
            className="history-toggle"
          >
            {showHistory ? '📖 Hide History' : '📚 Show Recent Queries'}
          </button>
          
          {showHistory && (
            <div className="history-content">
              <h3>Recent Queries</h3>
              {queryHistory.length === 0 ? (
                <p>No queries found</p>
              ) : (
                <div className="history-list">
                  {queryHistory.map((item) => (
                    <div key={item.id} className="history-item">
                      <div className="history-query">
                        <strong>Q:</strong> {item.query}
                      </div>
                      <div className="history-answer">
                        <strong>A:</strong> {item.answer.substring(0, 200)}
                        {item.answer.length > 200 ? '...' : ''}
                      </div>
                      {item.relevance && (
                        <div className="history-meta">
                          Relevance: {item.relevance} | Confidence: {item.confidence_score}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;