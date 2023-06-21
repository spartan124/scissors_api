import React, { useState } from 'react';
import api from './api';
import QRCode from 'react-qr-code';

const UrlShortenerForm = () => {
  const [original_url, setOriginalUrl] = useState('');
  const [short_code, setCustomShortcode] = useState('');
  const [shortenedUrl, setShortenedUrl] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const response = await api.post('/shorten', {
       original_url,
       short_code,
      });
      const { data } = response;
      setShortenedUrl(data.shortened_url);

      // Handle the response
      console.log(response.data);
      setOriginalUrl('');
      setCustomShortcode('');
      
    } catch (error) {
      // Handle the error
      
      console.error(error);
    }
  };

  const handleCopyClick = () => {
    navigator.clipboard.writeText(shortenedUrl);
    alert("Url copied to clipboard!");
  };

  return (
      <div className='wrapper text-center'>
          
          <form onSubmit={handleSubmit}>
          <div className='inputField'>
          <h2>Shorten URL</h2>        
        <div className="mb-3">
          <input
            type="url"
            value={original_url}
            onChange={(e) => setOriginalUrl(e.target.value)}
            className="form-control" id="url" placeholder="Paste url to shorten"/>
        </div>
        <div className="mb-3">
          <input
            type="custom shortcode"
            value={short_code}
            onChange={(e) => setCustomShortcode(e.target.value)}
            className="form-control" id="Custom shortcode" placeholder="Custom shortcode"/>
        </div>
        <button type="button" className="btn btn-primary" onClick={handleSubmit}>Shorten</button>
        </div>
      </form>
      {shortenedUrl && (
        <div>
            <p>
                Shortened URL:
                <a href={shortenedUrl} target='_blank' rel='noopener noreferrer'>
                    {shortenedUrl}
                </a>
            </p>
            
            <button onClick={handleCopyClick}>Copy</button>
            
            <div>
            <QRCode value={shortenedUrl} fgColor="seagreen"/>
            </div>
        </div>
        
       
      )}
    </div>
  );
};

export default UrlShortenerForm;
