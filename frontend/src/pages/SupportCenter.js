import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Mail, CheckCircle, Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function SupportCenter({ onLogout }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [replyDialogOpen, setReplyDialogOpen] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [replyText, setReplyText] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/support/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data);
    } catch (error) {
      console.error("Failed to fetch support messages:", error);
      if (error.response?.status === 403) {
        toast.error("Access denied. This feature is only available to Lonestar.");
        navigate("/");
      } else {
        toast.error("Failed to load support messages");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async () => {
    if (!replyText.trim()) {
      toast.error("Please enter a reply");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `${API}/support/messages/${selectedMessage.id}/reply`,
        { reply_text: replyText },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success("Reply sent successfully!");
      setReplyDialogOpen(false);
      setReplyText("");
      setSelectedMessage(null);
      fetchMessages();
    } catch (error) {
      console.error("Failed to send reply:", error);
      toast.error("Failed to send reply");
    }
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
                <Mail className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                <h1 className="text-lg sm:text-2xl font-bold text-slate-100">Support Center</h1>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <div className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 p-4 sm:p-6">
          <h2 className="text-base sm:text-lg font-semibold text-slate-100 mb-4 sm:mb-6">
            Support Messages
          </h2>

          {loading ? (
            <p className="text-center text-slate-400 py-8">Loading messages...</p>
          ) : messages.length === 0 ? (
            <p className="text-center text-slate-400 py-8">No support messages yet</p>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className="bg-slate-700 rounded-lg p-4 border border-slate-600"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-slate-100">{msg.name}</h3>
                      <p className="text-sm text-slate-400">{msg.email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {msg.status === "closed" ? (
                        <span className="flex items-center gap-1 text-xs bg-green-900 text-green-300 px-2 py-1 rounded-full">
                          <CheckCircle className="w-3 h-3" />
                          Replied
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs bg-yellow-900 text-yellow-300 px-2 py-1 rounded-full">
                          <Clock className="w-3 h-3" />
                          Open
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mb-3">
                    <p className="text-xs text-slate-400 mb-2">
                      Submitted: {formatDate(msg.timestamp)}
                    </p>
                    <p className="text-sm text-slate-200 bg-slate-800 rounded p-3">
                      {msg.message}
                    </p>
                  </div>

                  {msg.reply_text && (
                    <div className="mt-3 pt-3 border-t border-slate-600">
                      <p className="text-xs text-slate-400 mb-2">
                        Your Reply ({formatDate(msg.replied_at)}):
                      </p>
                      <p className="text-sm text-slate-200 bg-slate-800 rounded p-3">
                        {msg.reply_text}
                      </p>
                    </div>
                  )}

                  {msg.status === "open" && (
                    <div className="mt-3 flex justify-end">
                      <Button
                        size="sm"
                        onClick={() => {
                          setSelectedMessage(msg);
                          setReplyDialogOpen(true);
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Reply
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Dialog open={replyDialogOpen} onOpenChange={setReplyDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Reply to {selectedMessage?.name}</DialogTitle>
          </DialogHeader>
          
          {selectedMessage && (
            <div className="space-y-4">
              <div className="bg-slate-800 rounded p-3">
                <p className="text-xs text-slate-400 mb-1">Original Message:</p>
                <p className="text-sm text-slate-200">{selectedMessage.message}</p>
              </div>

              <div>
                <label className="text-sm text-slate-200 mb-2 block">
                  Your Reply (will be sent to {selectedMessage.email}):
                </label>
                <Textarea
                  placeholder="Type your reply here..."
                  rows={6}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="bg-slate-700 text-slate-100"
                />
              </div>

              <div className="flex gap-3 justify-end">
                <Button
                  type="button"
                  variant="outline"
                  className="text-white"
                  onClick={() => {
                    setReplyDialogOpen(false);
                    setReplyText("");
                    setSelectedMessage(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleReply}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Send Reply
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
