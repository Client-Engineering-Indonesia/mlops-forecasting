// src/PDFViewer.js
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BE_URL = process.env.REACT_APP_API_URL;

console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

function PDFViewer() {
  const [searchParams] = useSearchParams();
  const [pdfUrl, setPdfUrl] = useState(null);
  const fileName = searchParams.get("file");

  useEffect(() => {
    if (fileName) {
      axios.get(`${BE_URL}/pdf_viewer?file=${fileName}`)
        .then(res => setPdfUrl(res.data.url))
        .catch(err => console.error(err));
    }
  }, [fileName]);

  if (!fileName) return <div>Missing file parameter in URL</div>;
  if (!pdfUrl) return <div>Loading...</div>;

  return (
    <div style={{ height: '100vh', width: '100%' }}>
      <iframe
        src={pdfUrl}
        style={{ width: '100%', height: '100%', border: 'none' }}
        title="PDF Viewer"
      />
    </div>
  );
}

export default PDFViewer;
