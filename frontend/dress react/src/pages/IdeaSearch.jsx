import React, { useState } from 'react';
import './IdeaSearch.css';

export default function IdeaSearch({ user }) {
  const [idea, setIdea] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [queryUsed, setQueryUsed] = useState('');
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!idea.trim()) return;

    setLoading(true);
    setResults([]);
    setError(null);
    setQueryUsed('');

    try {
      const response = await fetch('http://localhost:5000/search-ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, username: user })
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data.results || []);
        setQueryUsed(data.query_used || '');
      } else {
        if (data.error === 'gemini_api_key_missing') {
          setError("⚠️ Please ask the server administrator to input the GEMINI_API_KEY inside the .env file.");
        } else {
          setError(data.message || data.details || data.error || 'Something went wrong.');
        }
      }
    } catch (err) {
      setError('Connection error: Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="idea-search-container">
      <h2>✨ Magic Dress Idea Search</h2>
      <p className="idea-subtitle">Describe your dream dress in plain text, and our AI will track it down online!</p>
      
      <form onSubmit={handleSearch} className="idea-form">
        <textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="e.g., A flowy emerald green dress perfect for a winter formal gala"
          rows={3}
        />
        <button type="submit" disabled={loading || !idea.trim()} className="btn btn-gradient search-btn">
          {loading ? 'Searching the web...' : 'Find Matches'}
        </button>
      </form>

      {error && <div className="error-box">{error}</div>}

      {queryUsed && (
        <div className="query-box">
          <strong>AI actively searched for: </strong> "{queryUsed}"
        </div>
      )}

      {loading && <div className="spinner idea-spinner" />}

      {results.length > 0 && (
        <div className="idea-results">
          {results.map((item, idx) => (
            <a href={item.link} target="_blank" rel="noopener noreferrer" className="idea-card" key={idx}>
              <div className="card-img-container">
                <img src={item.thumbnail} alt={item.title} />
              </div>
              <div className="card-info">
                <h4 className="card-title">{item.title}</h4>
                <p className="card-price">{item.price}</p>
                <p className="card-source">{item.source}</p>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
