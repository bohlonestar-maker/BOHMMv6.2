import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { ArrowLeft, Mail, Save, Send, RefreshCw, AlertTriangle, CheckCircle, Clock, Users, Shield, X, Plus, RotateCcw, Gift, ChevronDown, ChevronUp } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DuesReminders() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [status, setStatus] = useState(null);
  const [extensions, setExtensions] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [editedTemplate, setEditedTemplate] = useState(null);
  const [testEmailDialog, setTestEmailDialog] = useState(false);
  const [testEmail, setTestEmail] = useState("");
  const [runningCheck, setRunningCheck] = useState(false);
  const [extensionDialog, setExtensionDialog] = useState(false);
  const [selectedMemberForExtension, setSelectedMemberForExtension] = useState(null);
  const [extensionDate, setExtensionDate] = useState("");
  const [extensionReason, setExtensionReason] = useState("");
  const [activeTab, setActiveTab] = useState("templates");
  const [forgiveDialog, setForgiveDialog] = useState(false);
  const [selectedMemberForForgive, setSelectedMemberForForgive] = useState(null);
  const [forgiveReason, setForgiveReason] = useState("");
  const [expandedMember, setExpandedMember] = useState(null);
  const [settings, setSettings] = useState({
    suspension_enabled: true,
    discord_kick_enabled: true,
    email_reminders_enabled: true
  });
  const [savingSettings, setSavingSettings] = useState(false);
  
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [templatesRes, statusRes, extensionsRes, settingsRes] = await Promise.all([
        axios.get(`${API}/dues-reminders/templates`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/dues-reminders/status`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/dues-reminders/extensions`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/dues-reminders/settings`, {
          headers: { Authorization: `Bearer ${token}` },
        })
      ]);
      
      setTemplates(templatesRes.data.templates || []);
      setStatus(statusRes.data);
      setExtensions(extensionsRes.data.extensions || []);
      setSettings(settingsRes.data || {
        suspension_enabled: true,
        discord_kick_enabled: true,
        email_reminders_enabled: true
      });
    } catch (error) {
      console.error("Failed to fetch data:", error);
      if (error.response?.status === 403) {
        toast.error("You don't have permission to access this page");
        navigate("/");
      } else {
        toast.error("Failed to load dues reminders");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSettings = async (key, value) => {
    try {
      setSavingSettings(true);
      const newSettings = { ...settings, [key]: value };
      await axios.put(`${API}/dues-reminders/settings`, newSettings, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSettings(newSettings);
      toast.success("Settings updated");
    } catch (error) {
      console.error("Failed to update settings:", error);
      toast.error("Failed to update settings");
    } finally {
      setSavingSettings(false);
    }
  };

  const handleSelectTemplate = (template) => {
    setSelectedTemplate(template);
    setEditedTemplate({
      subject: template.subject,
      body: template.body,
      is_active: template.is_active
    });
  };

  const handleSaveTemplate = async () => {
    if (!selectedTemplate || !editedTemplate) return;
    
    try {
      setSaving(true);
      await axios.put(`${API}/dues-reminders/templates/${selectedTemplate.id}`, editedTemplate, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success("Template saved successfully");
      
      setTemplates(prev => prev.map(t => 
        t.id === selectedTemplate.id 
          ? { ...t, ...editedTemplate }
          : t
      ));
      setSelectedTemplate(prev => ({ ...prev, ...editedTemplate }));
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save template");
    } finally {
      setSaving(false);
    }
  };

  const handleSendTest = async () => {
    if (!selectedTemplate || !testEmail) return;
    
    try {
      const response = await axios.post(`${API}/dues-reminders/send-test`, null, {
        params: { template_id: selectedTemplate.id, email: testEmail },
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success("Test email preview generated");
      setTestEmailDialog(false);
      alert(`Email Preview:\n\nTo: ${response.data.preview.to}\nSubject: ${response.data.preview.subject}\n\n${response.data.preview.body}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send test email");
    }
  };

  const handleRunCheck = async () => {
    try {
      setRunningCheck(true);
      const response = await axios.post(`${API}/dues-reminders/run-check`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success(`${response.data.emails_sent} reminders queued`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to run check");
    } finally {
      setRunningCheck(false);
    }
  };

  const openExtensionDialog = (member) => {
    setSelectedMemberForExtension(member);
    const today = new Date();
    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    setExtensionDate(endOfMonth.toISOString().split('T')[0]);
    setExtensionReason("");
    setExtensionDialog(true);
  };

  const handleGrantExtension = async () => {
    if (!selectedMemberForExtension || !extensionDate) return;
    
    try {
      await axios.post(`${API}/dues-reminders/extensions`, {
        member_id: selectedMemberForExtension.id,
        extension_until: extensionDate,
        reason: extensionReason
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success(`Extension granted to ${selectedMemberForExtension.handle}`);
      setExtensionDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to grant extension");
    }
  };

  const handleRevokeExtension = async (memberId, handle) => {
    if (!confirm(`Revoke extension for ${handle}?`)) return;
    
    try {
      await axios.delete(`${API}/dues-reminders/extensions/${memberId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success("Extension revoked");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to revoke extension");
    }
  };

  const handleReinstate = async (memberId, handle) => {
    if (!confirm(`Reinstate ${handle}? This will restore their Discord permissions.`)) return;
    
    try {
      const response = await axios.post(`${API}/dues-reminders/reinstate/${memberId}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.data.discord_restored) {
        toast.success(`${handle} reinstated and Discord permissions restored`);
      } else {
        toast.success(`${handle} reinstated. Discord: ${response.data.discord_message}`);
      }
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to reinstate member");
    }
  };

  const openForgiveDialog = (member) => {
    setSelectedMemberForForgive(member);
    setForgiveReason("");
    setForgiveDialog(true);
  };

  const handleForgive = async () => {
    if (!selectedMemberForForgive) return;
    
    try {
      await axios.post(`${API}/dues-reminders/forgive`, {
        member_id: selectedMemberForForgive.id,
        reason: forgiveReason
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success(`Dues forgiven for ${selectedMemberForForgive.handle}`);
      setForgiveDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to forgive dues");
    }
  };

  const getDayBadgeColor = (day) => {
    if (day === 3) return "bg-yellow-600";
    if (day === 8) return "bg-orange-600";
    if (day === 10) return "bg-red-600";
    if (day === 30) return "bg-red-900";
    return "bg-slate-600";
  };

  const formatDate = (isoDate) => {
    if (!isoDate) return "-";
    try {
      return new Date(isoDate).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      });
    } catch {
      return isoDate;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  const activeExtensions = extensions.filter(e => e.is_active);

  // Mobile member card component
  const MemberCard = ({ member }) => {
    const isExpanded = expandedMember === member.id;
    const isSuspended = member.reminders_sent?.includes("dues_reminder_day10");
    
    return (
      <div className="bg-slate-700/50 rounded-lg p-3 mb-2">
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setExpandedMember(isExpanded ? null : member.id)}
        >
          <div className="flex-1 min-w-0">
            <div className="font-medium text-white truncate">{member.handle}</div>
            <div className="text-xs text-slate-400 truncate">{member.chapter}</div>
          </div>
          <div className="flex items-center gap-2 ml-2">
            {member.has_extension ? (
              <Badge className="bg-green-600 text-xs whitespace-nowrap">Extended</Badge>
            ) : isSuspended ? (
              <Badge className="bg-red-600 text-xs">Suspended</Badge>
            ) : (
              <Badge variant="outline" className="border-slate-500 text-slate-400 text-xs">Pending</Badge>
            )}
            {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </div>
        </div>
        
        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-slate-600">
            <div className="text-xs text-slate-400 mb-2">
              <div>Email: {member.email || 'No email'}</div>
              {member.has_extension && (
                <div className="text-green-400">Extended until: {formatDate(member.extension_until)}</div>
              )}
              <div className="flex gap-1 mt-1">
                {member.reminders_sent?.includes("dues_reminder_day3") && (
                  <Badge className="bg-yellow-600 text-xs">Day 3</Badge>
                )}
                {member.reminders_sent?.includes("dues_reminder_day8") && (
                  <Badge className="bg-orange-600 text-xs">Day 8</Badge>
                )}
                {member.reminders_sent?.includes("dues_reminder_day10") && (
                  <Badge className="bg-red-600 text-xs">Day 10</Badge>
                )}
                {!member.reminders_sent?.length && (
                  <span className="text-slate-500">No reminders sent</span>
                )}
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mt-3">
              <Button
                size="sm"
                onClick={() => openForgiveDialog(member)}
                className="bg-purple-600 hover:bg-purple-700 text-xs flex-1"
              >
                <Gift className="w-3 h-3 mr-1" />
                Forgive
              </Button>
              
              {member.has_extension ? (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleRevokeExtension(member.id, member.handle)}
                  className="text-xs flex-1"
                >
                  <X className="w-3 h-3 mr-1" />
                  Revoke
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => openExtensionDialog(member)}
                  className="bg-green-600 hover:bg-green-700 text-xs flex-1"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Extend
                </Button>
              )}
              
              {isSuspended && !member.has_extension && (
                <Button
                  size="sm"
                  onClick={() => handleReinstate(member.id, member.handle)}
                  className="bg-blue-600 hover:bg-blue-700 text-xs flex-1"
                >
                  <RotateCcw className="w-3 h-3 mr-1" />
                  Reinstate
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <nav className="bg-slate-800 border-b border-slate-700 shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => navigate("/")}
                className="text-slate-400 hover:text-white p-2"
              >
                <ArrowLeft className="w-4 h-4" />
              </Button>
              <Mail className="w-5 h-5 text-amber-400" />
              <h1 className="text-lg font-bold text-white">Dues Reminders</h1>
            </div>
            <Button 
              onClick={handleRunCheck}
              disabled={runningCheck}
              size="sm"
              className="bg-amber-600 hover:bg-amber-700 w-full sm:w-auto"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${runningCheck ? 'animate-spin' : ''}`} />
              {runningCheck ? "Running..." : "Run Check Now"}
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4">
        {/* Status Cards - Responsive Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3 mb-4 sm:mb-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <Clock className="w-6 h-6 sm:w-8 sm:h-8 text-blue-400 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-lg sm:text-2xl font-bold text-white truncate">{status?.current_month || '-'}</div>
                  <div className="text-xs text-slate-400">Month</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <Users className="w-6 h-6 sm:w-8 sm:h-8 text-amber-400 flex-shrink-0" />
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-white">{status?.unpaid_count || 0}</div>
                  <div className="text-xs text-slate-400">Unpaid</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <AlertTriangle className="w-6 h-6 sm:w-8 sm:h-8 text-red-400 flex-shrink-0" />
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-white">{status?.suspended_count || 0}</div>
                  <div className="text-xs text-slate-400">Suspended</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <Shield className="w-6 h-6 sm:w-8 sm:h-8 text-green-400 flex-shrink-0" />
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-white">{activeExtensions.length}</div>
                  <div className="text-xs text-slate-400">Extensions</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800 border-slate-700 col-span-2 sm:col-span-1">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <CheckCircle className="w-6 h-6 sm:w-8 sm:h-8 text-green-400 flex-shrink-0" />
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-white">Day {status?.day_of_month || '-'}</div>
                  <div className="text-xs text-slate-400">Of Month</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tab Navigation - Scrollable on mobile */}
        <div className="flex gap-2 mb-4 sm:mb-6 overflow-x-auto pb-2">
          <Button
            variant={activeTab === "templates" ? "default" : "outline"}
            onClick={() => setActiveTab("templates")}
            size="sm"
            className={`whitespace-nowrap ${activeTab === "templates" ? "bg-purple-600" : "border-slate-600 text-slate-300"}`}
          >
            <Mail className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">Email </span>Templates
          </Button>
          <Button
            variant={activeTab === "extensions" ? "default" : "outline"}
            onClick={() => setActiveTab("extensions")}
            size="sm"
            className={`whitespace-nowrap ${activeTab === "extensions" ? "bg-green-600" : "border-slate-600 text-slate-300"}`}
          >
            <Shield className="w-4 h-4 mr-1 sm:mr-2" />
            Extensions ({activeExtensions.length})
          </Button>
          <Button
            variant={activeTab === "members" ? "default" : "outline"}
            onClick={() => setActiveTab("members")}
            size="sm"
            className={`whitespace-nowrap ${activeTab === "members" ? "bg-amber-600" : "border-slate-600 text-slate-300"}`}
          >
            <Users className="w-4 h-4 mr-1 sm:mr-2" />
            Unpaid ({status?.unpaid_count || 0})
          </Button>
          <Button
            variant={activeTab === "settings" ? "default" : "outline"}
            onClick={() => setActiveTab("settings")}
            size="sm"
            className={`whitespace-nowrap ${activeTab === "settings" ? "bg-slate-600" : "border-slate-600 text-slate-300"}`}
          >
            <AlertTriangle className="w-4 h-4 mr-1 sm:mr-2" />
            Settings
          </Button>
        </div>

        {/* Settings Tab */}
        {activeTab === "settings" && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="p-3 sm:p-6">
              <CardTitle className="text-white text-base sm:text-lg">Automation Settings</CardTitle>
              <CardDescription className="text-slate-400">
                Control what happens automatically when members don't pay dues
              </CardDescription>
            </CardHeader>
            <CardContent className="p-3 sm:p-6 pt-0 sm:pt-0 space-y-6">
              {/* Email Reminders Toggle */}
              <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                <div className="space-y-1">
                  <div className="font-medium text-white flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    Email Reminders
                  </div>
                  <p className="text-sm text-slate-400">
                    Send automatic email reminders on days 3, 8, 10, and 30
                  </p>
                </div>
                <button
                  onClick={() => handleUpdateSettings("email_reminders_enabled", !settings.email_reminders_enabled)}
                  disabled={savingSettings}
                  className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
                    settings.email_reminders_enabled ? 'bg-green-600' : 'bg-slate-600'
                  } ${savingSettings ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform duration-200 ease-in-out ${
                      settings.email_reminders_enabled ? 'translate-x-8' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Suspension Toggle */}
              <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                <div className="space-y-1">
                  <div className="font-medium text-white flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Auto Suspension (Day 10)
                  </div>
                  <p className="text-sm text-slate-400">
                    Automatically suspend Discord permissions when dues are 10+ days overdue
                  </p>
                </div>
                <button
                  onClick={() => handleUpdateSettings("suspension_enabled", !settings.suspension_enabled)}
                  disabled={savingSettings}
                  className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
                    settings.suspension_enabled ? 'bg-amber-600' : 'bg-slate-600'
                  } ${savingSettings ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform duration-200 ease-in-out ${
                      settings.suspension_enabled ? 'translate-x-8' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Discord Kick Toggle */}
              <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                <div className="space-y-1">
                  <div className="font-medium text-white flex items-center gap-2">
                    <X className="w-4 h-4 text-red-400" />
                    Auto Removal (Day 30)
                  </div>
                  <p className="text-sm text-slate-400">
                    Automatically kick member from Discord server after 30 days unpaid
                  </p>
                </div>
                <button
                  onClick={() => handleUpdateSettings("discord_kick_enabled", !settings.discord_kick_enabled)}
                  disabled={savingSettings}
                  className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
                    settings.discord_kick_enabled ? 'bg-red-600' : 'bg-slate-600'
                  } ${savingSettings ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform duration-200 ease-in-out ${
                      settings.discord_kick_enabled ? 'translate-x-8' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Status Summary */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-600">
                <h4 className="text-sm font-medium text-slate-300 mb-2">Current Status:</h4>
                <ul className="text-sm text-slate-400 space-y-1">
                  <li className="flex items-center gap-2">
                    {settings.email_reminders_enabled ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <X className="w-4 h-4 text-red-400" />
                    )}
                    Email reminders are {settings.email_reminders_enabled ? "enabled" : "disabled"}
                  </li>
                  <li className="flex items-center gap-2">
                    {settings.suspension_enabled ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <X className="w-4 h-4 text-red-400" />
                    )}
                    Auto suspension is {settings.suspension_enabled ? "enabled" : "disabled"}
                  </li>
                  <li className="flex items-center gap-2">
                    {settings.discord_kick_enabled ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <X className="w-4 h-4 text-red-400" />
                    )}
                    Auto removal is {settings.discord_kick_enabled ? "enabled" : "disabled"}
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Templates Tab */}
        {activeTab === "templates" && (
          <div className="grid lg:grid-cols-3 gap-4 sm:gap-6">
            {/* Template List */}
            <div className="lg:col-span-1">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="p-3 sm:p-6">
                  <CardTitle className="text-white text-base sm:text-lg">Email Templates</CardTitle>
                  <CardDescription className="text-slate-400 text-sm">
                    Select to edit
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-3 sm:p-6 pt-0 sm:pt-0 space-y-2">
                  {templates.map((template) => (
                    <button
                      key={template.id}
                      onClick={() => handleSelectTemplate(template)}
                      className={`w-full p-3 rounded-lg text-left transition-colors ${
                        selectedTemplate?.id === template.id
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-sm truncate">{template.name}</span>
                        <Badge className={`${getDayBadgeColor(template.day_trigger)} flex-shrink-0`}>
                          Day {template.day_trigger}
                        </Badge>
                      </div>
                      {!template.is_active && (
                        <Badge variant="outline" className="mt-2 text-xs border-red-500 text-red-400">
                          Disabled
                        </Badge>
                      )}
                    </button>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Template Editor */}
            <div className="lg:col-span-2">
              {selectedTemplate ? (
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader className="p-3 sm:p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div>
                        <CardTitle className="text-white text-base sm:text-lg">{selectedTemplate.name}</CardTitle>
                        <CardDescription className="text-slate-400 text-sm">
                          Sent on day {selectedTemplate.day_trigger}
                        </CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-400">Active</span>
                        <Switch
                          checked={editedTemplate?.is_active || false}
                          onCheckedChange={(checked) => setEditedTemplate(prev => ({ ...prev, is_active: checked }))}
                          className="data-[state=checked]:bg-green-600"
                        />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-3 sm:p-6 pt-0 sm:pt-0 space-y-4">
                    <div>
                      <label className="text-sm text-slate-300 mb-2 block">Subject Line</label>
                      <Input
                        value={editedTemplate?.subject || ''}
                        onChange={(e) => setEditedTemplate(prev => ({ ...prev, subject: e.target.value }))}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    
                    <div>
                      <label className="text-sm text-slate-300 mb-2 block">Email Body</label>
                      <Textarea
                        value={editedTemplate?.body || ''}
                        onChange={(e) => setEditedTemplate(prev => ({ ...prev, body: e.target.value }))}
                        className="bg-slate-700 border-slate-600 text-white min-h-[200px] sm:min-h-[250px] font-mono text-sm"
                      />
                      <p className="text-xs text-slate-500 mt-2">
                        Variables: {"{{member_name}}"}, {"{{month}}"}, {"{{year}}"}
                      </p>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-2 pt-2">
                      <Button
                        onClick={handleSaveTemplate}
                        disabled={saving}
                        className="bg-green-600 hover:bg-green-700 flex-1"
                      >
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? "Saving..." : "Save"}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setTestEmailDialog(true)}
                        className="border-slate-600 text-slate-300 hover:bg-slate-700 flex-1 sm:flex-none"
                      >
                        <Send className="w-4 h-4 mr-2" />
                        Test
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-8 sm:p-12 text-center">
                    <Mail className="w-12 h-12 sm:w-16 sm:h-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">Select a template to edit</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Extensions Tab */}
        {activeTab === "extensions" && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="p-3 sm:p-6">
              <CardTitle className="text-white text-base sm:text-lg">Active Extensions</CardTitle>
              <CardDescription className="text-slate-400 text-sm">
                Members with payment extensions
              </CardDescription>
            </CardHeader>
            <CardContent className="p-3 sm:p-6 pt-0 sm:pt-0">
              {activeExtensions.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="w-12 h-12 sm:w-16 sm:h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">No active extensions</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {activeExtensions.map((ext) => (
                    <div key={ext.member_id} className="bg-slate-700/50 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="font-medium text-white">{ext.member_handle}</div>
                          <div className="text-xs text-slate-400">{ext.member_chapter}</div>
                        </div>
                        <div className="flex items-center gap-2 ml-2">
                          <Badge className="bg-green-600 text-xs whitespace-nowrap">
                            {formatDate(ext.extension_until)}
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleRevokeExtension(ext.member_id, ext.member_handle)}
                            className="text-red-400 hover:text-red-300 hover:bg-red-900/30 p-1"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      {ext.reason && (
                        <div className="text-xs text-slate-400 mt-1 truncate">{ext.reason}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Unpaid Members Tab */}
        {activeTab === "members" && status?.unpaid_members?.length > 0 && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="p-3 sm:p-6">
              <CardTitle className="text-white text-base sm:text-lg">Unpaid Members - {status.current_month}</CardTitle>
              <CardDescription className="text-slate-400 text-sm">
                Tap to expand and manage
              </CardDescription>
            </CardHeader>
            <CardContent className="p-3 sm:p-6 pt-0 sm:pt-0">
              {/* Mobile Card View */}
              <div className="block lg:hidden">
                {status.unpaid_members.slice(0, 30).map((member) => (
                  <MemberCard key={member.id} member={member} />
                ))}
              </div>
              
              {/* Desktop Table View */}
              <div className="hidden lg:block overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left p-2 text-slate-400">Member</th>
                      <th className="text-left p-2 text-slate-400">Chapter</th>
                      <th className="text-left p-2 text-slate-400">Email</th>
                      <th className="text-left p-2 text-slate-400">Status</th>
                      <th className="text-left p-2 text-slate-400">Reminders</th>
                      <th className="text-right p-2 text-slate-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {status.unpaid_members.slice(0, 30).map((member) => (
                      <tr key={member.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="p-2">
                          <div className="text-white font-medium">{member.handle}</div>
                          <div className="text-xs text-slate-400">{member.name}</div>
                        </td>
                        <td className="p-2 text-slate-300">{member.chapter}</td>
                        <td className="p-2 text-slate-300 text-xs max-w-[150px] truncate">{member.email || 'No email'}</td>
                        <td className="p-2">
                          {member.has_extension ? (
                            <Badge className="bg-green-600 text-xs">
                              <Shield className="w-3 h-3 mr-1" />
                              Extended
                            </Badge>
                          ) : member.reminders_sent?.includes("dues_reminder_day10") ? (
                            <Badge className="bg-red-600 text-xs">Suspended</Badge>
                          ) : (
                            <Badge variant="outline" className="border-slate-500 text-slate-400 text-xs">Pending</Badge>
                          )}
                        </td>
                        <td className="p-2">
                          <div className="flex gap-1 flex-wrap">
                            {member.reminders_sent?.map(r => {
                              const day = r.replace('dues_reminder_day', '');
                              return <Badge key={r} className={`${getDayBadgeColor(parseInt(day))} text-xs`}>Day {day}</Badge>;
                            })}
                            {!member.reminders_sent?.length && <span className="text-slate-500 text-xs">None</span>}
                          </div>
                        </td>
                        <td className="p-2 text-right">
                          <div className="flex gap-1 justify-end">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openForgiveDialog(member)}
                              className="text-purple-400 hover:text-purple-300 hover:bg-purple-900/30"
                              title="Forgive"
                            >
                              <Gift className="w-4 h-4" />
                            </Button>
                            
                            {member.has_extension ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleRevokeExtension(member.id, member.handle)}
                                className="text-red-400 hover:text-red-300 hover:bg-red-900/30"
                                title="Revoke Extension"
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => openExtensionDialog(member)}
                                className="text-green-400 hover:text-green-300 hover:bg-green-900/30"
                                title="Extend"
                              >
                                <Plus className="w-4 h-4" />
                              </Button>
                            )}
                            
                            {member.reminders_sent?.includes("dues_reminder_day10") && !member.has_extension && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleReinstate(member.id, member.handle)}
                                className="text-blue-400 hover:text-blue-300 hover:bg-blue-900/30"
                                title="Reinstate"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {status.unpaid_members.length > 30 && (
                <p className="text-center text-slate-500 text-sm mt-4">
                  Showing 30 of {status.unpaid_members.length} members
                </p>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Test Email Dialog */}
      <Dialog open={testEmailDialog} onOpenChange={setTestEmailDialog}>
        <DialogContent className="bg-slate-800 border-slate-700 mx-4 sm:mx-auto max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Send Test Email</DialogTitle>
            <DialogDescription className="text-slate-400">
              Preview how this email will look
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              type="email"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              className="bg-slate-700 border-slate-600 text-white"
              placeholder="your@email.com"
            />
          </div>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => setTestEmailDialog(false)} className="border-slate-600 text-slate-300 w-full sm:w-auto">
              Cancel
            </Button>
            <Button onClick={handleSendTest} className="bg-purple-600 hover:bg-purple-700 w-full sm:w-auto">
              <Send className="w-4 h-4 mr-2" />
              Preview
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Extension Dialog */}
      <Dialog open={extensionDialog} onOpenChange={setExtensionDialog}>
        <DialogContent className="bg-slate-800 border-slate-700 mx-4 sm:mx-auto max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Grant Extension</DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedMemberForExtension?.handle} won't receive reminders until extension expires
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div>
              <label className="text-sm text-slate-300 mb-2 block">Extension Until</label>
              <Input
                type="date"
                value={extensionDate}
                onChange={(e) => setExtensionDate(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white"
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div>
              <label className="text-sm text-slate-300 mb-2 block">Reason (optional)</label>
              <Textarea
                value={extensionReason}
                onChange={(e) => setExtensionReason(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white"
                placeholder="e.g., Financial hardship..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => setExtensionDialog(false)} className="border-slate-600 text-slate-300 w-full sm:w-auto">
              Cancel
            </Button>
            <Button onClick={handleGrantExtension} className="bg-green-600 hover:bg-green-700 w-full sm:w-auto">
              <Shield className="w-4 h-4 mr-2" />
              Grant Extension
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Forgive Dialog */}
      <Dialog open={forgiveDialog} onOpenChange={setForgiveDialog}>
        <DialogContent className="bg-slate-800 border-slate-700 mx-4 sm:mx-auto max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Forgive Dues</DialogTitle>
            <DialogDescription className="text-slate-400">
              Waive dues for <span className="text-white font-medium">{selectedMemberForForgive?.handle}</span> for {status?.current_month}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm text-slate-300 mb-2 block">Reason (optional)</label>
            <Textarea
              value={forgiveReason}
              onChange={(e) => setForgiveReason(e.target.value)}
              className="bg-slate-700 border-slate-600 text-white"
              placeholder="e.g., Hardship waiver..."
              rows={2}
            />
          </div>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => setForgiveDialog(false)} className="border-slate-600 text-slate-300 w-full sm:w-auto">
              Cancel
            </Button>
            <Button onClick={handleForgive} className="bg-purple-600 hover:bg-purple-700 w-full sm:w-auto">
              <Gift className="w-4 h-4 mr-2" />
              Forgive Dues
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
