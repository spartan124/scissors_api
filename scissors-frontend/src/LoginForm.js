import React, {  useState } from 'react';
import api from './api';
import { useNavigate, Link } from 'react-router-dom';

function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const navigate = useNavigate()
  
  const handleSubmit = async (event) => {
        event.preventDefault();
    
        try {
          const response = await api.post('/auth/login', {
            email,
            password,
          });
          
    
          // Handle successful login
          const { access_token } = response.data;
         
          const accessToken = access_token;  
          api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
          
       
          
          setEmail('');
          setPassword('');
          setError('');
        } catch (error) {
          // Handle login error
          setError('Invalid email or password');
          console.error(error);
        }
          navigate("/shorten")
      };

      return (
        <div className='wrapper text-center'>
          <div className='formImg'>

          </div>
          
          <form onSubmit={handleSubmit}>
          <div className='inputField'>
          <h2>Login</h2>
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
            <button type="button" class="btn btn-primary" onClick={handleSubmit}>Login</button>
            {error && <p>{error}</p>}
            </div>
            <div class='mb-3 text-center' id="regLink" >
            <p>Don't have an account? <Link to ='/register'>Please Signup</Link></p>
            </div>
          </form>
        </div>
      );
    };
    
    
    
function LogoutButton() {
const navigate = useNavigate();

const handleLogout = async () => {
  try {
      await api.post("/auth/logout");
  }
  catch (error) {
      console.error("Logout failed", error);
  }
  navigate('/login');
};

  return (
      <button class="btn btn-outline-primary me-2" type="button" onClick={handleLogout}>Logout</button>
  );
};

const refreshAccessToken = async (refreshToken) => {
  try {
    // const refreshToken = localStorage.getItem('refreshToken'); 
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    const { access_token } = response.data;
    localStorage.setItem('accessToken', access_token); 
  } catch (error) {
      console.error("Refresh token failed")
  }
};


    
export { LogoutButton, LoginForm, refreshAccessToken };
    