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
    const search = linkedMemberSearch.toLowerCase();
    return (
      m.member_handle?.toLowerCase().includes(search) ||
      m.member_name?.toLowerCase().includes(search) ||
      m.discord_display_name?.toLowerCase().includes(search) ||
      m.discord_username?.toLowerCase().includes(search)
    );
  });

  const formatLastActivity = (dateStr) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
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

  const formatDuration = (seconds) => {
    if (!seconds) return "0m";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div className="flex items-center gap-3">
              <Button
                onClick={() => navigate("/users")}
                variant="ghost"
                size="sm"
                className="text-slate-300 hover:text-white"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to User Management
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-white">Discord Analytics</h1>
                <p className="text-slate-400">30-day activity overview</p>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                onClick={fetchDiscordMembers}
                variant="outline"
                size="sm"
                disabled={refreshing}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                onClick={handleImportMembers}
                variant="default"
                size="sm"
                disabled={importing}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
              >
                <Users className="w-4 h-4" />
                {importing ? "Importing..." : "Import & Link Members"}
              </Button>
            </div>
          </div>

          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card 
              className="bg-slate-800 border-slate-700 cursor-pointer hover:bg-slate-700 transition-colors"
              onClick={openLinkedMembersDialog}
            >
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Total Members
                  <span className="text-xs text-blue-400 ml-auto">Click to view</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {analytics?.total_members || 0}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Volume2 className="w-4 h-4" />
                  Voice Sessions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {analytics?.voice_stats?.total_sessions || 0}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Text Messages
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {analytics?.text_stats?.total_messages || 0}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Daily Average
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {analytics?.voice_stats?.total_sessions ? (analytics.voice_stats.total_sessions / 30).toFixed(1) : 0}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Analytics Content */}
        <Tabs defaultValue="voice" className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-slate-800">
            <TabsTrigger value="voice" className="data-[state=active]:bg-slate-700 text-white">
              Voice Activity
            </TabsTrigger>
            <TabsTrigger value="channels" className="data-[state=active]:bg-slate-700 text-white">
              By Channel
            </TabsTrigger>
            <TabsTrigger value="text" className="data-[state=active]:bg-slate-700 text-white">
              Text Activity
            </TabsTrigger>
            <TabsTrigger value="inactive" className="data-[state=active]:bg-slate-700 text-white">
              Least Active
            </TabsTrigger>
            <TabsTrigger value="members" className="data-[state=active]:bg-slate-700 text-white">
              Members
            </TabsTrigger>
          </TabsList>

          {/* Voice Activity Tab */}
          <TabsContent value="voice" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Volume2 className="w-5 h-5" />
                  Top Voice Chat Users (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Most active members in voice channels
                </CardDescription>
              </CardHeader>
              <CardContent>
                {analytics?.top_voice_users?.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.top_voice_users.map((user, index) => (
                      <div key={user._id} className="flex items-center justify-between p-3 bg-slate-900 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-white">{user.username}</p>
                            <p className="text-sm text-slate-400">{user.total_sessions} sessions</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-white">{formatDuration(user.total_duration)}</p>
                          <p className="text-sm text-slate-400">total time</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8">No voice activity recorded yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* By Channel Tab */}
          <TabsContent value="channels" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Volume2 className="w-5 h-5" />
                  Top Users By Channel (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Most active members in each voice channel
                </CardDescription>
              </CardHeader>
              <CardContent>
                {analytics?.channel_stats?.length > 0 ? (
                  <div className="space-y-4 max-h-[500px] overflow-y-auto">
                    {analytics.channel_stats.map((channel) => (
                      <div key={channel.channel_id} className="p-4 bg-slate-900 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-medium text-white flex items-center gap-2">
                            <Volume2 className="w-4 h-4 text-blue-400" />
                            {channel.channel_name}
                          </h3>
                          <div className="text-right text-sm">
                            <span className="text-slate-400">{channel.total_sessions} sessions</span>
                            <span className="text-slate-500 mx-2">•</span>
                            <span className="text-blue-400">{formatDuration(channel.total_duration)}</span>
                          </div>
                        </div>
                        {channel.top_users?.length > 0 ? (
                          <div className="space-y-2">
                            {channel.top_users.map((user, index) => (
                              <div key={user.user_id} className="flex items-center justify-between py-2 px-3 bg-slate-800 rounded">
                                <div className="flex items-center gap-2">
                                  <span className="text-xs text-slate-500 w-4">{index + 1}.</span>
                                  <span className="text-sm text-white">{user.username}</span>
                                </div>
                                <div className="text-sm text-slate-400">
                                  {user.sessions} sessions • {formatDuration(user.duration)}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500">No activity</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8">No channel activity recorded yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Text Activity Tab */}
          <TabsContent value="text" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Top Text Chat Users (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Most active members in text channels
                </CardDescription>
              </CardHeader>
              <CardContent>
                {analytics?.top_text_users?.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.top_text_users.map((user, index) => (
                      <div key={user._id} className="flex items-center justify-between p-3 bg-slate-900 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-sm font-bold">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-white">{user.username}</p>
                            <p className="text-sm text-slate-400">User ID: {user._id.substring(0, 8)}...</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-white">{user.total_messages}</p>
                          <p className="text-sm text-slate-400">messages</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8">No text activity recorded yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Least Active Members Tab */}
          <TabsContent value="inactive" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Users className="w-5 h-5 text-orange-500" />
                  Least Active Members (30 days)
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Members with no voice or text activity - may need engagement
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Engagement Overview */}
                {analytics?.engagement_stats && (
                  <div className="bg-slate-900 rounded-lg p-4 mb-4">
                    <h4 className="text-white font-medium mb-3">Engagement Overview</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">
                          {analytics.engagement_stats.engagement_rate}%
                        </div>
                        <div className="text-slate-400">Engagement Rate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">
                          {analytics.engagement_stats.voice_active_members}
                        </div>
                        <div className="text-slate-400">Voice Active</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">
                          {analytics.engagement_stats.text_active_members}
                        </div>
                        <div className="text-slate-400">Text Active</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-400">
                          {analytics.engagement_stats.inactive_members}
                        </div>
                        <div className="text-slate-400">Inactive</div>
                      </div>
                    </div>
                  </div>
                )}

                {analytics?.least_active_members?.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.least_active_members.map((member, index) => (
                      <div key={member.discord_id} className="flex items-center justify-between p-3 bg-slate-900 rounded-lg border-l-4 border-orange-500">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-sm font-bold">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-white">{member.display_name}</p>
                            <p className="text-sm text-slate-400">@{member.username}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex gap-2">
                            <span className="px-2 py-1 bg-red-600 text-white text-xs rounded">
                              No Voice
                            </span>
                            <span className="px-2 py-1 bg-red-600 text-white text-xs rounded">
                              No Text
                            </span>
                          </div>
                          <p className="text-sm text-slate-400 mt-1">No activity in 30 days</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                      <TrendingUp className="w-8 h-8 text-white" />
                    </div>
                    <p className="text-green-400 font-medium">Excellent Engagement!</p>
                    <p className="text-slate-400">All members have been active in voice or text chat</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Members Tab */}
          <TabsContent value="members" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Discord Members ({filteredDiscordMembers.length})
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Server members and their connection status. Click Link/Unlink to manage connections.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {filteredDiscordMembers.length > 0 ? (
                  <div className="space-y-2 max-h-[500px] overflow-y-auto">
                    {filteredDiscordMembers.map((member) => (
                      <div key={member.discord_id} className="p-3 bg-slate-900 rounded-lg">
                        {/* Top row: Avatar, Name, Status */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            {member.avatar_url ? (
                              <img 
                                src={member.avatar_url} 
                                alt={member.username}
                                className="w-8 h-8 rounded-full flex-shrink-0"
                              />
                            ) : (
                              <div className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center flex-shrink-0">
                                <Users className="w-4 h-4" />
                              </div>
                            )}
                            <div className="min-w-0 flex-1">
                              <p className="font-medium text-white text-sm truncate">
                                {member.display_name || member.username}
                              </p>
                              <p className="text-xs text-slate-400 truncate">@{member.username}</p>
                            </div>
                          </div>
                          
                          {/* Status badge */}
                          <div className="flex-shrink-0 ml-2">
                            {member.is_bot ? (
                              <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">Bot</span>
                            ) : member.member_id ? (
                              <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">Linked</span>
                            ) : (
                              <span className="px-2 py-1 bg-slate-600 text-slate-300 text-xs rounded">Unlinked</span>
                            )}
                          </div>
                        </div>
                        
                        {/* Bottom row: Linked info + Action button */}
                        {!member.is_bot && (
                          <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-700">
                            <div className="text-xs text-slate-400 truncate flex-1 mr-2">
                              {member.member_id && member.linked_member ? (
                                <span className="text-green-400">→ {member.linked_member.handle}</span>
                              ) : (
                                <span>Not linked to database</span>
                              )}
                            </div>
                            {member.member_id ? (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleUnlinkMember(member.discord_id)}
                                className="border-red-600 text-red-400 hover:bg-red-600 hover:text-white h-7 px-2 text-xs"
                              >
                                <Unlink className="w-3 h-3 sm:mr-1" />
                                <span className="hidden sm:inline">Unlink</span>
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openLinkDialog(member)}
                                className="border-green-600 text-green-400 hover:bg-green-600 hover:text-white h-7 px-2 text-xs"
                              >
                                <Link className="w-3 h-3 sm:mr-1" />
                                <span className="hidden sm:inline">Link</span>
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8">No Discord members found. Click "Refresh" to load members.</p>
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
    </div>
  );
}