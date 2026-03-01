import React, { useState, useEffect } from 'react';

const AsyncImageUpload = ({ username = "testuser" }) => {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, completed, error
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setStatus('idle');
    setResult(null);
  };

  const pollTaskStatus = async (taskId) => {
    try {
      const response = await fetch(`http://localhost:5000/task-status/${taskId}`);
      const data = await response.json();

      if (data.status === 'completed') {
        setStatus('completed');
        setResult(data);
      } else if (data.status === 'error') {
        setStatus('error');
        setErrorMessage(data.error || 'Failed during processing');
      } else {
        // Still processing, check again in 2 seconds
        setTimeout(() => pollTaskStatus(taskId), 2000);
      }
    } catch (err) {
      setStatus('error');
      setErrorMessage('Lost connection to server while checking status.');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    const formData = new FormData();
    formData.append('image', file);
    formData.append('username', username);

    try {
      const response = await fetch('http://localhost:5000/classify-async', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();

      if (data.status === 'completed') {
        // Handled instantly (duplicate image)
        setStatus('completed');
        setResult(data);
      } else if (data.status === 'processing') {
        // Upload successful, ML model is now running in background
        setStatus('processing');
        pollTaskStatus(data.task_id);
      } else {
        setStatus('error');
        setErrorMessage(data.error || 'Unknown error occurred.');
      }
    } catch (err) {
      setStatus('error');
      setErrorMessage('Failed to upload image. Server might be down.');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h3>Upload Dress for Classification</h3>
      
      <input type="file" accept="image/*" onChange={handleFileChange} disabled={status === 'uploading' || status === 'processing'} />
      
      <button 
        onClick={handleUpload} 
        disabled={!file || status === 'uploading' || status === 'processing'}
        style={{ marginTop: '10px', display: 'block' }}
      >
        Upload & Classify
      </button>

      {/* Dynamic Status Feedback */}
      <div style={{ marginTop: '20px' }}>
        {status === 'uploading' && <p>Uploading image to server...</p>}
        {status === 'processing' && (
          <p style={{ color: 'blue' }}>
            Image uploaded successfully! AI is currently classifying the dress. Please wait...
          </p>
        )}
        {status === 'error' && <p style={{ color: 'red' }}>Error: {errorMessage}</p>}
        
        {status === 'completed' && result && (
          <div style={{ borderTop: '1px solid #eee', paddingTop: '10px' }}>
            <h4 style={{ color: 'green' }}>Classification Complete!</h4>
            <img src={result.image_url} alt="Uploaded dress" style={{ width: '100%', borderRadius: '4px' }} />
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li><strong>Position:</strong> {result.position}</li>
              <li><strong>Style:</strong> {result.style}</li>
              <li><strong>Color:</strong> {result.color}</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default AsyncImageUpload;