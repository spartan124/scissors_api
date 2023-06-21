import React, { useEffect, useState } from 'react';
import api from './api';
import { useParams } from 'react-router-dom';

function AnalyticsPage() {
  const [imageSrc, setImageSrc] = useState(null);
  const [error, setError] = useState(null);
  const { shortCode } = useParams();

  useEffect(() => {
    const fetchAnalyticsImage = async () => {
      try {
        const response = await api.get(`/analytics/${shortCode}`, {
          responseType: 'arraybuffer', // Receive response as array buffer
        });

        // Convert the array buffer to base64 data URL
        const imageSrc = `data:image/png;base64,${btoa(
          String.fromCharCode(...new Uint8Array(response.data))
        )}`;

        setImageSrc(imageSrc);
      } catch (error) {
        setError('Failed to fetch analytics data');
        console.error('Failed to fetch analytics data:', error);
      }
    };

    fetchAnalyticsImage();
  }, [shortCode]);

  return (
    <div>
      <h1>Analytics for Shortened URL: {shortCode}</h1>
      {imageSrc ? (
        <img src={imageSrc} alt="Clicks per Location" />
      ) : (
        <p>Loading analytics data...</p>
      )}
      {error && <p>{error}</p>}
    </div>
  );
}

export default AnalyticsPage;
