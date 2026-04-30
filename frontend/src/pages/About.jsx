import React from 'react';
import './Home.css';
import { Helmet } from 'react-helmet-async';

export default function About() {
  return (
    <div className="home-content">
      <Helmet>
        <title>About FashionAI</title>
        <meta name="description" content="Learn more about FashionAI, your AI-powered style and fashion guide." />
        <link rel="icon" type="image/jpeg" href="/icon.jpg" />
      </Helmet>
      <div className="hero-section floating">
        <h2>👗 About FashionAI</h2>
        <p>FashionAI is your trusted companion for smart, AI-powered fashion advice and style recommendations.</p>
        <p>Our mission is to help you look and feel your best, every day and for every occasion.</p>
      </div>
      <div className="features-grid">
        <div className="feature-card">
          <span className="feature-icon">🤖</span>
          <h3>Our Technology</h3>
          <p>We use advanced machine learning to analyze your outfits and provide personalized suggestions.</p>
        </div>
        <div className="feature-card">
          <span className="feature-icon">🌈</span>
          <h3>Color & Style</h3>
          <p>Our AI understands color theory and style trends to help you create stunning combinations.</p>
        </div>
        <div className="feature-card">
          <span className="feature-icon">🛡️</span>
          <h3>Privacy First</h3>
          <p>Your photos and data are secure. We respect your privacy and never share your information.</p>
        </div>
        <div className="feature-card">
          <span className="feature-icon">🌍</span>
          <h3>For Everyone</h3>
          <p>FashionAI is designed for all ages, styles, and occasions. Join our global community!</p>
        </div>
      </div>
      <div className="cta-section">
        <h3>Have Questions?</h3>
        <p>Contact us or explore the app to discover all that FashionAI can do for you.</p>
      </div>
      {/* Creator/Contact Section */}
      <div className="creator-section">
        <div className="creator-card">
          <div className="creator-avatar">
            <img src="/icon.jpg" alt="Creator Avatar" />
          </div>
          <div className="creator-info">
            <h4>Created by <span className="creator-name">Loga Mathesh M</span></h4>
            <p><span className="creator-icon">📧</span> <a href="mailto:matheshloki2006@gmail.com">matheshloki2006@gmail.com</a></p>
            <p><span className="creator-icon">💻</span> <a href="https://github.com/LogaMathesh" target="_blank" rel="noopener noreferrer">@LogaMathesh</a></p>
          </div>
        </div>
      </div>
    </div>
  );
} 