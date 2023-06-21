import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthService from './authService';

const Navbar = () => {
    const [currentUser, setCurrentUser] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const user = AuthService.getCurrentUser();
                setCurrentUser(user);
            } catch (error) {
                console.error("Failed to fetch user:", error);
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
        <nav className="navbar sticky-top navbar-expand-lg navbar-dark bg-dark mb-5">
        <div className="container-fluid">
            <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarSupportedContent">

            <ul className="navbar-nav me-auto mr-auto mb-2 mb-lg-0 ">
                <li className="nav-item">
                <Link to="/">Home</Link>                
                </li>
                <li className="nav-item">
                <Link to="/shorten">Shorten URL</Link>
                </li>
                <li className="nav-item">
                <Link to="/history">History</Link>
                </li>
               
      </ul>
      {currentUser ? (
          <>
            <li>
              <p><span>Welcome, {currentUser.username}!</span></p>
            </li>
            <li>
              <button onClick={handleLogout}>Logout</button>
            </li>
          </>
        ) : (
          <li>
            <button>
            <Link to="/login">Login</Link>
            </button>
          </li>
        )}
        
        </div>
    </div>
        </nav>
    );
}
export default Navbar;