import React, { useEffect, useState } from 'react';
import './History.css';

export default function History({ username }) {
  const [uploads, setUploads] = useState([]);
  const [groupedUploads, setGroupedUploads] = useState({});
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, [username]);

  // Group uploads by position
  const groupByPosition = (uploads) => {
    return uploads.reduce((groups, upload) => {
      const pos = upload.style || 'Unknown';
      if (!groups[pos]) {
        groups[pos] = [];
      }
      groups[pos].push(upload);
      return groups;
    }, {});
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`http://localhost:5000/history/${username}`);
      const data = await res.json();
      setUploads(data);
      setGroupedUploads(groupByPosition(data));
    } catch {
      setUploads([]);
      setGroupedUploads({});
    }
  };

  const handleDelete = async (uploadId) => {
    const res = await fetch('http://localhost:5000/delete_upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upload_id: uploadId }),
    });

    const result = await res.json();
    if (result.status === 'success') {
      const updatedUploads = uploads.filter(upload => upload.id !== uploadId);
      setUploads(updatedUploads);
      setGroupedUploads(groupByPosition(updatedUploads));
    } else {
      alert('Failed to delete image.');
    }
  };

  const handleToggleFavorite = async (uploadId) => {
    try {
      const res = await fetch('http://localhost:5000/toggle_favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ upload_id: uploadId, username: username }),
      });

      const result = await res.json();
      if (result.status === 'success') {
        // Update the upload in the state
        const updatedUploads = uploads.map(upload => 
          upload.id === uploadId 
            ? { ...upload, favorite: result.favorite }
            : upload
        );
        setUploads(updatedUploads);
        setGroupedUploads(groupByPosition(updatedUploads));
      } else {
        alert('Failed to update favorite status.');
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Failed to update favorite status.');
    }
  };

  // Filter uploads based on favorite status
  const filteredUploads = showFavoritesOnly 
    ? uploads.filter(upload => upload.favorite)
    : uploads;

  const filteredGroupedUploads = groupByPosition(filteredUploads);

  return (
    <div className="history-container">
      <h2 className="history-title">Your Upload History</h2>
      
      {/* Filter Toggle */}
      <div className="filter-controls">
        <button 
          onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
          className={`filter-button ${showFavoritesOnly ? 'show-favorites' : 'show-all'}`}
        >
          {showFavoritesOnly ? 'Show All' : 'Show Favorites Only'}
        </button>
        <span className="filter-status">
          {showFavoritesOnly 
            ? `Showing ${filteredUploads.length} favorite items` 
            : `Showing all ${uploads.length} items`
          }
        </span>
      </div>

      {/* Main History Section */}
      {filteredUploads.length === 0 ? (
        <div className="no-uploads">
          <p>{showFavoritesOnly ? 'No favorite uploads yet.' : 'No uploads yet.'}</p>
        </div>
      ) : (
        Object.keys(filteredGroupedUploads).map((position) => (
          <div key={position} className="style-section">
            <h3 className="style-title">{position.toUpperCase()}</h3>
            <ul className="upload-grid">
              {filteredGroupedUploads[position].map((upload) => (
                <li key={upload.id} className={`upload-item ${upload.favorite ? 'favorite' : ''}`}>
                  <div className="image-container">
                    <img src={upload.image_url} alt="uploaded" className="upload-image" />
                    <button 
                      onClick={() => handleToggleFavorite(upload.id)}
                      className={`favorite-button ${upload.favorite ? 'favorited' : ''}`}
                    >
                      {upload.favorite ? '❤️' : '🤍'}
                    </button>
                  </div>
                  <div className="upload-info">
                    <p><strong>Position:</strong> {upload.position}</p>
                    <p><strong>Style:</strong> {upload.style}</p>
                    <p className="upload-date">{new Date(upload.uploaded_at).toLocaleString()}</p>
                    <button onClick={() => handleDelete(upload.id)} className="delete-button">
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  );
}
