import React, { useState } from 'react';
import './Upload.css';
import { apiUrl } from '../lib/api';

export default function Upload({ username }) {
  const [uploads, setUploads] = useState([]);
  const [isIndexing, setIsIndexing] = useState(false);
  const [globalMessage, setGlobalMessage] = useState('');

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    const newUploads = selectedFiles.map((file) => ({
      id: Math.random().toString(36).substring(2, 9),
      file: file,
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
    if (uploads.length === 0) return setGlobalMessage('Please select images first.');

    uploads.forEach(async (uploadItem) => {
      if (uploadItem.status === 'completed') return;

      updateUploadState(uploadItem.id, { status: 'uploading', message: 'Uploading to Cloudinary...' });

      const cloudinaryFormData = new FormData();
      cloudinaryFormData.append('file', uploadItem.file);
      cloudinaryFormData.append('upload_preset', import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET || 'unsigned_preset');

      try {
        // 1. Upload to Cloudinary directly
        const cloudRes = await fetch(
          `https://api.cloudinary.com/v1_1/${import.meta.env.VITE_CLOUDINARY_CLOUD_NAME || 'demo'}/image/upload`,
          { method: 'POST', body: cloudinaryFormData }
        );
        
        if (!cloudRes.ok) throw new Error('Cloudinary upload failed');
        
        const cloudData = await cloudRes.json();
        const imageUrl = cloudData.secure_url;

        updateUploadState(uploadItem.id, { status: 'processing', message: 'AI Analyzing...' });

        // 2. Send URL to Backend for Gemini Processing
        const backendRes = await fetch(apiUrl('/classify'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_url: imageUrl, username: username }),
        });

        const data = await backendRes.json();

        if (backendRes.ok) {
          updateUploadState(uploadItem.id, { 
            status: 'completed', 
            result: data, 
            message: data.message || '✅ Success!' 
          });
        } else {
          updateUploadState(uploadItem.id, { status: 'error', message: `❌ Error: ${data.error}` });
        }
      } catch (err) {
        console.error(err);
        updateUploadState(uploadItem.id, { status: 'error', message: '❌ Upload failed' });
      }
    });
  };

  const handleIndexExisting = async () => {
    setGlobalMessage("Chatbot integration needs URL updates for serverless.");
  };

  const isAnyLoading = uploads.some(u => u.status === 'uploading' || u.status === 'processing');

  return (
    <div className="upload-container">
      <h2>Upload Your Outfits</h2>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileChange}
          disabled={isAnyLoading}
        />
        <button type="submit" disabled={isAnyLoading || uploads.length === 0}>
          {isAnyLoading ? 'Processing Images...' : `Analyze ${uploads.length} Outfits`}
        </button>
      </form>

      <div className="index-section">
        <h3>🤖 Chatbot Integration</h3>
        <button onClick={handleIndexExisting} disabled={isIndexing} className="index-button">
          {isIndexing ? 'Indexing...' : '📚 Index Selected Images'}
        </button>
        {globalMessage && <p style={{marginTop: '10px', fontWeight: 'bold'}}>{globalMessage}</p>}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginTop: '20px' }}>
        {uploads.map((upload) => (
          <div key={upload.id} style={{ border: '1px solid #ccc', padding: '10px', width: '250px', borderRadius: '8px' }}>
            <img src={upload.previewUrl} alt="Preview" style={{ width: '100%', height: '200px', objectFit: 'cover' }} />
            
            <p style={{ fontSize: '14px', color: upload.status === 'error' ? 'red' : 'blue' }}>
              {upload.message}
            </p>

            {(upload.status === 'uploading' || upload.status === 'processing') && (
              <div className="spinner" style={{ margin: '10px auto' }} />
            )}

            {upload.status === 'completed' && upload.result && (
              <div style={{ fontSize: '14px', marginTop: '10px' }}>
                <p><strong>Position:</strong> {upload.result.position}</p>
                <p><strong>Style:</strong> {upload.result.style}</p>
                <p><strong>Color:</strong> {upload.result.color}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
