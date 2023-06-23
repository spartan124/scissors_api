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
    <section>
    <div className='container mt-5 text-white wrapper'>
      <div className='row'>
        <div className='col-12 col-md-3'>
        </div>
      <div className='image-container col-12 text-center col-md-6'>
      <h2>Analytics for Shortened URL: {shortCode}</h2>
      {imageSrc ? (
        <img src={imageSrc} alt="Clicks per Location" />
      ) : (
        <p>Loading analytics data...</p>
      )}
      {error && <p>{error}</p>}
      </div>
      <div className='col-12 col-md-3'>
        </div>
    </div>
   </div>
   </section>
  );
}

export default AnalyticsPage;
