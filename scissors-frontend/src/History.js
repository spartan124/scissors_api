import React, { useEffect, useState } from 'react';
import api from './api';
import { Link } from 'react-router-dom';

function HistoryPage() {
  const [history, setHistory] = useState({});
  const [error, setError] = useState(null);
  // const navigate = useNavigate()

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await api.get('/history');
      setHistory(response.data);
    } catch (error) {
      setError('Failed to fetch history');
      console.error('Failed to fetch history:', error);
    }
  };

  const handleDelete = async (shortCode) => {
    try {
      await api.delete(`/shortened/${shortCode}`);
      setHistory((prevHistory) => {
        const updatedHistory = { ...prevHistory };
        delete updatedHistory[shortCode];
        return updatedHistory;
      });
    } catch (error) {
      setError('Failed to delete link');
      console.error('Failed to delete link:', error);
    }
  };

  const handleDeleteAll = async () => {
    try {
      await api.delete('/history');
      setHistory({});
    } catch (error) {
      setError('Failed to delete link history');
      console.error('Failed to delete link history:', error);
    }
  };


  return (
    <div className='container mt-5 text-white wrapper'>
      <h1>Shortened URLs History</h1>
      {Object.entries(history).length > 0 ? (
        <div>
          <ul>
            {Object.entries(history).map(([shortCode, shortenedUrl]) => (
              <li key={shortCode}>
                <a href={shortenedUrl}>{shortenedUrl}</a>
                <button onClick={() => handleDelete(shortCode)}>Delete</button>
                <Link to={`/analytics/${shortCode}`}><button>View Analytics</button></Link>
                <Link to={`/${shortCode}/qrcode`}><button>View QRCode</button></Link>


              </li>
            ))}
          </ul>
          <button onClick={handleDeleteAll}>Delete All</button>
        </div>
      ) : (
        <p>No history available.</p>
      )}
      {error && <p>{error}</p>}
    </div>
  );
}

export default HistoryPage;
