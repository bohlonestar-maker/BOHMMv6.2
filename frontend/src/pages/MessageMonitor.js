import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Search, MessageCircle, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MessageMonitor() {
  const [messages, setMessages] = useState([]);
  const [filteredMessages, setFilteredMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedConversation, setSelectedConversation] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAllMessages();
  }, []);

  useEffect(() => {
    filterMessages();
  }, [searchTerm, messages]);

  const fetchAllMessages = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/messages/monitor/all`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages(response.data);
      setFilteredMessages(response.data);
    } catch (error) {
      console.error("Failed to load messages:", error);
      if (error.response?.status === 403) {
        alert("Access denied. This feature is restricted to Lonestar only.");
        navigate("/");
      }
    } finally {
      setLoading(false);
    }
  };

  const filterMessages = () => {
    if (!searchTerm) {
      setFilteredMessages(messages);
      return;
    }

    const term = searchTerm.toLowerCase();
    const filtered = messages.filter(
      (msg) =>
        msg.sender.toLowerCase().includes(term) ||
        msg.recipient.toLowerCase().includes(term) ||
        msg.message.toLowerCase().includes(term)
    );
    setFilteredMessages(filtered);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getConversations = () => {
    const conversationsMap = {};
    
    messages.forEach((msg) => {
      const key = [msg.sender, msg.recipient].sort().join("-");
      if (!conversationsMap[key]) {
        conversationsMap[key] = {
          users: [msg.sender, msg.recipient],
          messageCount: 0,
          lastMessage: msg,
          messages: []
        };
      }
      conversationsMap[key].messageCount++;
      conversationsMap[key].messages.push(msg);
      if (new Date(msg.timestamp) > new Date(conversationsMap[key].lastMessage.timestamp)) {
        conversationsMap[key].lastMessage = msg;
      }
    });

    return Object.values(conversationsMap).sort(
      (a, b) => new Date(b.lastMessage.timestamp) - new Date(a.lastMessage.timestamp)
    );
  };

  const viewConversation = (conversation) => {
    setSelectedConversation(conversation);
  };

  const closeConversation = () => {
    setSelectedConversation(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-slate-300">Loading messages...</div>
      </div>
    );
  }

  if (selectedConversation) {
    const sortedMessages = [...selectedConversation.messages].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    );

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <nav className="bg-slate-800 border-b border-slate-700 shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-4">
                <Button
                  onClick={closeConversation}
                  variant="outline"
                  size="sm"
                  className="border-slate-600 text-slate-200 hover:bg-slate-700"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to All Conversations
                </Button>
                <div className="flex items-center gap-2">
                  <MessageCircle className="w-6 h-6 text-blue-400" />
                  <h1 className="text-2xl font-bold text-slate-100">
                    Conversation: {selectedConversation.users.join(" ↔ ")}
                  </h1>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          <div className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 p-6">
            <div className="mb-4 text-sm text-slate-400">
              {sortedMessages.length} messages in this conversation
            </div>
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {sortedMessages.map((msg, index) => (
                <div
                  key={index}
                  className="bg-slate-700/50 rounded-lg p-4 border border-slate-600"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-blue-400">{msg.sender}</span>
                      <span className="text-slate-500">→</span>
                      <span className="font-semibold text-green-400">{msg.recipient}</span>
                    </div>
                    <span className="text-xs text-slate-400">
                      {formatTimestamp(msg.timestamp)}
                    </span>
                  </div>
                  <p className="text-slate-200 whitespace-pre-wrap">{msg.message}</p>
                  {!msg.read && (
                    <span className="inline-block mt-2 text-xs bg-yellow-900 text-yellow-300 px-2 py-1 rounded">
                      Unread
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const conversations = getConversations();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <nav className="bg-slate-800 border-b border-slate-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => navigate("/")}
                variant="outline"
                size="sm"
                className="border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div className="flex items-center gap-2">
                <MessageCircle className="w-6 h-6 text-blue-400" />
                <h1 className="text-2xl font-bold text-slate-100">Message Monitor</h1>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 p-6">
          <div className="mb-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  type="text"
                  placeholder="Search by username or message content..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-slate-700 border-slate-600 text-slate-100"
                />
              </div>
              <Button
                onClick={fetchAllMessages}
                variant="outline"
                className="border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                Refresh
              </Button>
            </div>
            <div className="text-sm text-slate-400">
              Monitoring {messages.length} total messages across {conversations.length} conversations
            </div>
          </div>

          {conversations.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No messages found</p>
            </div>
          ) : (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Conversations
              </h2>
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700 hover:bg-slate-700/50">
                    <TableHead className="text-slate-300">Participants</TableHead>
                    <TableHead className="text-slate-300">Message Count</TableHead>
                    <TableHead className="text-slate-300">Last Message</TableHead>
                    <TableHead className="text-slate-300">Time</TableHead>
                    <TableHead className="text-slate-300 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {conversations.map((conv, index) => (
                    <TableRow key={index} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell className="text-slate-200 font-medium">
                        {conv.users.join(" ↔ ")}
                      </TableCell>
                      <TableCell className="text-slate-300">{conv.messageCount}</TableCell>
                      <TableCell className="text-slate-300 max-w-md truncate">
                        {conv.lastMessage.message}
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {formatTimestamp(conv.lastMessage.timestamp)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          onClick={() => viewConversation(conv)}
                          variant="outline"
                          size="sm"
                          className="border-slate-600 text-slate-200 hover:bg-slate-700"
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
