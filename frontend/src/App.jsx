import React, { useState, useEffect } from 'react'; 
import './App.css';
import Header from './components/Header';
import Footer from './components/Footer';
import Login from './pages/Login';
import Signup from './pages/Signup';
import History from './pages/History';
import Favorites from './pages/Favorites';
import Upload from './pages/Upload';
import Suggestions from './pages/Suggestions';
import Home from './pages/Home';
import About from './pages/About';
import IdeaSearch from './pages/IdeaSearch';
import Profile from './pages/Profile';
import Chatbot from './components/Chatbot';
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
            {view === 'profile' && <Profile username={user} />}
            {view === 'dashboard' && <Upload username={user} />}
            {view === 'history' && <History username={user} />}
            {view === 'favorites' && <Favorites username={user} />}
            {view === 'suggestions' && <Suggestions username={user} />}
            {view === 'chatbot' && <Chatbot currentUser={{ id: user }} />}
            {view === 'idea_search' && <IdeaSearch user={user} />}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default App;
