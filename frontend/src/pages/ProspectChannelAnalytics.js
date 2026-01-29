import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BarChart3, RefreshCw, Trash2, Clock, Users, ChevronDown, ChevronRight, Settings, ArrowLeft, Radio } from "lucide-react";
import { useNavigate } from "react-router-dom";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function ProspectChannelAnalytics() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [activeSessions, setActiveSessions] = useState(null);
  const [settings, setSettings] = useState({ tracking_enabled: true });
  const [loading, setLoading] = useState(true);
  const [expandedUser, setExpandedUser] = useState(null);
  const [dateRange, setDateRange] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [tick, setTick] = useState(0); // For live timer updates

  const fetchActiveSessions = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/prospect-channel-analytics/active`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setActiveSessions(response.data);
    } catch (error) {
      console.error("Failed to fetch active sessions:", error);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  // Update active sessions every 5 seconds
  useEffect(() => {
    fetchActiveSessions();
    const interval = setInterval(() => {
      fetchActiveSessions();
      setTick(t => t + 1); // Trigger re-render for timer updates
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchActiveSessions]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };

      const [analyticsRes, settingsRes, activeRes] = await Promise.all([
        axios.get(`${API}/prospect-channel-analytics`, { headers }),
        axios.get(`${API}/prospect-channel-analytics/settings`, { headers }),
        axios.get(`${API}/prospect-channel-analytics/active`, { headers }),
      ]);

      setAnalytics(analyticsRes.data);
      setSettings(settingsRes.data);
      setActiveSessions(activeRes.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("You don't have permission to view this page");
        navigate("/prospects");
      } else {
        toast.error("Failed to load analytics");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredAnalytics = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams();
      
      if (dateRange === "custom" && startDate) {
        params.append("start_date", startDate);
      }
      if (dateRange === "custom" && endDate) {
        params.append("end_date", endDate);
      }
      if (dateRange === "7days") {
        const d = new Date();
        d.setDate(d.getDate() - 7);
        params.append("start_date", d.toISOString().split("T")[0]);
      }
      if (dateRange === "30days") {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        params.append("start_date", d.toISOString().split("T")[0]);
      }

      const response = await axios.get(
        `${API}/prospect-channel-analytics?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnalytics(response.data);
    } catch (error) {
      toast.error("Failed to filter analytics");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleTracking = async (enabled) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `${API}/prospect-channel-analytics/settings?tracking_enabled=${enabled}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSettings({ ...settings, tracking_enabled: enabled });
      toast.success(`Tracking ${enabled ? "enabled" : "disabled"}`);
    } catch (error) {
      toast.error("Failed to update settings");
    }
  };

  const handleReset = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API}/prospect-channel-analytics/reset`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
      setResetDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error("Failed to reset analytics");
    }
  };

  const toggleUserExpanded = (userId) => {
    setExpandedUser(expandedUser === userId ? null : userId);
  };

  // Calculate live duration from joined_at
  const getLiveDuration = (joinedAt) => {
    if (!joinedAt) return "0s";
    try {
      const joined = new Date(joinedAt);
      const now = new Date();
      const seconds = Math.floor((now - joined) / 1000);
      return formatTotalTime(seconds);
    } catch {
      return "0s";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-lg">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/prospects")}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back to Prospects
            </Button>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-blue-400" />
            Prospect Channel Analytics
          </h1>
          <div className="flex gap-2">
            <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="bg-slate-700 border-slate-600 text-white hover:bg-slate-600">
                  <Settings className="w-4 h-4 mr-1" />
                  Settings
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Prospect Channel Tracking Settings</DialogTitle>
                </DialogHeader>
                <div className="space-y-6 mt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base">Enable Tracking</Label>
                      <p className="text-sm text-slate-400">Track voice activity in Prospect channels</p>
                    </div>
                    <Switch
                      checked={settings.tracking_enabled}
                      onCheckedChange={handleToggleTracking}
                    />
                  </div>
                  {settings.last_reset && (
                    <div className="text-sm text-slate-400">
                      Last reset: {new Date(settings.last_reset).toLocaleString()} by {settings.reset_by}
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="bg-red-600 border-red-600 text-white hover:bg-red-700">
                  <Trash2 className="w-4 h-4 mr-1" />
                  Reset Data
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Reset All Analytics Data</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <p className="text-slate-300">
                    This will permanently delete all Prospect channel analytics data. This action cannot be undone.
                  </p>
                  <div className="flex gap-3 justify-end">
                    <Button variant="outline" onClick={() => setResetDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button variant="destructive" onClick={handleReset}>
                      Reset All Data
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            <Button
              size="sm"
              onClick={fetchData}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Status Banner */}
        {!settings.tracking_enabled && (
          <div className="bg-yellow-600/20 border border-yellow-600 text-yellow-300 p-4 rounded-lg mb-6">
            <strong>Tracking is disabled.</strong> Enable tracking in Settings to start collecting data.
          </div>
        )}

        {/* Active Sessions - Currently in Channel */}
        {activeSessions && activeSessions.active_count > 0 && (
          <div className="bg-green-900/30 border border-green-700 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Radio className="w-5 h-5 text-green-400 animate-pulse" />
              <h2 className="text-lg font-semibold text-green-400">
                Currently in Prospect Channels ({activeSessions.active_count})
              </h2>
            </div>
            <div className="grid gap-3">
              {activeSessions.sessions.map((session) => (
                <div
                  key={session.id}
                  className="bg-slate-800/80 rounded-lg p-4 border border-green-800"
                >
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="font-medium text-white text-lg">{session.display_name}</span>
                      <span className="text-slate-400 text-sm">in {session.channel_name}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="bg-blue-600/30 px-4 py-2 rounded-lg">
                        <span className="text-blue-400 font-mono text-xl" key={tick}>
                          {getLiveDuration(session.joined_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2 text-sm">
                    {session.prospects_present?.length > 0 && (
                      <span className="text-green-400">
                        With Prospects: {session.prospects_present.join(", ")}
                      </span>
                    )}
                    {session.hangarounds_present?.length > 0 && (
                      <span className="text-amber-400">
                        With Hangarounds: {session.hangarounds_present.join(", ")}
                      </span>
                    )}
                    {session.others_in_channel?.length > 0 && (
                      <span className="text-slate-500">
                        Others: {session.others_in_channel.map(o => o.display_name).slice(0, 5).join(", ")}
                        {session.others_in_channel.length > 5 && ` +${session.others_in_channel.length - 5} more`}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-slate-800 rounded-lg p-4 mb-6 border border-slate-700">
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <Label className="text-slate-300 text-sm">Date Range (Completed Sessions)</Label>
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger className="w-40 bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  <SelectItem value="all" className="text-white">All Time</SelectItem>
                  <SelectItem value="7days" className="text-white">Last 7 Days</SelectItem>
                  <SelectItem value="30days" className="text-white">Last 30 Days</SelectItem>
                  <SelectItem value="custom" className="text-white">Custom Range</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {dateRange === "custom" && (
              <>
                <div>
                  <Label className="text-slate-300 text-sm">Start Date</Label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
                <div>
                  <Label className="text-slate-300 text-sm">End Date</Label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </>
            )}

            <Button onClick={fetchFilteredAnalytics} className="bg-slate-600 hover:bg-slate-500">
              Apply Filter
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Users className="w-5 h-5" />
              <span className="text-sm">Unique Visitors</span>
            </div>
            <div className="text-3xl font-bold text-white">{analytics?.unique_users || 0}</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <BarChart3 className="w-5 h-5" />
              <span className="text-sm">Completed Sessions</span>
            </div>
            <div className="text-3xl font-bold text-white">{analytics?.total_records || 0}</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex items-center gap-2 text-green-400 mb-2">
              <Clock className="w-5 h-5" />
              <span className="text-sm">Sessions w/ Prospect</span>
            </div>
            <div className="text-3xl font-bold text-green-400">
              {analytics?.users?.reduce((sum, u) => sum + u.sessions_with_prospect, 0) || 0}
            </div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex items-center gap-2 text-blue-400 mb-2">
              <Clock className="w-5 h-5" />
              <span className="text-sm">Total Time</span>
            </div>
            <div className="text-2xl font-bold text-blue-400">
              {formatTotalTime(analytics?.users?.reduce((sum, u) => sum + u.total_time_minutes * 60, 0) || 0)}
            </div>
          </div>
        </div>

        {/* Completed Sessions Table */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-lg font-semibold text-white">Completed Sessions History</h3>
          </div>
          <Table>
            <TableHeader>
              <TableRow className="border-slate-700 hover:bg-transparent">
                <TableHead className="text-slate-300 w-8"></TableHead>
                <TableHead className="text-slate-300">Discord User</TableHead>
                <TableHead className="text-slate-300 text-center">Sessions</TableHead>
                <TableHead className="text-slate-300 text-center">Total Time</TableHead>
                <TableHead className="text-slate-300 text-center">
                  <span className="text-green-400">Sessions w/ Prospect</span>
                </TableHead>
                <TableHead className="text-slate-300 text-center">
                  <span className="text-green-400">Time w/ Prospect</span>
                </TableHead>
                <TableHead className="text-slate-300">Prospects/Hangarounds Met</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analytics?.users?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-slate-400 py-8">
                    No completed sessions yet. Sessions will appear here when users leave Prospect channels.
                  </TableCell>
                </TableRow>
              ) : (
                analytics?.users?.map((user) => (
                  <>
                    <TableRow
                      key={user.discord_id}
                      className="border-slate-700 hover:bg-slate-700/50 cursor-pointer"
                      onClick={() => toggleUserExpanded(user.discord_id)}
                    >
                      <TableCell className="text-slate-400">
                        {expandedUser === user.discord_id ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </TableCell>
                      <TableCell className="text-white font-medium">{user.display_name}</TableCell>
                      <TableCell className="text-center text-slate-300">{user.total_sessions}</TableCell>
                      <TableCell className="text-center text-slate-300">{user.total_time_formatted}</TableCell>
                      <TableCell className="text-center">
                        <span className={`px-2 py-1 rounded text-sm ${
                          user.sessions_with_prospect > 0 ? 'bg-green-600/30 text-green-400' : 'text-slate-500'
                        }`}>
                          {user.sessions_with_prospect}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className={user.sessions_with_prospect > 0 ? 'text-green-400' : 'text-slate-500'}>
                          {user.time_with_prospect_formatted}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {user.unique_prospects_met?.map((p) => (
                            <span key={p} className="px-2 py-0.5 bg-blue-600/30 text-blue-400 rounded text-xs">
                              {p}
                            </span>
                          ))}
                          {user.unique_hangarounds_met?.map((h) => (
                            <span key={h} className="px-2 py-0.5 bg-amber-600/30 text-amber-400 rounded text-xs">
                              {h}
                            </span>
                          ))}
                          {(!user.unique_prospects_met?.length && !user.unique_hangarounds_met?.length) && (
                            <span className="text-slate-500 text-xs">None</span>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                    {expandedUser === user.discord_id && (
                      <TableRow className="bg-slate-900/50">
                        <TableCell colSpan={7} className="p-4">
                          <div className="text-sm text-slate-400 mb-2">Session Details:</div>
                          <div className="space-y-2 max-h-64 overflow-y-auto">
                            {user.sessions?.map((session, idx) => (
                              <div
                                key={idx}
                                className={`p-3 rounded-lg border ${
                                  session.prospects_present?.length > 0 || session.hangarounds_present?.length > 0
                                    ? 'bg-green-900/20 border-green-800'
                                    : 'bg-slate-800 border-slate-700'
                                }`}
                              >
                                <div className="flex flex-wrap gap-4 items-center">
                                  <span className="text-slate-300">{session.date}</span>
                                  <span className="text-slate-400">{session.channel}</span>
                                  <span className="text-blue-400">{session.duration_minutes} min</span>
                                  {session.prospects_present?.length > 0 && (
                                    <span className="text-green-400">
                                      Prospects: {session.prospects_present.join(", ")}
                                    </span>
                                  )}
                                  {session.hangarounds_present?.length > 0 && (
                                    <span className="text-amber-400">
                                      Hangarounds: {session.hangarounds_present.join(", ")}
                                    </span>
                                  )}
                                  {session.others_present?.length > 0 && (
                                    <span className="text-slate-500 text-xs">
                                      Also present: {session.others_present.slice(0, 5).join(", ")}
                                      {session.others_present.length > 5 && ` +${session.others_present.length - 5} more`}
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}

function formatTotalTime(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}
