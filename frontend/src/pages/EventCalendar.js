import { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Checkbox } from "../components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Calendar, Plus, Edit, Trash2, MapPin, Clock, Users, Filter, Send, Hash, ChevronLeft, ChevronRight, Cake, Award, CalendarDays, Repeat } from "lucide-react";
import PageLayout from "@/components/PageLayout";

const API = process.env.REACT_APP_BACKEND_URL || "";

export default function EventCalendar({ userRole }) {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  
  // Calendar state
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [birthdays, setBirthdays] = useState([]);
  const [anniversaries, setAnniversaries] = useState([]);
  const [selectedDateItems, setSelectedDateItems] = useState(null);
  const [dateDialogOpen, setDateDialogOpen] = useState(false);
  
  // Discord channel state
  const [availableChannels, setAvailableChannels] = useState([]);
  const [canSchedule, setCanSchedule] = useState(false);
  
  const [chapterFilter, setChapterFilter] = useState("");
  const [titleFilter, setTitleFilter] = useState("");
  
  // Check if user is admin (can create/edit events)
  const isAdmin = userRole === 'admin';

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    date: "",
    time: "",
    location: "",
    chapter: "all",
    title_filter: "all",
    discord_notifications_enabled: true,
    discord_channel: "member-chat",
    repeat_type: "none",
    repeat_interval: 1,
    repeat_end_date: "",
    repeat_count: "",
    repeat_days: [],
  });

  const [editFormData, setEditFormData] = useState({
    title: "",
    description: "",
    date: "",
    time: "",
    location: "",
    chapter: "all",
    title_filter: "all",
    discord_notifications_enabled: true,
    discord_channel: "member-chat",
  });

  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  useEffect(() => {
    fetchEvents();
    fetchDiscordChannels();
  }, []);

  // Fetch birthdays and anniversaries when month changes
  useEffect(() => {
    fetchBirthdays();
    fetchAnniversaries();
  }, [currentMonth]);

  useEffect(() => {
    applyFilters();
  }, [events, chapterFilter, titleFilter]);

  const fetchEvents = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/api/events`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEvents(response.data);
    } catch (error) {
      toast.error("Failed to load events");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDiscordChannels = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/api/events/discord-channels`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAvailableChannels(response.data.channels || []);
      setCanSchedule(response.data.can_schedule || false);
    } catch (error) {
      console.error("Failed to fetch Discord channels:", error);
      setAvailableChannels([]);
      setCanSchedule(false);
    }
  };

  const fetchBirthdays = async () => {
    try {
      const token = localStorage.getItem("token");
      const month = currentMonth.getMonth() + 1;
      const year = currentMonth.getFullYear();
      const response = await axios.get(`${API}/api/birthdays/monthly?month=${month}&year=${year}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setBirthdays(response.data.members || []);
    } catch (error) {
      console.error("Failed to fetch birthdays:", error);
    }
  };

  const fetchAnniversaries = async () => {
    try {
      const token = localStorage.getItem("token");
      const month = currentMonth.getMonth() + 1;
      const year = currentMonth.getFullYear();
      const response = await axios.get(`${API}/api/anniversaries/monthly?month=${month}&year=${year}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAnniversaries(response.data.members || []);
    } catch (error) {
      console.error("Failed to fetch anniversaries:", error);
    }
  };

  // Calendar helper functions
  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const formatMonthYear = (date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  const getItemsForDate = (day) => {
    const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const items = { events: [], birthdays: [], anniversaries: [] };
    
    // Check events
    events.forEach(event => {
      if (event.date === dateStr) {
        items.events.push(event);
      }
    });
    
    // Check birthdays (compare full date from API)
    birthdays.forEach(bday => {
      if (bday.birthday_date === dateStr) {
        items.birthdays.push(bday);
      }
    });
    
    // Check anniversaries (show on first day of the month)
    anniversaries.forEach(anniv => {
      if (day === 1) {
        items.anniversaries.push(anniv);
      }
    });
    
    return items;
  };

  const handleDateClick = (day) => {
    const items = getItemsForDate(day);
    if (items.events.length > 0 || items.birthdays.length > 0 || items.anniversaries.length > 0) {
      const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      setSelectedDateItems({ date: dateStr, ...items });
      setDateDialogOpen(true);
    }
  };

  const applyFilters = () => {
    let filtered = [...events];

    if (chapterFilter) {
      filtered = filtered.filter(
        (event) => event.chapter === chapterFilter || event.chapter === null
      );
    }

    if (titleFilter) {
      filtered = filtered.filter(
        (event) => event.title_filter === titleFilter || event.title_filter === null
      );
    }

    setFilteredEvents(filtered);
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      date: "",
      time: "",
      location: "",
      chapter: "all",
      title_filter: "all",
      discord_notifications_enabled: true,
      discord_channel: availableChannels.length > 0 ? availableChannels[0].id : "member-chat",
      repeat_type: "none",
      repeat_interval: 1,
      repeat_end_date: "",
      repeat_count: "",
      repeat_days: [],
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    // Convert "all" to null for API
    const apiData = {
      ...formData,
      chapter: formData.chapter === "all" ? null : formData.chapter,
      title_filter: formData.title_filter === "all" ? null : formData.title_filter,
      repeat_type: formData.repeat_type === "none" ? null : formData.repeat_type,
      repeat_interval: formData.repeat_interval || 1,
      repeat_end_date: formData.repeat_end_date || null,
      repeat_count: formData.repeat_count ? parseInt(formData.repeat_count) : null,
      repeat_days: formData.repeat_days.length > 0 ? formData.repeat_days : null,
    };

    try {
      const response = await axios.post(`${API}/api/events`, apiData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const occurrences = response.data.occurrences || 1;
      toast.success(occurrences > 1 
        ? `Recurring event created (${occurrences} occurrences)` 
        : "Event created successfully"
      );
      setDialogOpen(false);
      resetForm();
      fetchEvents();
    } catch (error){
      toast.error(error.response?.data?.detail || "Failed to create event");
    }
  };

  const handleEdit = (event, e) => {
    e.stopPropagation(); // Prevent row click when clicking edit button
    setEditingEvent(event);
    setEditFormData({
      title: event.title,
      description: event.description || "",
      date: event.date,
      time: event.time || "",
      location: event.location || "",
      chapter: event.chapter || "all",
      title_filter: event.title_filter || "all",
      discord_notifications_enabled: event.discord_notifications_enabled !== false,
      discord_channel: event.discord_channel || "member-chat",
    });
    setEditDialogOpen(true);
  };

  const handleViewDetails = (event) => {
    setSelectedEvent(event);
    setDetailDialogOpen(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    // Convert "all" to null for API
    const apiData = {
      ...editFormData,
      chapter: editFormData.chapter === "all" ? null : editFormData.chapter,
      title_filter: editFormData.title_filter === "all" ? null : editFormData.title_filter,
    };

    try {
      await axios.put(`${API}/api/events/${editingEvent.id}`, apiData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Event updated successfully");
      setEditDialogOpen(false);
      setEditingEvent(null);
      fetchEvents();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update event");
    }
  };

  const handleDelete = async (eventId, eventTitle, e) => {
    e.stopPropagation(); // Prevent row click when clicking delete button
    if (!window.confirm(`Are you sure you want to delete "${eventTitle}"?`)) {
      return;
    }

    const token = localStorage.getItem("token");
    try {
      await axios.delete(`${API}/api/events/${eventId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Event deleted successfully");
      fetchEvents();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete event");
    }
  };

  const handleSendDiscordNow = async (event, e) => {
    e.stopPropagation(); // Prevent row click
    
    if (!event.discord_notifications_enabled) {
      toast.error("Discord notifications are disabled for this event");
      return;
    }

    if (!window.confirm(`Send Discord notification for "${event.title}" now?`)) {
      return;
    }

    const token = localStorage.getItem("token");
    try {
      await axios.post(`${API}/api/events/${event.id}/send-discord-notification`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Discord notification sent successfully!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send Discord notification");
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      timeZone: 'America/Chicago'
    });
  };

  const isUpcoming = (dateStr) => {
    const eventDate = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return eventDate >= today;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-slate-300">Loading events...</div>
      </div>
    );
  }

  // Render calendar grid
  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(currentMonth);
    const firstDay = getFirstDayOfMonth(currentMonth);
    const days = [];
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    // Day headers
    const dayHeaders = dayNames.map(day => (
      <div key={day} className="text-center text-xs font-medium text-slate-400 py-2">
        {day}
      </div>
    ));
    
    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="p-1 min-h-[60px] sm:min-h-[80px]"></div>);
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const items = getItemsForDate(day);
      const hasItems = items.events.length > 0 || items.birthdays.length > 0 || items.anniversaries.length > 0;
      const isToday = new Date().toDateString() === new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day).toDateString();
      
      days.push(
        <div 
          key={day} 
          onClick={() => handleDateClick(day)}
          className={`p-1 min-h-[60px] sm:min-h-[80px] border border-slate-700 rounded-lg ${
            hasItems ? 'cursor-pointer hover:bg-slate-700/50' : ''
          } ${isToday ? 'bg-blue-900/30 border-blue-500' : 'bg-slate-800/50'}`}
        >
          <div className={`text-xs sm:text-sm font-medium mb-1 ${isToday ? 'text-blue-400' : 'text-slate-300'}`}>
            {day}
          </div>
          <div className="space-y-0.5">
            {items.events.slice(0, 2).map((event, idx) => (
              <div key={`e-${idx}`} className="text-[9px] sm:text-[10px] px-1 py-0.5 bg-green-600/80 text-white rounded truncate">
                📅 {event.title}
              </div>
            ))}
            {items.birthdays.slice(0, 2).map((bday, idx) => (
              <div key={`b-${idx}`} className="text-[9px] sm:text-[10px] px-1 py-0.5 bg-pink-600/80 text-white rounded truncate">
                🎂 {bday.handle} ({bday.chapter}{bday.title ? ` - ${bday.title}` : ''})
              </div>
            ))}
            {items.anniversaries.slice(0, 2).map((anniv, idx) => (
              <div key={`a-${idx}`} className="text-[9px] sm:text-[10px] px-1 py-0.5 bg-purple-600/80 text-white rounded truncate">
                🎉 {anniv.handle} ({anniv.chapter}{anniv.title ? ` - ${anniv.title}` : ''})
              </div>
            ))}
            {(items.events.length + items.birthdays.length + items.anniversaries.length > 2) && (
              <div className="text-[9px] text-slate-400">+more</div>
            )}
          </div>
        </div>
      );
    }
    
    return (
      <div className="bg-slate-800 rounded-lg p-3 sm:p-4 mb-6">
        {/* Calendar Header */}
        <div className="flex items-center justify-between mb-4">
          <Button variant="ghost" size="sm" onClick={prevMonth} className="text-slate-300 hover:text-white">
            <ChevronLeft className="w-5 h-5" />
          </Button>
          <h3 className="text-lg sm:text-xl font-bold text-white">{formatMonthYear(currentMonth)}</h3>
          <Button variant="ghost" size="sm" onClick={nextMonth} className="text-slate-300 hover:text-white">
            <ChevronRight className="w-5 h-5" />
          </Button>
        </div>
        
        {/* Legend */}
        <div className="flex flex-wrap gap-2 sm:gap-4 mb-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-600 rounded"></div>
            <span className="text-slate-400">Events</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-pink-600 rounded"></div>
            <span className="text-slate-400">Birthdays</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-purple-600 rounded"></div>
            <span className="text-slate-400">Anniversaries</span>
          </div>
        </div>
        
        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1">
          {dayHeaders}
          {days}
        </div>
      </div>
    );
  };

  const headerActions = isAdmin ? (
    <>
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-green-600 hover:bg-green-700">
                  <Plus className="w-4 h-4 sm:mr-2" />
                  <span className="hidden sm:inline">Add Event</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="w-[95vw] max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">Create New Event</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-3 sm:space-y-4 mt-3 sm:mt-4">
                  <div>
                    <Label className="text-sm">Event Title *</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) =>
                        setFormData({ ...formData, title: e.target.value })
                      }
                      required
                      className="mt-1 h-10"
                      placeholder="e.g., Chapter Meeting"
                    />
                  </div>

                  <div>
                    <Label className="text-sm">Description</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) =>
                        setFormData({ ...formData, description: e.target.value })
                      }
                      rows={2}
                      className="mt-1"
                      placeholder="Optional event details..."
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    <div>
                      <Label className="text-sm">Date *</Label>
                      <Input
                        type="date"
                        value={formData.date}
                        onChange={(e) =>
                          setFormData({ ...formData, date: e.target.value })
                        }
                        required
                        className="mt-1 h-10"
                      />
                    </div>
                    <div>
                      <Label className="text-sm">Time (CST/CDT)</Label>
                      <Input
                        type="time"
                        value={formData.time}
                        onChange={(e) =>
                          setFormData({ ...formData, time: e.target.value })
                        }
                        className="mt-1 h-10"
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm">Location</Label>
                    <Input
                      value={formData.location}
                      onChange={(e) =>
                        setFormData({ ...formData, location: e.target.value })
                      }
                      className="mt-1 h-10"
                      placeholder="e.g., Discord, City Park"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    <div>
                      <Label className="text-sm">Chapter</Label>
                      <Select
                        value={formData.chapter}
                        onValueChange={(value) =>
                          setFormData({ ...formData, chapter: value })
                        }
                      >
                        <SelectTrigger className="mt-1 h-10">
                          <SelectValue placeholder="All Chapters" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Chapters</SelectItem>
                          <SelectItem value="National">National</SelectItem>
                          <SelectItem value="AD">Asphalt Demons</SelectItem>
                          <SelectItem value="HA">Highway Asylum</SelectItem>
                          <SelectItem value="HS">Highway Souls</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label className="text-sm">Title Filter</Label>
                      <Select
                        value={formData.title_filter}
                        onValueChange={(value) =>
                          setFormData({ ...formData, title_filter: value })
                        }
                      >
                        <SelectTrigger className="mt-1 h-10">
                          <SelectValue placeholder="All Titles" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Titles</SelectItem>
                          <SelectItem value="Prez">Prez</SelectItem>
                          <SelectItem value="VP">VP</SelectItem>
                          <SelectItem value="S@A">S@A</SelectItem>
                          <SelectItem value="Secretary">Secretary</SelectItem>
                          <SelectItem value="Member">Member</SelectItem>
                          <SelectItem value="Prospect">Prospect</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Discord Notifications Toggle */}
                  <div className="flex items-start sm:items-center space-x-2 bg-slate-700/30 p-3 sm:p-4 rounded-lg">
                    <Checkbox
                      id="discord-notifications"
                      checked={formData.discord_notifications_enabled}
                      onCheckedChange={(checked) =>
                        setFormData({ ...formData, discord_notifications_enabled: checked })
                      }
                      className="mt-0.5 sm:mt-0"
                    />
                    <label
                      htmlFor="discord-notifications"
                      className="text-xs sm:text-sm font-medium leading-tight sm:leading-none cursor-pointer"
                    >
                      📢 Send Discord notifications (24h & 3h before)
                    </label>
                  </div>

                  {/* Discord Channel Selector */}
                  {formData.discord_notifications_enabled && availableChannels.length > 0 && (
                    <div className="bg-slate-700/30 p-3 sm:p-4 rounded-lg">
                      <Label className="flex items-center gap-2 mb-2 text-sm">
                        <Hash className="w-4 h-4 text-blue-400" />
                        Discord Channel
                      </Label>
                      <Select
                        value={formData.discord_channel}
                        onValueChange={(value) =>
                          setFormData({ ...formData, discord_channel: value })
                        }
                      >
                        <SelectTrigger className="bg-slate-700 border-slate-600 h-10">
                          <SelectValue placeholder="Select channel" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          {availableChannels.map((channel) => (
                            <SelectItem 
                              key={channel.id} 
                              value={channel.id}
                              className="text-white"
                            >
                              #{channel.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {/* Repeat/Recurring Event Options */}
                  <div className="bg-slate-700/30 p-3 sm:p-4 rounded-lg space-y-3 sm:space-y-4">
                    <Label className="flex items-center gap-2 text-sm">
                      <Repeat className="w-4 h-4 text-purple-400" />
                      Repeat Event
                    </Label>
                    
                    <Select
                      value={formData.repeat_type}
                      onValueChange={(value) =>
                        setFormData({ ...formData, repeat_type: value, repeat_days: [] })
                      }
                    >
                      <SelectTrigger className="bg-slate-700 border-slate-600 h-10">
                        <SelectValue placeholder="Does not repeat" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="none">Does not repeat</SelectItem>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>

                    {/* Repeat interval (for daily, weekly, monthly) */}
                    {formData.repeat_type && formData.repeat_type !== "none" && (
                      <div>
                        <Label className="text-xs sm:text-sm text-slate-300">Repeat every</Label>
                        <div className="flex items-center gap-2 mt-1">
                          <Input
                            type="number"
                            min="1"
                            max="30"
                            value={formData.repeat_interval}
                            onChange={(e) =>
                              setFormData({ ...formData, repeat_interval: parseInt(e.target.value) || 1 })
                            }
                            className="w-16 sm:w-20 bg-slate-700 border-slate-600 h-10"
                          />
                          <span className="text-sm text-slate-300">
                            {formData.repeat_type === "daily" && "day(s)"}
                            {formData.repeat_type === "weekly" && "week(s)"}
                            {formData.repeat_type === "monthly" && "month(s)"}
                            {formData.repeat_type === "custom" && "day(s)"}
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Day selection for weekly repeat */}
                    {formData.repeat_type === "weekly" && (
                      <div>
                        <Label className="text-xs sm:text-sm text-slate-300 mb-2 block">Repeat on (optional)</Label>
                        <div className="flex flex-wrap gap-1.5 sm:gap-2">
                          {dayNames.map((day, index) => (
                            <button
                              key={index}
                              type="button"
                              onClick={() => {
                                const days = formData.repeat_days.includes(index)
                                  ? formData.repeat_days.filter(d => d !== index)
                                  : [...formData.repeat_days, index];
                                setFormData({ ...formData, repeat_days: days.sort() });
                              }}
                              className={`px-2 sm:px-3 py-1.5 sm:py-1 rounded text-xs sm:text-sm font-medium transition-colors ${
                                formData.repeat_days.includes(index)
                                  ? "bg-purple-600 text-white"
                                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                              }`}
                            >
                              {day}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* End condition */}
                    {formData.repeat_type && formData.repeat_type !== "none" && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                        <div>
                          <Label className="text-xs sm:text-sm text-slate-300">End date</Label>
                          <Input
                            type="date"
                            value={formData.repeat_end_date}
                            onChange={(e) =>
                              setFormData({ ...formData, repeat_end_date: e.target.value, repeat_count: "" })
                            }
                            min={formData.date}
                            className="mt-1 bg-slate-700 border-slate-600 h-10"
                          />
                        </div>
                        <div>
                          <Label className="text-xs sm:text-sm text-slate-300">Or # of times</Label>
                          <Input
                            type="number"
                            min="2"
                            max="52"
                            placeholder="e.g., 12"
                            value={formData.repeat_count}
                            onChange={(e) =>
                              setFormData({ ...formData, repeat_count: e.target.value, repeat_end_date: "" })
                            }
                            className="mt-1 bg-slate-700 border-slate-600 h-10"
                          />
                        </div>
                      </div>
                    )}

                    {formData.repeat_type && formData.repeat_type !== "none" && (
                      <p className="text-xs text-slate-400">
                        💡 Default: up to 52 occurrences if no end set
                      </p>
                    )}
                  </div>

                  <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 mt-4 sm:mt-6 pt-2 border-t border-slate-700">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setDialogOpen(false)}
                      className="w-full sm:w-auto"
                    >
                      Cancel
                    </Button>
                    <Button type="submit" className="w-full sm:w-auto bg-green-600 hover:bg-green-700">
                      Create Event
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
    </>
  ) : null;

  return (
    <PageLayout
      title="Event Calendar"
      icon={Calendar}
      backTo="/"
      backLabel="Back"
      actions={headerActions}
    >
        {/* Monthly Calendar */}
        {renderCalendar()}
        
        {/* Date Details Dialog */}
        <Dialog open={dateDialogOpen} onOpenChange={setDateDialogOpen}>
          <DialogContent className="max-w-lg bg-slate-800 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <CalendarDays className="w-5 h-5" />
                {selectedDateItems?.date && new Date(selectedDateItems.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {/* Events */}
              {selectedDateItems?.events?.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-green-400 flex items-center gap-2 mb-2">
                    <Calendar className="w-4 h-4" />
                    Events
                  </h4>
                  <div className="space-y-2">
                    {selectedDateItems.events.map((event, idx) => (
                      <div key={idx} className="bg-green-900/30 border border-green-600/30 rounded-lg p-3">
                        <div className="font-medium text-white">{event.title}</div>
                        {event.time && <div className="text-sm text-slate-400"><Clock className="w-3 h-3 inline mr-1" />{event.time} CST</div>}
                        {event.location && <div className="text-sm text-slate-400"><MapPin className="w-3 h-3 inline mr-1" />{event.location}</div>}
                        {event.description && <div className="text-sm text-slate-300 mt-2">{event.description}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Birthdays */}
              {selectedDateItems?.birthdays?.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-pink-400 flex items-center gap-2 mb-2">
                    <Cake className="w-4 h-4" />
                    Birthdays
                  </h4>
                  <div className="space-y-2">
                    {selectedDateItems.birthdays.map((bday, idx) => (
                      <div key={idx} className="bg-pink-900/30 border border-pink-600/30 rounded-lg p-3">
                        <div className="font-medium text-white">🎂 {bday.handle}</div>
                        <div className="text-sm text-slate-400">{bday.chapter} {bday.title && `• ${bday.title}`}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Anniversaries */}
              {selectedDateItems?.anniversaries?.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-purple-400 flex items-center gap-2 mb-2">
                    <Award className="w-4 h-4" />
                    Anniversaries
                  </h4>
                  <div className="space-y-2">
                    {selectedDateItems.anniversaries.map((anniv, idx) => (
                      <div key={idx} className="bg-purple-900/30 border border-purple-600/30 rounded-lg p-3">
                        <div className="font-medium text-white">🎉 {anniv.handle}</div>
                        <div className="text-sm text-slate-400">{anniv.chapter} {anniv.title && `• ${anniv.title}`}</div>
                        <div className="text-sm text-purple-300">{anniv.years} years with the Brotherhood</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Admin-only: Filters and Events Table */}
        {isAdmin && (
          <>
            {/* Filters */}
            <div className="bg-slate-800 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Filter className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-300">Event Filters</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm text-slate-400">Chapter</Label>
                  <Select value={chapterFilter} onValueChange={setChapterFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Chapters" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Chapters</SelectItem>
                      <SelectItem value="National">National</SelectItem>
                      <SelectItem value="AD">Asphalt Demons</SelectItem>
                      <SelectItem value="HA">Highway Asylum</SelectItem>
                      <SelectItem value="HS">Highway Souls</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm text-slate-400">Title</Label>
                  <Select value={titleFilter} onValueChange={setTitleFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Titles" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Titles</SelectItem>
                      <SelectItem value="Prez">Prez</SelectItem>
                      <SelectItem value="VP">VP</SelectItem>
                      <SelectItem value="S@A">S@A</SelectItem>
                      <SelectItem value="Secretary">Secretary</SelectItem>
                      <SelectItem value="Member">Member</SelectItem>
                      <SelectItem value="Prospect">Prospect</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

        {/* Events Table */}
            <div className="bg-slate-800 rounded-lg shadow-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Event</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Chapter</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEvents.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-slate-400 py-8">
                        No events found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredEvents.map((event) => (
                      <TableRow
                        key={event.id}
                        onClick={() => handleViewDetails(event)}
                        className={`cursor-pointer transition-colors ${
                          isUpcoming(event.date) 
                            ? "bg-slate-700/30 hover:bg-slate-700/50" 
                            : "hover:bg-slate-700/30"
                        }`}
                      >
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium">{formatDate(event.date)}</span>
                            {isUpcoming(event.date) && (
                              <span className="text-xs text-green-400">Upcoming</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{event.title}</div>
                            {event.description && (
                              <div className="text-sm text-slate-400 mt-1 line-clamp-2">
                                {event.description}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {event.time ? (
                            <div className="flex items-center gap-1 text-sm">
                              <Clock className="w-3 h-3 text-slate-400" />
                              {event.time}
                            </div>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {event.location ? (
                            <div className="flex items-center gap-1 text-sm">
                              <MapPin className="w-3 h-3 text-slate-400" />
                              {event.location}
                            </div>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {event.chapter || <span className="text-slate-500">All</span>}
                        </TableCell>
                        <TableCell>
                          {event.title_filter || <span className="text-slate-500">All</span>}
                        </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {event.discord_notifications_enabled && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => handleSendDiscordNow(event, e)}
                            className="text-green-400 hover:text-green-300"
                            title="Send Discord notification now"
                          >
                            <Send className="w-4 h-4" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => handleEdit(event, e)}
                          className="text-blue-400 hover:text-blue-300"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => handleDelete(event.id, event.title, e)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
            </div>
          </>
        )}

        {/* Edit Dialog - Admin only */}
        {isAdmin && (
          <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Edit Event</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleEditSubmit} className="space-y-4 mt-4">
                <div>
                  <Label>Event Title *</Label>
                  <Input
                    value={editFormData.title}
                    onChange={(e) =>
                    setEditFormData({ ...editFormData, title: e.target.value })
                  }
                  required
                />
              </div>

              <div>
                <Label>Description</Label>
                <Textarea
                  value={editFormData.description}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, description: e.target.value })
                  }
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Date *</Label>
                  <Input
                    type="date"
                    value={editFormData.date}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, date: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <Label>Time (Central Time - CST/CDT)</Label>
                  <Input
                    type="time"
                    value={editFormData.time}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, time: e.target.value })
                    }
                  />
                </div>
              </div>

              <div>
                <Label>Location</Label>
                <Input
                  value={editFormData.location}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, location: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Chapter</Label>
                  <Select
                    value={editFormData.chapter}
                    onValueChange={(value) =>
                      setEditFormData({ ...editFormData, chapter: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All Chapters" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Chapters</SelectItem>
                      <SelectItem value="National">National</SelectItem>
                      <SelectItem value="AD">Asphalt Demons</SelectItem>
                      <SelectItem value="HA">Highway Asylum</SelectItem>
                      <SelectItem value="HS">Highway Souls</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Title</Label>
                  <Select
                    value={editFormData.title_filter}
                    onValueChange={(value) =>
                      setEditFormData({ ...editFormData, title_filter: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All Titles" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Titles</SelectItem>
                      <SelectItem value="Prez">Prez</SelectItem>
                      <SelectItem value="VP">VP</SelectItem>
                      <SelectItem value="S@A">S@A</SelectItem>
                      <SelectItem value="Secretary">Secretary</SelectItem>
                      <SelectItem value="Member">Member</SelectItem>
                      <SelectItem value="Prospect">Prospect</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Discord Notifications Toggle */}
              <div className="flex items-center space-x-2 bg-slate-700/30 p-4 rounded-lg">
                <Checkbox
                  id="edit-discord-notifications"
                  checked={editFormData.discord_notifications_enabled}
                  onCheckedChange={(checked) =>
                    setEditFormData({ ...editFormData, discord_notifications_enabled: checked })
                  }
                />
                <label
                  htmlFor="edit-discord-notifications"
                  className="text-sm font-medium leading-none cursor-pointer"
                >
                  📢 Send Discord notifications (24 hours & 3 hours before event)
                </label>
              </div>

              {/* Discord Channel Selector for Edit */}
              {editFormData.discord_notifications_enabled && availableChannels.length > 0 && (
                <div className="bg-slate-700/30 p-4 rounded-lg">
                  <Label className="flex items-center gap-2 mb-2">
                    <Hash className="w-4 h-4 text-blue-400" />
                    Discord Channel
                  </Label>
                  <Select
                    value={editFormData.discord_channel}
                    onValueChange={(value) =>
                      setEditFormData({ ...editFormData, discord_channel: value })
                    }
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue placeholder="Select channel" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      {availableChannels.map((channel) => (
                        <SelectItem 
                          key={channel.id} 
                          value={channel.id}
                          className="text-white"
                        >
                          #{channel.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-400 mt-1">
                    Choose which Discord channel to post the event notification
                  </p>
                </div>
              )}

              <div className="flex justify-end gap-2 mt-6">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                  Update Event
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
        )}

        {/* Event Detail View Dialog - For all users */}
        <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Event Details</DialogTitle>
            </DialogHeader>
            {selectedEvent && (
              <div className="space-y-6 mt-4">
                {/* Event Title and Status */}
                <div>
                  <h2 className="text-3xl font-bold text-slate-100 mb-2">
                    {selectedEvent.title}
                  </h2>
                  {isUpcoming(selectedEvent.date) && (
                    <span className="inline-block bg-green-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                      UPCOMING
                    </span>
                  )}
                </div>

                {/* Date and Time */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-start gap-3 bg-slate-700/30 p-4 rounded-lg">
                    <Calendar className="w-6 h-6 text-blue-400 mt-1" />
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Date</div>
                      <div className="text-lg font-semibold">{formatDate(selectedEvent.date)}</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 bg-slate-700/30 p-4 rounded-lg">
                    <Clock className="w-6 h-6 text-blue-400 mt-1" />
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Time (Central Time)</div>
                      <div className="text-lg font-semibold">
                        {selectedEvent.time ? `${selectedEvent.time} CST` : <span className="text-slate-500">Not specified</span>}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Location */}
                {selectedEvent.location && (
                  <div className="flex items-start gap-3 bg-slate-700/30 p-4 rounded-lg">
                    <MapPin className="w-6 h-6 text-blue-400 mt-1" />
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Location</div>
                      <div className="text-lg">{selectedEvent.location}</div>
                    </div>
                  </div>
                )}

                {/* Description */}
                {selectedEvent.description && (
                  <div className="bg-slate-700/30 p-4 rounded-lg">
                    <div className="text-sm text-slate-400 mb-2">Description</div>
                    <div className="text-base leading-relaxed whitespace-pre-wrap">
                      {selectedEvent.description}
                    </div>
                  </div>
                )}

                {/* Chapter and Title Filters */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-start gap-3 bg-slate-700/30 p-4 rounded-lg">
                    <Users className="w-6 h-6 text-blue-400 mt-1" />
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Chapter</div>
                      <div className="text-lg font-semibold">
                        {selectedEvent.chapter || <span className="text-slate-400">All Chapters</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 bg-slate-700/30 p-4 rounded-lg">
                    <Users className="w-6 h-6 text-blue-400 mt-1" />
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Title</div>
                      <div className="text-lg font-semibold">
                        {selectedEvent.title_filter || <span className="text-slate-400">All Titles</span>}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Created By */}
                <div className="bg-slate-700/30 p-4 rounded-lg">
                  <div className="text-sm text-slate-400 mb-2">Created By</div>
                  <div className="space-y-1">
                    {selectedEvent.creator_chapter && (
                      <div className="text-base">
                        <span className="text-slate-400">Chapter:</span> <span className="font-semibold text-slate-200">{selectedEvent.creator_chapter}</span>
                      </div>
                    )}
                    {selectedEvent.creator_title && (
                      <div className="text-base">
                        <span className="text-slate-400">Title:</span> <span className="font-semibold text-slate-200">{selectedEvent.creator_title}</span>
                      </div>
                    )}
                    {selectedEvent.creator_handle && (
                      <div className="text-base">
                        <span className="text-slate-400">Handle:</span> <span className="font-semibold text-slate-200">{selectedEvent.creator_handle}</span>
                      </div>
                    )}
                    <div className="text-sm text-slate-500 mt-2">
                      {selectedEvent.created_by} on {new Date(selectedEvent.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                {/* Discord Channel Info */}
                {selectedEvent.discord_notifications_enabled && (
                  <div className="flex items-start gap-3 bg-blue-900/20 p-4 rounded-lg border border-blue-600/30">
                    <Hash className="w-6 h-6 text-blue-400 mt-1" />
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Discord Channel</div>
                      <div className="text-lg font-semibold text-blue-400">
                        #{(selectedEvent.discord_channel || "member-chat").replace("-", " ").replace(/\b\w/g, l => l.toUpperCase()).replace(" ", "-")}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        Notifications will be sent to this channel
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-between items-center pt-4">
                  {selectedEvent.discord_notifications_enabled ? (
                    <Button
                      onClick={(e) => {
                        setDetailDialogOpen(false);
                        handleSendDiscordNow(selectedEvent, e);
                      }}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Send Discord Now
                    </Button>
                  ) : (
                    <div className="text-sm text-slate-500">
                      Discord notifications disabled
                    </div>
                  )}
                  <Button
                    variant="outline"
                    onClick={() => setDetailDialogOpen(false)}
                    className="bg-slate-700 hover:bg-slate-600"
                  >
                    Close
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
    </PageLayout>
  );
}
