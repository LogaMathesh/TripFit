import React, { useState, useEffect } from 'react';
import './Profile.css';
import { apiUrl } from '../lib/api';
import { BadgeIndianRupee, Ruler, Save, Shirt, Sparkles, User } from 'lucide-react';

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
    const fetchProfile = async () => {
      try {
        const response = await fetch(apiUrl(`/profile?username=${encodeURIComponent(username)}`));
        if (response.ok) {
          const data = await response.json();
          setProfile(data);
        }
      } catch (error) {
        console.error('Failed to fetch profile', error);
      }
    };

    if (username) {
      fetchProfile();
    }
  }, [username]);

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
      const response = await fetch(apiUrl('/profile'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...profile, username })
      });

      if (response.ok) {
        setMessage('Profile saved successfully.');
      } else {
        setMessage('Failed to save profile.');
      }
    } catch {
      setMessage('Connection error.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-container">
      <section className="profile-card">
        <aside className="profile-summary">
          <div className="profile-avatar">
            <User size={30} />
          </div>
          <span className="profile-kicker">Shopping profile</span>
          <h2>{username}</h2>
          <p>Keep your style, fit, and budget updated so recommendations feel more personal.</p>

          <div className="profile-meta">
            <div>
              <Shirt size={17} />
              <span>{profile.gender || 'Gender not set'}</span>
            </div>
            <div>
              <BadgeIndianRupee size={17} />
              <span>{profile.budget_level || 'Budget not set'}</span>
            </div>
            <div>
              <Ruler size={17} />
              <span>{profile.sizes || 'Sizes not set'}</span>
            </div>
            <div>
              <Sparkles size={17} />
              <span>{profile.style_preferences || 'Style not set'}</span>
            </div>
          </div>
        </aside>

        <form onSubmit={handleSave} className="profile-form">
          <div className="profile-form-header">
            <div>
              <span className="profile-kicker">Preferences</span>
              <h3>Style settings</h3>
            </div>
            {message && <div className={`profile-message ${message.includes('success') ? 'success' : 'error'}`}>{message}</div>}
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label>Gender</label>
              <select name="gender" value={profile.gender} onChange={handleChange}>
                <option value="">Select gender</option>
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Unisex">Unisex</option>
              </select>
            </div>

            <div className="form-group">
              <label>Budget Level</label>
              <select name="budget_level" value={profile.budget_level} onChange={handleChange}>
                <option value="">Select budget</option>
                <option value="Budget-friendly (Under ₹1500)">Budget-friendly (Under ₹1500)</option>
                <option value="Mid-range (₹1500 - ₹4000)">Mid-range (₹1500 - ₹4000)</option>
                <option value="Premium (₹4000 - ₹10000)">Premium (₹4000 - ₹10000)</option>
                <option value="Luxury (Above ₹10000)">Luxury (Above ₹10000)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Sizes</label>
              <input
                type="text"
                name="sizes"
                value={profile.sizes}
                onChange={handleChange}
                placeholder="M, 32, US 8"
              />
            </div>

            <div className="form-group">
              <label>Style Preferences</label>
              <input
                type="text"
                name="style_preferences"
                value={profile.style_preferences}
                onChange={handleChange}
                placeholder="Minimal, formal, streetwear"
              />
            </div>
          </div>

          <button type="submit" disabled={loading} className="profile-btn">
            <Save size={18} />
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
        </form>
      </section>
    </div>
  );
}
