import axios from 'axios';
import Cookies from 'js-cookie';

const api = axios.create({
    baseURL: 'https://www.scix.me/'
  });

  api.interceptors.request.use((config) => {
    const accessToken = Cookies.get('access_token');
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  });

  
export default api;

  