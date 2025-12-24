import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { ArrowLeft, Download, RefreshCw, Users, Volume2, MessageSquare, TrendingUp, Clock, Calendar, Link, Unlink, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DiscordAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [discordMembers, setDiscordMembers] = useState([]);
  const [databaseMembers, setDatabaseMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [linkedMembersDialogOpen, setLinkedMembersDialogOpen] = useState(false);
  const [selectedDiscordMember, setSelectedDiscordMember] = useState(null);
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [memberSearch, setMemberSearch] = useState("");
  const [linkedMemberSearch, setLinkedMemberSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetchDiscordAnalytics();
    fetchDiscordMembers();
    fetchDatabaseMembers();
  }, []);

  const fetchDatabaseMembers = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await axios.get(`${API}/members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDatabaseMembers(response.data);
    } catch (error) {
      console.error("Error fetching database members:", error);
    }
  };

  const handleLinkMember = async () => {
    if (!selectedDiscordMember || !selectedMemberId) {
      toast.error("Please select a member to link");
      return;
    }
    
    const token = localStorage.getItem("token");
    try {
      await axios.post(`${API}/discord/link`, {
        discord_id: selectedDiscordMember.discord_id,
        member_id: selectedMemberId
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success("Member linked successfully");
      setLinkDialogOpen(false);
      setSelectedDiscordMember(null);
      setSelectedMemberId("");
      setMemberSearch("");
      fetchDiscordMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to link member");
    }
  };

  const handleUnlinkMember = async (discordId) => {
    const token = localStorage.getItem("token");
    try {
      await axios.post(`${API}/discord/unlink/${discordId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success("Member unlinked successfully");
      fetchDiscordMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to unlink member");
    }
  };

  const openLinkDialog = (discordMember) => {
    setSelectedDiscordMember(discordMember);
    setSelectedMemberId("");
    setMemberSearch("");
    setLinkDialogOpen(true);
  };

  const filteredDatabaseMembers = databaseMembers.filter(m => {
    const search = memberSearch.toLowerCase();
    return (
      m.handle?.toLowerCase().includes(search) ||
      m.name?.toLowerCase().includes(search) ||
      m.chapter?.toLowerCase().includes(search)
    );
  });

  // Filter out bots and specific names from Discord members
  const filteredDiscordMembers = discordMembers.filter(m => {
    const displayName = (m.display_name || '').toLowerCase();
    const username = (m.username || '').toLowerCase();
    return !m.is_bot &&  // Filter out Discord bots
           !displayName.includes('bot') && 
           !displayName.includes('tv') && 
           !displayName.includes('testdummy') &&
           !username.includes('bot') && 
           !username.includes('tv') &&
           !username.includes('testdummy') &&
           !displayName.startsWith('aoh') &&
           !username.startsWith('aoh') &&
           displayName !== 'craig' &&
           username !== 'craig';
  });

  const [linkedMembers, setLinkedMembers] = useState([]);
  const [loadingLinkedMembers, setLoadingLinkedMembers] = useState(false);

  const fetchLinkedMembers = async () => {
    const token = localStorage.getItem("token");
    setLoadingLinkedMembers(true);
    try {
      const response = await axios.get(`${API}/discord/linked-members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLinkedMembers(response.data);
    } catch (error) {
      toast.error("Failed to load linked members");
    } finally {
      setLoadingLinkedMembers(false);
    }
  };

  const openLinkedMembersDialog = () => {
    fetchLinkedMembers();
    setLinkedMemberSearch("");
    setLinkedMembersDialogOpen(true);
  };

  const filteredLinkedMembers = linkedMembers.filter(m => {
    // First filter out aoh, bot, tv names
    const displayName = (m.discord_display_name || '').toLowerCase();
    const username = (m.discord_username || '').toLowerCase();
    const handle = (m.member_handle || '').toLowerCase();
    
    const isFiltered = displayName.includes('bot') || 
           displayName.includes('tv') || 
           displayName.startsWith('aoh') ||
           username.includes('bot') || 
           username.includes('tv') ||
           username.startsWith('aoh') ||
           handle.includes('bot') ||
           handle.includes('tv') ||
           handle.startsWith('aoh');
    
    if (isFiltered) return false;
    
    // Then apply search filter
    const search = linkedMemberSearch.toLowerCase();
    if (!search) return true;
    
    return (
      m.member_handle?.toLowerCase().includes(search) ||
      m.member_name?.toLowerCase().includes(search) ||
      m.discord_display_name?.toLowerCase().includes(search) ||
      m.discord_username?.toLowerCase().includes(search)
    );
  });

  const formatLastActivity = (timeStr) => {
    // Backend now sends pre-formatted CST time strings
    if (!timeStr) return "Never";
    return timeStr;
  };

  const fetchDiscordAnalytics = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await axios.get(`${API}/discord/analytics?days=30`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      toast.error("Failed to load Discord analytics");
      console.error("Analytics error:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDiscordMembers = async () => {
    const token = localStorage.getItem("token");
    try {
      setRefreshing(true);
      const response = await axios.get(`${API}/discord/members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDiscordMembers(response.data);
      toast.success("Discord members refreshed");
    } catch (error) {
      toast.error("Failed to load Discord members");
      console.error("Members error:", error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleImportMembers = async () => {
    const token = localStorage.getItem("token");
    try {
      setImporting(true);
      const response = await axios.post(`${API}/discord/import-members`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message);
      await fetchDiscordMembers(); // Refresh the list
    } catch (error) {
      toast.error("Failed to import Discord members");
      console.error("Import error:", error);
    } finally {
      setImporting(false);
    }
  };

  const [syncing, setSyncing] = useState(false);
  
  const handleSyncMembers = async () => {
    const token = localStorage.getItem("token");
    try {
      setSyncing(true);
      const response = await axios.post(`${API}/discord/sync-members`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = response.data;
      toast.success(`Synced! Removed ${data.removed} stale members. Now ${data.database_count} members.`);
      await fetchDiscordMembers(); // Refresh the list
      await fetchAnalytics(); // Refresh analytics
    } catch (error) {
      toast.error("Failed to sync Discord members");
      console.error("Sync error:", error);
    } finally {
      setSyncing(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds || seconds === 0) return "0m";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${secs > 0 ? `${secs}s` : ''}`.trim();
    }
    return `${secs}s`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Loading Discord Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-8">
        {/* Header */}
        <div className="mb-4 sm:mb-6">
          {/* Back Button - Full Width on Mobile */}
          <Button
            onClick={() => navigate("/users")}
            variant="ghost"
            size="sm"
            className="text-slate-300 hover:text-white mb-3 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to User Management
          </Button>
          
          {/* Title and Actions */}
          <div className="flex flex-col gap-4 mb-4 sm:mb-6">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-white">Discord Analytics</h1>
              <p className="text-sm text-slate-400">30-day activity overview</p>
            </div>
            
            {/* Action Buttons - Stack on mobile, inline on tablet+ */}
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={fetchDiscordMembers}
                variant="outline"
                size="sm"
                disabled={refreshing}
                className="flex items-center gap-2 flex-1 sm:flex-none min-w-[100px] justify-center"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                <span className="hidden xs:inline">Refresh</span>
                <span className="xs:hidden">Refresh</span>
              </Button>
              <Button
                onClick={handleSyncMembers}
                variant="outline"
                size="sm"
                disabled={syncing}
                className="flex items-center gap-2 flex-1 sm:flex-none min-w-[100px] justify-center border-yellow-600 text-yellow-400 hover:bg-yellow-600 hover:text-white"
              >
                <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                <span>{syncing ? "Syncing..." : "Sync"}</span>
              </Button>
              <Button
                onClick={handleImportMembers}
                variant="default"
                size="sm"
                disabled={importing}
                className="flex items-center gap-2 w-full sm:w-auto justify-center bg-blue-600 hover:bg-blue-700 mt-1 sm:mt-0"
              >
                <Users className="w-4 h-4" />
                <span>{importing ? "Importing..." : "Import & Link"}</span>
              </Button>
            </div>
          </div>

          {/* Overview Cards - 2 cols on mobile, 4 on desktop */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-4 sm:mb-6">
            <Card 
              className="bg-slate-800 border-slate-700 cursor-pointer hover:bg-slate-700 transition-colors"
              onClick={openLinkedMembersDialog}
            >
              <CardHeader className="p-3 sm:pb-3 sm:pt-4 sm:px-4">
                <CardTitle className="text-xs sm:text-sm font-medium text-slate-300 flex items-center gap-1.5 sm:gap-2">
                  <Users className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                  <span className="truncate">Total Members</span>
                </CardTitle>
                <span className="text-[10px] sm:text-xs text-blue-400 block mt-1">Click to view</span>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-4 sm:pt-0">
                <div className="text-2xl sm:text-3xl font-bold text-white">
                  {analytics?.total_members || 0}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:pb-3 sm:pt-4 sm:px-4">
                <CardTitle className="text-xs sm:text-sm font-medium text-slate-300 flex items-center gap-1.5 sm:gap-2">
                  <Volume2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                  <span className="truncate">Voice Sessions</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-4 sm:pt-0">
                <div className="text-2xl sm:text-3xl font-bold text-white">
                  {analytics?.voice_stats?.total_sessions || 0}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:pb-3 sm:pt-4 sm:px-4">
                <CardTitle className="text-xs sm:text-sm font-medium text-slate-300 flex items-center gap-1.5 sm:gap-2">
                  <MessageSquare className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                  <span className="truncate">Text Messages</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-4 sm:pt-0">
                <div className="text-2xl sm:text-3xl font-bold text-white">
                  {analytics?.text_stats?.total_messages || 0}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:pb-3 sm:pt-4 sm:px-4">
                <CardTitle className="text-xs sm:text-sm font-medium text-slate-300 flex items-center gap-1.5 sm:gap-2">
                  <TrendingUp className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                  <span className="truncate">Daily Average</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-4 sm:pt-0">
                <div className="text-2xl sm:text-3xl font-bold text-white">
                  {analytics?.voice_stats?.total_sessions ? (analytics.voice_stats.total_sessions / 30).toFixed(1) : 0}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Analytics Content */}
        <Tabs defaultValue="voice" className="w-full">
          <TabsList className="w-full bg-slate-800 overflow-x-auto flex justify-start sm:grid sm:grid-cols-4 gap-0 p-1 rounded-lg">
            <TabsTrigger value="voice" className="flex-shrink-0 px-3 sm:px-4 py-2 text-xs sm:text-sm data-[state=active]:bg-slate-700 text-white whitespace-nowrap">
              Voice Activity
            </TabsTrigger>
            <TabsTrigger value="channels" className="flex-shrink-0 px-3 sm:px-4 py-2 text-xs sm:text-sm data-[state=active]:bg-slate-700 text-white whitespace-nowrap">
              By Channel
            </TabsTrigger>
            <TabsTrigger value="text" className="flex-shrink-0 px-3 sm:px-4 py-2 text-xs sm:text-sm data-[state=active]:bg-slate-700 text-white whitespace-nowrap">
              Text Activity
            </TabsTrigger>
            <TabsTrigger value="inactive" className="flex-shrink-0 px-3 sm:px-4 py-2 text-xs sm:text-sm data-[state=active]:bg-slate-700 text-white whitespace-nowrap">
              Least Active
            </TabsTrigger>
          </TabsList>

          {/* Voice Activity Tab */}
          <TabsContent value="voice" className="space-y-4 mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:p-6">
                <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
                  <Volume2 className="w-4 h-4 sm:w-5 sm:h-5" />
                  Top Voice Chat Users (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400 text-xs sm:text-sm">
                  Most active members in voice channels
                </CardDescription>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-6 sm:pt-0">
                {analytics?.top_voice_users?.length > 0 ? (
                  <div className="space-y-2 sm:space-y-3">
                    {analytics.top_voice_users.map((user, index) => (
                      <div key={user._id} className="flex items-center justify-between p-2 sm:p-3 bg-slate-900 rounded-lg">
                        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                          <div className="w-7 h-7 sm:w-8 sm:h-8 bg-blue-600 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold flex-shrink-0">
                            {index + 1}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-medium text-white text-sm sm:text-base truncate">{user.username}</p>
                            <p className="text-xs sm:text-sm text-slate-400">{user.total_sessions} sessions</p>
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0 ml-2">
                          <p className="font-medium text-white text-sm sm:text-base">{formatDuration(user.total_duration)}</p>
                          <p className="text-xs sm:text-sm text-slate-400">total time</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8 text-sm">No voice activity recorded yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* By Channel Tab */}
          <TabsContent value="channels" className="space-y-4 mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:p-6">
                <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
                  <Volume2 className="w-4 h-4 sm:w-5 sm:h-5" />
                  Top Users By Channel (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400 text-xs sm:text-sm">
                  Most active members in each voice channel
                </CardDescription>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-6 sm:pt-0">
                {analytics?.channel_stats?.length > 0 ? (
                  <div className="space-y-3 sm:space-y-4 max-h-[500px] overflow-y-auto">
                    {analytics.channel_stats.map((channel) => (
                      <div key={channel.channel_id} className="p-3 sm:p-4 bg-slate-900 rounded-lg">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-0 mb-3">
                          <h3 className="font-medium text-white flex items-center gap-2 text-sm sm:text-base">
                            <Volume2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-400 flex-shrink-0" />
                            <span className="truncate">{channel.channel_name}</span>
                          </h3>
                          <div className="text-xs sm:text-sm text-slate-400 pl-5 sm:pl-0">
                            <span>{channel.total_sessions} sessions</span>
                            <span className="mx-1 sm:mx-2">•</span>
                            <span className="text-blue-400">{formatDuration(channel.total_duration)}</span>
                          </div>
                        </div>
                        {channel.top_users?.length > 0 ? (
                          <div className="space-y-1.5 sm:space-y-2">
                            {channel.top_users.map((user, index) => (
                              <div key={user.user_id} className="flex items-center justify-between py-1.5 sm:py-2 px-2 sm:px-3 bg-slate-800 rounded text-xs sm:text-sm">
                                <div className="flex items-center gap-2 min-w-0 flex-1">
                                  <span className="text-slate-500 w-4 flex-shrink-0">{index + 1}.</span>
                                  <span className="text-white truncate">{user.username}</span>
                                </div>
                                <div className="text-slate-400 flex-shrink-0 ml-2">
                                  <span className="hidden sm:inline">{user.sessions} sessions • </span>
                                  <span className="sm:hidden">{user.sessions}s • </span>
                                  {formatDuration(user.duration)}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs sm:text-sm text-slate-500">No activity</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8 text-sm">No channel activity recorded yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Text Activity Tab */}
          <TabsContent value="text" className="space-y-4 mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:p-6">
                <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
                  <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5" />
                  Top Text Chat Users (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400 text-xs sm:text-sm">
                  Most active members in text channels
                </CardDescription>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-6 sm:pt-0">
                {analytics?.top_text_users?.length > 0 ? (
                  <div className="space-y-2 sm:space-y-3">
                    {analytics.top_text_users.map((user, index) => (
                      <div key={user._id} className="flex items-center justify-between p-2 sm:p-3 bg-slate-900 rounded-lg">
                        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                          <div className="w-7 h-7 sm:w-8 sm:h-8 bg-green-600 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold flex-shrink-0">
                            {index + 1}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-medium text-white text-sm sm:text-base truncate">{user.username}</p>
                            <p className="text-xs text-slate-400 truncate">ID: {user._id.substring(0, 8)}...</p>
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0 ml-2">
                          <p className="font-medium text-white text-sm sm:text-base">{user.total_messages}</p>
                          <p className="text-xs sm:text-sm text-slate-400">messages</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8 text-sm">No text activity recorded yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Least Active Members Tab */}
          <TabsContent value="inactive" className="space-y-4 mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:p-6">
                <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
                  <Users className="w-4 h-4 sm:w-5 sm:h-5 text-orange-500" />
                  Least Active Members (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400 text-xs sm:text-sm">
                  Members with no voice or text activity - may need engagement
                </CardDescription>
              </CardHeader>
              <CardContent className="p-3 pt-0 sm:p-6 sm:pt-0">
                {/* Engagement Overview */}
                {analytics?.engagement_stats && (
                  <div className="bg-slate-900 rounded-lg p-3 sm:p-4 mb-4">
                    <h4 className="text-white font-medium mb-2 sm:mb-3 text-sm sm:text-base">Engagement Overview</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 text-xs sm:text-sm">
                      <div className="text-center p-2 sm:p-0">
                        <div className="text-xl sm:text-2xl font-bold text-green-400">
                          {analytics.engagement_stats.engagement_rate}%
                        </div>
                        <div className="text-slate-400 text-[10px] sm:text-sm">Engagement</div>
                      </div>
                      <div className="text-center p-2 sm:p-0">
                        <div className="text-xl sm:text-2xl font-bold text-blue-400">
                          {analytics.engagement_stats.voice_active_members}
                        </div>
                        <div className="text-slate-400 text-[10px] sm:text-sm">Voice Active</div>
                      </div>
                      <div className="text-center p-2 sm:p-0">
                        <div className="text-xl sm:text-2xl font-bold text-green-400">
                          {analytics.engagement_stats.text_active_members}
                        </div>
                        <div className="text-slate-400 text-[10px] sm:text-sm">Text Active</div>
                      </div>
                      <div className="text-center p-2 sm:p-0">
                        <div className="text-xl sm:text-2xl font-bold text-orange-400">
                          {analytics.engagement_stats.inactive_members}
                        </div>
                        <div className="text-slate-400 text-[10px] sm:text-sm">Inactive</div>
                      </div>
                    </div>
                  </div>
                )}

                {analytics?.least_active_members?.length > 0 ? (
                  <div className="space-y-2 sm:space-y-3">
                    {analytics.least_active_members.map((member, index) => (
                      <div key={member.discord_id} className="flex items-center justify-between p-2 sm:p-3 bg-slate-900 rounded-lg border-l-4 border-orange-500">
                        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                          <div className="w-7 h-7 sm:w-8 sm:h-8 bg-orange-500 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold flex-shrink-0">
                            {index + 1}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-medium text-white text-sm sm:text-base truncate">{member.display_name}</p>
                            <p className="text-xs sm:text-sm text-slate-400 truncate">@{member.username}</p>
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0 ml-2">
                          <div className="flex gap-1 sm:gap-2 flex-wrap justify-end">
                            <span className="px-1.5 sm:px-2 py-0.5 sm:py-1 bg-red-600 text-white text-[10px] sm:text-xs rounded">
                              No Voice
                            </span>
                            <span className="px-1.5 sm:px-2 py-0.5 sm:py-1 bg-red-600 text-white text-[10px] sm:text-xs rounded">
                              No Text
                            </span>
                          </div>
                          <p className="text-[10px] sm:text-sm text-slate-400 mt-1 hidden sm:block">No activity in 30 days</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 sm:py-8">
                    <div className="w-12 h-12 sm:w-16 sm:h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
                      <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
                    </div>
                    <p className="text-green-400 font-medium text-sm sm:text-base">Excellent Engagement!</p>
                    <p className="text-slate-400 text-xs sm:text-sm">All members have been active in voice or text chat</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Link Member Dialog */}
      <Dialog open={linkDialogOpen} onOpenChange={setLinkDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">
              Link Discord Member
            </DialogTitle>
          </DialogHeader>
          
          {selectedDiscordMember && (
            <div className="space-y-4">
              <div className="p-3 bg-slate-900 rounded-lg">
                <p className="text-sm text-slate-400">Discord User:</p>
                <p className="text-white font-medium">
                  {selectedDiscordMember.display_name || selectedDiscordMember.username}
                </p>
                <p className="text-sm text-slate-400">@{selectedDiscordMember.username}</p>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm text-slate-300">Search Database Members:</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    value={memberSearch}
                    onChange={(e) => setMemberSearch(e.target.value)}
                    placeholder="Search by handle, name, or chapter..."
                    className="pl-9 bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm text-slate-300">Select Member to Link:</label>
                <Select value={selectedMemberId} onValueChange={setSelectedMemberId}>
                  <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                    <SelectValue placeholder="Select a member..." />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700 max-h-60">
                    {filteredDatabaseMembers.map((member) => (
                      <SelectItem 
                        key={member.id} 
                        value={member.id}
                        className="text-white hover:bg-slate-700"
                      >
                        {member.handle} - {member.name} ({member.chapter})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex gap-3 justify-end pt-4">
                <Button
                  variant="outline"
                  onClick={() => setLinkDialogOpen(false)}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleLinkMember}
                  disabled={!selectedMemberId}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <Link className="w-4 h-4 mr-2" />
                  Link Member
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Linked Members Dialog */}
      <Dialog open={linkedMembersDialogOpen} onOpenChange={setLinkedMembersDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Users className="w-5 h-5" />
              Linked Members ({linkedMembers.length})
            </DialogTitle>
            <p className="text-xs text-slate-400">All times shown in Central Time (CST)</p>
          </DialogHeader>
          
          <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                value={linkedMemberSearch}
                onChange={(e) => setLinkedMemberSearch(e.target.value)}
                placeholder="Search by name, handle, or Discord username..."
                className="pl-9 bg-slate-700 border-slate-600 text-white"
              />
            </div>
            
            {/* Members List */}
            <div className="flex-1 overflow-y-auto space-y-2">
              {loadingLinkedMembers ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-400 mx-auto mb-2" />
                  <p className="text-slate-400">Loading linked members...</p>
                </div>
              ) : filteredLinkedMembers.length > 0 ? (
                filteredLinkedMembers.map((member) => (
                  <div key={member.discord_id} className="p-3 bg-slate-900 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        {member.avatar_url ? (
                          <img 
                            src={member.avatar_url} 
                            alt={member.discord_username}
                            className="w-10 h-10 rounded-full flex-shrink-0"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-slate-600 rounded-full flex items-center justify-center flex-shrink-0">
                            <Users className="w-5 h-5" />
                          </div>
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-white truncate">
                            {member.member_handle || member.member_name}
                          </p>
                          <p className="text-sm text-slate-400 truncate">
                            {member.member_chapter} • {member.member_title}
                          </p>
                          <p className="text-xs text-slate-500 truncate">
                            Discord: @{member.discord_username}
                          </p>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0 ml-3 space-y-1">
                        <div className="flex items-center justify-end gap-2">
                          <span className="text-xs">🎤</span>
                          <span className={`text-sm ${member.last_voice_time ? 'text-green-400' : 'text-slate-500'}`}>
                            {formatLastActivity(member.last_voice_time)}
                          </span>
                        </div>
                        {member.last_voice_channel && (
                          <p className="text-xs text-slate-500 truncate max-w-[120px]">{member.last_voice_channel}</p>
                        )}
                        <div className="flex items-center justify-end gap-2 pt-1">
                          <span className="text-xs">💬</span>
                          <span className={`text-sm ${member.last_text_time ? 'text-green-400' : 'text-slate-500'}`}>
                            {formatLastActivity(member.last_text_time)}
                          </span>
                        </div>
                        {member.last_text_channel && (
                          <p className="text-xs text-slate-500 truncate max-w-[120px]">{member.last_text_channel}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-slate-400">No linked members found</p>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}