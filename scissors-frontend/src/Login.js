// Login.js

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthService from './authService';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    AuthService.login(email, password)
      .then(() => {
        navigate('/shorten'); // Redirect to the dashboard or desired page after successful login
      })
      .catch(error => {
        setLoading(false);
        setError('Invalid username or password');
      });
  };

  return (
    <div className='wrapper text-center'>
      <div className='formImg'>

      </div>
      
      <form onSubmit={handleLogin}>
      <div className='inputField'>
      <h2>Login</h2>
      {error && <div>{error}</div>}

      <div class="mb-3">
            <input type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            class="form-control" id="email" placeholder="Email Address"/>
        </div>
        <div class="mb-3">
            <input type="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            class="form-control" id="password" placeholder="Password"/>
        </div>
        <button type="button" class="btn btn-primary" disabled={loading} onClick={handleLogin}>Login</button>
        
        </div>
        <div class='mb-3 text-center' id="regLink" >
        <p>Don't have an account? <Link to ='/register'>Please Signup</Link></p>
        </div>
       
      </form>
    </div>
  );
};

export default Login;
