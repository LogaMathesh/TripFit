import React, { useEffect, useState } from 'react';
import './History.css';
import { apiUrl } from '../lib/api';

export default function History({ username }) {
  const [uploads, setUploads] = useState([]);
  const [favoriteFilter, setFavoriteFilter] = useState('all');
  const [styleFilter, setStyleFilter] = useState('all');
  const [positionFilter, setPositionFilter] = useState('all');
  const [sortOrder, setSortOrder] = useState('newest');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(apiUrl(`/history/${username}`));
        const data = await res.json();
        setUploads(data);
      } catch {
        setUploads([]);
      }
    };

    fetchHistory();
  }, [username]);

  const normalizeValue = (value) => value || 'Unknown';

  const groupByStyle = (uploadList) => {
    return uploadList.reduce((groups, upload) => {
      const style = normalizeValue(upload.style);
      if (!groups[style]) {
        groups[style] = [];
      }
      groups[style].push(upload);
      return groups;
    }, {});
  };

  const getUniqueOptions = (key) => {
    return [...new Set(uploads.map(upload => normalizeValue(upload[key])))]
      .sort((a, b) => a.localeCompare(b));
  };

  const formatDate = (dateValue) => {
    return new Date(dateValue).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const handleDelete = async (uploadId) => {
    const res = await fetch(apiUrl('/delete_upload'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upload_id: uploadId }),
    });

    const result = await res.json();
    if (result.status === 'success') {
      setUploads(prevUploads => prevUploads.filter(upload => upload.id !== uploadId));
    } else {
      alert('Failed to delete image.');
    }
  };

  const handleToggleFavorite = async (uploadId) => {
    try {
      const res = await fetch(apiUrl('/toggle_favorite'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ upload_id: uploadId, username }),
      });

      const result = await res.json();
      if (result.status === 'success') {
        setUploads(prevUploads => prevUploads.map(upload =>
          upload.id === uploadId
            ? { ...upload, favorite: result.favorite }
            : upload
        ));
      } else {
        alert('Failed to update favorite status.');
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Failed to update favorite status.');
    }
  };

  const clearFilters = () => {
    setFavoriteFilter('all');
    setStyleFilter('all');
    setPositionFilter('all');
    setSortOrder('newest');
  };

  const styleOptions = getUniqueOptions('style');
  const positionOptions = getUniqueOptions('position');
  const favoriteCount = uploads.filter(upload => upload.favorite).length;
  const hasActiveFilters = favoriteFilter !== 'all' || styleFilter !== 'all' || positionFilter !== 'all' || sortOrder !== 'newest';

  const filteredUploads = uploads
    .filter(upload => favoriteFilter === 'favorites' ? upload.favorite : true)
    .filter(upload => styleFilter === 'all' ? true : normalizeValue(upload.style) === styleFilter)
    .filter(upload => positionFilter === 'all' ? true : normalizeValue(upload.position) === positionFilter)
    .sort((a, b) => {
      const aTime = new Date(a.uploaded_at).getTime();
      const bTime = new Date(b.uploaded_at).getTime();
      return sortOrder === 'oldest' ? aTime - bTime : bTime - aTime;
    });

  const filteredGroupedUploads = groupByStyle(filteredUploads);

  return (
    <div className="history-container">
      <section className="history-hero">
        <div className="history-heading">
          <span className="history-eyebrow">Wardrobe</span>
          <h2 className="history-title">History</h2>
        </div>

        <div className="history-stats" aria-label="Wardrobe summary">
          <div className="stat-tile">
            <span className="stat-value">{uploads.length}</span>
            <span className="stat-label">Items</span>
          </div>
          <div className="stat-tile">
            <span className="stat-value">{favoriteCount}</span>
            <span className="stat-label">Favorites</span>
          </div>
          <div className="stat-tile">
            <span className="stat-value">{styleOptions.length}</span>
            <span className="stat-label">Styles</span>
          </div>
          <div className="stat-tile">
            <span className="stat-value">{filteredUploads.length}</span>
            <span className="stat-label">Visible</span>
          </div>
        </div>
      </section>

      <section className="filter-panel" aria-label="History filters">
        <div className="filter-panel-header">
          <div>
            <span className="filter-panel-kicker">Filters</span>
            <h3>Find saved looks</h3>
          </div>

          {hasActiveFilters && (
            <button onClick={clearFilters} className="reset-filter-button">
              Reset
            </button>
          )}
        </div>

        <div className="filter-controls">
          <div className="filter-group favorite-filter" role="group" aria-label="Favorite filter">
            <span className="filter-label">Show</span>
            <button
              onClick={() => setFavoriteFilter('all')}
              className={`filter-button ${favoriteFilter === 'all' ? 'active' : ''}`}
            >
              All
            </button>
            <button
              onClick={() => setFavoriteFilter('favorites')}
              className={`filter-button ${favoriteFilter === 'favorites' ? 'active show-favorites' : ''}`}
            >
              Favorites
            </button>
          </div>

          <label className="filter-field">
            <span className="filter-label">Style</span>
            <select value={styleFilter} onChange={(event) => setStyleFilter(event.target.value)}>
              <option value="all">All styles</option>
              {styleOptions.map(style => (
                <option key={style} value={style}>{style}</option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span className="filter-label">Position</span>
            <select value={positionFilter} onChange={(event) => setPositionFilter(event.target.value)}>
              <option value="all">All positions</option>
              {positionOptions.map(position => (
                <option key={position} value={position}>{position}</option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span className="filter-label">Sort</span>
            <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
            </select>
          </label>
        </div>
      </section>

      {filteredUploads.length === 0 ? (
        <div className="no-uploads">
          <h3>{uploads.length === 0 ? 'No uploads yet' : 'No matching items'}</h3>
          <p>{uploads.length === 0 ? 'Your uploaded outfits will appear here.' : 'Adjust the filters to view more saved looks.'}</p>
        </div>
      ) : (
        Object.keys(filteredGroupedUploads).map((style) => (
          <section key={style} className="style-section">
            <div className="style-section-header">
              <h3 className="style-title">{style}</h3>
              <span className="style-count">{filteredGroupedUploads[style].length} items</span>
            </div>

            <ul className="upload-grid">
              {filteredGroupedUploads[style].map((upload) => (
                <li key={upload.id} className={`upload-item ${upload.favorite ? 'favorite' : ''}`}>
                  <div className="image-container">
                    <img src={upload.image_url} alt={`${normalizeValue(upload.style)} outfit`} className="upload-image" />
                    <button
                      onClick={() => handleToggleFavorite(upload.id)}
                      className={`favorite-button ${upload.favorite ? 'favorited' : ''}`}
                      aria-label={upload.favorite ? 'Remove from favorites' : 'Add to favorites'}
                      title={upload.favorite ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      {upload.favorite ? '\u2665' : '\u2661'}
                    </button>
                  </div>

                  <div className="upload-info">
                    <div className="upload-info-header">
                      <h4>{normalizeValue(upload.style)}</h4>
                      <span>{formatDate(upload.uploaded_at)}</span>
                    </div>

                    <div className="upload-tags">
                      <span>{normalizeValue(upload.position)}</span>
                      {upload.color && <span>{upload.color}</span>}
                      {upload.favorite && <span>Favorite</span>}
                    </div>

                    <button onClick={() => handleDelete(upload.id)} className="delete-button">
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}
