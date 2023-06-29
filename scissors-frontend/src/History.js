import React, { useEffect, useState } from 'react';
import api from './api';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify'
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
      toast.error(error)
      console.error('Failed to delete link:', error);
    }
  };

  // const handleDeleteAll = async () => {
  //   try {
  //     await api.delete('/history');
  //     setHistory({});
  //   } catch (error) {
  //     setError('Failed to delete link history');
  //     console.error('Failed to delete link history:', error);
  //   }
  // };


  return (
    <div className='wrapper text-center mb-3 mr-3'>

      {Object.entries(history).length > 0 ? (
        <div>
          <h2>Shortened URLs History</h2>
          
          <ul>
            {Object.entries(history).map(([shortCode, shortenedUrl]) => (
              <div className='copy-box'>
              <li key={shortCode}>
                
                <a className='copy-input mb-3' href={shortenedUrl}>{shortenedUrl}</a>
               
                <div className='input-group-append'>
                <Link to={`/analytics/${shortCode}`}><button type="button" class="btn btn-primary mb-3 mr-3">View Analytics</button></Link>
                <Link to={`/${shortCode}/qrcode`}><button type="button" class="btn btn-primary mb-3 mr-3">View QRCode</button></Link>
                <button type="button" className="btn btn-danger ml-3 mb-3" onClick={() => handleDelete(shortCode)}>Delete</button>
                
                </div>
               
              </li>
              </div>
            ))}
          </ul>
          {/* <button onClick={handleDeleteAll}>Delete All</button> */}
        </div>
      ) : (
        <p>No history available.</p>
      )}
      {error && <p>{error}</p>}
    </div>
  );
}

export default HistoryPage;
