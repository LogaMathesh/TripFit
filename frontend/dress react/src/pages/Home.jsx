// src/components/Home.jsx
import React, { useState } from 'react';
import './Home.css';
import { Helmet } from 'react-helmet-async';
import Chatbot from '../components/Chatbot';

export default function Home({ setView, user }) {
  const [showChatbot, setShowChatbot] = useState(false);
  return (
    <div className="home-content">
      <Helmet>
        <title>FashionAI - Your Ultimate Style Guide</title>
        <meta name="description" content="Upload your outfit and get smart fashion suggestions based on style, occasion, and color analysis." />
        <link rel="icon" type="image/jpeg" href="/icon.jpg" />
      </Helmet>
      
      <div className="hero-section floating">
        <h2>✨ Your Ultimate Fashion Guide</h2>
        <p>Upload your outfit and get intelligent style suggestions powered by AI</p>
        <p>Discover perfect combinations for any occasion, season, or mood</p>
      </div>

      <div className="features-grid">
        <div className="feature-card">
          <span className="feature-icon">🎨</span>
          <h3>Smart Color Analysis</h3>
          <p>Our AI analyzes dominant colors and suggests perfect color combinations for your outfit</p>
        </div>
        
        <div className="feature-card">
          <span className="feature-icon">👗</span>
          <h3>Style Recommendations</h3>
          <p>Get personalized fashion suggestions based on your style preferences and the occasion</p>
        </div>
        
        <div className="feature-card">
          <span className="feature-icon">💡</span>
          <h3>AI-Powered Insights</h3>
          <p>Advanced machine learning algorithms provide intelligent outfit recommendations</p>
        </div>
        
        <div className="feature-card">
          <span className="feature-icon">📱</span>
          <h3>Easy Upload</h3>
          <p>Simply upload a photo of your outfit and get instant fashion advice and suggestions</p>
        </div>
      </div>

      <div className="cta-section">
        <h3>Ready to Transform Your Style?</h3>
        <p>Join thousands of fashion enthusiasts who trust our AI-powered recommendations</p>
        <div className="cta-buttons">
          <button className="cta-button primary" onClick={() => setView('signup')}>Get Started Now</button>
          <button className="cta-button secondary" onClick={() => setView('about')}>Learn More</button>
        </div>
      </div>

      {/* Chatbot Icon - Only show if user is logged in */}
      {user && (
        <div className="chatbot-icon-container">
          <button 
            className="chatbot-icon-button"
            onClick={() => setShowChatbot(true)}
            title="Ask our AI Fashion Assistant"
          >
            💬
          </button>
        </div>
      )}

      {/* Chatbot Modal */}
      {showChatbot && user && (
        <div className="chatbot-modal-overlay" onClick={() => setShowChatbot(false)}>
          <div className="chatbot-modal" onClick={(e) => e.stopPropagation()}>
            <div className="chatbot-modal-header">
              <h3>💬 AI Fashion Assistant</h3>
              <button 
                className="chatbot-close-button"
                onClick={() => setShowChatbot(false)}
              >
                ✕
              </button>
            </div>
            <div className="chatbot-modal-content">
              <Chatbot currentUser={{ id: user }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
