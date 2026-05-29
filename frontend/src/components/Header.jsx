import React, { useState } from 'react';
import {
  History,
  LogIn,
  LogOut,
  Menu,
  MessageCircle,
  Sparkles,
  UploadCloud,
  User,
  UserPlus,
  X,
} from 'lucide-react';

import { useNavigate, useLocation } from 'react-router-dom';

import './Header.css';

export default function Header({ user, handleLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  const goToPage = (path) => {
    navigate(path);
    setMenuOpen(false);
  };

  const logout = () => {
    handleLogout();
    navigate('/');
    setMenuOpen(false);
  };

  const navItems = user
    ? [
        { path: '/profile', label: 'Profile', icon: User },
        { path: '/upload', label: 'Upload', icon: UploadCloud },
        { path: '/history', label: 'History', icon: History },
        { path: '/chatbot', label: 'Chatbot', icon: MessageCircle },
        { path: '/idea-search', label: 'Dress Ideas', icon: Sparkles },
      ]
    : [
        { path: '/login', label: 'Login', icon: LogIn, variant: 'outline' },
        { path: '/signup', label: 'Signup', icon: UserPlus, variant: 'primary' },
      ];

  return (
    <header className="header">
      <button
        className="brand-button"
        onClick={() => goToPage('/')}
        aria-label="Go to home"
      >
        <span className="brand-mark">
          <img src="/fitfinder-logo.svg" alt="" aria-hidden="true" />
        </span>

        <span className="brand-text">
          <span className="app-title">FitFinder</span>
          <span className="app-subtitle">AI wardrobe studio</span>
        </span>
      </button>

      <button
        className="menu-toggle"
        onClick={() => setMenuOpen((open) => !open)}
        aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
        aria-expanded={menuOpen}
      >
        {menuOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      <nav
        className={`nav-panel ${menuOpen ? 'open' : ''}`}
        aria-label="Main navigation"
      >
        <div className="auth-buttons">
          {navItems.map((item) => {
            const Icon = item.icon;

            const isActive = location.pathname === item.path;

            return (
              <button
                key={item.path}
                className={`btn ${
                  item.variant
                    ? `btn-${item.variant}`
                    : 'btn-gradient'
                } ${isActive ? 'active' : ''}`}
                onClick={() => goToPage(item.path)}
              >
                <Icon size={17} />
                <span>{item.label}</span>
              </button>
            );
          })}

          {user && (
            <button className="btn btn-danger" onClick={logout}>
              <LogOut size={17} />
              <span>Logout</span>
            </button>
          )}
        </div>
      </nav>
    </header>
  );
}