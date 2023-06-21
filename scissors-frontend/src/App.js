import React from 'react';
import UrlShortenerForm from './UrlShortenerForm';

import NavBar from './NavigationBar';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import RegisterForm from './RegisterForm';
import HistoryPage from './History';
import Login from './Login';
import AnalyticsPage from './Analytics'
import QrCodePage from './QrCode';

function App() {
  
  return (
    <Router>
      <NavBar  />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/shorten" element={<UrlShortenerForm />} />
        <Route path="/register" element={<RegisterForm />}/>
        <Route path="/analytics/:shortCode" element={<AnalyticsPage />} />
        <Route path="/:shortCode/qrcode" element={<QrCodePage />} />
       
      </Routes>
    </Router>


  );
}

export default App;