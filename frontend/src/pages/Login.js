import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { HelpCircle, Send, X, ShoppingBag, Truck, Eye, EyeOff, KeyRound, Mail } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Login({ onLogin }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // Store status
  const [supporterStoreOpen, setSupporterStoreOpen] = useState(true);
  
  // Experience stats
  const [totalExperience, setTotalExperience] = useState(null);
  
  // Support form state
  const [supportDialogOpen, setSupportDialogOpen] = useState(false);
  const [supportForm, setSupportForm] = useState({
    name: "",
    handle: "",
    contact_info: "",
    reason: ""
  });
  const [submittingSupport, setSubmittingSupport] = useState(false);

  // Password reset state
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetStep, setResetStep] = useState(1); // 1 = enter email, 2 = enter code & new password
  const [resetEmail, setResetEmail] = useState("");
  const [resetEmailDisplay, setResetEmailDisplay] = useState(""); // Masked email for display
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState("");

  // Fetch store settings and experience stats on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [storeResponse, experienceResponse] = await Promise.all([
          axios.get(`${API}/store/settings/public`),
          axios.get(`${API}/stats/experience`)
        ]);
        setSupporterStoreOpen(storeResponse.data.supporter_store_open);
        setTotalExperience(experienceResponse.data);
      } catch (error) {
        console.error("Error fetching data:", error);
        setSupporterStoreOpen(true);
      }
    };
    fetchData();
  }, []);

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
      
      const chapter = userResponse.data.chapter || null;
      const title = userResponse.data.title || null;
      
      onLogin(token, user, role, permissions, chapter, title);
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
    
    if (!supportForm.name.trim() || !supportForm.contact_info.trim() || !supportForm.reason.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }
    
    setSubmittingSupport(true);
    
    try {
      await axios.post(`${API}/support/request`, supportForm);
      toast.success("Support request submitted successfully! We'll get back to you soon.");
      setSupportDialogOpen(false);
      setSupportForm({ name: "", handle: "", contact_info: "", reason: "" });
    } catch (error) {
      console.error("Support request error:", error);
      toast.error("Failed to submit support request. Please try again or email us directly.");
    } finally {
      setSubmittingSupport(false);
    }
  };

  // Password reset functions
  const handleRequestResetCode = async (e) => {
    e.preventDefault();
    setResetError("");
    
    if (!resetEmail.trim()) {
      setResetError("Please enter your email or username");
      toast.error("Please enter your email or username");
      return;
    }
    
    setResetLoading(true);
    
    try {
      const response = await axios.post(`${API}/auth/request-reset`, { email: resetEmail });
      // Extract masked email from response message
      const message = response.data.message || "";
      const maskedMatch = message.match(/sent to (.+)$/);
      setResetEmailDisplay(maskedMatch ? maskedMatch[1] : resetEmail);
      toast.success("Reset code sent! Check your email.");
      setResetStep(2);
    } catch (error) {
      console.error("Reset request error:", error);
      const errorMsg = error.response?.data?.detail || "Failed to send reset code. Please verify your email or username is correct.";
      setResetError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setResetLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (!resetCode.trim() || !newPassword.trim() || !confirmNewPassword.trim()) {
      toast.error("Please fill in all fields");
      return;
    }
    
    if (newPassword !== confirmNewPassword) {
      toast.error("Passwords do not match");
      return;
    }
    
    if (newPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    
    setResetLoading(true);
    
    try {
      await axios.post(`${API}/auth/reset-password`, {
        email: resetEmail,
        code: resetCode,
        new_password: newPassword
      });
      toast.success("Password reset successfully! You can now log in.");
      closeResetDialog();
    } catch (error) {
      console.error("Password reset error:", error);
      toast.error(error.response?.data?.detail || "Failed to reset password. Please check your code and try again.");
    } finally {
      setResetLoading(false);
    }
  };

  const closeResetDialog = () => {
    setResetDialogOpen(false);
    setResetStep(1);
    setResetEmail("");
    setResetCode("");
    setNewPassword("");
    setConfirmNewPassword("");
    setShowNewPassword(false);
    setResetError("");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-4 py-6">
      <div className="w-full max-w-sm">
        <div className="bg-slate-800 rounded-2xl shadow-2xl p-5 sm:p-6 border border-slate-700">
          {/* Logo - Compact for laptop */}
          <div className="flex justify-center mb-3">
            <img 
              src="/brothers-logo.png" 
              alt="Brothers of the Highway Logo" 
              className="w-28 sm:w-36 h-auto"
            />
          </div>
          
          <h1 className="text-xl sm:text-2xl font-bold text-center mb-1 text-white">
            Brothers of the Highway
          </h1>
          <p className="text-center text-slate-300 mb-2 text-xs sm:text-sm">
            Member Management <span className="text-slate-500 ml-1">v6.0</span>
          </p>
          
          {/* Total Experience Badge */}
          {totalExperience && totalExperience.total_years > 0 && (
            <div className="flex justify-center mb-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-900/50 text-blue-300 text-xs font-semibold rounded-full border border-blue-700/50">
                <Truck className="w-3.5 h-3.5" />
                {totalExperience.total_years_formatted}+ Years Combined Experience
              </span>
            </div>
          )}
          
          {/* Encryption badge - smaller */}
          <div className="flex justify-center mb-3">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-900/50 text-green-300 text-[10px] font-semibold rounded-full border border-green-700/50">
              <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              256-bit Encryption
            </span>
          </div>
          
          {/* Supporter Store Button - Only show if store is open */}
          {supporterStoreOpen && (
            <div className="mb-4">
              <Button
                type="button"
                onClick={() => navigate("/supporter-store")}
                variant="outline"
                className="w-full border-green-600 text-green-400 hover:bg-green-900/30 py-2.5 rounded-lg font-medium text-sm"
              >
                <ShoppingBag className="w-4 h-4 mr-2" />
                Supporter Store
              </Button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <Label htmlFor="username" className="text-slate-200 text-sm">Username</Label>
              <Input
                id="username"
                data-testid="login-username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                className="mt-1 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 h-9"
              />
            </div>

            <div>
              <Label htmlFor="password" className="text-slate-200 text-sm">Password</Label>
              <div className="relative mt-1">
                <Input
                  id="password"
                  data-testid="login-password-input"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 h-9 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-1"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Forgot Password Link */}
            <div className="text-right">
              <button
                type="button"
                onClick={() => setResetDialogOpen(true)}
                className="text-xs text-blue-400 hover:text-blue-300 hover:underline"
              >
                Forgot Password?
              </button>
            </div>

            <Button
              type="submit"
              data-testid="login-submit-button"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-medium text-sm"
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          
          {/* Footer inside the card - no overlap */}
          <div className="mt-4 pt-3 border-t border-slate-700 text-center space-y-1">
            <p className="text-slate-500 text-[10px]">Property of Brothers of the Highway TC</p>
            <button 
              onClick={() => setSupportDialogOpen(true)}
              className="text-slate-400 text-xs hover:text-slate-200 underline inline-flex items-center gap-1"
            >
              <HelpCircle className="w-3 h-3" />
              Support
            </button>
          </div>
        </div>
      </div>

      {/* Support Request Dialog */}
      <Dialog open={supportDialogOpen} onOpenChange={setSupportDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 w-[95vw] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-blue-400" />
              Support Request
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSupportSubmit} className="space-y-4 mt-2">
            <div>
              <Label htmlFor="support-name" className="text-slate-200">
                Name <span className="text-red-400">*</span>
              </Label>
              <Input
                id="support-name"
                type="text"
                value={supportForm.name}
                onChange={(e) => setSupportForm({ ...supportForm, name: e.target.value })}
                placeholder="Your name"
                required
                className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>

            <div>
              <Label htmlFor="support-handle" className="text-slate-200">
                Handle <span className="text-slate-500 text-xs">(optional)</span>
              </Label>
              <Input
                id="support-handle"
                type="text"
                value={supportForm.handle}
                onChange={(e) => setSupportForm({ ...supportForm, handle: e.target.value })}
                placeholder="Your member handle (if applicable)"
                className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>

            <div>
              <Label htmlFor="support-contact" className="text-slate-200">
                Contact Info <span className="text-red-400">*</span>
              </Label>
              <Input
                id="support-contact"
                type="text"
                value={supportForm.contact_info}
                onChange={(e) => setSupportForm({ ...supportForm, contact_info: e.target.value })}
                placeholder="Email or phone number"
                required
                className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
              <p className="text-xs text-slate-500 mt-1">We&apos;ll use this to respond to your request</p>
            </div>

            <div>
              <Label htmlFor="support-reason" className="text-slate-200">
                Reason for Request <span className="text-red-400">*</span>
              </Label>
              <Textarea
                id="support-reason"
                value={supportForm.reason}
                onChange={(e) => setSupportForm({ ...supportForm, reason: e.target.value })}
                placeholder="Please describe your issue or question..."
                required
                rows={4}
                className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 resize-none"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setSupportDialogOpen(false)}
                className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submittingSupport}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {submittingSupport ? (
                  "Sending..."
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Submit
                  </>
                )}
              </Button>
            </div>
          </form>
          
          <p className="text-xs text-slate-500 text-center mt-2">
            Or email us directly at{" "}
            <a href="mailto:support@boh2158.org" className="text-blue-400 hover:underline">
              support@boh2158.org
            </a>
          </p>
        </DialogContent>
      </Dialog>

      {/* Password Reset Dialog */}
      <Dialog open={resetDialogOpen} onOpenChange={(open) => !open && closeResetDialog()}>
        <DialogContent className="bg-slate-800 border-slate-700 w-[95vw] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-blue-400" />
              Reset Password
            </DialogTitle>
          </DialogHeader>
          
          {resetStep === 1 ? (
            // Step 1: Enter email or username
            <form onSubmit={handleRequestResetCode} className="space-y-4 mt-2">
              <p className="text-sm text-slate-400">
                Enter your email address or username and we'll send a reset code to your registered email.
              </p>
              
              <div>
                <Label htmlFor="reset-email" className="text-slate-200">
                  Email or Username <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="reset-email"
                  type="text"
                  value={resetEmail}
                  onChange={(e) => { setResetEmail(e.target.value); setResetError(""); }}
                  placeholder="Enter your email or username"
                  required
                  className={`mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 ${resetError ? 'border-red-500' : ''}`}
                />
                {resetError && (
                  <p className="text-red-400 text-sm mt-2 flex items-center gap-1">
                    <X className="w-4 h-4" />
                    {resetError}
                  </p>
                )}
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={closeResetDialog}
                  className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={resetLoading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {resetLoading ? (
                    "Sending..."
                  ) : (
                    <>
                      <Mail className="w-4 h-4 mr-2" />
                      Send Code
                    </>
                  )}
                </Button>
              </div>
            </form>
          ) : (
            // Step 2: Enter code and new password
            <form onSubmit={handleResetPassword} className="space-y-4 mt-2">
              <p className="text-sm text-slate-400">
                Enter the 6-digit code sent to <span className="text-blue-400">{resetEmail}</span>
              </p>
              
              <div>
                <Label htmlFor="reset-code" className="text-slate-200">
                  Reset Code <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="reset-code"
                  type="text"
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="Enter 6-digit code"
                  required
                  maxLength={6}
                  className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 text-center tracking-widest text-lg font-mono"
                />
              </div>

              <div>
                <Label htmlFor="new-password" className="text-slate-200">
                  New Password <span className="text-red-400">*</span>
                </Label>
                <div className="relative mt-1.5">
                  <Input
                    id="new-password"
                    type={showNewPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    required
                    minLength={6}
                    className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-1"
                    tabIndex={-1}
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <Label htmlFor="confirm-new-password" className="text-slate-200">
                  Confirm Password <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="confirm-new-password"
                  type={showNewPassword ? "text" : "password"}
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  placeholder="Confirm new password"
                  required
                  className="mt-1.5 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setResetStep(1)}
                  className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  disabled={resetLoading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {resetLoading ? "Resetting..." : "Reset Password"}
                </Button>
              </div>
              
              <button
                type="button"
                onClick={handleRequestResetCode}
                className="w-full text-xs text-slate-400 hover:text-slate-300"
                disabled={resetLoading}
              >
                Didn't receive the code? Send again
              </button>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
