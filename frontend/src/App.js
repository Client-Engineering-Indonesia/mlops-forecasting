// src/App.js
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Login from './Login';
import Project from './Project';
import Home from './Home';  // This is the component you want to render after successful login
import PDFViewer from './PDFViewer';

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/project" element={<Project />} />
        <Route path="/pdf_viewer" element={<PDFViewer />} />
        <Route path="/home" element={<Home />} />  {/* Redirect here after login */}
      </Routes>
    </div>
  );
}

export default App;