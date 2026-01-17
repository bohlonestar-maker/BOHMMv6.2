import { useState, useEffect, useRef, Component } from "react";
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
import QuarterlyReports from "@/pages/QuarterlyReports";
import AIKnowledgeManager from "@/pages/AIKnowledgeManager";
import OfficerTracking from "@/pages/OfficerTracking";
import SuggestionBox from "@/pages/SuggestionBox";
import PermissionPanel from "@/pages/PermissionPanel";
import DuesReminders from "@/pages/DuesReminders";
import Forms from "@/pages/Forms";
import ChatBot from "@/components/ChatBot";
import { Toaster } from "@/components/ui/sonner";

// Error Boundary to prevent white screen crashes
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React Error Boundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-md w-full text-center">
            <h2 className="text-xl font-bold text-red-400 mb-4">Something went wrong</h2>
            <p className="text-slate-300 mb-4">The application encountered an error. Please try refreshing the page.</p>
            <button
              onClick={() => {
                localStorage.clear();
                window.location.href = '/login';
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg mr-2"
            >
              Clear & Login
            </button>
            <button
              onClick={() => window.location.reload()}
              className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}


const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Keep-alive component to prevent backend from sleeping
function KeepAlive() {
  useEffect(() => {
    const ping = async () => {
      try {
        await axios.get(`${API}/ping`, { timeout: 5000 });
      } catch (error) {
        // Silently ignore ping errors - this is just keep-alive
        console.debug("Keep-alive ping failed:", error.message);
      }
    };

    // Initial ping
    ping();

    // Ping every 30 seconds
    const interval = setInterval(ping, 30000);

    return () => clearInterval(interval);
  }, []);

  return null;
}

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
  const [userTitle, setUserTitle] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const permissions = localStorage.getItem('permissions');
    const chapter = localStorage.getItem('chapter');
    const title = localStorage.getItem('title');
    if (token && role) {
      setIsAuthenticated(true);
      setUserRole(role);
      try {
        setUserPermissions(permissions ? JSON.parse(permissions) : null);
      } catch (e) {
        console.error("Failed to parse permissions:", e);
        setUserPermissions(null);
      }
      setUserChapter(chapter || null);
      setUserTitle(title || null);
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, username, role, permissions, chapter, title) => {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('role', role);
    localStorage.setItem('permissions', JSON.stringify(permissions));
    if (chapter) {
      localStorage.setItem('chapter', chapter);
    }
    if (title) {
      localStorage.setItem('title', title);
    }
    setIsAuthenticated(true);
    setUserRole(role);
    setUserPermissions(permissions);
    setUserChapter(chapter);
    setUserTitle(title);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('permissions');
    localStorage.removeItem('chapter');
    localStorage.removeItem('title');
    setIsAuthenticated(false);
    setUserRole(null);
    setUserPermissions(null);
    setUserChapter(null);
    setUserTitle(null);
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
                <Dashboard onLogout={handleLogout} userRole={userRole} userPermissions={userPermissions} userChapter={userChapter} userTitle={userTitle} />
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
                <Store userRole={userRole} userChapter={userChapter} userTitle={userTitle} />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route
            path="/quarterly-reports"
            element={
              isAuthenticated && userTitle && !['PM', 'Member', 'CC', 'CCLC', 'MD'].includes(userTitle) ? (
                <QuarterlyReports />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/ai-knowledge"
            element={
              isAuthenticated && (userRole === 'admin' || ['National President', 'National Vice President', 'National Secretary', 'NPrez', 'NVP', 'NSEC'].includes(userTitle)) ? (
                <AIKnowledgeManager token={localStorage.getItem('token')} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/officer-tracking"
            element={
              isAuthenticated ? (
                <OfficerTracking />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/suggestions"
            element={
              isAuthenticated ? (
                <SuggestionBox />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/permissions"
            element={
              isAuthenticated ? (
                <PermissionPanel />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/dues-reminders"
            element={
              isAuthenticated ? (
                <DuesReminders />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/forms"
            element={
              isAuthenticated ? (
                <Forms />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
        </Routes>
        <KeepAlive />
        {isAuthenticated && <MessageNotifier />}
        {isAuthenticated && <ChatBot />}
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}

export default AppWithErrorBoundary;