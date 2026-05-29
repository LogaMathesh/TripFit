import React, { useState, useEffect } from 'react';
import './App.css';
import { Routes, Route, Navigate } from 'react-router-dom';

import Header from './components/Header';
import Footer from './components/Footer';

import Login from './pages/Login';
import Signup from './pages/Signup';
import History from './pages/History';
import Upload from './pages/Upload';
import Home from './pages/Home';
import About from './pages/About';
import IdeaSearch from './pages/IdeaSearch';
import Profile from './pages/Profile';
import Chatbot from './components/Chatbot';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');

    if (storedUser) {
      setUser(storedUser);
    }
  }, []);

  const handleLogin = (username) => {
    setUser(username);
    localStorage.setItem('user', username);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <div className="app">
      <Header user={user} handleLogout={handleLogout} />

      <main>
        <Routes>
          {/* Public Routes */}
          <Route
            path="/"
            element={<Home user={user} />}
          />

          <Route
            path="/about"
            element={<About />}
          />

          <Route
            path="/login"
            element={
              !user ? (
                <Login onLogin={handleLogin} />
              ) : (
                <Navigate to="/" />
              )
            }
          />

          <Route
            path="/signup"
            element={
              !user ? (
                <Signup onSignup={handleLogin} />
              ) : (
                <Navigate to="/" />
              )
            }
          />

          {/* Protected Routes */}

          <Route
            path="/upload"
            element={
              user ? (
                <Upload username={user} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />

          <Route
            path="/history"
            element={
              user ? (
                <History username={user} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />

          <Route
            path="/profile"
            element={
              user ? (
                <Profile username={user} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />

          <Route
            path="/chatbot"
            element={
              user ? (
                <Chatbot currentUser={{ id: user }} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />

          <Route
            path="/idea-search"
            element={
              user ? (
                <IdeaSearch user={user} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}

export default App;