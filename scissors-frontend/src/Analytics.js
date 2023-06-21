import React, { useEffect, useState } from 'react';
import api from './api';
import { Bar } from 'react-chartjs-2';
import { useParams } from 'react-router-dom';


function AnalyticsPage({ match }) {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [error, setError] = useState(null);
  const { shortCode } = useParams();


  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        const response = await api.get(`/analytics/${shortCode}`);
        setAnalyticsData(response.data);
      } catch (error) {
        setError('Failed to fetch analytics data');
        console.error('Failed to fetch analytics data:', error);
      }
    };
    fetchAnalyticsData();
  }, [shortCode]);

 

  return (
    <div>
      <h1>Analytics for Shortened URL: {shortCode}</h1>
      {analyticsData ? (
        <div>
          {/* <p>Original URL: {analyticsData.original_url}</p>
          <p>Click Count: {analyticsData.click_count}</p>
          <p>Created At: {analyticsData.created_at}</p>
          <p>Last Used At: {analyticsData.last_used_at}</p>
          <h2>Click Data</h2> */}
          <Bar
            data={{
              labels: Object.keys(analyticsData.click_data),
              datasets: [
                {
                  label: 'Clicks per Location',
                  data: Object.values(analyticsData.click_data),
                  backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
              ],
            }}
            options={{
              scales: {
                y: {
                  beginAtZero: true,
                  stepSize: 1,
                },
              },
            }}
          />
        </div>
      ) : (
        <p>Loading analytics data...</p>
      )}
      {error && <p>{error}</p>}
    </div>
  );
}

export default AnalyticsPage;
