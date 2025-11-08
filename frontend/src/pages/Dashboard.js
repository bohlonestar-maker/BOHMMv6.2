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
  const [actionsDialogOpen, setActionsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [memberToDelete, setMemberToDelete] = useState(null);
  const [deleteReason, setDeleteReason] = useState("");
  const [selectedMember, setSelectedMember] = useState(null);
  const [actionForm, setActionForm] = useState({ type: "merit", date: "", description: "" });
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

  const handleViewCSV = async () => {
    const token = localStorage.getItem("token");
    
    try {
      const response = await axios.get(`${API}/members/export/csv`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "text",
      });
      
      const csvData = response.data;
      
      // Escape the CSV data for embedding in JavaScript
      const escapedCSV = csvData
        .replace(/\\/g, '\\\\')
        .replace(/`/g, '\\`')
        .replace(/\$/g, '\\$');
      
      // Open CSV in new window with formatted view
      const csvWindow = window.open("", "_blank");
      csvWindow.document.write(`
        <html>
          <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
            <meta charset="UTF-8">
            <title>Members Export - Brothers of the Highway</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
              * {
                box-sizing: border-box;
              }
              
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                color: #e2e8f0;
                padding: 10px;
                margin: 0;
                min-height: 100vh;
              }
              
              .header {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 15px 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
              }
              
              h1 {
                color: white;
                margin: 0;
                font-size: 1.25rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 10px;
              }
              
              .subtitle {
                color: rgba(255, 255, 255, 0.9);
                font-size: 0.75rem;
                margin-top: 5px;
                font-weight: 400;
              }
              
              .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 10px;
                margin-bottom: 15px;
              }
              
              .stat-card {
                background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
                padding: 12px;
                border-radius: 10px;
                border: 1px solid #475569;
                text-align: center;
                transition: transform 0.2s, box-shadow 0.2s;
              }
              
              .stat-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
              }
              
              .stat-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #10b981;
                display: block;
              }
              
              .stat-label {
                font-size: 0.75rem;
                color: #94a3b8;
                margin-top: 4px;
              }
              
              .search-bar {
                background: #334155;
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 15px;
                border: 1px solid #475569;
              }
              
              .search-input {
                width: 100%;
                padding: 10px 12px;
                background: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 0.875rem;
                outline: none;
                transition: border-color 0.2s;
              }
              
              .search-input:focus {
                border-color: #10b981;
              }
              
              .search-input::placeholder {
                color: #64748b;
              }
              
              .controls {
                margin-bottom: 15px;
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
              }
              
              button {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.875rem;
                flex: 1 1 auto;
                min-width: 120px;
                touch-action: manipulation;
                -webkit-tap-highlight-color: transparent;
                box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
              }
              
              button:active {
                transform: scale(0.98);
                box-shadow: 0 1px 4px rgba(16, 185, 129, 0.4);
              }
              
              button i {
                font-size: 1rem;
              }
              
              .btn-secondary {
                background: linear-gradient(135deg, #475569 0%, #334155 100%);
                box-shadow: 0 2px 8px rgba(71, 85, 105, 0.3);
              }
              
              .table-container {
                overflow-x: auto;
                overflow-y: auto;
                background: #1e293b;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.4);
                max-height: calc(100vh - 350px);
                -webkit-overflow-scrolling: touch;
                border: 1px solid #334155;
              }
              
              table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.75rem;
                min-width: 800px;
              }
              
              th {
                background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
                color: #10b981;
                font-weight: 700;
                padding: 12px 8px;
                text-align: left;
                position: sticky;
                top: 0;
                border-bottom: 2px solid #10b981;
                white-space: nowrap;
                z-index: 10;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
              }
              
              tbody tr {
                transition: background-color 0.2s;
              }
              
              tbody tr:nth-child(even) {
                background: rgba(51, 65, 85, 0.3);
              }
              
              tbody tr:hover {
                background: rgba(16, 185, 129, 0.1);
              }
              
              td {
                padding: 10px 8px;
                border-bottom: 1px solid #334155;
                white-space: nowrap;
                font-size: 0.75rem;
                color: #cbd5e1;
              }
              
              tr:active td {
                background: rgba(16, 185, 129, 0.2);
              }
              
              .no-results {
                text-align: center;
                padding: 40px 20px;
                color: #64748b;
                font-size: 1rem;
              }
              
              .no-results i {
                font-size: 3rem;
                margin-bottom: 15px;
                display: block;
                opacity: 0.5;
              }
              
              pre {
                background: #1e293b;
                padding: 12px;
                border-radius: 8px;
                overflow-x: auto;
                border: 1px solid #475569;
                display: none;
                max-height: calc(100vh - 350px);
                font-size: 0.75rem;
                line-height: 1.4;
                -webkit-overflow-scrolling: touch;
                white-space: pre-wrap;
                word-wrap: break-word;
              }
              
              .scroll-hint {
                text-align: center;
                color: #94a3b8;
                font-size: 0.75rem;
                padding: 8px;
                background: #334155;
                border-radius: 6px;
                margin-top: 10px;
              }
              
              /* Tablet styles (768px and up) */
              @media (min-width: 768px) {
                body {
                  padding: 20px;
                }
                
                .header {
                  padding: 20px 25px;
                }
                
                h1 {
                  font-size: 1.75rem;
                }
                
                .subtitle {
                  font-size: 0.875rem;
                }
                
                .stats-grid {
                  grid-template-columns: repeat(3, 1fr);
                  gap: 15px;
                }
                
                .stat-card {
                  padding: 15px;
                }
                
                .stat-value {
                  font-size: 1.75rem;
                }
                
                .search-input {
                  font-size: 0.9375rem;
                  padding: 12px 15px;
                }
                
                .controls {
                  gap: 10px;
                  margin-bottom: 20px;
                }
                
                button {
                  padding: 12px 20px;
                  font-size: 0.9375rem;
                  flex: 0 1 auto;
                  min-width: 150px;
                }
                
                .table-container {
                  max-height: calc(100vh - 400px);
                }
                
                table {
                  font-size: 0.8125rem;
                }
                
                th, td {
                  padding: 12px 10px;
                  font-size: 0.8125rem;
                }
                
                pre {
                  font-size: 0.8125rem;
                  padding: 15px;
                }
                
                .scroll-hint {
                  font-size: 0.8125rem;
                }
              }
              
              /* Laptop/Desktop styles (1024px and up) */
              @media (min-width: 1024px) {
                body {
                  padding: 30px;
                  max-width: 1600px;
                  margin: 0 auto;
                }
                
                .header {
                  padding: 25px 30px;
                }
                
                h1 {
                  font-size: 2rem;
                }
                
                .subtitle {
                  font-size: 1rem;
                }
                
                .stat-value {
                  font-size: 2rem;
                }
                
                .stat-label {
                  font-size: 0.875rem;
                }
                
                .search-input {
                  font-size: 1rem;
                  padding: 14px 18px;
                }
                
                button {
                  font-size: 1rem;
                  min-width: 180px;
                  padding: 14px 24px;
                }
                
                button:hover {
                  transform: translateY(-2px);
                  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
                }
                
                .table-container {
                  max-height: calc(100vh - 450px);
                }
                
                table {
                  font-size: 0.875rem;
                }
                
                th, td {
                  font-size: 0.875rem;
                  padding: 14px 12px;
                }
                
                pre {
                  font-size: 0.875rem;
                }
              }
              
              /* Print styles */
              @media print {
                @page {
                  size: landscape;
                  margin: 0.5cm;
                }
                
                * {
                  -webkit-print-color-adjust: exact !important;
                  print-color-adjust: exact !important;
                }
                
                body {
                  background: white !important;
                  color: black !important;
                  padding: 0 !important;
                  margin: 0 !important;
                  font-size: 7pt !important;
                }
                
                .header {
                  background: #10b981 !important;
                  padding: 10px !important;
                  margin-bottom: 10px !important;
                  page-break-after: avoid;
                }
                
                .header h1 {
                  font-size: 14pt !important;
                  color: white !important;
                }
                
                .subtitle {
                  font-size: 9pt !important;
                  color: white !important;
                }
                
                .stats-grid {
                  display: flex !important;
                  justify-content: space-between !important;
                  margin-bottom: 10px !important;
                  page-break-after: avoid;
                  page-break-inside: avoid;
                }
                
                .stat-card {
                  border: 1px solid #ccc !important;
                  padding: 5px 10px !important;
                  background: #f8f9fa !important;
                  flex: 1;
                  margin: 0 5px !important;
                }
                
                .stat-value {
                  font-size: 12pt !important;
                  color: #10b981 !important;
                }
                
                .stat-label {
                  font-size: 8pt !important;
                  color: #333 !important;
                }
                
                .controls, .scroll-hint, .search-bar, #rawCSV {
                  display: none !important;
                }
                
                .table-container {
                  max-height: none !important;
                  overflow: visible !important;
                  box-shadow: none !important;
                  background: white !important;
                  border: none !important;
                }
                
                table {
                  width: 100% !important;
                  min-width: 100% !important;
                  font-size: 6pt !important;
                  border-collapse: collapse !important;
                  page-break-inside: auto;
                }
                
                thead {
                  display: table-header-group;
                  page-break-inside: avoid;
                  page-break-after: avoid;
                }
                
                tbody {
                  display: table-row-group;
                }
                
                tr {
                  page-break-inside: avoid;
                  page-break-after: auto;
                }
                
                th {
                  background: #e5e7eb !important;
                  color: #000 !important;
                  font-weight: bold !important;
                  padding: 4px 2px !important;
                  border: 1px solid #999 !important;
                  font-size: 6pt !important;
                  text-align: left !important;
                  white-space: nowrap !important;
                  position: static !important;
                }
                
                td {
                  padding: 3px 2px !important;
                  border: 1px solid #ddd !important;
                  font-size: 6pt !important;
                  color: #000 !important;
                  white-space: nowrap !important;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  max-width: 150px;
                }
                
                tbody tr:nth-child(even) {
                  background: #f9fafb !important;
                }
                
                tbody tr:nth-child(odd) {
                  background: white !important;
                }
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>
                <i class="fas fa-table"></i>
                Members Export
              </h1>
              <div class="subtitle">Brothers of the Highway - Member Directory</div>
            </div>
            
            <div class="stats-grid">
              <div class="stat-card">
                <span class="stat-value" id="memberCount">0</span>
                <span class="stat-label">Total Members</span>
              </div>
              <div class="stat-card">
                <span class="stat-value" id="columnCount">69</span>
                <span class="stat-label">Data Columns</span>
              </div>
              <div class="stat-card">
                <span class="stat-value">${new Date().toLocaleDateString('en-US', {month: 'short', day: 'numeric'})}</span>
                <span class="stat-label">Export Date</span>
              </div>
            </div>
            
            <div class="search-bar">
              <input 
                type="text" 
                class="search-input" 
                id="searchInput" 
                placeholder="Search members by name, handle, chapter, or any field..."
                onkeyup="filterTable()"
              >
            </div>
            
            <div class="controls">
              <button onclick="openGoogleSheetsModal()" style="background: linear-gradient(135deg, #34a853 0%, #1e8e3e 100%);">
                <i class="fab fa-google"></i>
                Google Sheets
              </button>
              <button onclick="downloadFullCSV()">
                <i class="fas fa-download"></i>
                Download
              </button>
              <button class="btn-secondary" onclick="toggleView()">
                <i class="fas fa-code"></i>
                <span id="toggleText">Raw View</span>
              </button>
              <button class="btn-secondary" onclick="openPrintOptions()">
                <i class="fas fa-print"></i>
                Print Custom
              </button>
            </div>
            
            <div id="printNote" style="display: none; background: #fef3c7; color: #92400e; padding: 10px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #fbbf24;">
              <i class="fas fa-info-circle"></i>
              <strong>Print Tips:</strong> Set to Landscape orientation for best results. All columns will be printed.
            </div>
            
            <div id="googleSheetsModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center;" onclick="if(event.target.id === 'googleSheetsModal') closeGoogleSheetsModal()">
              <div style="background: #1e293b; padding: 30px; border-radius: 12px; max-width: 600px; margin: 20px; border: 2px solid #10b981; box-shadow: 0 20px 60px rgba(0,0,0,0.6);">
                <h2 style="color: #10b981; margin: 0 0 20px 0; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;">
                  <i class="fab fa-google" style="color: #34a853;"></i>
                  Export to Google Sheets
                </h2>
                
                <div style="background: #334155; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                  <div style="font-size: 0.875rem; line-height: 1.6;">
                    <p style="margin: 0 0 15px 0;"><strong>Step 1:</strong> Data will be copied to your clipboard</p>
                    <p style="margin: 0 0 15px 0;"><strong>Step 2:</strong> Google Sheets will open automatically</p>
                    <p style="margin: 0 0 15px 0;"><strong>Step 3:</strong> Press <strong>Ctrl+V</strong> (or <strong>Cmd+V</strong> on Mac) to paste</p>
                    <p style="margin: 0;">That's it! All your data will be in Google Sheets instantly.</p>
                  </div>
                </div>
                
                <div style="background: #059669; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                  <div style="font-size: 0.875rem; color: white; margin-bottom: 8px;">
                    <i class="fas fa-info-circle"></i> One-Click Export
                  </div>
                  <div style="color: white; font-size: 0.8rem; line-height: 1.5;">
                    Click the button below to copy all <span id="modalMemberCount">0</span> members with all <span id="modalColumnCount">0</span> columns to clipboard and open Google Sheets.
                  </div>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                  <button onclick="closeGoogleSheetsModal()" style="background: #475569; padding: 10px 20px; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600;">
                    Cancel
                  </button>
                  <button onclick="exportToGoogleSheets(); event.target.disabled=true;" style="background: linear-gradient(135deg, #34a853 0%, #1e8e3e 100%); padding: 12px 24px; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600; box-shadow: 0 2px 8px rgba(52, 168, 83, 0.3); font-size: 1rem;">
                    <i class="fab fa-google"></i> Copy & Open Google Sheets
                  </button>
                </div>
              </div>
            </div>
            
            <div id="printOptionsModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; overflow-y: auto; padding: 20px;" onclick="if(event.target.id === 'printOptionsModal') closePrintOptionsModal()">
              <div style="background: #1e293b; padding: 30px; border-radius: 12px; max-width: 700px; width: 100%; margin: auto; border: 2px solid #8b5cf6; box-shadow: 0 20px 60px rgba(0,0,0,0.6); max-height: 90vh; overflow-y: auto;">
                <h2 style="color: #8b5cf6; margin: 0 0 20px 0; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;">
                  <i class="fas fa-print"></i>
                  Customize Print Columns
                </h2>
                
                <div style="background: #334155; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                  <div style="font-size: 0.875rem; line-height: 1.6; color: #cbd5e1;">
                    <p style="margin: 0 0 10px 0;">Select which columns to include in your print output:</p>
                  </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                  <h3 style="color: #a78bfa; font-size: 1rem; margin: 0 0 10px 0;">Quick Presets:</h3>
                  <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                    <button onclick="selectPreset('all')" style="background: #6366f1; padding: 8px 16px; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 0.875rem; font-weight: 500;">
                      All Fields
                    </button>
                    <button onclick="selectPreset('contact')" style="background: #8b5cf6; padding: 8px 16px; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 0.875rem; font-weight: 500;">
                      Contact Info
                    </button>
                    <button onclick="selectPreset('dues')" style="background: #a855f7; padding: 8px 16px; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 0.875rem; font-weight: 500;">
                      Dues Tracking
                    </button>
                    <button onclick="selectPreset('meetings')" style="background: #c084fc; padding: 8px 16px; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 0.875rem; font-weight: 500;">
                      Meeting Attendance
                    </button>
                    <button onclick="selectPreset('none')" style="background: #64748b; padding: 8px 16px; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 0.875rem; font-weight: 500;">
                      Clear All
                    </button>
                  </div>
                </div>
                
                <div id="columnCheckboxes" style="background: #334155; padding: 20px; border-radius: 8px; margin-bottom: 20px; max-height: 300px; overflow-y: auto;">
                  <!-- Checkboxes will be populated by JavaScript -->
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                  <button onclick="closePrintOptionsModal()" style="background: #475569; padding: 10px 20px; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600;">
                    Cancel
                  </button>
                  <button onclick="printSelectedColumns()" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 12px 24px; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600; box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3); font-size: 1rem;">
                    <i class="fas fa-print"></i> Print Selected
                  </button>
                </div>
              </div>
            </div>
            
            <div id="content" class="table-container">
              <table id="csvTable"></table>
            </div>
            <div class="scroll-hint">
              <i class="fas fa-arrows-left-right"></i>
              Swipe or scroll horizontally to view all columns
            </div>
            <pre id="rawCSV"></pre>
            <script>
              // CSV data is embedded directly
              const csvText = \`${escapedCSV}\`.replace(/\\\\n/g, '\\n').replace(/\\\\t/g, '\\t');
              
              console.log('CSV data loaded, length:', csvText.length);
              
              if (!csvText || csvText.length === 0) {
                document.body.innerHTML = '<div style="padding: 40px; text-align: center;"><h1 style="color: #ef4444; font-size: 2rem; margin-bottom: 20px;"><i class="fas fa-exclamation-triangle"></i> Error Loading Data</h1><p style="color: #94a3b8; font-size: 1.2rem;">CSV data could not be loaded. Please try again.</p><button onclick="window.close()" style="margin-top: 20px; background: #10b981; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer;">Close Window</button></div>';
              } else {
                // Set raw CSV
                document.getElementById('rawCSV').textContent = csvText;
                
                function parseCSV(text) {
                  const lines = text.split('\\n').filter(line => line.trim());
                  const result = [];
                  for (let line of lines) {
                    const row = [];
                    let cell = '';
                    let inQuotes = false;
                    for (let i = 0; i < line.length; i++) {
                      const char = line[i];
                      if (char === '"') {
                        inQuotes = !inQuotes;
                      } else if (char === ',' && !inQuotes) {
                        row.push(cell.trim());
                        cell = '';
                      } else {
                        cell += char;
                      }
                    }
                    row.push(cell.trim());
                    result.push(row);
                  }
                  return result;
                }

                const csvData = parseCSV(csvText);
                const table = document.getElementById('csvTable');
                
                // Update member count
                document.getElementById('memberCount').textContent = csvData.length - 1;
                
                // Update Google Sheets modal counts
                const modalMemberCount = document.getElementById('modalMemberCount');
                const modalColumnCount = document.getElementById('modalColumnCount');
                if (modalMemberCount) modalMemberCount.textContent = csvData.length - 1;
                if (modalColumnCount) modalColumnCount.textContent = csvData[0].length;
                
                // Create header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                csvData[0].forEach(cell => {
                  const th = document.createElement('th');
                  th.textContent = cell;
                  headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Create body
                const tbody = document.createElement('tbody');
                tbody.id = 'tableBody';
                for (let i = 1; i < csvData.length; i++) {
                  const tr = document.createElement('tr');
                  tr.setAttribute('data-row', i);
                  csvData[i].forEach(cell => {
                    const td = document.createElement('td');
                    td.textContent = cell;
                    tr.appendChild(td);
                  });
                  tbody.appendChild(tr);
                }
                table.appendChild(tbody);
                
                // Store csvData globally for search
                window.csvData = csvData;

                function downloadFullCSV() {
                  // Create blob with the complete CSV data
                  const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'brothers_of_highway_members_' + new Date().toISOString().split('T')[0] + '.csv';
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  window.URL.revokeObjectURL(url);
                  alert('Complete CSV file downloaded with all ' + (csvData.length - 1) + ' members and ' + csvData[0].length + ' columns!');
                }

                function toggleView() {
                  const content = document.getElementById('content');
                  const rawCSV = document.getElementById('rawCSV');
                  const toggleText = document.getElementById('toggleText');
                  const scrollHint = document.querySelector('.scroll-hint');
                  
                  // Toggle visibility
                  if (content.style.display === 'none') {
                    // Show table view
                    content.style.display = 'block';
                    rawCSV.style.display = 'none';
                    if (scrollHint) scrollHint.style.display = 'block';
                    toggleText.textContent = 'Raw View';
                  } else {
                    // Show raw view
                    content.style.display = 'none';
                    rawCSV.style.display = 'block';
                    if (scrollHint) scrollHint.style.display = 'none';
                    toggleText.textContent = 'Table View';
                  }
                }
                
                function filterTable() {
                  const input = document.getElementById('searchInput');
                  const filter = input.value.toLowerCase();
                  const tbody = document.getElementById('tableBody');
                  const rows = tbody.getElementsByTagName('tr');
                  let visibleCount = 0;
                  
                  for (let i = 0; i < rows.length; i++) {
                    const row = rows[i];
                    const cells = row.getElementsByTagName('td');
                    let found = false;
                    
                    for (let j = 0; j < cells.length; j++) {
                      const cellText = cells[j].textContent || cells[j].innerText;
                      if (cellText.toLowerCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                      }
                    }
                    
                    if (found) {
                      row.style.display = '';
                      visibleCount++;
                    } else {
                      row.style.display = 'none';
                    }
                  }
                  
                  // Update member count with filtered results
                  const memberCount = document.getElementById('memberCount');
                  if (filter) {
                    memberCount.textContent = visibleCount + ' / ' + (csvData.length - 1);
                  } else {
                    memberCount.textContent = csvData.length - 1;
                  }
                  
                  // Show no results message
                  if (visibleCount === 0 && filter) {
                    if (!document.getElementById('noResults')) {
                      const noResults = document.createElement('div');
                      noResults.id = 'noResults';
                      noResults.className = 'no-results';
                      noResults.innerHTML = '<i class="fas fa-search"></i><div>No members found matching "' + filter + '"</div>';
                      tbody.appendChild(noResults);
                    }
                  } else {
                    const noResults = document.getElementById('noResults');
                    if (noResults) noResults.remove();
                  }
                }
                
                function preparePrint() {
                  try {
                    console.log('preparePrint called');
                    
                    // Show print note
                    const printNote = document.getElementById('printNote');
                    if (printNote) {
                      printNote.style.display = 'block';
                    }
                    
                    // Make sure we're in table view
                    const content = document.getElementById('content');
                    const rawCSV = document.getElementById('rawCSV');
                    
                    if (content && content.style.display === 'none') {
                      content.style.display = 'block';
                      if (rawCSV) rawCSV.style.display = 'none';
                    }
                    
                    // Remove any search filters for printing
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput && searchInput.value) {
                      const confirmClear = confirm('Clear search filter to print all members?');
                      if (confirmClear) {
                        searchInput.value = '';
                        if (typeof filterTable === 'function') {
                          filterTable();
                        }
                      } else {
                        if (printNote) printNote.style.display = 'none';
                        return;
                      }
                    }
                    
                    console.log('Opening print dialog');
                    
                    // Show print dialog after a brief delay
                    setTimeout(() => {
                      window.print();
                      // Hide print note after printing
                      setTimeout(() => {
                        if (printNote) printNote.style.display = 'none';
                      }, 500);
                    }, 300);
                  } catch (error) {
                    console.error('Error in preparePrint:', error);
                    alert('Print function error: ' + error.message);
                  }
                }
                
                function exportToGoogleSheets() {
                  // Show loading message
                  const modal = document.getElementById('googleSheetsModal');
                  modal.querySelector('h2').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing Export...';
                  modal.style.display = 'flex';
                  
                  // Convert CSV to TSV for better Google Sheets compatibility
                  const rows = csvText.split('\\n');
                  const tsvData = rows.map(row => {
                    // Parse CSV properly handling quotes
                    const cells = [];
                    let cell = '';
                    let inQuotes = false;
                    for (let i = 0; i < row.length; i++) {
                      const char = row[i];
                      if (char === '"') {
                        inQuotes = !inQuotes;
                      } else if (char === ',' && !inQuotes) {
                        cells.push(cell);
                        cell = '';
                      } else {
                        cell += char;
                      }
                    }
                    cells.push(cell);
                    return cells.join('\\t');
                  }).join('\\n');
                  
                  // Copy TSV to clipboard
                  if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(tsvData).then(() => {
                      // Update modal with success message
                      modal.querySelector('h2').innerHTML = '<i class="fas fa-check-circle" style="color: #10b981;"></i> Ready to Paste!';
                      const contentDiv = modal.querySelector('div[style*="background: #334155"]');
                      contentDiv.innerHTML = '<div style="font-size: 1rem; line-height: 1.8; text-align: center;"><p style="margin: 0 0 20px 0; font-size: 1.2rem; color: #10b981;"><strong>✓ Data copied to clipboard!</strong></p><p style="margin: 0 0 15px 0;">Google Sheets will open in a new tab.</p><p style="margin: 0 0 15px 0;"><strong style="color: #10b981;">Simply press Ctrl+V (or Cmd+V on Mac)</strong></p><p style="margin: 0;">to paste all ' + (csvData.length - 1) + ' members with all ' + csvData[0].length + ' columns!</p></div>';
                      
                      // Open Google Sheets
                      setTimeout(() => {
                        window.open('https://sheets.google.com/create', '_blank');
                        
                        // Auto-close modal after opening
                        setTimeout(() => {
                          closeGoogleSheetsModal();
                          // Reset modal content for next use
                          setTimeout(() => {
                            modal.querySelector('h2').innerHTML = '<i class="fab fa-google" style="color: #34a853;"></i> Export to Google Sheets';
                          }, 500);
                        }, 2000);
                      }, 800);
                    }).catch(err => {
                      // Fallback if clipboard fails
                      console.error('Clipboard error:', err);
                      downloadAndOpenSheets();
                    });
                  } else {
                    // Fallback for browsers without clipboard API
                    downloadAndOpenSheets();
                  }
                }
                
                function closeGoogleSheetsModal() {
                  const modal = document.getElementById('googleSheetsModal');
                  modal.style.display = 'none';
                }
                
                function downloadAndOpenSheets() {
                  const modal = document.getElementById('googleSheetsModal');
                  modal.querySelector('h2').innerHTML = '<i class="fab fa-google" style="color: #34a853;"></i> Export to Google Sheets';
                  const contentDiv = modal.querySelector('div[style*="background: #334155"]');
                  contentDiv.innerHTML = '<div style="font-size: 0.875rem; line-height: 1.6;"><p style="margin: 0 0 15px 0;"><strong>Step 1:</strong> File will download automatically</p><p style="margin: 0 0 15px 0;"><strong>Step 2:</strong> Google Sheets will open in a new tab</p><p style="margin: 0 0 15px 0;"><strong>Step 3:</strong> Click <strong>File → Import</strong></p><p style="margin: 0 0 15px 0;"><strong>Step 4:</strong> Click <strong>Upload</strong> tab and select the downloaded file</p><p style="margin: 0;"><strong>Step 5:</strong> Click <strong>Import data</strong></p></div>';
                  
                  // Download the CSV file
                  const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'brothers_of_highway_members_' + new Date().toISOString().split('T')[0] + '.csv';
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  window.URL.revokeObjectURL(url);
                  
                  // Open Google Sheets in new tab
                  setTimeout(() => {
                    window.open('https://sheets.google.com/create', '_blank');
                  }, 500);
                  
                  // Close modal after a delay
                  setTimeout(() => {
                    closeGoogleSheetsModal();
                  }, 3000);
                }
                
                function openGoogleSheetsModal() {
                  const modal = document.getElementById('googleSheetsModal');
                  modal.style.display = 'flex';
                }
                
                function openPrintOptions() {
                  const modal = document.getElementById('printOptionsModal');
                  const checkboxContainer = document.getElementById('columnCheckboxes');
                  
                  // Clear previous checkboxes
                  checkboxContainer.innerHTML = '';
                  
                  // Get all column headers
                  const headers = csvData[0];
                  
                  // Create checkboxes for each column
                  headers.forEach((header, index) => {
                    const checkboxDiv = document.createElement('div');
                    checkboxDiv.style.cssText = 'display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 6px; transition: background 0.2s;';
                    checkboxDiv.onmouseenter = function() { this.style.background = '#475569'; };
                    checkboxDiv.onmouseleave = function() { this.style.background = 'transparent'; };
                    
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.id = 'col_' + index;
                    checkbox.value = index;
                    checkbox.checked = true; // All selected by default
                    checkbox.style.cssText = 'width: 18px; height: 18px; cursor: pointer; accent-color: #8b5cf6;';
                    
                    const label = document.createElement('label');
                    label.htmlFor = 'col_' + index;
                    label.textContent = header;
                    label.style.cssText = 'cursor: pointer; color: #e2e8f0; font-size: 0.875rem; flex: 1;';
                    
                    checkboxDiv.appendChild(checkbox);
                    checkboxDiv.appendChild(label);
                    checkboxContainer.appendChild(checkboxDiv);
                  });
                  
                  modal.style.display = 'flex';
                }
                
                function closePrintOptionsModal() {
                  const modal = document.getElementById('printOptionsModal');
                  modal.style.display = 'none';
                }
                
                function selectPreset(preset) {
                  const headers = csvData[0];
                  const checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
                  
                  checkboxes.forEach((checkbox, index) => {
                    const header = headers[index].toLowerCase();
                    
                    switch(preset) {
                      case 'all':
                        checkbox.checked = true;
                        break;
                      case 'none':
                        checkbox.checked = false;
                        break;
                      case 'contact':
                        // Select: Name, Handle, Chapter, Title, Email, Phone, Address
                        checkbox.checked = header.includes('name') || 
                                          header.includes('handle') || 
                                          header.includes('chapter') || 
                                          header.includes('title') || 
                                          header.includes('email') || 
                                          header.includes('phone') || 
                                          header.includes('address');
                        break;
                      case 'dues':
                        // Select: Handle and anything with "dues" or "$"
                        checkbox.checked = header.includes('handle') || 
                                          header.includes('dues') || 
                                          header.includes('paid') ||
                                          header.includes('balance');
                        break;
                      case 'meetings':
                        // Select: Handle and meeting attendance dates
                        checkbox.checked = header.includes('handle') || 
                                          header.includes('meeting') || 
                                          header.includes('attendance') ||
                                          (header.match(/\d{2}\/\d{2}/) !== null); // Match date patterns like 01/01
                        break;
                    }
                  });
                }
                
                function printSelectedColumns() {
                  const checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
                  const selectedIndices = [];
                  
                  checkboxes.forEach((checkbox) => {
                    if (checkbox.checked) {
                      selectedIndices.push(parseInt(checkbox.value));
                    }
                  });
                  
                  if (selectedIndices.length === 0) {
                    alert('Please select at least one column to print.');
                    return;
                  }
                  
                  // Close the modal
                  closePrintOptionsModal();
                  
                  // Create a new window for custom print
                  const printWindow = window.open('', '_blank');
                  
                  // Filter CSV data to include only selected columns
                  const filteredData = csvData.map(row => {
                    return selectedIndices.map(index => row[index]);
                  });
                  
                  // Generate HTML for print
                  let printHTML = \`
<!DOCTYPE html>
<html>
<head>
  <title>Brothers of the Highway - Custom Print</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @media print {
      @page {
        size: landscape;
        margin: 0.5cm;
      }
      body {
        margin: 0;
        padding: 10px;
      }
      .no-print {
        display: none !important;
      }
    }
    
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      padding: 20px;
    }
    
    h1 {
      color: #8b5cf6;
      text-align: center;
      margin-bottom: 20px;
      font-size: 1.5rem;
    }
    
    .controls {
      text-align: center;
      margin-bottom: 20px;
    }
    
    button {
      background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
      margin: 0 5px;
    }
    
    button:hover {
      background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      background: #1e293b;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    th {
      background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
      color: white;
      padding: 10px 8px;
      text-align: left;
      font-weight: 600;
      font-size: 0.75rem;
      border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    th:last-child {
      border-right: none;
    }
    
    td {
      padding: 8px;
      border-bottom: 1px solid #334155;
      border-right: 1px solid #334155;
      font-size: 0.7rem;
      color: #cbd5e1;
    }
    
    td:last-child {
      border-right: none;
    }
    
    tr:last-child td {
      border-bottom: none;
    }
    
    tbody tr:hover {
      background: #334155;
    }
    
    @media print {
      body {
        background: white;
        color: black;
      }
      
      h1 {
        color: #7c3aed;
      }
      
      table {
        background: white;
        box-shadow: none;
      }
      
      th {
        background: #8b5cf6 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        color: white !important;
      }
      
      td {
        color: black;
        border-color: #ddd;
      }
      
      tbody tr:nth-child(even) {
        background: #f5f5f5;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
    }
  </style>
</head>
<body>
  <div class="controls no-print">
    <button onclick="window.print()">
      <i class="fas fa-print"></i> Print
    </button>
    <button onclick="window.close()" style="background: #64748b;">
      <i class="fas fa-times"></i> Close
    </button>
  </div>
  
  <h1>
    <i class="fas fa-users"></i> Brothers of the Highway - Custom Export
  </h1>
  
  <table>
    <thead>
      <tr>
\`;
                  
                  // Add headers
                  filteredData[0].forEach(header => {
                    printHTML += \`        <th>\${header}</th>\n\`;
                  });
                  
                  printHTML += \`      </tr>
    </thead>
    <tbody>
\`;
                  
                  // Add data rows
                  for (let i = 1; i < filteredData.length; i++) {
                    printHTML += \`      <tr>\n\`;
                    filteredData[i].forEach(cell => {
                      printHTML += \`        <td>\${cell}</td>\n\`;
                    });
                    printHTML += \`      </tr>\n\`;
                  }
                  
                  printHTML += \`    </tbody>
  </table>
</body>
</html>
\`;
                  
                  printWindow.document.write(printHTML);
                  printWindow.document.close();
                  
                  // Automatically trigger print dialog after a short delay
                  setTimeout(() => {
                    printWindow.print();
                  }, 500);
                }
                
                // Make functions globally available
                window.downloadFullCSV = downloadFullCSV;
                window.toggleView = toggleView;
                window.filterTable = filterTable;
                window.preparePrint = preparePrint;
                window.openGoogleSheetsModal = openGoogleSheetsModal;
                window.exportToGoogleSheets = exportToGoogleSheets;
                window.closeGoogleSheetsModal = closeGoogleSheetsModal;
                window.downloadAndOpenSheets = downloadAndOpenSheets;
                window.openPrintOptions = openPrintOptions;
                window.closePrintOptionsModal = closePrintOptionsModal;
                window.selectPreset = selectPreset;
                window.printSelectedColumns = printSelectedColumns;
              }
            </script>
          </body>
        </html>
      `);
      csvWindow.document.close();
      toast.success("CSV opened in new window");
    } catch (error) {
      console.error("CSV export error:", error);
      toast.error("Failed to view CSV");
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
                        <div className="flex items-center space-x-2 mt-2">
                          <Checkbox
                            id="phone_private"
                            checked={formData.phone_private}
                            onCheckedChange={(checked) =>
                              setFormData({ ...formData, phone_private: checked })
                            }
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
                        <Label className="text-white">Join Date (optional)</Label>
                        <Input
                          type="date"
                          value={formData.join_date}
                          onChange={(e) =>
                            setFormData({ ...formData, join_date: e.target.value })
                          }
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
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-red-600 hover:text-red-700"
                              onClick={() => handleDeleteAction(action.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                          <p className="text-slate-200 text-sm mb-2">{action.description}</p>
                          <p className="text-slate-500 text-xs">
                            Added by {action.added_by} on {new Date(action.added_at).toLocaleDateString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 text-sm">No actions recorded yet.</p>
                  )}
                </div>

                {/* Add New Action Form */}
                <div className="border-t border-slate-700 pt-6">
                  <h3 className="text-lg font-semibold text-slate-100 mb-3">Add New Action</h3>
                  <form onSubmit={handleAddAction} className="space-y-4">
                    <div>
                      <Label>Type</Label>
                      <Select
                        value={actionForm.type}
                        onValueChange={(value) => setActionForm({ ...actionForm, type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="merit">Merit</SelectItem>
                          <SelectItem value="promotion">Promotion</SelectItem>
                          <SelectItem value="disciplinary">Disciplinary</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>Date</Label>
                      <Input
                        type="date"
                        value={actionForm.date}
                        onChange={(e) => setActionForm({ ...actionForm, date: e.target.value })}
                        required
                      />
                    </div>

                    <div>
                      <Label>Description</Label>
                      <Textarea
                        value={actionForm.description}
                        onChange={(e) => setActionForm({ ...actionForm, description: e.target.value })}
                        placeholder="Enter action details..."
                        rows={4}
                        required
                      />
                    </div>

                    <div className="flex gap-3 justify-end">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setActionsDialogOpen(false)}
                      >
                        Close
                      </Button>
                      <Button type="submit">Add Action</Button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Archive Member</DialogTitle>
            </DialogHeader>
            {memberToDelete && (
              <div className="space-y-4 mt-4">
                <p className="text-slate-200">
                  You are about to archive <span className="font-semibold">{memberToDelete.handle} - {memberToDelete.name}</span>. 
                  This action will move the member to the archived records.
                </p>
                <div>
                  <Label>Reason for Archiving *</Label>
                  <Textarea
                    value={deleteReason}
                    onChange={(e) => setDeleteReason(e.target.value)}
                    placeholder="Enter reason for archiving..."
                    rows={3}
                    required
                  />
                </div>
                <div className="flex gap-3 justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setDeleteDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleConfirmDelete}
                  >
                    Archive Member
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