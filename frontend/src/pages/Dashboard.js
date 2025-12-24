import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LogOut, Plus, Pencil, Trash2, Download, Users, Mail, Phone, MapPin, MessageCircle, Clock, LifeBuoy, FileText, Calendar } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHAPTERS = ["National", "AD", "HA", "HS"];
const TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM", "Member"];

// Helper function to get the Nth occurrence of a weekday in a month
const getNthWeekdayOfMonth = (year, month, weekday, n) => {
  const date = new Date(year, month, 1);
  let count = 0;
  
  while (date.getMonth() === month) {
    if (date.getDay() === weekday) {
      count++;
      if (count === n) {
        return new Date(date);
      }
    }
    date.setDate(date.getDate() + 1);
  }
  return null;
};

// Helper function to get 1st and 3rd Wednesday of each month
const getMeetingDates = (year) => {
  const dates = [];
  for (let month = 0; month < 12; month++) {
    // Get 1st Wednesday (weekday 3 = Wednesday)
    const firstWed = getNthWeekdayOfMonth(year, month, 3, 1);
    // Get 3rd Wednesday
    const thirdWed = getNthWeekdayOfMonth(year, month, 3, 3);
    dates.push(firstWed, thirdWed);
  }
  return dates;
};

// Helper function to format date as MM/DD
const formatMeetingDate = (date) => {
  if (!date) return '';
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${month}/${day}`;
};

// Helper function to sort members by chapter and title
const sortMembers = (members) => {
  return members.sort((a, b) => {
    // First sort by chapter
    const chapterA = CHAPTERS.indexOf(a.chapter);
    const chapterB = CHAPTERS.indexOf(b.chapter);
    
    if (chapterA !== chapterB) {
      return chapterA - chapterB;
    }
    
    // Then sort by title
    const titleA = TITLES.indexOf(a.title);
    const titleB = TITLES.indexOf(b.title);
    
    return titleA - titleB;
  });
};

export default function Dashboard({ onLogout, userRole, userPermissions }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionsDialogOpen, setActionsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [memberToDelete, setMemberToDelete] = useState(null);
  const [deleteReason, setDeleteReason] = useState("");
  const [selectedMember, setSelectedMember] = useState(null);
  const [actionForm, setActionForm] = useState({ type: "merit", date: "", description: "" });
  const [editingAction, setEditingAction] = useState(null);
  const [editingMember, setEditingMember] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [meetingDates, setMeetingDates] = useState([]);
  const [unreadPrivateCount, setUnreadPrivateCount] = useState(0);
  const [upcomingEventsCount, setUpcomingEventsCount] = useState(0);
  const navigate = useNavigate();

  // Helper to check permissions
  const hasPermission = (permission) => {
    if (userRole === 'admin') return true;
    return userPermissions?.[permission] === true;
  };


  // Generic error handler for API calls
  const handleApiError = (error, context) => {
    console.error(`${context}:`, error);
    
    // Handle token expiration
    if (error.response?.status === 401) {
      toast.error("Session expired. Please log in again.");
      setTimeout(() => {
        onLogout();
      }, 1500);
      return true; // Handled
    }
    
    return false; // Not handled
  };


  const [selectedDuesYear, setSelectedDuesYear] = useState(new Date().getFullYear());
  const [formData, setFormData] = useState({
    chapter: "",
    title: "",
    handle: "",
    name: "",
    email: "",
    phone: "",
    address: "",
    dob: "",
    join_date: "",
    phone_private: false,
    address_private: false,
    email_private: false,
    military_service: false,
    military_branch: "",
    is_first_responder: false,
    dues: {
      [new Date().getFullYear().toString()]: Array(12).fill(false)
    },
    meeting_attendance: {
      [new Date().getFullYear().toString()]: Array(24).fill(null).map(() => ({ status: 0, note: "" }))
    }
  });

  useEffect(() => {
    fetchMembers();
    fetchUnreadPrivateCount();
    fetchUpcomingEventsCount();
    // Auto-refresh counts every 30 seconds
    const interval = setInterval(() => {
      fetchUnreadPrivateCount();
      fetchUpcomingEventsCount();
    }, 30000);
    return () => clearInterval(interval);
  }, [userRole]);

  const fetchUnreadPrivateCount = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/messages/unread/count`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUnreadPrivateCount(response.data.unread_count);
    } catch (error) {
      if (!handleApiError(error, "Failed to fetch unread private messages count")) {
        console.error("Failed to fetch unread private messages count:", error);
      }
    }
  };

  const fetchUpcomingEventsCount = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/events/upcoming-count`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUpcomingEventsCount(response.data.count);
    } catch (error) {
      // Silently fail - events feature might not be critical
      console.error("Failed to fetch upcoming events count:", error);
    }
  };


  // Update meeting dates whenever the year changes
  useEffect(() => {
    const currentYear = new Date().getFullYear();
    const dates = getMeetingDates(currentYear);
    setMeetingDates(dates);
  }, [formData.meeting_attendance.year]);

  const fetchMembers = async () => {
    try {
      const token = localStorage.getItem("token");
      console.log("Fetching members with token:", token ? token.substring(0, 20) + "..." : "NO TOKEN");
      const response = await axios.get(`${API}/members`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log("Members loaded successfully:", response.data.length, "members");
      const sortedMembers = sortMembers(response.data);
      setMembers(sortedMembers);
    } catch (error) {
      if (handleApiError(error, "Failed to load members")) {
        return;
      }
      toast.error(`Failed to load members: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    try {
      if (editingMember) {
        await axios.put(`${API}/members/${editingMember.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success("Member updated successfully");
      } else {
        await axios.post(`${API}/members`, formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success("Member added successfully");
      }
      setDialogOpen(false);
      resetForm();
      fetchMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Operation failed");
    }
  };

  const handleDelete = (member) => {
    setMemberToDelete(member);
    setDeleteReason("");
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteReason.trim()) {
      toast.error("Please provide a reason for archiving");
      return;
    }

    const token = localStorage.getItem("token");
    try {
      await axios.delete(`${API}/members/${memberToDelete.id}`, {
        params: { reason: deleteReason },
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Member archived successfully");
      setDeleteDialogOpen(false);
      setMemberToDelete(null);
      setDeleteReason("");
      fetchMembers();
    } catch (error) {
      toast.error("Failed to archive member");
    }
  };

  const handleOpenActions = (member) => {
    setSelectedMember(member);
    setActionForm({ type: "merit", date: new Date().toISOString().split('T')[0], description: "" });
    setEditingAction(null); // Reset editing state
    setActionsDialogOpen(true);
  };

  const handleAddAction = async (e) => {
    e.preventDefault();
    if (!actionForm.description.trim()) {
      toast.error("Please enter a description");
      return;
    }

    const token = localStorage.getItem("token");
    try {
      await axios.post(
        `${API}/members/${selectedMember.id}/actions`,
        null,
        {
          params: {
            action_type: actionForm.type,
            date: actionForm.date,
            description: actionForm.description
          },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success("Action added successfully");
      setActionForm({ type: "merit", date: new Date().toISOString().split('T')[0], description: "" });
      fetchMembers(); // Refresh to get updated actions
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add action");
    }
  };

  const handleDeleteAction = async (actionId) => {
    if (!window.confirm("Are you sure you want to delete this action?")) return;

    const token = localStorage.getItem("token");
    try {
      await axios.delete(`${API}/members/${selectedMember.id}/actions/${actionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Action deleted successfully");
      fetchMembers(); // Refresh to get updated actions
    } catch (error) {
      toast.error("Failed to delete action");
    }
  };

  const handleEditAction = (action) => {
    setEditingAction(action);
    setActionForm({
      type: action.type,
      date: action.date,
      description: action.description
    });
  };

  const handleUpdateAction = async (e) => {
    e.preventDefault();
    if (!actionForm.description.trim()) {
      toast.error("Please enter a description");
      return;
    }

    const token = localStorage.getItem("token");
    try {
      await axios.put(
        `${API}/members/${selectedMember.id}/actions/${editingAction.id}`,
        {
          action_type: actionForm.type,
          date: actionForm.date,
          description: actionForm.description
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success("Action updated successfully");
      setEditingAction(null);
      setActionForm({ type: "merit", date: new Date().toISOString().split('T')[0], description: "" });
      fetchMembers(); // Refresh to get updated actions
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update action");
    }
  };

  const handleCancelEdit = () => {
    setEditingAction(null);
    setActionForm({ type: "merit", date: new Date().toISOString().split('T')[0], description: "" });
  };

  const handleEdit = (member) => {
    setEditingMember(member);
    
    // Handle meeting_attendance - support both old and new format
    let attendanceData = {};
    const currentYear = new Date().getFullYear().toString();
    
    if (member.meeting_attendance) {
      // Check if it's new format (keys are years) or old format (has 'year' key)
      if (member.meeting_attendance.year) {
        // Old format - convert to new
        const yearStr = member.meeting_attendance.year.toString();
        const meetings = member.meeting_attendance.meetings || [];
        attendanceData[yearStr] = meetings.map(m => {
          if (typeof m === 'object' && m !== null) {
            return { status: m.status || 0, note: m.note || "" };
          } else {
            return { status: m || 0, note: "" };
          }
        });
      } else {
        // New format - use as is, ensuring current year exists
        attendanceData = { ...member.meeting_attendance };
        if (!attendanceData[currentYear]) {
          attendanceData[currentYear] = Array(24).fill(null).map(() => ({ status: 0, note: "" }));
        }
      }
    } else {
      // No attendance data
      attendanceData[currentYear] = Array(24).fill(null).map(() => ({ status: 0, note: "" }));
    }
    
    // Handle dues - support both old and new format
    let duesData = {};
    if (member.dues) {
      if (member.dues.year) {
        // Old format - convert
        const yearStr = member.dues.year.toString();
        duesData[yearStr] = member.dues.months || Array(12).fill(false);
      } else {
        // New format - use as is
        duesData = { ...member.dues };
        if (!duesData[currentYear]) {
          duesData[currentYear] = Array(12).fill(false);
        }
      }
    } else {
      duesData[currentYear] = Array(12).fill(false);
    }
    
    setFormData({
      chapter: member.chapter,
      title: member.title,
      handle: member.handle,
      name: member.name,
      email: member.email,
      phone: member.phone,
      address: member.address,
      dob: member.dob || "",
      join_date: member.join_date || "",
      phone_private: member.phone_private || false,
      address_private: member.address_private || false,
      email_private: member.email_private || false,
      military_service: member.military_service || false,
      military_branch: member.military_branch || "",
      is_first_responder: member.is_first_responder || false,
      dues: duesData,
      meeting_attendance: attendanceData
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    const currentYear = new Date().getFullYear().toString();
    setFormData({
      chapter: "",
      title: "",
      handle: "",
      name: "",
      email: "",
      phone: "",
      address: "",
      dob: "",
      join_date: "",
      phone_private: false,
      address_private: false,
      email_private: false,
      military_service: false,
      military_branch: "",
      is_first_responder: false,
      dues: {
        [currentYear]: Array(12).fill(false)
      },
      meeting_attendance: {
        [currentYear]: Array(24).fill(null).map(() => ({ status: 0, note: "" }))
      }
    });
    setEditingMember(null);
  };

  const handleDuesToggle = (monthIndex) => {
    const currentYear = selectedDuesYear.toString();
    const yearMonths = formData.dues[currentYear] || Array(12).fill(null).map(() => ({ status: "unpaid", note: "" }));
    const currentStatus = yearMonths[monthIndex]?.status || "unpaid";
    
    // Cycle through: unpaid -> paid -> late -> unpaid
    let newStatus = "unpaid";
    if (currentStatus === "unpaid") newStatus = "paid";
    else if (currentStatus === "paid") newStatus = "late";
    else newStatus = "unpaid";
    
    const newMonths = [...yearMonths];
    newMonths[monthIndex] = {
      status: newStatus,
      note: yearMonths[monthIndex]?.note || ""
    };
    
    setFormData({
      ...formData,
      dues: {
        ...formData.dues,
        [currentYear]: newMonths
      }
    });
  };

  const handleDuesNoteChange = (monthIndex, note) => {
    const currentYear = selectedDuesYear.toString();
    const yearMonths = formData.dues[currentYear] || Array(12).fill(null).map(() => ({ status: "unpaid", note: "" }));
    const newMonths = [...yearMonths];
    newMonths[monthIndex] = {
      ...newMonths[monthIndex],
      note: note
    };
    
    setFormData({
      ...formData,
      dues: {
        ...formData.dues,
        [currentYear]: newMonths
      }
    });
  };

  const handleDuesYearChange = (newYear) => {
    setSelectedDuesYear(newYear);
    // Create year entry if doesn't exist
    if (!formData.dues[newYear.toString()]) {
      setFormData({
        ...formData,
        dues: {
          ...formData.dues,
          [newYear.toString()]: Array(12).fill(false)
        }
      });
    }
  };

  const handleAttendanceToggle = (meetingIndex) => {
    const currentYear = new Date().getFullYear().toString();
    const yearMeetings = formData.meeting_attendance[currentYear] || [];
    const newMeetings = [...yearMeetings];
    
    // Cycle through states: 0 (Absent) -> 1 (Present) -> 2 (Excused) -> 0
    const currentStatus = newMeetings[meetingIndex]?.status || 0;
    newMeetings[meetingIndex] = {
      ...newMeetings[meetingIndex],
      status: (currentStatus + 1) % 3
    };
    
    setFormData({
      ...formData,
      meeting_attendance: {
        ...formData.meeting_attendance,
        [currentYear]: newMeetings
      }
    });
  };

  const handleAttendanceNote = (meetingIndex, note) => {
    const currentYear = new Date().getFullYear().toString();
    const yearMeetings = formData.meeting_attendance[currentYear] || [];
    const newMeetings = [...yearMeetings];
    
    newMeetings[meetingIndex] = {
      ...newMeetings[meetingIndex],
      note: note
    };
    
    setFormData({
      ...formData,
      meeting_attendance: {
        ...formData.meeting_attendance,
        [currentYear]: newMeetings
      }
    });
  };

  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  const handleExportCSV = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await axios.get(`${API}/members/export/csv`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "members.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("CSV downloaded successfully");
    } catch (error) {
      toast.error("Failed to export CSV");
    }
  };

  const handleViewCSV = () => {
    // Navigate to the CSV export view page
    window.open('/export-view', '_blank');
    toast.success("Opening CSV export view...");
  };

  const filteredMembers = members.filter((member) => {
    const search = searchTerm.toLowerCase();
    return (
      member.name.toLowerCase().includes(search) ||
      member.handle.toLowerCase().includes(search) ||
      member.email.toLowerCase().includes(search) ||
      member.chapter.toLowerCase().includes(search)
    );
  });

  // Sort filtered members to maintain order
  const sortedFilteredMembers = sortMembers([...filteredMembers]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <nav className="bg-slate-800 border-b border-slate-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
            <h1 className="text-xl sm:text-2xl font-bold text-white">Brothers of the Highway</h1>
            <div className="flex items-center justify-between gap-2 flex-wrap w-full sm:w-auto">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs sm:text-sm text-slate-300">
                  {localStorage.getItem("username")} ({userRole})
                </span>
                {userRole === 'admin' && (
                  <>
                    <Button
                      onClick={() => navigate("/prospects")}
                      variant="outline"
                      size="sm"
                      className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
                    >
                      <Users className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span className="hidden sm:inline">Prospects</span>
                      <span className="sm:hidden">Prospects</span>
                    </Button>
                    <Button
                      onClick={() => navigate("/users")}
                      variant="outline"
                      size="sm"
                      data-testid="user-management-button"
                      className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
                    >
                      <Users className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span className="hidden sm:inline">Admin</span>
                      <span className="sm:hidden">Admin</span>
                    </Button>
                    <Button
                      onClick={() => navigate("/update-log")}
                      variant="outline"
                      size="sm"
                      className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
                    >
                      <Clock className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span className="hidden sm:inline">Updates</span>
                    </Button>
                  </>
                )}
                {localStorage.getItem("username") === "Lonestar" && (
                  <Button
                    onClick={() => navigate("/message-monitor")}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
                  >
                    <MessageCircle className="w-3 h-3 sm:w-4 sm:h-4" />
                    <span className="hidden sm:inline">Monitor</span>
                  </Button>
                )}
                <Button
                  onClick={() => navigate("/events")}
                  variant="outline"
                  size="sm"
                  className="relative flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
                >
                  <Calendar className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="hidden sm:inline">Events</span>
                  {upcomingEventsCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                      {upcomingEventsCount > 99 ? '99+' : upcomingEventsCount}
                    </span>
                  )}
                </Button>
                <Button
                  onClick={() => navigate("/messages")}
                  variant="outline"
                  size="sm"
                  className="relative flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
                >
                  <Mail className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="hidden sm:inline">Messages</span>
                  {unreadPrivateCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                      {unreadPrivateCount > 99 ? '99+' : unreadPrivateCount}
                    </span>
                  )}
                </Button>
              </div>
              <Button
                onClick={onLogout}
                variant="outline"
                size="sm"
                data-testid="logout-button"
                className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
              >
                <LogOut className="w-3 h-3 sm:w-4 sm:h-4" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700 p-4 sm:p-6">
          <div className="mb-4 sm:mb-6">
            <div className="relative max-w-2xl">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-slate-400 pointer-events-none z-10"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <Input
                placeholder="Search by chapter, name, or handle..."
                data-testid="search-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 py-4 sm:py-6 text-sm sm:text-base border-2 border-slate-300 focus:border-slate-600 rounded-lg"
              />
            </div>
          </div>
          
          {hasPermission('admin_actions') && (
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mb-4 sm:mb-6">
              <Button
                onClick={handleViewCSV}
                size="sm"
                className="flex items-center justify-center gap-2 w-full sm:w-auto bg-green-600 hover:bg-green-700 text-white"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                View Export
              </Button>
              <Dialog open={dialogOpen} onOpenChange={(open) => {
                setDialogOpen(open);
                if (!open) resetForm();
              }}>
                <DialogTrigger asChild>
                  <Button
                    data-testid="add-member-button"
                    size="sm"
                    className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-900 text-white w-full sm:w-auto"
                  >
                    <Plus className="w-4 h-4" />
                    Add Member
                  </Button>
                </DialogTrigger>
                  <DialogContent className="max-w-[95vw] sm:max-w-2xl max-h-[90vh] overflow-y-auto bg-slate-800 border-slate-700">
                    <DialogHeader>
                      <DialogTitle className="text-lg sm:text-xl text-white">
                        {editingMember ? "Edit Member" : "Add New Member"}
                      </DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-white">Chapter</Label>
                          <Select
                            value={formData.chapter}
                            onValueChange={(value) =>
                              setFormData({ ...formData, chapter: value })
                            }
                            required
                          >
                            <SelectTrigger data-testid="chapter-select" className="text-white">
                              <SelectValue placeholder="Select chapter" />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 text-white border-slate-700">
                              {CHAPTERS.map((ch) => (
                                <SelectItem key={ch} value={ch} className="text-white hover:bg-slate-700">
                                  {ch}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label className="text-white">Title</Label>
                          <Select
                            value={formData.title}
                            onValueChange={(value) =>
                              setFormData({ ...formData, title: value })
                            }
                            required
                          >
                            <SelectTrigger data-testid="title-select" className="text-white">
                              <SelectValue placeholder="Select title" />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 text-white border-slate-700">
                              {TITLES.map((t) => (
                                <SelectItem key={t} value={t} className="text-white hover:bg-slate-700">
                                  {t}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div>
                        <Label className="text-white">Member Handle</Label>
                        <Input
                          data-testid="handle-input"
                          value={formData.handle}
                          onChange={(e) =>
                            setFormData({ ...formData, handle: e.target.value })
                          }
                          required
                          className="text-white"
                        />
                      </div>

                      <div>
                        <Label className="text-white">Name</Label>
                        <Input
                          data-testid="name-input"
                          value={formData.name}
                          onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                          }
                          required
                          className="text-white"
                        />
                      </div>

                      <div>
                        <Label className="text-white">Email</Label>
                        <Input
                          data-testid="email-input"
                          type="email"
                          value={formData.email}
                          onChange={(e) =>
                            setFormData({ ...formData, email: e.target.value })
                          }
                          required
                          className="text-white"
                        />
                        <div className="flex items-center space-x-2 mt-2">
                          <Checkbox
                            id="email_private"
                            checked={formData.email_private}
                            onCheckedChange={(checked) =>
                              setFormData({ ...formData, email_private: checked })
                            }
                            className="border-slate-400 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                          />
                          <label htmlFor="email_private" className="text-sm font-medium cursor-pointer text-slate-300">
                            Make email private (visible only to National members & chapter officers)
                          </label>
                        </div>
                      </div>

                      <div>
                        <Label className="text-white">Phone</Label>
                        <Input
                          data-testid="phone-input"
                          value={formData.phone}
                          onChange={(e) =>
                            setFormData({ ...formData, phone: e.target.value })
                          }
                          required
                          className="text-white"
                        />
                        <div className="flex items-center space-x-2 mt-2">
                          <Checkbox
                            id="phone_private"
                            checked={formData.phone_private}
                            onCheckedChange={(checked) =>
                              setFormData({ ...formData, phone_private: checked })
                            }
                            className="border-slate-400 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                          />
                          <label htmlFor="phone_private" className="text-sm font-medium cursor-pointer text-slate-300">
                            Make phone number private (hide from non-admin users)
                          </label>
                        </div>
                      </div>

                      <div>
                        <Label className="text-white">Address</Label>
                        <Input
                          data-testid="address-input"
                          value={formData.address}
                          onChange={(e) =>
                            setFormData({ ...formData, address: e.target.value })
                          }
                          required
                          className="text-white"
                        />
                        <div className="flex items-center space-x-2 mt-2">
                          <Checkbox
                            id="address_private"
                            checked={formData.address_private}
                            onCheckedChange={(checked) =>
                              setFormData({ ...formData, address_private: checked })
                            }
                            className="border-slate-400 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                          />
                          <label htmlFor="address_private" className="text-sm font-medium cursor-pointer text-slate-300">
                            Make address private (hide from non-admin users)
                          </label>
                        </div>
                      </div>

                      <div>
                        <Label className="text-white">Date of Birth (optional)</Label>
                        <Input
                          type="date"
                          value={formData.dob}
                          onChange={(e) =>
                            setFormData({ ...formData, dob: e.target.value })
                          }
                          className="text-white"
                        />
                      </div>

                      <div>
                        <Label className="text-white">Anniversary Date (MM/YYYY)</Label>
                        <Input
                          type="text"
                          placeholder="MM/YYYY"
                          value={formData.join_date}
                          onChange={(e) => {
                            let value = e.target.value.replace(/[^\d/]/g, '');
                            // Auto-add slash after 2 digits
                            if (value.length === 2 && !value.includes('/') && formData.join_date.length < value.length) {
                              value = value + '/';
                            }
                            // Limit to 7 characters (MM/YYYY)
                            if (value.length <= 7) {
                              setFormData({ ...formData, join_date: value });
                            }
                          }}
                          className="text-white"
                        />
                      </div>

                      {/* Military Service Section */}
                      <div className="space-y-3 p-3 bg-slate-800 rounded-lg border border-slate-700">
                        <Label className="text-white font-semibold">🎖️ Military Service</Label>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="military_service"
                            checked={formData.military_service || false}
                            onCheckedChange={(checked) =>
                              setFormData({ ...formData, military_service: checked, military_branch: checked ? formData.military_branch : "" })
                            }
                          />
                          <label htmlFor="military_service" className="text-sm text-slate-200 cursor-pointer">
                            Served in Military
                          </label>
                        </div>
                        {formData.military_service && (
                          <div className="ml-6">
                            <Label className="text-slate-300 text-sm">Branch of Service</Label>
                            <Select
                              value={formData.military_branch || ""}
                              onValueChange={(value) => setFormData({ ...formData, military_branch: value })}
                            >
                              <SelectTrigger className="bg-slate-900 border-slate-600 text-white">
                                <SelectValue placeholder="Select branch" />
                              </SelectTrigger>
                              <SelectContent className="bg-slate-800 border-slate-600">
                                <SelectItem value="Army" className="text-white hover:bg-slate-700">Army</SelectItem>
                                <SelectItem value="Navy" className="text-white hover:bg-slate-700">Navy</SelectItem>
                                <SelectItem value="Air Force" className="text-white hover:bg-slate-700">Air Force</SelectItem>
                                <SelectItem value="Marines" className="text-white hover:bg-slate-700">Marines</SelectItem>
                                <SelectItem value="Coast Guard" className="text-white hover:bg-slate-700">Coast Guard</SelectItem>
                                <SelectItem value="Space Force" className="text-white hover:bg-slate-700">Space Force</SelectItem>
                                <SelectItem value="National Guard" className="text-white hover:bg-slate-700">National Guard</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        )}
                      </div>

                      {/* First Responder Section */}
                      <div className="space-y-3 p-3 bg-slate-800 rounded-lg border border-slate-700">
                        <Label className="text-white font-semibold">🚨 First Responder Service</Label>
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              id="is_police"
                              checked={formData.is_police || false}
                              onCheckedChange={(checked) =>
                                setFormData({ ...formData, is_police: checked })
                              }
                            />
                            <label htmlFor="is_police" className="text-sm text-slate-200 cursor-pointer">
                              🚔 Police / Law Enforcement
                            </label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              id="is_fire"
                              checked={formData.is_fire || false}
                              onCheckedChange={(checked) =>
                                setFormData({ ...formData, is_fire: checked })
                              }
                            />
                            <label htmlFor="is_fire" className="text-sm text-slate-200 cursor-pointer">
                              🚒 Fire / Firefighter
                            </label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              id="is_ems"
                              checked={formData.is_ems || false}
                              onCheckedChange={(checked) =>
                                setFormData({ ...formData, is_ems: checked })
                              }
                            />
                            <label htmlFor="is_ems" className="text-sm text-slate-200 cursor-pointer">
                              🚑 EMS / Paramedic
                            </label>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <Label className="text-white">Dues Tracking</Label>
                          <div className="flex items-center gap-2">
                            <Label className="text-sm text-white">Year:</Label>
                            <Input
                              type="number"
                              value={selectedDuesYear}
                              onChange={(e) => handleDuesYearChange(parseInt(e.target.value))}
                              className="w-24 text-white"
                              data-testid="dues-year-input"
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                          {monthNames.map((month, index) => {
                            const yearMonths = formData.dues[selectedDuesYear.toString()] || Array(12).fill(null).map(() => ({ status: "unpaid", note: "" }));
                            const monthDue = yearMonths[index] || { status: "unpaid", note: "" };
                            const status = typeof monthDue === 'object' ? monthDue.status : (monthDue ? 'paid' : 'unpaid');
                            const note = typeof monthDue === 'object' ? monthDue.note : '';
                            
                            return (
                            <div key={index} className="space-y-1">
                              <button
                                type="button"
                                onClick={() => handleDuesToggle(index)}
                                className={`w-full px-3 py-2 rounded text-sm font-medium transition-colors ${
                                  status === 'paid'
                                    ? 'bg-green-600 text-white hover:bg-green-700'
                                    : status === 'late'
                                    ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                                    : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                                }`}
                                data-testid={`dues-month-${index}`}
                              >
                                {month}
                              </button>
                              {status === 'late' && (
                                <Input
                                  type="text"
                                  placeholder="Late reason..."
                                  value={note}
                                  onChange={(e) => handleDuesNoteChange(index, e.target.value)}
                                  className="text-xs bg-slate-900 border-slate-700 text-slate-100"
                                  onClick={(e) => e.stopPropagation()}
                                />
                              )}
                            </div>
                          )})}
                        </div>
                        <div className="text-xs text-slate-400 space-y-1">
                          <p>Click to cycle: <span className="text-slate-200">Unpaid</span> → <span className="text-green-400">Paid</span> → <span className="text-yellow-400">Late</span></p>
                          <p>Add note when marked as Late</p>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <Label>Meeting Attendance ({new Date().getFullYear()})</Label>
                        </div>
                        <div className="space-y-3">
                          {monthNames.map((month, monthIndex) => {
                            const currentYear = new Date().getFullYear().toString();
                            const yearMeetings = formData.meeting_attendance[currentYear] || Array(24).fill(null).map(() => ({ status: 0, note: "" }));
                            
                            return (
                            <div key={month} className="space-y-2">
                              <div className="grid grid-cols-2 gap-2">
                                <button
                                  type="button"
                                  onClick={() => handleAttendanceToggle(monthIndex * 2)}
                                  className={`px-2 py-2 rounded text-xs font-medium transition-colors ${
                                    yearMeetings[monthIndex * 2]?.status === 1
                                      ? 'bg-green-600 text-white hover:bg-green-700'
                                      : yearMeetings[monthIndex * 2]?.status === 2
                                      ? 'bg-orange-500 text-white hover:bg-orange-600'
                                      : 'bg-red-600 text-white hover:bg-red-700'
                                  }`}
                                  data-testid={`attendance-${monthIndex}-1st`}
                                >
                                  {month}-1st {meetingDates[monthIndex * 2] && `(${formatMeetingDate(meetingDates[monthIndex * 2])})`}
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleAttendanceToggle(monthIndex * 2 + 1)}
                                  className={`px-2 py-2 rounded text-xs font-medium transition-colors ${
                                    yearMeetings[monthIndex * 2 + 1]?.status === 1
                                      ? 'bg-green-600 text-white hover:bg-green-700'
                                      : yearMeetings[monthIndex * 2 + 1]?.status === 2
                                      ? 'bg-orange-500 text-white hover:bg-orange-600'
                                      : 'bg-red-600 text-white hover:bg-red-700'
                                  }`}
                                  data-testid={`attendance-${monthIndex}-3rd`}
                                >
                                  {month}-3rd {meetingDates[monthIndex * 2 + 1] && `(${formatMeetingDate(meetingDates[monthIndex * 2 + 1])})`}
                                </button>
                              </div>
                              {(yearMeetings[monthIndex * 2]?.status === 0 || yearMeetings[monthIndex * 2]?.status === 2) && (
                                <Input
                                  placeholder={`${month}-1st note (${yearMeetings[monthIndex * 2]?.status === 2 ? 'excused' : 'unexcused'} absence)`}
                                  value={yearMeetings[monthIndex * 2]?.note || ''}
                                  onChange={(e) => handleAttendanceNote(monthIndex * 2, e.target.value)}
                                  className="text-xs text-white"
                                />
                              )}
                              {(yearMeetings[monthIndex * 2 + 1]?.status === 0 || yearMeetings[monthIndex * 2 + 1]?.status === 2) && (
                                <Input
                                  placeholder={`${month}-3rd note (${yearMeetings[monthIndex * 2 + 1]?.status === 2 ? 'excused' : 'unexcused'} absence)`}
                                  value={yearMeetings[monthIndex * 2 + 1]?.note || ''}
                                  onChange={(e) => handleAttendanceNote(monthIndex * 2 + 1, e.target.value)}
                                  className="text-xs text-white"
                                />
                              )}
                            </div>
                          )})}
                        </div>
                        <p className="text-xs text-slate-600">
                          Click to cycle: <span className="font-medium">Gray (Absent)</span> → <span className="font-medium text-green-600">Green (Present)</span> → <span className="font-medium text-yellow-600">Yellow (Excused)</span>
                        </p>
                      </div>

                      <div className="flex gap-3 justify-end pt-4">
                        <Button
                          type="button"
                          variant="outline"
                          className="text-white"
                          onClick={() => {
                            setDialogOpen(false);
                            resetForm();
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          type="submit"
                          data-testid="submit-member-button"
                          className="bg-slate-800 hover:bg-slate-900 text-white"
                        >
                          {editingMember ? "Update" : "Add"} Member
                        </Button>
                      </div>
                    </form>
                  </DialogContent>
                </Dialog>
            </div>
          )}

          {loading ? (
            <div className="text-center py-12 text-slate-600">Loading members...</div>
          ) : sortedFilteredMembers.length === 0 ? (
            <div className="text-center py-12 text-slate-600">
              {searchTerm ? "No members found" : "No members yet. Add your first member!"}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-white">Chapter</TableHead>
                    <TableHead className="text-white">Title</TableHead>
                    <TableHead className="text-white">Handle</TableHead>
                    <TableHead className="text-white">Name</TableHead>
                    {hasPermission('email') && <TableHead className="text-white">Email</TableHead>}
                    {hasPermission('phone') && <TableHead className="text-white">Phone</TableHead>}
                    {hasPermission('address') && <TableHead className="text-white">Address</TableHead>}
                    {hasPermission('dues_tracking') && <TableHead className="text-white">Dues</TableHead>}
                    {hasPermission('meeting_attendance') && <TableHead className="text-white">Attendance</TableHead>}
                    {hasPermission('admin_actions') && <TableHead className="text-right text-white">Actions</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedFilteredMembers.map((member) => (
                    <TableRow key={member.id} data-testid={`member-row-${member.id}`}>
                      <TableCell className="font-medium text-white">{member.chapter}</TableCell>
                      <TableCell className="text-white">{member.title}</TableCell>
                      <TableCell className="text-white">{member.handle}</TableCell>
                      <TableCell className="text-white">{member.name}</TableCell>
                      {hasPermission('email') && (
                        <TableCell>
                          <a
                            href={`mailto:${member.email}`}
                            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline text-sm"
                            data-testid={`email-link-${member.id}`}
                          >
                            <Mail className="w-3 h-3" />
                            <span className="text-white">{member.email}</span>
                          </a>
                        </TableCell>
                      )}
                      {hasPermission('phone') && (
                        <TableCell>
                          <a
                            href={`tel:${member.phone}`}
                            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline text-sm"
                            data-testid={`phone-link-${member.id}`}
                          >
                            <Phone className="w-3 h-3" />
                            <span className="text-white">{member.phone}</span>
                          </a>
                        </TableCell>
                      )}
                      {hasPermission('address') && (
                        <TableCell>
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                              member.address
                            )}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline text-sm"
                            data-testid={`address-link-${member.id}`}
                          >
                            <MapPin className="w-3 h-3" />
                            <span className="text-white">{member.address}</span>
                          </a>
                        </TableCell>
                      )}
                      {hasPermission('dues_tracking') && (
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            {(() => {
                              const dues = member.dues || {};
                              
                              // Handle old format where dues has 'year' and 'months' keys
                              if (dues.year && dues.months && Array.isArray(dues.months)) {
                                const paidCount = dues.months.filter(m => m === true).length;
                                return (
                                  <>
                                    <span className="text-xs text-white">{dues.year}</span>
                                    <div className="flex items-center gap-2 text-xs">
                                      <span className="text-green-400 font-medium">
                                        Paid: {paidCount}
                                      </span>
                                    </div>
                                  </>
                                );
                              }
                              
                              // Handle new format where dues is object with years as keys
                              const years = Object.keys(dues).filter(k => k !== 'year' && k !== 'months').sort((a, b) => b - a);
                              const latestYear = years[0] || new Date().getFullYear();
                              const months = dues[latestYear] || [];
                              
                              if (!Array.isArray(months) || months.length === 0) {
                                return (
                                  <>
                                    <span className="text-xs text-white">{latestYear}</span>
                                    <span className="text-xs text-white">No data</span>
                                  </>
                                );
                              }
                              
                              // Handle both old boolean format and new object format
                              const paidCount = months.filter(m => 
                                typeof m === 'object' ? m.status === 'paid' : m === true
                              ).length;
                              const lateCount = months.filter(m => 
                                typeof m === 'object' && m.status === 'late'
                              ).length;
                              
                              return (
                                <>
                                  <span className="text-xs text-white">{latestYear}</span>
                                  <div className="flex items-center gap-2 text-xs">
                                    <span className="text-green-400 font-medium">
                                      Paid: {paidCount}
                                    </span>
                                    {lateCount > 0 && (
                                      <span className="text-yellow-400 font-medium">
                                        Late: {lateCount}
                                      </span>
                                    )}
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        </TableCell>
                      )}
                      {hasPermission('meeting_attendance') && (
                        <TableCell>
                          <div className="flex flex-col gap-0.5">
                            <span className="text-xs text-white">{member.meeting_attendance?.year || new Date().getFullYear()}</span>
                            <div className="flex items-center gap-1 text-xs">
                              <span className="text-green-600 font-medium">
                                P:{member.meeting_attendance?.meetings?.filter(m => (typeof m === 'object' ? m.status === 1 : m === 1)).length || 0}
                              </span>
                              <span className="text-yellow-600 font-medium">
                                E:{member.meeting_attendance?.meetings?.filter(m => (typeof m === 'object' ? m.status === 2 : m === 2)).length || 0}
                              </span>
                              <span className="text-slate-500">
                                A:{member.meeting_attendance?.meetings?.filter(m => (typeof m === 'object' ? (m.status === 0 || !m.status) : (m === 0 || !m))).length || 24}
                              </span>
                            </div>
                          </div>
                        </TableCell>
                      )}
                      {hasPermission('admin_actions') && (
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1.5">
                            {/* Info/View Group */}
                            <div className="flex gap-1 p-1 bg-slate-700/20 rounded border border-slate-600/30">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-blue-500 hover:text-blue-600 hover:bg-blue-950/50 h-8 w-8 p-0"
                                onClick={() => handleOpenActions(member)}
                                title="View/Add Actions"
                              >
                                <FileText className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-slate-300 hover:text-white hover:bg-slate-600 h-8 w-8 p-0"
                                onClick={() => handleEdit(member)}
                                data-testid={`edit-member-${member.id}`}
                                title="Edit Member"
                              >
                                <Pencil className="w-4 h-4" />
                              </Button>
                            </div>
                            
                            {/* Delete Action */}
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-red-500 hover:text-red-600 hover:bg-red-950/50 h-8 w-8 p-0"
                              onClick={() => handleDelete(member)}
                              data-testid={`delete-member-${member.id}`}
                              title="Archive Member"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>

        {/* Actions Dialog */}
        <Dialog open={actionsDialogOpen} onOpenChange={setActionsDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Actions History - {selectedMember?.handle}</DialogTitle>
            </DialogHeader>
            {selectedMember && (
              <div className="space-y-6 mt-4">
                {/* Existing Actions List */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-100 mb-3">History</h3>
                  {selectedMember.actions && selectedMember.actions.length > 0 ? (
                    <div className="space-y-2">
                      {selectedMember.actions.sort((a, b) => new Date(b.date) - new Date(a.date)).map((action) => (
                        <div key={action.id} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                action.type === 'merit' ? 'bg-green-600 text-white' :
                                action.type === 'promotion' ? 'bg-blue-600 text-white' :
                                'bg-red-600 text-white'
                              }`}>
                                {action.type.toUpperCase()}
                              </span>
                              <span className="text-slate-400 text-sm">{action.date}</span>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-blue-600 hover:text-blue-700"
                                onClick={() => handleEditAction(action)}
                                title="Edit Action"
                              >
                                <Pencil className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-red-600 hover:text-red-700"
                                onClick={() => handleDeleteAction(action.id)}
                                title="Delete Action"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          <p className="text-slate-200 text-sm mb-2">{action.description}</p>
                          <p className="text-slate-500 text-xs">
                            Added by {action.added_by} on {new Date(action.added_at).toLocaleDateString('en-US', { timeZone: 'America/Chicago' })}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 text-sm">No actions recorded yet.</p>
                  )}
                </div>

                {/* Add/Edit Action Form */}
                <div className="border-t border-slate-700 pt-6">
                  <h3 className="text-lg font-semibold text-slate-100 mb-3">
                    {editingAction ? 'Edit Action' : 'Add New Action'}
                  </h3>
                  <form onSubmit={editingAction ? handleUpdateAction : handleAddAction} className="space-y-4">
                    <div>
                      <Label className="text-white">Type</Label>
                      <Select
                        value={actionForm.type}
                        onValueChange={(value) => setActionForm({ ...actionForm, type: value })}
                      >
                        <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                          <SelectValue className="text-white" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-700 border-slate-600">
                          <SelectItem value="merit" className="text-white hover:bg-slate-600">Merit</SelectItem>
                          <SelectItem value="promotion" className="text-white hover:bg-slate-600">Promotion</SelectItem>
                          <SelectItem value="disciplinary" className="text-white hover:bg-slate-600">Disciplinary</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label className="text-white">Date</Label>
                      <Input
                        type="date"
                        value={actionForm.date}
                        onChange={(e) => setActionForm({ ...actionForm, date: e.target.value })}
                        required
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>

                    <div>
                      <Label className="text-white">Description</Label>
                      <Textarea
                        value={actionForm.description}
                        onChange={(e) => setActionForm({ ...actionForm, description: e.target.value })}
                        placeholder="Enter action details..."
                        rows={4}
                        required
                        className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                      />
                    </div>

                    <div className="flex gap-3 justify-end">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={editingAction ? handleCancelEdit : () => setActionsDialogOpen(false)}
                        className="border-slate-600 text-white hover:bg-slate-700"
                      >
                        {editingAction ? 'Cancel' : 'Close'}
                      </Button>
                      <Button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white">
                        {editingAction ? 'Update Action' : 'Add Action'}
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog - Custom Implementation */}
        {deleteDialogOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div 
              className="absolute inset-0 bg-black/80" 
              onClick={() => setDeleteDialogOpen(false)}
            />
            
            {/* Dialog */}
            <div className="relative bg-slate-800 border border-slate-700 rounded-lg p-6 mx-4 max-w-sm w-full shadow-xl">
              {/* Header */}
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-white">Archive Member</h3>
                <button 
                  onClick={() => setDeleteDialogOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              
              {memberToDelete && (
                <div className="space-y-4">
                  <p className="text-slate-200 text-sm">
                    You are about to archive <span className="font-semibold text-white">{memberToDelete.handle} - {memberToDelete.name}</span>. 
                    This action will move the member to the archived records.
                  </p>
                  
                  <div>
                    <label className="block text-sm text-slate-300 mb-2">
                      Reason for Archiving *
                    </label>
                    <textarea
                      value={deleteReason}
                      onChange={(e) => setDeleteReason(e.target.value)}
                      placeholder="Enter reason..."
                      rows={2}
                      required
                      className="w-full p-2 text-sm bg-slate-700 border border-slate-600 rounded text-white placeholder:text-slate-400"
                    />
                  </div>
                  
                  {/* Buttons */}
                  <div className="flex gap-3 justify-end pt-4 border-t border-slate-700">
                    <button
                      type="button"
                      onClick={() => setDeleteDialogOpen(false)}
                      className="px-4 py-2 text-sm border border-slate-600 text-slate-300 hover:text-white hover:border-slate-500 rounded"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirmDelete}
                      className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded"
                    >
                      Archive Member
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}