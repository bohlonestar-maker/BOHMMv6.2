import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { ArrowLeft, Mail, Save, Send, RefreshCw, AlertTriangle, CheckCircle, Clock, Users } from "lucide-react";
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
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [editedTemplate, setEditedTemplate] = useState(null);
  const [testEmailDialog, setTestEmailDialog] = useState(false);
  const [testEmail, setTestEmail] = useState("");
  const [runningCheck, setRunningCheck] = useState(false);
  
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [templatesRes, statusRes] = await Promise.all([
        axios.get(`${API}/dues-reminders/templates`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/dues-reminders/status`, {
          headers: { Authorization: `Bearer ${token}` },
        })
      ]);
      
      setTemplates(templatesRes.data.templates || []);
      setStatus(statusRes.data);
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
      
      // Update local state
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
      
      // Show preview in a dialog or alert
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
      fetchData(); // Refresh status
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to run check");
    } finally {
      setRunningCheck(false);
    }
  };

  const getDayBadgeColor = (day) => {
    if (day === 3) return "bg-yellow-600";
    if (day === 8) return "bg-orange-600";
    if (day === 10) return "bg-red-600";
    return "bg-slate-600";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <nav className="bg-slate-800 border-b border-slate-700 shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div className="flex items-center gap-2 sm:gap-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => navigate("/")}
                className="text-slate-400 hover:text-white p-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline ml-2">Back</span>
              </Button>
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 sm:w-6 sm:h-6 text-amber-400" />
                <h1 className="text-lg sm:text-xl font-bold text-white">Dues Reminders</h1>
              </div>
            </div>
            <Button 
              onClick={handleRunCheck}
              disabled={runningCheck}
              className="bg-amber-600 hover:bg-amber-700"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${runningCheck ? 'animate-spin' : ''}`} />
              {runningCheck ? "Running..." : "Run Check Now"}
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6">
        {/* Status Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Clock className="w-8 h-8 text-blue-400" />
                <div>
                  <div className="text-2xl font-bold text-white">{status?.current_month || '-'}</div>
                  <div className="text-xs text-slate-400">Current Month</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Users className="w-8 h-8 text-amber-400" />
                <div>
                  <div className="text-2xl font-bold text-white">{status?.unpaid_count || 0}</div>
                  <div className="text-xs text-slate-400">Unpaid Members</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-8 h-8 text-red-400" />
                <div>
                  <div className="text-2xl font-bold text-white">{status?.suspended_count || 0}</div>
                  <div className="text-xs text-slate-400">Suspended</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-8 h-8 text-green-400" />
                <div>
                  <div className="text-2xl font-bold text-white">Day {status?.day_of_month || '-'}</div>
                  <div className="text-xs text-slate-400">Of Month</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Template List */}
          <div className="lg:col-span-1">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-lg">Email Templates</CardTitle>
                <CardDescription className="text-slate-400">
                  Select a template to edit
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
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
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{template.name}</span>
                      <Badge className={getDayBadgeColor(template.day_trigger)}>
                        Day {template.day_trigger}
                      </Badge>
                    </div>
                    <div className="text-xs mt-1 opacity-70 truncate">
                      {template.subject}
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
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-white">{selectedTemplate.name}</CardTitle>
                      <CardDescription className="text-slate-400">
                        Sent on day {selectedTemplate.day_trigger} of each month if dues unpaid
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
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm text-slate-300 mb-2 block">Subject Line</label>
                    <Input
                      value={editedTemplate?.subject || ''}
                      onChange={(e) => setEditedTemplate(prev => ({ ...prev, subject: e.target.value }))}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="Email subject..."
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-300 mb-2 block">Email Body</label>
                    <Textarea
                      value={editedTemplate?.body || ''}
                      onChange={(e) => setEditedTemplate(prev => ({ ...prev, body: e.target.value }))}
                      className="bg-slate-700 border-slate-600 text-white min-h-[250px] font-mono text-sm"
                      placeholder="Email body..."
                    />
                    <p className="text-xs text-slate-500 mt-2">
                      Available placeholders: {"{{member_name}}"}, {"{{month}}"}, {"{{year}}"}
                    </p>
                  </div>
                  
                  <div className="flex flex-col sm:flex-row gap-2 pt-4">
                    <Button
                      onClick={handleSaveTemplate}
                      disabled={saving}
                      className="bg-green-600 hover:bg-green-700 flex-1"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {saving ? "Saving..." : "Save Template"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setTestEmailDialog(true)}
                      className="border-slate-600 text-slate-300 hover:bg-slate-700"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Send Test
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-12 text-center">
                  <Mail className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">Select a template to edit</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Unpaid Members List */}
        {status?.unpaid_members?.length > 0 && (
          <Card className="bg-slate-800 border-slate-700 mt-6">
            <CardHeader>
              <CardTitle className="text-white">Unpaid Members - {status.current_month}</CardTitle>
              <CardDescription className="text-slate-400">
                Members who haven't paid dues this month
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left p-2 text-slate-400">Member</th>
                      <th className="text-left p-2 text-slate-400">Chapter</th>
                      <th className="text-left p-2 text-slate-400">Email</th>
                      <th className="text-left p-2 text-slate-400">Reminders Sent</th>
                    </tr>
                  </thead>
                  <tbody>
                    {status.unpaid_members.slice(0, 20).map((member) => (
                      <tr key={member.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="p-2">
                          <div className="text-white font-medium">{member.handle}</div>
                          <div className="text-xs text-slate-400">{member.name}</div>
                        </td>
                        <td className="p-2 text-slate-300">{member.chapter}</td>
                        <td className="p-2 text-slate-300 text-xs">{member.email || 'No email'}</td>
                        <td className="p-2">
                          <div className="flex gap-1">
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
                              <span className="text-slate-500 text-xs">None yet</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {status.unpaid_members.length > 20 && (
                  <p className="text-center text-slate-500 text-sm mt-4">
                    Showing 20 of {status.unpaid_members.length} unpaid members
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Test Email Dialog */}
      <Dialog open={testEmailDialog} onOpenChange={setTestEmailDialog}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Send Test Email</DialogTitle>
            <DialogDescription className="text-slate-400">
              Preview how this email template will look
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm text-slate-300 mb-2 block">Send to email address</label>
            <Input
              type="email"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              className="bg-slate-700 border-slate-600 text-white"
              placeholder="your@email.com"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTestEmailDialog(false)} className="border-slate-600 text-slate-300">
              Cancel
            </Button>
            <Button onClick={handleSendTest} className="bg-purple-600 hover:bg-purple-700">
              <Send className="w-4 h-4 mr-2" />
              Preview Email
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
