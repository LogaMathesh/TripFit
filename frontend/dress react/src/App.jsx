import React, { useState, useEffect } from 'react'; 
import './App.css';
import Header from './components/Header';
import Footer from './components/Footer';
import Login from './components/Login';
import Signup from './components/Signup';
import History from './components/History';
import Favorites from './components/Favorites';
import Upload from './components/Upload';
import Suggestions from './components/Suggestions';
import Home from './components/Home';
import About from './components/About';
import Chatbot from './components/Chatbot';
import AsyncImageUpload from './components/AsyncImageUpload';
function App() {
  const [view, setView] = useState('home');
  const [user, setUser] = useState(null);

  // Load user and last visited page from localStorage on app load
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const lastView = localStorage.getItem('lastView');
    
    if (storedUser) {
      setUser(storedUser);
      // Use last visited page or default to 'home' instead of 'dashboard'
      setView(lastView || 'home');
    }
  }, []);

  // Save user to localStorage on login
  const handleLogin = (username) => {
    setUser(username);
    localStorage.setItem('user', username);
    setView('home'); // Default to home after login
  };

  // Clear user from localStorage on logout
  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('lastView');
    setView('home');
  };

  // Custom setView function that also saves to localStorage
  const handleViewChange = (newView) => {
    setView(newView);
    localStorage.setItem('lastView', newView);
  };

  return (
    <div className="app">
      <Header user={user} setView={handleViewChange} handleLogout={handleLogout} />
      
      <main>
        {/* Unauthenticated routes */}
        {view === 'home' && <Home setView={handleViewChange} user={user} />}
        {view === 'login' && !user && <Login onLogin={handleLogin} />}
        {view === 'signup' && !user && <Signup onSignup={handleLogin} />}
        {view === 'about' && <About />}
        
        {/* Authenticated routes */}
        {user && (
          <>
            {view === 'dashboard' && <Upload username={user} />}
            {view === 'history' && <History username={user} />}
            {view === 'favorites' && <Favorites username={user} />}
            {view === 'suggestions' && <Suggestions username={user} />}
            {view === 'chatbot' && <Chatbot currentUser={{ id: user }} />}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default App;
