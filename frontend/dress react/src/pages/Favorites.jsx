import React, { useEffect, useState } from 'react';
import './History.css'; // Reusing the same CSS for consistency

export default function Favorites({ username }) {
  const [favoriteUploads, setFavoriteUploads] = useState([]);

  useEffect(() => {
    fetchFavorites();
  }, [username]);

  const fetchFavorites = async () => {
    try {
      const res = await fetch(`http://localhost:5000/history/${username}`);
      const data = await res.json();
      // Filter only favorite uploads
      const favorites = data.filter(upload => upload.favorite);
      setFavoriteUploads(favorites);
    } catch {
      setFavoriteUploads([]);
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
        // Remove the item from favorites if it was unfavorited
        if (!result.favorite) {
          setFavoriteUploads(prev => prev.filter(upload => upload.id !== uploadId));
        }
      } else {
        alert('Failed to update favorite status.');
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Failed to update favorite status.');
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
      setFavoriteUploads(prev => prev.filter(upload => upload.id !== uploadId));
    } else {
      alert('Failed to delete image.');
    }
  };

  return (
    <div className="history-container">
      <h2 className="history-title">❤️ Your Favorites</h2>
      
      {favoriteUploads.length === 0 ? (
        <div className="no-uploads">
          <p>No favorite uploads yet. Add some favorites from your history!</p>
        </div>
      ) : (
        <div className="favorites-section">
          <h3 className="favorites-title">
            ❤️ Favorites ({favoriteUploads.length})
          </h3>
          <ul className="upload-grid">
            {favoriteUploads.map((upload) => (
              <li key={upload.id} className="upload-item favorite">
                <div className="image-container">
                  <img src={upload.image_url} alt="uploaded" className="upload-image" />
                  <button 
                    onClick={() => handleToggleFavorite(upload.id)}
                    className="favorite-button favorited"
                  >
                    ❤️
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
      )}
    </div>
  );
} 