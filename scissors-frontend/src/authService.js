import api from './api';
import Cookies from 'js-cookie';

class AuthService {
  login(email, password) {
    return api
      .post('/auth/login', { email, password })
      .then((response) => {
        if (response.data.access_token) {
          Cookies.set('access_token', response.data.access_token, { expires: 7 }); // Set access token cookie with a 7-day expiration
          Cookies.set('refresh_token', response.data.refresh_token); // Set refresh token cookie (no expiration)
          Cookies.set(response.data.username);
        };

        return response.data;
      });
  };

  logout() {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
  };

  refreshToken() {
    const refreshToken = Cookies.get('refresh_token');

    if (refreshToken) {
      return api
        .post('/auth/refresh', { refresh_token: refreshToken })
        .then((response) => {
          if (response.data.access_token) {
            Cookies.set('access_token', response.data.access_token, { expires: 7 }); // Update the access token cookie with the refreshed token
          };

          return response.data;
        });
    } else {
      return Promise.reject('No refresh token available');
    };
  };

  getCurrentUser() {
    // Implement this method to retrieve user data from the server based on the access token
    const accessToken = Cookies.get('access_token');
    if (accessToken) {
      return api.get('/auth/user')
        .then((response) => {
          return response.data['username'];
        })
        .catch((error) => {
          console.error('Failed to get user data:', error);
          return null;
        });
    }

    return null;

  };
  
  checkLoggedIn() {
    const user = this.getCurrentUser();

    if (user && user.access_token) {
      // You can add additional checks here, such as token expiration validation
      return true;
    };

    return false;
  };
};

// eslint-disable-next-line import/no-anonymous-default-export
export default new AuthService();
