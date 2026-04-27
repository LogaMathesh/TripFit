import React, { useState, useEffect } from 'react';
import './Profile.css';

export default function Profile({ username }) {
  const [profile, setProfile] = useState({
    gender: '',
    budget_level: '',
    sizes: '',
    style_preferences: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (username) {
      fetchProfile();
    }
  }, [username]);

  const fetchProfile = async () => {
    try {
      const response = await fetch(`http://localhost:5000/profile?username=${username}`);
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
      }
    } catch (error) {
      console.error('Failed to fetch profile', error);
    }
  };

  const handleChange = (e) => {
    setProfile({
      ...profile,
      [e.target.name]: e.target.value
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:5000/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...profile, username })
      });

      if (response.ok) {
        setMessage('✅ Profile saved successfully!');
      } else {
        setMessage('❌ Failed to save profile.');
      }
    } catch (error) {
      setMessage('❌ Connection error.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-container">
      <h2>👤 Your Shopping Profile</h2>
      <p className="profile-subtitle">Set your preferences so our AI can find the perfect outfits for you!</p>
      
      <form onSubmit={handleSave} className="profile-form">
        <div className="form-group">
          <label>Gender</label>
          <select name="gender" value={profile.gender} onChange={handleChange}>
            <option value="">Select Gender...</option>
            <option value="Female">Female</option>
            <option value="Male">Male</option>
            <option value="Unisex">Unisex</option>
          </select>
        </div>

        <div className="form-group">
          <label>Budget Level</label>
          <select name="budget_level" value={profile.budget_level} onChange={handleChange}>
            <option value="">Select Budget...</option>
            <option value="Budget-friendly (Under ₹1500)">Budget-friendly (Under ₹1500)</option>
            <option value="Mid-range (₹1500 - ₹4000)">Mid-range (₹1500 - ₹4000)</option>
            <option value="Premium (₹4000 - ₹10000)">Premium (₹4000 - ₹10000)</option>
            <option value="Luxury (Above ₹10000)">Luxury (Above ₹10000)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Sizes (e.g., M, 32, US 8)</label>
          <input 
            type="text" 
            name="sizes" 
            value={profile.sizes} 
            onChange={handleChange} 
            placeholder="What are your typical sizes?" 
          />
        </div>

        <div className="form-group">
          <label>Style Preferences</label>
          <input 
            type="text" 
            name="style_preferences" 
            value={profile.style_preferences} 
            onChange={handleChange} 
            placeholder="e.g., Minimalist, Boho, Formal, Streetwear" 
          />
        </div>

        <button type="submit" disabled={loading} className="btn btn-gradient profile-btn">
          {loading ? 'Saving...' : 'Save Profile'}
        </button>
      </form>

      {message && <div className="profile-message">{message}</div>}
    </div>
  );
}
