import React, { useState } from 'react';
import {
  History,
  LogIn,
  LogOut,
  Menu,
  MessageCircle,
  Shirt,
  Sparkles,
  UploadCloud,
  User,
  UserPlus,
  X,
} from 'lucide-react';
import './Header.css';

export default function Header({ user, view, setView, handleLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const goToView = (nextView) => {
    setView(nextView);
    setMenuOpen(false);
  };

  const logout = () => {
    handleLogout();
    setMenuOpen(false);
  };

  const navItems = user
    ? [
        { view: 'profile', label: 'Profile', icon: User },
        { view: 'dashboard', label: 'Upload', icon: UploadCloud },
        { view: 'history', label: 'History', icon: History },
        { view: 'chatbot', label: 'Chatbot', icon: MessageCircle },
        { view: 'idea_search', label: 'Dress Ideas', icon: Sparkles },
      ]
    : [
        { view: 'login', label: 'Login', icon: LogIn, variant: 'outline' },
        { view: 'signup', label: 'Signup', icon: UserPlus, variant: 'primary' },
      ];

  return (
    <header className="header">
      <button className="brand-button" onClick={() => goToView('home')} aria-label="Go to home">
        <span className="brand-mark"><Shirt size={20} /></span>
        <span className="brand-text">
          <span className="app-title">FitFinder</span>
          <span className="app-subtitle">AI wardrobe studio</span>
        </span>
      </button>

      <button
        className="menu-toggle"
        onClick={() => setMenuOpen(open => !open)}
        aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
        aria-expanded={menuOpen}
      >
        {menuOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      <nav className={`nav-panel ${menuOpen ? 'open' : ''}`} aria-label="Main navigation">
        <div className="auth-buttons">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = view === item.view;
            return (
              <button
                key={item.view}
                className={`btn ${item.variant ? `btn-${item.variant}` : 'btn-gradient'} ${isActive ? 'active' : ''}`}
                onClick={() => goToView(item.view)}
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
