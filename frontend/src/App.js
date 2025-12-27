import { useState, useEffect, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import UserManagement from "@/pages/UserManagement";
import AcceptInvite from "@/pages/AcceptInvite";
import Prospects from "@/pages/Prospects";
import Messages from "@/pages/Messages";
import UpdateLog from "@/pages/UpdateLog";
import MessageMonitor from "@/pages/MessageMonitor";
import EventCalendar from "@/pages/EventCalendar";
import CSVExportView from "@/pages/CSVExportView";
import ArchivedMembers from "@/pages/ArchivedMembers";
import ArchivedProspects from "@/pages/ArchivedProspects";
import DiscordAnalytics from "@/pages/DiscordAnalytics";
import WallOfHonor from "@/pages/WallOfHonor";
import Store from "@/pages/Store";
import SupporterStore from "@/pages/SupporterStore";
import ChatBot from "@/components/ChatBot";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Component to handle message notifications
function MessageNotifier() {
  const previousUnreadCount = useRef(0);
  const isFirstLoad = useRef(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) return;

        const response = await axios.get(`${API}/messages/unread/count`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const newCount = response.data.unread_count;

        // Check if we have new messages (count increased)
        // Don't show notification on first load
        if (!isFirstLoad.current && newCount > previousUnreadCount.current) {
          const newMessages = newCount - previousUnreadCount.current;
          toast.info(
            `You have ${newMessages} new private message${newMessages > 1 ? 's' : ''}!`,
            {
              duration: 5000,
              action: {
                label: 'View',
                onClick: () => navigate('/messages')
              }
            }
          );
        }

        // Update the counts
        previousUnreadCount.current = newCount;

        // Mark first load as complete
        if (isFirstLoad.current) {
          isFirstLoad.current = false;
        }
      } catch (error) {
        console.error("Failed to fetch unread messages count:", error);
      }
    };

    // Fetch immediately and then every 30 seconds
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);

    return () => clearInterval(interval);
  }, [navigate]);

  return null;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [userPermissions, setUserPermissions] = useState(null);
  const [userChapter, setUserChapter] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const permissions = localStorage.getItem('permissions');
    const chapter = localStorage.getItem('chapter');
    if (token && role) {
      setIsAuthenticated(true);
      setUserRole(role);
      setUserPermissions(permissions ? JSON.parse(permissions) : null);
      setUserChapter(chapter || null);
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, username, role, permissions, chapter) => {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('role', role);
    localStorage.setItem('permissions', JSON.stringify(permissions));
    if (chapter) {
      localStorage.setItem('chapter', chapter);
    }
    setIsAuthenticated(true);
    setUserRole(role);
    setUserPermissions(permissions);
    setUserChapter(chapter);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('permissions');
    localStorage.removeItem('chapter');
    setIsAuthenticated(false);
    setUserRole(null);
    setUserPermissions(null);
    setUserChapter(null);
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
            path="/supporter-store"
            element={<SupporterStore />}
          />
          <Route
            path="/"
            element={
              isAuthenticated ? (
                <Dashboard onLogout={handleLogout} userRole={userRole} userPermissions={userPermissions} userChapter={userChapter} />
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
              isAuthenticated && userRole === 'admin' && (userChapter === 'National' || userChapter === 'HA') ? (
                <Prospects onLogout={handleLogout} userRole={userRole} userChapter={userChapter} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/events"
            element={
              isAuthenticated ? (
                <EventCalendar onLogout={handleLogout} userRole={userRole} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/wall-of-honor"
            element={
              isAuthenticated ? (
                <WallOfHonor token={localStorage.getItem('token')} userRole={userRole} userChapter={userChapter} />
              ) : (
                <Navigate to="/login" replace />
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
            path="/message-monitor"
            element={
              isAuthenticated && localStorage.getItem("username") === "Lonestar" ? (
                <MessageMonitor onLogout={handleLogout} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/export-view"
            element={
              isAuthenticated ? (
                <CSVExportView />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route
            path="/archived-members"
            element={
              isAuthenticated && (userRole === 'admin' || userPermissions?.admin_actions) ? (
                <ArchivedMembers />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/archived-prospects"
            element={
              isAuthenticated && (userRole === 'admin' || userPermissions?.admin_actions) ? (
                <ArchivedProspects />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/discord-analytics"
            element={
              isAuthenticated && (userRole === 'admin' || userPermissions?.admin_actions) ? (
                <DiscordAnalytics />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/store"
            element={
              isAuthenticated ? (
                <Store userRole={userRole} userChapter={userChapter} />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
        {isAuthenticated && <MessageNotifier />}
        {isAuthenticated && <ChatBot />}
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;