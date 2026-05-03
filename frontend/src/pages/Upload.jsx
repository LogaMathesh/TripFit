import React, { useState } from 'react';
import './Upload.css';
import { apiUrl } from '../lib/api';
import { CheckCircle2, ImagePlus, Loader2, UploadCloud, XCircle } from 'lucide-react';

export default function Upload({ username }) {
  const [uploads, setUploads] = useState([]);
  const [globalMessage, setGlobalMessage] = useState('');

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);

    const newUploads = selectedFiles.map((file) => ({
      id: Math.random().toString(36).substring(2, 9),
      file,
      previewUrl: URL.createObjectURL(file),
      status: 'idle',
      result: null,
      message: ''
    }));

    setUploads(newUploads);
    setGlobalMessage('');
  };

  const updateUploadState = (id, updates) => {
    setUploads((prev) =>
      prev.map((item) => (item.id === id ? { ...item, ...updates } : item))
    );
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (uploads.length === 0) {
      setGlobalMessage('Please select images first.');
      return;
    }

    uploads.forEach(async (uploadItem) => {
      if (uploadItem.status === 'completed') return;

      updateUploadState(uploadItem.id, { status: 'uploading', message: 'Uploading to Cloudinary...' });

      const cloudinaryFormData = new FormData();
      cloudinaryFormData.append('file', uploadItem.file);
      cloudinaryFormData.append('upload_preset', import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET || 'unsigned_preset');

      try {
        const cloudRes = await fetch(
          `https://api.cloudinary.com/v1_1/${import.meta.env.VITE_CLOUDINARY_CLOUD_NAME || 'demo'}/image/upload`,
          { method: 'POST', body: cloudinaryFormData }
        );

        if (!cloudRes.ok) throw new Error('Cloudinary upload failed');

        const cloudData = await cloudRes.json();
        const imageUrl = cloudData.secure_url;

        updateUploadState(uploadItem.id, { status: 'processing', message: 'AI analyzing this outfit...' });

        const backendRes = await fetch(apiUrl('/classify'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_url: imageUrl, username }),
        });

        const data = await backendRes.json();

        if (backendRes.ok) {
          updateUploadState(uploadItem.id, {
            status: 'completed',
            result: data,
            message: data.message || 'Saved to your wardrobe.'
          });
        } else {
          updateUploadState(uploadItem.id, { status: 'error', message: `Error: ${data.error || 'Unable to analyze image'}` });
        }
      } catch (err) {
        console.error(err);
        updateUploadState(uploadItem.id, { status: 'error', message: 'Upload failed. Please try again.' });
      }
    });
  };

  const isAnyLoading = uploads.some((u) => u.status === 'uploading' || u.status === 'processing');
  const selectedCount = uploads.length;
  const completedCount = uploads.filter((u) => u.status === 'completed').length;

  return (
    <div className="upload-container">
      <div className="upload-header">
        <span className="upload-kicker">Wardrobe intake</span>
        <h2>Upload Your Outfits</h2>
        <p>Choose one or more outfit photos. Each image is analyzed and saved for history, suggestions, and chatbot search.</p>
      </div>

      <form onSubmit={handleUpload} className="upload-form">
        <label className={`file-dropzone ${isAnyLoading ? 'disabled' : ''}`}>
          <ImagePlus size={30} />
          <span>{selectedCount ? `${selectedCount} image${selectedCount > 1 ? 's' : ''} selected` : 'Select outfit images'}</span>
          <small>JPG, PNG, or WEBP</small>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileChange}
            disabled={isAnyLoading}
          />
        </label>

        <div className="upload-actions">
          <button type="submit" disabled={isAnyLoading || uploads.length === 0}>
            {isAnyLoading ? <Loader2 size={18} className="spin-icon" /> : <UploadCloud size={18} />}
            <span>{isAnyLoading ? 'Processing Images...' : `Analyze ${uploads.length || 0} Outfits`}</span>
          </button>
          {selectedCount > 0 && (
            <span className="upload-summary">{completedCount}/{selectedCount} saved</span>
          )}
        </div>
      </form>

      {globalMessage && <p className="message error">{globalMessage}</p>}

      <div className="upload-preview-grid">
        {uploads.map((upload) => (
          <article key={upload.id} className={`upload-preview-card ${upload.status}`}>
            <div className="upload-preview-image">
              <img src={upload.previewUrl} alt="Selected outfit preview" />
              <span className="upload-status-badge">
                {upload.status === 'completed' && <CheckCircle2 size={15} />}
                {upload.status === 'error' && <XCircle size={15} />}
                {(upload.status === 'uploading' || upload.status === 'processing') && <Loader2 size={15} className="spin-icon" />}
                {upload.status}
              </span>
            </div>

            {upload.message && <p className="upload-card-message">{upload.message}</p>}

            {upload.status === 'completed' && upload.result && (
              <div className="upload-result-tags">
                <span>{upload.result.position}</span>
                <span>{upload.result.style}</span>
                <span>{upload.result.color}</span>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
