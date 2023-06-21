import { Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import AuthService from './authService';

const ProtectedRoute = ({ path, element: Element }) => {
    const [loading, setLoading] = useState(true);
    const [authenticated, setAuthenticated] = useState(false);
    // const location = useLocation();
  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        await AuthService.refreshToken();
        setAuthenticated(true);
      } catch (error) {
        AuthService.logout();
        setAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuthentication();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!authenticated) {
    return <Navigate to="/login" />;
  }

//   return (
//     <Routes location={location}>
//         <Route path={path} element={<Element />} />
//     </Routes>
//   );
};

export default ProtectedRoute;
