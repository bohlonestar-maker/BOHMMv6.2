import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { ArrowLeft, Send, MessageCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import VoiceChat from "@/components/VoiceChat";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/chat/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages(response.data);
      
      // Mark messages as read
      await axios.post(`${API}/chat/mark_read`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (error) {
      console.error("Failed to load messages:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(fetchMessages, 15000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) {
      toast.error("Message cannot be empty");
      return;
    }

    setSending(true);
    const token = localStorage.getItem("token");

    try {
      await axios.post(
        `${API}/chat/messages`,
        { message: newMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setNewMessage("");
      toast.success("Message sent");
      
      // Fetch messages immediately to show the new message
      await fetchMessages();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return "Just now";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    
    // Show date for older messages
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <nav className="bg-slate-800 border-b border-slate-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2 sm:gap-4">
              <Button
                onClick={() => navigate("/")}
                variant="outline"
                size="sm"
                className="flex items-center gap-1 sm:gap-2 border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                <ArrowLeft className="w-3 h-3 sm:w-4 sm:h-4" />
                <span className="hidden sm:inline">Back</span>
              </Button>
              <div className="flex items-center gap-2">
                <MessageCircle className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                <h1 className="text-lg sm:text-2xl font-bold text-slate-100">Admin Chat</h1>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <div className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 flex flex-col h-[calc(100vh-200px)]">
          {/* Chat Header */}
          <div className="p-4 border-b border-slate-700 bg-slate-800/50">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base sm:text-lg font-semibold text-slate-100">Admin Discussion</h2>
                <p className="text-xs sm:text-sm text-slate-400">Messages auto-refresh every 15 seconds</p>
              </div>
              <Button
                onClick={fetchMessages}
                variant="outline"
                size="sm"
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                Refresh
              </Button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-900/30">
            {loading ? (
              <div className="text-center py-12 text-slate-400">Loading messages...</div>
            ) : messages.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No messages yet. Start the conversation!</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-slate-600 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-blue-400 text-sm">{msg.username}</span>
                        <span className="text-xs text-slate-500">{formatTimestamp(msg.timestamp)}</span>
                      </div>
                      <p className="text-slate-200 text-sm break-words">{msg.message}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <div className="p-4 border-t border-slate-700 bg-slate-800/50">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <Input
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-blue-500"
                disabled={sending}
                maxLength={500}
              />
              <Button
                type="submit"
                disabled={sending || !newMessage.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                <Send className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Send</span>
              </Button>
            </form>
            <p className="text-xs text-slate-500 mt-2">
              {newMessage.length}/500 characters
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
