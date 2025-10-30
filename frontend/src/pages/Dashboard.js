import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { LogOut, Plus, Pencil, Trash2, Download, Users, Mail, Phone, MapPin, MessageCircle, Clock, LifeBuoy } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHAPTERS = ["National", "AD", "HA", "HS"];
const TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM"];

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
  const [editingMember, setEditingMember] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [meetingDates, setMeetingDates] = useState([]);
  const [unreadPrivateCount, setUnreadPrivateCount] = useState(0);
  const [openSupportCount, setOpenSupportCount] = useState(0);
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
    fetchOpenSupportCount();
    // Auto-refresh counts every 30 seconds
    const interval = setInterval(() => {
      fetchUnreadPrivateCount();
      fetchOpenSupportCount();
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


  const fetchOpenSupportCount = async () => {
    // Only fetch if user is Lonestar
    if (localStorage.getItem("username") !== "Lonestar") {
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/support/messages/count`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOpenSupportCount(response.data.count);
    } catch (error) {
      if (!handleApiError(error, "Failed to fetch support messages count")) {
        console.error("Failed to fetch support messages count:", error);
      }
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

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this member?")) return;

    const token = localStorage.getItem("token");
    try {
      await axios.delete(`${API}/members/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Member deleted successfully");
      fetchMembers();
    } catch (error) {
      toast.error("Failed to delete member");
    }
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
      toast.success("CSV exported successfully");
    } catch (error) {
      toast.error("Failed to export CSV");
    }
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
                    onClick={() => navigate("/support-center")}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600 relative"
                  >
                    <LifeBuoy className="w-3 h-3 sm:w-4 sm:h-4" />
                    <span className="hidden sm:inline">Support</span>
                    {openSupportCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {openSupportCount > 9 ? '9+' : openSupportCount}
                      </span>
                    )}
                  </Button>
                )}
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
                onClick={handleExportCSV}
                size="sm"
                data-testid="export-csv-button"
                className="flex items-center justify-center gap-2 w-full sm:w-auto bg-green-600 hover:bg-green-700 text-white"
              >
                <Download className="w-4 h-4" />
                Export CSV
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
                  <DialogContent className="max-w-[95vw] sm:max-w-2xl max-h-[90vh] overflow-y-auto">
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
                                      ? 'bg-yellow-500 text-white hover:bg-yellow-600'
                                      : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
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
                                      ? 'bg-yellow-500 text-white hover:bg-yellow-600'
                                      : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
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
                    <TableHead>Chapter</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Handle</TableHead>
                    <TableHead>Name</TableHead>
                    {hasPermission('email') && <TableHead>Email</TableHead>}
                    {hasPermission('phone') && <TableHead>Phone</TableHead>}
                    {hasPermission('address') && <TableHead>Address</TableHead>}
                    {hasPermission('dues_tracking') && <TableHead>Dues</TableHead>}
                    {hasPermission('meeting_attendance') && <TableHead>Attendance</TableHead>}
                    {hasPermission('admin_actions') && <TableHead className="text-right">Actions</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedFilteredMembers.map((member) => (
                    <TableRow key={member.id} data-testid={`member-row-${member.id}`}>
                      <TableCell className="font-medium">{member.chapter}</TableCell>
                      <TableCell>{member.title}</TableCell>
                      <TableCell>{member.handle}</TableCell>
                      <TableCell>{member.name}</TableCell>
                      {hasPermission('email') && (
                        <TableCell>
                          <a
                            href={`mailto:${member.email}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline text-sm"
                            data-testid={`email-link-${member.id}`}
                          >
                            <Mail className="w-3 h-3" />
                            {member.email}
                          </a>
                        </TableCell>
                      )}
                      {hasPermission('phone') && (
                        <TableCell>
                          <a
                            href={`tel:${member.phone}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline text-sm"
                            data-testid={`phone-link-${member.id}`}
                          >
                            <Phone className="w-3 h-3" />
                            {member.phone}
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
                            className="flex items-center gap-1 text-blue-600 hover:underline text-sm"
                            data-testid={`address-link-${member.id}`}
                          >
                            <MapPin className="w-3 h-3" />
                            {member.address}
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
                                    <span className="text-xs text-slate-400">{dues.year}</span>
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
                                    <span className="text-xs text-slate-400">{latestYear}</span>
                                    <span className="text-xs text-slate-400">No data</span>
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
                                  <span className="text-xs text-slate-400">{latestYear}</span>
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
                            <span className="text-xs text-slate-600">{member.meeting_attendance?.year || new Date().getFullYear()}</span>
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
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEdit(member)}
                              data-testid={`edit-member-${member.id}`}
                            >
                              <Pencil className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleDelete(member.id)}
                              data-testid={`delete-member-${member.id}`}
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
      </div>
    </div>
  );
}