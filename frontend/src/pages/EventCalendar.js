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
import { Calendar, Plus, Edit, Trash2, MapPin, Clock, Users, ArrowLeft, Filter } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL || "";

export default function EventCalendar() {
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  
  const [chapterFilter, setChapterFilter] = useState("");
  const [titleFilter, setTitleFilter] = useState("");

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    date: "",
    time: "",
    location: "",
    chapter: "all",
    title_filter: "all",
    discord_notifications_enabled: true,
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
  });

  useEffect(() => {
    fetchEvents();
  }, []);

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
    };

    try {
      await axios.post(`${API}/api/events`, apiData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Event created successfully");
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

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
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

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate("/dashboard")}
            className="mb-4 text-slate-300 hover:text-slate-100"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <Calendar className="w-8 h-8 text-blue-400" />
              <h1 className="text-3xl font-bold">Event Calendar</h1>
            </div>

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-green-600 hover:bg-green-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Event
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Event</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div>
                    <Label>Event Title *</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) =>
                        setFormData({ ...formData, title: e.target.value })
                      }
                      required
                    />
                  </div>

                  <div>
                    <Label>Description</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) =>
                        setFormData({ ...formData, description: e.target.value })
                      }
                      rows={3}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Date *</Label>
                      <Input
                        type="date"
                        value={formData.date}
                        onChange={(e) =>
                          setFormData({ ...formData, date: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div>
                      <Label>Time</Label>
                      <Input
                        type="time"
                        value={formData.time}
                        onChange={(e) =>
                          setFormData({ ...formData, time: e.target.value })
                        }
                      />
                    </div>
                  </div>

                  <div>
                    <Label>Location</Label>
                    <Input
                      value={formData.location}
                      onChange={(e) =>
                        setFormData({ ...formData, location: e.target.value })
                      }
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Chapter (Leave empty for all chapters)</Label>
                      <Select
                        value={formData.chapter}
                        onValueChange={(value) =>
                          setFormData({ ...formData, chapter: value })
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
                      <Label>Title (Leave empty for all titles)</Label>
                      <Select
                        value={formData.title_filter}
                        onValueChange={(value) =>
                          setFormData({ ...formData, title_filter: value })
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
                      id="discord-notifications"
                      checked={formData.discord_notifications_enabled}
                      onCheckedChange={(checked) =>
                        setFormData({ ...formData, discord_notifications_enabled: checked })
                      }
                    />
                    <label
                      htmlFor="discord-notifications"
                      className="text-sm font-medium leading-none cursor-pointer"
                    >
                      📢 Send Discord notifications (24 hours & 3 hours before event)
                    </label>
                  </div>

                  <div className="flex justify-end gap-2 mt-6">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" className="bg-green-600 hover:bg-green-700">
                      Create Event
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-slate-800 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-300">Filters</h3>
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

        {/* Edit Dialog */}
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
                  <Label>Time</Label>
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

        {/* Event Detail View Dialog */}
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
                      <div className="text-sm text-slate-400 mb-1">Time</div>
                      <div className="text-lg font-semibold">
                        {selectedEvent.time || <span className="text-slate-500">Not specified</span>}
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
                <div className="text-sm text-slate-500 pt-4 border-t border-slate-700">
                  Created by {selectedEvent.created_by} on {new Date(selectedEvent.created_at).toLocaleDateString()}
                </div>

                {/* Close Button */}
                <div className="flex justify-end pt-4">
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
      </div>
    </div>
  );
}
