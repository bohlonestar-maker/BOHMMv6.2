import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import UserManagement from "@/pages/UserManagement";
import AcceptInvite from "@/pages/AcceptInvite";
import Prospects from "@/pages/Prospects";
import Messages from "@/pages/Messages";
import UpdateLog from "@/pages/UpdateLog";
import SupportCenter from "@/pages/SupportCenter";
import { Toaster } from "@/components/ui/sonner";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [userPermissions, setUserPermissions] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const permissions = localStorage.getItem('permissions');
    if (token && role) {
      setIsAuthenticated(true);
      setUserRole(role);
      setUserPermissions(permissions ? JSON.parse(permissions) : null);
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, username, role, permissions) => {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('role', role);
    localStorage.setItem('permissions', JSON.stringify(permissions));
    setIsAuthenticated(true);
    setUserRole(role);
    setUserPermissions(permissions);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('permissions');
    setIsAuthenticated(false);
    setUserRole(null);
    setUserPermissions(null);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onLogin={handleLogin} />
              )
            }
          />
          <Route
            path="/accept-invite"
            element={<AcceptInvite />}
          />
          <Route
            path="/"
            element={
              isAuthenticated ? (
                <Dashboard onLogout={handleLogout} userRole={userRole} userPermissions={userPermissions} />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route
            path="/users"
            element={
              isAuthenticated && (userRole === 'admin' || userPermissions?.admin_actions) ? (
                <UserManagement onLogout={handleLogout} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/prospects"
            element={
              isAuthenticated && userRole === 'admin' ? (
                <Prospects onLogout={handleLogout} userRole={userRole} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/messages"
            element={
              isAuthenticated ? (
                <Messages onLogout={handleLogout} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/update-log"
            element={
              isAuthenticated && userRole === 'admin' ? (
                <UpdateLog />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/support-center"
            element={
              isAuthenticated && localStorage.getItem("username") === "Lonestar" ? (
                <SupportCenter onLogout={handleLogout} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;