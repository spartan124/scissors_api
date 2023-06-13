import React, { useState } from 'react';
import api from './api';
import QRCode from 'react-qr-code';

function UrlShortenerForm() {
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
    <div>
      <h2>URL Shortener</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Original URL:
          <input
            type="text"
            value={original_url}
            onChange={(e) => setOriginalUrl(e.target.value)}
          />
        </label>
        <label>
          Custom Shortcode:
          <input
            type="text"
            value={short_code}
            onChange={(e) => setCustomShortcode(e.target.value)}
          />
        </label>
        <button type="submit">Shorten URL</button>
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
