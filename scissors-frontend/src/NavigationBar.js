import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthService from './authService';
import { toast } from 'react-toastify'

const Navbar = () => {
    const [currentUser, setCurrentUser] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const user = AuthService.getCurrentUser();
                setCurrentUser(user);
            } catch (error) {
                toast.error("Failed to fetch user")
                
            }
        };
        fetchUser();
    }, []);

    const handleLogout = () => {
    AuthService.logout();
    setCurrentUser(null);
    navigate('/login');
  };


    return (
      <nav className="navbar sticky-top navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
            <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarSupportedContent">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              <li class="nav-item">
                <Link to="/shorten" className="nav-link">Home</Link>            
              </li>
                <li class="nav-item">
                <Link to="/shorten" className="nav-link">Shorten URL</Link>
                </li>
                <li class="nav-item">
                <Link to="/history" className="nav-link">History</Link>
                </li>
               
      </ul>
      {currentUser ? (
          <>
            <li>
              <p className='text-white'><span>Welcome, {}!</span></p>
            </li>
            <li>
              <button onClick={handleLogout}>Logout</button>
            </li>
          </>
        ) : ( 
          <li>
             <button>
            <Link to="/login" className="nav-link">Login</Link>
            </button>
          </li>
          
        )}
        
        </div>
    </div>
        </nav>
    );
}
export default Navbar;