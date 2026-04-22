import React, { useState } from 'react';
import './Suggestions.css';

export default function Suggestions({ username }) {
  const [destination, setDestination] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchSuggestions = async () => {
    if (!destination) return;
    if (!username) {
      setMessage('Please log in to get dress suggestions.');
      return;
    }
    
    setLoading(true);
    setMessage('');
    
    try {
      const res = await fetch('http://localhost:5000/get-suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination, username })
      });

      const data = await res.json();

      if (data.suggestions.length === 0) {
        setMessage('No matching dresses found for this destination.');
        setSuggestions([]);
      } else {
        setSuggestions(data.suggestions);
        setMessage('');
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
      setMessage('Failed to fetch suggestions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="suggestions">
      <h2>Dress Suggestions</h2>
      
      {!username ? (
        <div className="message error">
          Please log in to view your dress suggestions.
        </div>
      ) : (
        <div className="suggestions-container">
        <div className="selection-section">
          <label>Select your destination:</label>
          <select 
            className="destination-select"
            value={destination} 
            onChange={(e) => setDestination(e.target.value)}
          >
            <option value="">--Select Destination--</option>
            <option value="casual">👕 Casual</option>
            <option value="formal">👔 Formal</option>
            <option value="traditional">👘 Traditional</option>
          </select>

          <button 
            className="suggest-button"
            onClick={fetchSuggestions} 
            disabled={!destination || loading}
          >
            {loading ? 'Loading...' : 'Show Suggestions'}
          </button>
        </div>

        {message && (
          <div className={`message ${message.includes('Failed') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}

        {loading && (
          <div className="loading">
            Finding perfect dresses for you...
          </div>
        )}

        {suggestions.length > 0 && (
          <div className="suggestion-grid">
            {suggestions.map((item, index) => (
              <div key={index} className="suggestion-card">
                <div className="card-badge">{item.style}</div>
                <img
                  className="card-image"
                  src={item.image_url}
                  alt={`${item.style} dress`}
                  onError={(e) => { 
                    e.target.src = 'https://via.placeholder.com/300x250/f0f0f0/999?text=Dress+Image'; 
                  }}
                />
                <div className="card-content">
                  <h3 className="card-title">{item.style} Dress</h3>
                  <div className="card-info">
                    <p>
                      <strong>Style:</strong> 
                      <span style={{ textTransform: 'capitalize' }}>{item.style}</span>
                    </p>
                    <p>
                      <strong>Uploaded:</strong> 
                      {new Date(item.uploaded_at).toLocaleDateString()}
                    </p>
                    <p>
                      <strong>Time:</strong> 
                      {new Date(item.uploaded_at).toLocaleTimeString()}
                    </p>
                    <p>
                      <strong>Position:</strong> 
                      {item.position}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        </div>
      )}
    </div>
  );
}
