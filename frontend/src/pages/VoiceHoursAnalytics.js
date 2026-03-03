import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { ArrowLeft, Clock, Calendar, Users, Search, ChevronDown, ChevronUp } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function VoiceHoursAnalytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedMembers, setExpandedMembers] = useState({});
  const [sortBy, setSortBy] = useState("hours"); // "hours" or "name"
  const navigate = useNavigate();

  const months = [
    { value: 1, label: "January" },
    { value: 2, label: "February" },
    { value: 3, label: "March" },
    { value: 4, label: "April" },
    { value: 5, label: "May" },
    { value: 6, label: "June" },
    { value: 7, label: "July" },
    { value: 8, label: "August" },
    { value: 9, label: "September" },
    { value: 10, label: "October" },
    { value: 11, label: "November" },
    { value: 12, label: "December" }
  ];

  const years = [];
  const currentYear = new Date().getFullYear();
  for (let y = currentYear; y >= currentYear - 2; y--) {
    years.push(y);
  }

  useEffect(() => {
    fetchVoiceHours();
  }, [selectedMonth, selectedYear]);

  const fetchVoiceHours = async () => {
    setLoading(true);
    const token = localStorage.getItem("token");
    try {
      const response = await axios.get(
        `${API}/discord/voice-hours?month=${selectedMonth}&year=${selectedYear}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setData(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to load voice hours data");
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (discordId) => {
    setExpandedMembers(prev => ({
      ...prev,
      [discordId]: !prev[discordId]
    }));
  };

  const formatHours = (hours) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`;
    }
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  const filteredMembers = data?.members?.filter(member => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      member.display_name?.toLowerCase().includes(query) ||
      member.username?.toLowerCase().includes(query) ||
      member.linked_member_handle?.toLowerCase().includes(query)
    );
  }) || [];

  const sortedMembers = [...filteredMembers].sort((a, b) => {
    if (sortBy === "hours") {
      return b.monthly_total_hours - a.monthly_total_hours;
    }
    return (a.display_name || a.username).localeCompare(b.display_name || b.username);
  });

  const totalHours = data?.members?.reduce((sum, m) => sum + m.monthly_total_hours, 0) || 0;

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4 md:p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/discord-analytics")}
          className="text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Discord Analytics
        </Button>
      </div>

      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3">
              <Clock className="w-8 h-8 text-purple-400" />
              Voice Chat Hours
            </h1>
            <p className="text-slate-400 mt-1">Track daily and monthly voice activity for all members</p>
          </div>

          {/* Month/Year Selector */}
          <div className="flex gap-2">
            <Select value={selectedMonth.toString()} onValueChange={(v) => setSelectedMonth(parseInt(v))}>
              <SelectTrigger className="w-[140px] bg-slate-800 border-slate-600">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {months.map(m => (
                  <SelectItem key={m.value} value={m.value.toString()}>{m.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
              <SelectTrigger className="w-[100px] bg-slate-800 border-slate-600">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {years.map(y => (
                  <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-purple-500/20 rounded-lg">
                  <Clock className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Total Hours</p>
                  <p className="text-2xl font-bold text-white">{formatHours(totalHours)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-500/20 rounded-lg">
                  <Users className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Active Members</p>
                  <p className="text-2xl font-bold text-white">{data?.total_members_with_activity || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-green-500/20 rounded-lg">
                  <Calendar className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Days in Month</p>
                  <p className="text-2xl font-bold text-white">{data?.days_in_month || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Sort */}
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search by name or handle..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-slate-800 border-slate-600 text-white"
            />
          </div>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-[160px] bg-slate-800 border-slate-600">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="hours">Sort by Hours</SelectItem>
              <SelectItem value="name">Sort by Name</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Members List */}
        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading voice hours data...</div>
        ) : sortedMembers.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            {searchQuery ? "No members found matching your search" : "No voice activity recorded for this month"}
          </div>
        ) : (
          <div className="space-y-2">
            {sortedMembers.map((member, index) => (
              <Card 
                key={member.discord_id} 
                className="bg-slate-800 border-slate-700 overflow-hidden"
              >
                <div 
                  className="p-4 cursor-pointer hover:bg-slate-700/50 transition-colors"
                  onClick={() => toggleExpand(member.discord_id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 flex items-center justify-center bg-slate-700 rounded-full text-sm font-bold text-slate-300">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium text-white">
                          {member.linked_member_handle || member.display_name || member.username}
                        </div>
                        {member.linked_member_handle && (
                          <div className="text-xs text-slate-400">
                            Discord: {member.display_name || member.username}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-lg font-bold text-purple-400">
                          {formatHours(member.monthly_total_hours)}
                        </div>
                        <div className="text-xs text-slate-400">
                          {member.days_active} day{member.days_active !== 1 ? 's' : ''} active
                        </div>
                      </div>
                      {expandedMembers[member.discord_id] ? (
                        <ChevronUp className="w-5 h-5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-slate-400" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Daily Breakdown (Expanded) */}
                {expandedMembers[member.discord_id] && (
                  <div className="border-t border-slate-700 bg-slate-850 p-4">
                    <h4 className="text-sm font-medium text-slate-300 mb-3">Daily Breakdown</h4>
                    {member.daily_breakdown.length === 0 ? (
                      <p className="text-slate-400 text-sm">No daily data available</p>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
                        {member.daily_breakdown.map((day) => {
                          const date = new Date(day.date + 'T00:00:00');
                          const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
                          const dayNum = date.getDate();
                          return (
                            <div 
                              key={day.date}
                              className="bg-slate-700/50 rounded-lg p-2 text-center"
                            >
                              <div className="text-xs text-slate-400">{dayName}</div>
                              <div className="text-sm font-medium text-white">{dayNum}</div>
                              <div className="text-sm font-bold text-purple-400 mt-1">
                                {formatHours(day.hours)}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
