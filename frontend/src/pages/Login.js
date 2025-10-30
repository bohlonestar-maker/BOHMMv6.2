import { useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [supportDialogOpen, setSupportDialogOpen] = useState(false);
  const [supportForm, setSupportForm] = useState({
    name: "",
    email: "",
    message: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log("Attempting login for user:", username);
      console.log("Backend URL:", API);
      
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password,
      });

      console.log("Login response:", response.data);
      const { token, username: user, role } = response.data;
      console.log("Token received:", token ? token.substring(0, 20) + "..." : "NO TOKEN");
      console.log("User role:", role);
      
      // Fetch user permissions
      const userResponse = await axios.get(`${API}/auth/verify`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log("User verification response:", userResponse.data);
      
      const permissions = userResponse.data.permissions || {
        basic_info: true,
        contact_info: false,
        dues_tracking: false,
        admin_actions: false
      };
      
      onLogin(token, user, role, permissions);
      toast.success("Login successful!");
    } catch (error) {
      console.error("Login error:", error);
      console.error("Error response:", error.response?.data);
      console.error("Status code:", error.response?.status);
      toast.error(error.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSupportSubmit = async (e) => {
    e.preventDefault();
    
    if (!supportForm.name || !supportForm.email || !supportForm.message) {
      toast.error("Please fill in all fields");
      return;
    }
    
    try {
      await axios.post(`${API}/support/messages`, supportForm);
      toast.success("Support message sent successfully! We'll reply to your email.");
      setSupportDialogOpen(false);
      setSupportForm({ name: "", email: "", message: "" });
    } catch (error) {
      console.error("Support message error:", error);
      toast.error("Failed to send support message. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <div className="bg-slate-800 rounded-2xl shadow-2xl p-6 sm:p-8 border border-slate-700">
          <div className="flex justify-center mb-6">
            <img 
              src="/brothers-logo.png" 
              alt="Brothers of the Highway Logo" 
              className="w-40 sm:w-48 h-auto"
            />
          </div>
          
          <h1 className="text-2xl sm:text-3xl font-bold text-center mb-2 text-white">
            Brothers of the Highway
          </h1>
          <p className="text-center text-slate-300 mb-2 text-sm sm:text-base">
            Member Directory <span className="text-slate-500 text-xs sm:text-sm ml-2">v.1.6a</span>
          </p>
          <div className="flex justify-center mb-6 sm:mb-8">
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-900 text-green-300 text-xs font-semibold rounded-full border border-green-700">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              256-bit Encryption
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
            <div>
              <Label htmlFor="username" className="text-slate-200">Username</Label>
              <Input
                id="username"
                data-testid="login-username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>

            <div>
              <Label htmlFor="password" className="text-slate-200">Password</Label>
              <Input
                id="password"
                data-testid="login-password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>

            <Button
              type="submit"
              data-testid="login-submit-button"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-5 sm:py-6 rounded-lg font-medium text-sm sm:text-base"
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
        </div>
      </div>
      
      <div className="absolute bottom-4 left-0 right-0 text-center space-y-2 px-4">
        <p className="text-slate-400 text-xs sm:text-sm">Property of Brothers of the Highway TC</p>
        <Dialog open={supportDialogOpen} onOpenChange={setSupportDialogOpen}>
          <DialogTrigger asChild>
            <Button 
              variant="link" 
              className="text-slate-400 text-xs sm:text-sm hover:text-slate-200 underline"
            >
              Support
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Contact Support</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSupportSubmit} className="space-y-4">
              <div>
                <Label htmlFor="support-name">Name</Label>
                <Input
                  id="support-name"
                  type="text"
                  placeholder="Your name"
                  value={supportForm.name}
                  onChange={(e) => setSupportForm({...supportForm, name: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="support-email">Email</Label>
                <Input
                  id="support-email"
                  type="email"
                  placeholder="your.email@example.com"
                  value={supportForm.email}
                  onChange={(e) => setSupportForm({...supportForm, email: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="support-message">Message</Label>
                <Textarea
                  id="support-message"
                  placeholder="Describe your issue or question..."
                  rows={5}
                  value={supportForm.message}
                  onChange={(e) => setSupportForm({...supportForm, message: e.target.value})}
                  required
                />
              </div>
              <div className="flex gap-3 justify-end">
                <Button 
                  type="button" 
                  variant="outline"
                  className="text-white"
                  onClick={() => setSupportDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-slate-800 hover:bg-slate-900 text-white">
                  Send Message
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}