import { useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

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
            Member Management <span className="text-slate-500 text-xs sm:text-sm ml-2">v.2.0</span>
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
        <a 
          href="mailto:supp.boh2158@gmail.com?subject=Support Request"
          className="text-slate-400 text-xs sm:text-sm hover:text-slate-200 underline inline-block"
        >
          Support
        </a>
      </div>
    </div>
  );
}