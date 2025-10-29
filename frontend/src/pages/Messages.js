import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { ArrowLeft, Send, MessageCircle, User, Trash2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Messages() {
  const [conversations, setConversations] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [allUsers, setAllUsers] = useState([]);
  const [showNewChat, setShowNewChat] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [archivedConversations, setArchivedConversations] = useState([]);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchConversations = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/messages/conversations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setConversations(response.data);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchArchivedConversations = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/messages/conversations/archived`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setArchivedConversations(response.data);
    } catch (error) {
      console.error("Failed to load archived conversations:", error);
    }
  };

  const fetchAllUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Filter out current user
      const currentUser = localStorage.getItem("username");
      setAllUsers(response.data.filter(u => u.username !== currentUser));
    } catch (error) {
      console.error("Failed to load users:", error);
    }
  };

  const fetchMessages = async (username) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/messages/${username}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages(response.data);
      
      // Mark messages as read
      await axios.post(`${API}/messages/mark_read/${username}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      // Refresh conversations to update unread count
      fetchConversations();
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  useEffect(() => {
    fetchConversations();
    fetchAllUsers();
    fetchArchivedConversations();
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(() => {
      if (showArchived) {
        fetchArchivedConversations();
      } else {
        fetchConversations();
      }
      if (selectedUser) {
        fetchMessages(selectedUser);
      }
    }, 15000);
    
    return () => clearInterval(interval);
  }, [showArchived]);

  useEffect(() => {
    if (selectedUser) {
      fetchMessages(selectedUser);
    }
  }, [selectedUser]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) {
      toast.error("Message cannot be empty");
      return;
    }

    if (!selectedUser) {
      toast.error("Please select a user to message");
      return;
    }

    setSending(true);
    const token = localStorage.getItem("token");

    try {
      await axios.post(
        `${API}/messages`,
        { recipient: selectedUser, message: newMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setNewMessage("");
      
      // Fetch messages immediately to show the new message
      await fetchMessages(selectedUser);
      await fetchConversations();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleDeleteConversation = async () => {
    if (!userToDelete) return;

    const token = localStorage.getItem("token");

    try {
      await axios.delete(`${API}/messages/conversation/${userToDelete}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success(`Conversation with ${userToDelete} deleted`);
      
      // Clear selection if we deleted the currently selected conversation
      if (selectedUser === userToDelete) {
        setSelectedUser(null);
        setMessages([]);
      }
      
      // Refresh conversations list
      await fetchConversations();
      if (showArchived) {
        await fetchArchivedConversations();
      }
      
      setDeleteDialogOpen(false);
      setUserToDelete(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete conversation");
    }
  };

  const handleArchiveConversation = async () => {
    if (!userToDelete) return;

    const token = localStorage.getItem("token");

    try {
      await axios.post(`${API}/messages/conversation/${userToDelete}/archive`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success(`Conversation with ${userToDelete} archived`);
      
      // Clear selection if we archived the currently selected conversation
      if (selectedUser === userToDelete) {
        setSelectedUser(null);
        setMessages([]);
      }
      
      // Refresh conversations list
      await fetchConversations();
      await fetchArchivedConversations();
      
      setDeleteDialogOpen(false);
      setUserToDelete(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to archive conversation");
    }
  };

  const handleUnarchiveConversation = async (username) => {
    const token = localStorage.getItem("token");

    try {
      await axios.post(`${API}/messages/conversation/${username}/unarchive`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success(`Conversation with ${username} unarchived`);
      
      // Refresh both lists
      await fetchConversations();
      await fetchArchivedConversations();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to unarchive conversation");
    }
  };

  const confirmDeleteConversation = (username) => {
    setUserToDelete(username);
    setDeleteDialogOpen(true);
  };

  const startNewConversation = (username) => {
    setSelectedUser(username);
    setShowNewChat(false);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return "Just now";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const currentUsername = localStorage.getItem("username");

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
                <h1 className="text-lg sm:text-2xl font-bold text-slate-100">Messages</h1>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-[calc(100vh-180px)]">
          {/* Conversations List */}
          <div className="md:col-span-1 bg-slate-800 rounded-xl shadow-xl border border-slate-700 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-700">
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-lg font-semibold text-slate-100">Conversations</h2>
                <Button
                  onClick={() => setShowNewChat(!showNewChat)}
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  New Chat
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => setShowArchived(false)}
                  size="sm"
                  variant={!showArchived ? "default" : "outline"}
                  className={!showArchived ? "bg-blue-600 hover:bg-blue-700" : "border-slate-600 text-slate-300 hover:bg-slate-700"}
                >
                  Active
                </Button>
                <Button
                  onClick={() => setShowArchived(true)}
                  size="sm"
                  variant={showArchived ? "default" : "outline"}
                  className={showArchived ? "bg-blue-600 hover:bg-blue-700" : "border-slate-600 text-slate-300 hover:bg-slate-700"}
                >
                  Archived
                </Button>
              </div>
            </div>

            {showNewChat && (
              <div className="p-4 border-b border-slate-700 bg-slate-900/50">
                <p className="text-sm text-slate-400 mb-2">Start a new conversation:</p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {allUsers.map((user) => (
                    <button
                      key={user.id}
                      onClick={() => startNewConversation(user.username)}
                      className="w-full text-left p-2 rounded hover:bg-slate-700 text-slate-200 text-sm"
                    >
                      <User className="w-4 h-4 inline mr-2" />
                      {user.username} ({user.role})
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="text-center py-8 text-slate-400">Loading conversations...</div>
              ) : showArchived ? (
                archivedConversations.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">
                    <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No archived conversations</p>
                  </div>
                ) : (
                  archivedConversations.map((conv) => (
                    <div
                      key={conv.username}
                      className={`relative p-4 border-b border-slate-700 hover:bg-slate-700 transition-colors ${
                        selectedUser === conv.username ? 'bg-slate-700' : ''
                      }`}
                    >
                      <button
                        onClick={() => setSelectedUser(conv.username)}
                        className="w-full text-left"
                      >
                        <div className="flex justify-between items-start pr-8">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-slate-100">{conv.username}</span>
                              <span className="text-xs text-slate-500 italic">(Archived)</span>
                            </div>
                            <p className="text-sm text-slate-400 truncate mt-1">
                              {conv.lastMessage.message}
                            </p>
                          </div>
                          <span className="text-xs text-slate-500 ml-2">
                            {formatTimestamp(conv.lastMessage.timestamp)}
                          </span>
                        </div>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUnarchiveConversation(conv.username);
                        }}
                        className="absolute top-4 right-4 p-1 rounded hover:bg-green-500/20 text-green-400 hover:text-green-300 transition-colors text-xs"
                        title="Unarchive conversation"
                      >
                        Unarchive
                      </button>
                    </div>
                  ))
                )
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No conversations yet</p>
                  <p className="text-sm mt-2">Click "New Chat" to start messaging</p>
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.username}
                    className={`relative p-4 border-b border-slate-700 hover:bg-slate-700 transition-colors ${
                      selectedUser === conv.username ? 'bg-slate-700' : ''
                    }`}
                  >
                    <button
                      onClick={() => setSelectedUser(conv.username)}
                      className="w-full text-left"
                    >
                      <div className="flex justify-between items-start pr-8">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-100">{conv.username}</span>
                            {conv.unreadCount > 0 && (
                              <span className="bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5">
                                {conv.unreadCount}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-400 truncate mt-1">
                            {conv.lastMessage.message}
                          </p>
                        </div>
                        <span className="text-xs text-slate-500 ml-2">
                          {formatTimestamp(conv.lastMessage.timestamp)}
                        </span>
                      </div>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        confirmDeleteConversation(conv.username);
                      }}
                      className="absolute top-4 right-4 p-1 rounded hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors"
                      title="Delete conversation"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Messages Area */}
          <div className="md:col-span-2 bg-slate-800 rounded-xl shadow-xl border border-slate-700 flex flex-col">
            {selectedUser ? (
              <>
                {/* Chat Header */}
                <div className="p-4 border-b border-slate-700">
                  <h2 className="text-lg font-semibold text-slate-100">
                    <User className="w-5 h-5 inline mr-2" />
                    {selectedUser}
                  </h2>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-900/30">
                  {messages.length === 0 ? (
                    <div className="text-center py-12 text-slate-400">
                      <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No messages yet. Start the conversation!</p>
                    </div>
                  ) : (
                    messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender === currentUsername ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[70%] rounded-lg p-3 ${
                            msg.sender === currentUsername
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-700 text-slate-100'
                          }`}
                        >
                          <p className="text-sm break-words">{msg.message}</p>
                          <p className={`text-xs mt-1 ${
                            msg.sender === currentUsername ? 'text-blue-100' : 'text-slate-400'
                          }`}>
                            {formatTimestamp(msg.timestamp)}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Message Input */}
                <div className="p-4 border-t border-slate-700">
                  <form onSubmit={handleSendMessage} className="flex gap-2">
                    <Input
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Type your message..."
                      className="flex-1 bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                      disabled={sending}
                      maxLength={500}
                    />
                    <Button
                      type="submit"
                      disabled={sending || !newMessage.trim()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </form>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-400">
                <div className="text-center">
                  <MessageCircle className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">Select a conversation to start messaging</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Delete/Archive Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="bg-slate-800 border-slate-700">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-slate-100">Manage Conversation</AlertDialogTitle>
            <AlertDialogDescription className="text-slate-400">
              What would you like to do with your conversation with <span className="font-semibold text-slate-200">{userToDelete}</span>?
              <div className="mt-3 space-y-2">
                <p className="text-sm"><strong className="text-slate-300">Archive:</strong> Hide the conversation but keep all messages. You can unarchive it later.</p>
                <p className="text-sm"><strong className="text-slate-300">Delete:</strong> Permanently delete all messages. This cannot be undone.</p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col sm:flex-row gap-2">
            <AlertDialogCancel className="bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600 m-0">
              Cancel
            </AlertDialogCancel>
            <Button
              onClick={handleArchiveConversation}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Archive
            </Button>
            <AlertDialogAction 
              onClick={handleDeleteConversation}
              className="bg-red-600 hover:bg-red-700 text-white m-0"
            >
              Delete Permanently
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
