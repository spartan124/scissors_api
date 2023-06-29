import React, { useEffect, useState } from 'react';
import api from './api';
import { useParams } from 'react-router-dom';
import Row from 'react-bootstrap/esm/Row';
import Col from 'react-bootstrap/esm/Col';
function QrCodePage() {
  const [imageSrc, setImageSrc] = useState(null);
  const [error, setError] = useState(null);
  const { shortCode } = useParams();
  const [shortenedUrl, setShortenedUrl] = useState('');

  useEffect(() => {
    const fetchQrCode = async () => {
      try {
        const response = await api.get(`/${shortCode}/qrcode`, {
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
    const fetchShortenedUrl = async () => {
        try {
          const response = await api.get(`/shortened/${shortCode}`);

          setShortenedUrl(response.data['shortened_url']);
         
        } catch (error) {
          setError('Failed to fetch shortened URL');
          console.error('Failed to fetch shortened URL:', error);
        }
      };

    fetchQrCode();
    fetchShortenedUrl();
  }, [shortCode]);

  return (
    <div className='wrapper text-center mt-3'>
      <Row>
        <Col>
        
      {imageSrc ? (
        <div className=''>
          <h2 className='text-center'>QRCODE{shortenedUrl}</h2>
        <img src={imageSrc} alt="QR code for short url" />
        </div>
        
      ) : (
        <p>Loading QRCode data...</p>
      )}
      <p>QrCode for: <a href={` https://scix.me/${shortCode}`}>{` https://scix.me/${shortCode}`}</a> </p>
      {error && <p>{error}</p>}
        </Col>
      </Row>
      
    </div>
  );
}

export default QrCodePage;
