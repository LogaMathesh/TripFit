import React, { useState } from 'react';
import './Upload.css';

export default function Upload({ username }) {
  // We now store an ARRAY of files instead of a single file
  const [uploads, setUploads] = useState([]);
  const [isIndexing, setIsIndexing] = useState(false);
  const [globalMessage, setGlobalMessage] = useState('');

  // 1. Handle Multiple File Selection
  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    // Create a state object for each file to track them independently
    const newUploads = selectedFiles.map((file) => ({
      id: Math.random().toString(36).substring(2, 9), // Unique ID for React
      file: file,
      previewUrl: URL.createObjectURL(file),
      status: 'idle', // 'idle', 'uploading', 'processing', 'completed', 'error'
      result: null,
      message: ''
    }));

    setUploads(newUploads);
    setGlobalMessage('');
  };

  // Helper to update the state of one specific file without affecting the others
  const updateUploadState = (id, updates) => {
    setUploads((prev) => 
      prev.map((item) => (item.id === id ? { ...item, ...updates } : item))
    );
  };

  // 2. Poll Status for a specific file
  const pollTaskStatus = async (taskId, fileId) => {
    try {
      const response = await fetch(`http://localhost:5000/task-status/${taskId}`);
      const data = await response.json();

      if (data.status === 'completed') {
        updateUploadState(fileId, { 
          status: 'completed', 
          result: data, 
          message: '✅ Success!' 
        });
      } else if (data.status === 'error') {
        updateUploadState(fileId, { 
          status: 'error', 
          message: `❌ Error: ${data.error}` 
        });
      } else {
        updateUploadState(fileId, { message: 'AI is analyzing...' });
        setTimeout(() => pollTaskStatus(taskId, fileId), 2000);
      }
    } catch (err) {
      updateUploadState(fileId, { status: 'error', message: '❌ Connection lost.' });
    }
  };

  // 3. Upload all files one by one
  const handleUpload = async (e) => {
    e.preventDefault();
    if (uploads.length === 0) return setGlobalMessage('Please select images first.');

    // Process each file in the uploads array
    uploads.forEach(async (uploadItem) => {
      if (uploadItem.status === 'completed') return; // Skip already done ones

      updateUploadState(uploadItem.id, { status: 'uploading', message: 'Uploading...' });

      const formData = new FormData();
      formData.append('image', uploadItem.file);
      formData.append('username', username);

      try {
        const res = await fetch('http://localhost:5000/classify-async', {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();

        if (data.status === 'completed') {
          // Instant duplicate
          updateUploadState(uploadItem.id, { 
            status: 'completed', 
            result: data, 
            message: '✅ Duplicate found & loaded!' 
          });
        } else if (data.status === 'processing') {
          // Send to background task
          updateUploadState(uploadItem.id, { status: 'processing', message: 'Starting AI...' });
          pollTaskStatus(data.task_id, uploadItem.id);
        } else {
          updateUploadState(uploadItem.id, { status: 'error', message: '❌ Upload failed' });
        }
      } catch {
        updateUploadState(uploadItem.id, { status: 'error', message: '❌ Server error' });
      }
    });
  };

  // Your existing Chatbot Indexing Logic (Adjusted for multiple files)
  const handleIndexExisting = async () => {
    if (uploads.length === 0) return setGlobalMessage("Please select images first.");
    setIsIndexing(true);
    setGlobalMessage("");

    // Send the first file as an example (or you can loop this too)
    const formData = new FormData();
    formData.append("image", uploads[0].file); 
    formData.append("user_id", username);
    formData.append("style", "Unknown");
    formData.append("color", "Unknown");

    try {
      const res = await fetch("http://localhost:5000/chatbot/upload", {
        method: "POST",
        body: formData,
      });
      if (res.ok) setGlobalMessage(`✅ Chatbot indexing complete!`);
      else setGlobalMessage(`❌ Failed to index.`);
    } catch (err) {
      setGlobalMessage("❌ Failed to index image");
    } finally {
      setIsIndexing(false);
    }
  };

  // Check if ANY file is currently loading to disable the submit button
  const isAnyLoading = uploads.some(u => u.status === 'uploading' || u.status === 'processing');

  return (
    <div className="upload-container">
      <h2>Upload Your Outfits</h2>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          accept="image/*"
          multiple /* <-- THIS IS THE MAGIC WORD THAT ALLOWS MULTIPLE FILES */
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

      {/* Grid to display all uploaded files and their independent statuses */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginTop: '20px' }}>
        {uploads.map((upload) => (
          <div key={upload.id} style={{ border: '1px solid #ccc', padding: '10px', width: '250px', borderRadius: '8px' }}>
            <img src={upload.previewUrl} alt="Preview" style={{ width: '100%', height: '200px', objectFit: 'cover' }} />
            
            {/* Show individual status */}
            <p style={{ fontSize: '14px', color: upload.status === 'error' ? 'red' : 'blue' }}>
              {upload.message}
            </p>

            {/* Show spinner if this specific file is processing */}
            {(upload.status === 'uploading' || upload.status === 'processing') && (
              <div className="spinner" style={{ margin: '10px auto' }} />
            )}

            {/* Show result when finished */}
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