import React, { useState } from 'react';
import api from './api';
// import { setAccessToken, setRefreshToken } from './api';

// After successful login, set the access token


function LoginForm() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const handleSubmit = async (event) => {
        event.preventDefault();
    
        try {
          const response = await api.post('/auth/login', {
            email,
            password,
          });
    
          // Handle successful login
          const { access_token,  } = response.data;
          
          
          const accessToken = access_token;  // Replace with the actual token
          api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
          
          // const refreshToken = refresh_token;  // Replace with the actual token
          // api.defaults.headers.common['Authorization'] = `Bearer ${refreshToken}`;

          // console.log('Access Token:', access_token);
          // console.log('Refresh Token:', refresh_token);
    
          // Reset form fields and error state
          setEmail('');
          setPassword('');
          setError('');
        } catch (error) {
          // Handle login error
          setError('Invalid email or password');
          console.error(error);
        }

      };
      return (
        <div>
          <h2>Login</h2>
          <form onSubmit={handleSubmit}>
            <label>
              Email:
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label>
              Password:
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <button type="submit">Login</button>
            {error && <p>{error}</p>}
          </form>
        </div>
      );
    }
    
    export default LoginForm;
    