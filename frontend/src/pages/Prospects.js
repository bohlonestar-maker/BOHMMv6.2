import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
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
import { LogOut, Plus, Pencil, Trash2, Download, Users, Mail, Phone, MapPin, MessageCircle, UserPlus, FileText, UserCheck, Printer } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageLayout from "@/components/PageLayout";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
    const firstWed = getNthWeekdayOfMonth(year, month, 3, 1);
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

export default function Prospects({ onLogout, userRole }) {
  const [prospects, setProspects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [promoteDialogOpen, setPromoteDialogOpen] = useState(false);
  const [bulkPromoteDialogOpen, setBulkPromoteDialogOpen] = useState(false);
  const [actionsDialogOpen, setActionsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingProspect, setEditingProspect] = useState(null);
  const [promotingProspect, setPromotingProspect] = useState(null);
  const [selectedProspects, setSelectedProspects] = useState([]);
  const [prospectToDelete, setProspectToDelete] = useState(null);
  const [deleteReason, setDeleteReason] = useState("");
  const [selectedProspect, setSelectedProspect] = useState(null);
  const [actionForm, setActionForm] = useState({ type: "merit", date: "", description: "" });
  const [searchTerm, setSearchTerm] = useState("");
  const [meetingDates, setMeetingDates] = useState([]);
  const [attendanceExpanded, setAttendanceExpanded] = useState(false);
  const [editingNoteIndex, setEditingNoteIndex] = useState(null);
  const [addMeetingDialogOpen, setAddMeetingDialogOpen] = useState(false);
  const [newMeetingDate, setNewMeetingDate] = useState("");
  const [newMeetingStatus, setNewMeetingStatus] = useState(1);
  const [showPrintModal, setShowPrintModal] = useState(false);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [csvData, setCsvData] = useState([]);
  const [newMeetingNote, setNewMeetingNote] = useState("");
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    handle: "",
    name: "",
    email: "",
    phone: "",
    address: "",
    dob: "",
    join_date: "",
    military_service: false,
    military_branch: "",
    is_first_responder: false,
    meeting_attendance: {
      [new Date().getFullYear().toString()]: []
    }
  });

  const [promoteFormData, setPromoteFormData] = useState({
    chapter: "",
    title: ""
  });

  useEffect(() => {
    fetchProspects();
  }, []);

  useEffect(() => {
    const dates = getMeetingDates(formData.meeting_attendance.year);
    setMeetingDates(dates);
  }, [formData.meeting_attendance.year]);

  const fetchProspects = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/prospects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setProspects(response.data);
    } catch (error) {
      toast.error("Failed to load prospects");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    try {
      if (editingProspect) {
        await axios.put(
          `${API}/prospects/${editingProspect.id}`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success("Prospect updated successfully");
      } else {
        await axios.post(`${API}/prospects`, formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success("Prospect added successfully");
      }
      fetchProspects();
      setDialogOpen(false);
      resetForm();
    } catch (error) {
      toast.error("Failed to save prospect");
    }
  };

  const handleEdit = (prospect) => {
    setEditingProspect(prospect);
    const currentYear = new Date().getFullYear().toString();
    
    // Handle meeting_attendance - support both old and new format
    let attendanceData = {};
    
    if (prospect.meeting_attendance) {
      if (prospect.meeting_attendance.year && prospect.meeting_attendance.meetings) {
        // Old format - convert to new flexible format
        const yearStr = prospect.meeting_attendance.year.toString();
        const meetings = prospect.meeting_attendance.meetings || [];
        attendanceData[yearStr] = meetings.map((m, idx) => {
          const monthIdx = Math.floor(idx / 2);
          const weekNum = (idx % 2) + 1;
          const approxDate = new Date(parseInt(yearStr), monthIdx, weekNum * 7);
          return {
            date: approxDate.toISOString().split('T')[0],
            status: typeof m === 'object' ? (m.status || 0) : (m || 0),
            note: typeof m === 'object' ? (m.note || '') : ''
          };
        }).filter(m => m.status !== 0 || m.note);
      } else {
        // New format - use as is
        attendanceData = { ...prospect.meeting_attendance };
      }
    }
    
    if (!attendanceData[currentYear]) {
      attendanceData[currentYear] = [];
    }

    setFormData({
      handle: prospect.handle,
      name: prospect.name,
      email: prospect.email,
      phone: prospect.phone,
      address: prospect.address,
      dob: prospect.dob || "",
      join_date: prospect.join_date || "",
      military_service: prospect.military_service || false,
      military_branch: prospect.military_branch || "",
      is_first_responder: prospect.is_first_responder || false,
      meeting_attendance: attendanceData
    });
    setDialogOpen(true);
  };

  const handleDelete = (prospect) => {
    setProspectToDelete(prospect);
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
      await axios.delete(`${API}/prospects/${prospectToDelete.id}`, {
        params: { reason: deleteReason },
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Prospect archived successfully");
      setDeleteDialogOpen(false);
      setProspectToDelete(null);
      setDeleteReason("");
      fetchProspects();
    } catch (error) {
      toast.error("Failed to archive prospect");
    }
  };

  const handlePromote = (prospect) => {
    setPromotingProspect(prospect);
    setPromoteFormData({
      chapter: "",
      title: ""
    });
    setPromoteDialogOpen(true);
  };

  const handlePromoteSubmit = async (e) => {
    e.preventDefault();
    
    if (!promoteFormData.chapter || !promoteFormData.title) {
      toast.error("Please select both chapter and title");
      return;
    }

    const token = localStorage.getItem("token");
    try {
      await axios.post(
        `${API}/prospects/${promotingProspect.id}/promote`,
        null,
        {
          params: {
            chapter: promoteFormData.chapter,
            title: promoteFormData.title
          },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success(`${promotingProspect.handle} promoted to member successfully!`);
      setPromoteDialogOpen(false);
      setPromotingProspect(null);
      fetchProspects();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to promote prospect");
    }
  };

  const handleToggleSelect = (prospectId) => {
    setSelectedProspects(prev => 
      prev.includes(prospectId) 
        ? prev.filter(id => id !== prospectId)
        : [...prev, prospectId]
    );
  };

  const handleSelectAll = () => {
    if (selectedProspects.length === filteredProspects.length) {
      setSelectedProspects([]);
    } else {
      setSelectedProspects(filteredProspects.map(p => p.id));
    }
  };

  const handleBulkPromote = () => {
    if (selectedProspects.length === 0) {
      toast.error("Please select prospects to promote");
      return;
    }
    setPromoteFormData({ chapter: "", title: "" });
    setBulkPromoteDialogOpen(true);
  };

  const handleBulkPromoteSubmit = async (e) => {
    e.preventDefault();
    
    if (!promoteFormData.chapter || !promoteFormData.title) {
      toast.error("Please select both chapter and title");
      return;
    }

    const token = localStorage.getItem("token");
    try {
      const response = await axios.post(
        `${API}/prospects/bulk-promote`,
        {
          prospect_ids: selectedProspects,
          chapter: promoteFormData.chapter,
          title: promoteFormData.title
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      toast.success(`Successfully promoted ${response.data.promoted_count} prospects!`);
      if (response.data.failed_count > 0) {
        toast.error(`Failed to promote ${response.data.failed_count} prospects`);
      }
      
      setBulkPromoteDialogOpen(false);
      setSelectedProspects([]);
      fetchProspects();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to bulk promote prospects");
    }
  };

  const handleOpenActions = (prospect) => {
    setSelectedProspect(prospect);
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
        `${API}/prospects/${selectedProspect.id}/actions`,
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
      fetchProspects(); // Refresh to get updated actions
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add action");
    }
  };

  const handleDeleteAction = async (actionId) => {
    if (!window.confirm("Are you sure you want to delete this action?")) return;

    const token = localStorage.getItem("token");
    try {
      await axios.delete(`${API}/prospects/${selectedProspect.id}/actions/${actionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Action deleted successfully");
      fetchProspects(); // Refresh to get updated actions
    } catch (error) {
      toast.error("Failed to delete action");
    }
  };

  const resetForm = () => {
    const currentYear = new Date().getFullYear().toString();
    setFormData({
      handle: "",
      name: "",
      email: "",
      phone: "",
      address: "",
      dob: "",
      join_date: "",
      military_service: false,
      military_branch: "",
      is_first_responder: false,
      meeting_attendance: {
        [currentYear]: []
      }
    });
    setEditingProspect(null);
  };

  const handleAttendanceToggle = (index) => {
    const yearMeetings = formData.meeting_attendance[selectedYear] || [];
    const newMeetings = [...yearMeetings];
    const currentStatus = newMeetings[index]?.status || 0;
    
    newMeetings[index] = {
      ...newMeetings[index],
      status: (currentStatus + 1) % 3
    };
    
    setFormData({
      ...formData,
      meeting_attendance: {
        ...formData.meeting_attendance,
        [selectedYear]: newMeetings
      }
    });
  };

  const handleAttendanceNoteChange = (index, note) => {
    const yearMeetings = formData.meeting_attendance[selectedYear] || [];
    const newMeetings = [...yearMeetings];
    
    newMeetings[index] = {
      ...newMeetings[index],
      note: note
    };
    
    setFormData({
      ...formData,
      meeting_attendance: {
        ...formData.meeting_attendance,
        [selectedYear]: newMeetings
      }
    });
  };

  const handleAddMeeting = () => {
    if (!newMeetingDate) {
      toast.error("Please select a date");
      return;
    }
    
    const meetingYear = newMeetingDate.split('-')[0];
    const yearMeetings = formData.meeting_attendance[meetingYear] || [];
    
    if (yearMeetings.some(m => m.date === newMeetingDate)) {
      toast.error("A meeting already exists for this date");
      return;
    }
    
    const newMeeting = {
      date: newMeetingDate,
      status: newMeetingStatus,
      note: newMeetingNote
    };
    
    const newMeetings = [...yearMeetings, newMeeting].sort((a, b) => a.date.localeCompare(b.date));
    
    setFormData({
      ...formData,
      meeting_attendance: {
        ...formData.meeting_attendance,
        [meetingYear]: newMeetings
      }
    });
    
    setNewMeetingDate("");
    setNewMeetingStatus(1);
    setNewMeetingNote("");
    setAddMeetingDialogOpen(false);
    toast.success("Meeting added");
  };

  const handleDeleteMeeting = (meetingIndex) => {
    const yearMeetings = formData.meeting_attendance[selectedYear] || [];
    const newMeetings = yearMeetings.filter((_, idx) => idx !== meetingIndex);
    
    setFormData({
      ...formData,
      meeting_attendance: {
        ...formData.meeting_attendance,
        [selectedYear]: newMeetings
      }
    });
    toast.success("Meeting removed");
  };

  const formatMeetingDate = (dateStr) => {
    if (!dateStr) return "";
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const handleExportCSV = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/prospects/export/csv`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'prospects.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("CSV exported successfully");
    } catch (error) {
      toast.error("Failed to export CSV");
    }
  };

  // Print Custom functions
  const fetchCSVData = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/prospects/export/csv`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Parse CSV text into array
      const text = response.data;
      const rows = [];
      let row = [];
      let cell = '';
      let inQuotes = false;
      
      for (let i = 0; i < text.length; i++) {
        const char = text[i];
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          row.push(cell.trim());
          cell = '';
        } else if ((char === '\n' || char === '\r') && !inQuotes) {
          if (cell || row.length > 0) {
            row.push(cell.trim());
            if (row.some(c => c)) rows.push(row);
            row = [];
            cell = '';
          }
        } else {
          cell += char;
        }
      }
      if (cell || row.length > 0) {
        row.push(cell.trim());
        if (row.some(c => c)) rows.push(row);
      }
      
      setCsvData(rows);
    } catch (error) {
      console.error("Failed to fetch CSV data:", error);
    }
  };

  const openPrintModal = async () => {
    await fetchCSVData();
    setShowPrintModal(true);
  };

  const selectPreset = (preset) => {
    if (!csvData[0]) return;
    
    const headers = csvData[0].map(h => h.toLowerCase());
    let columns = [];
    
    switch (preset) {
      case 'all':
        columns = headers.map((_, i) => i);
        break;
      case 'contact':
        columns = headers.map((h, i) => 
          ['handle', 'name', 'email', 'phone', 'address'].some(c => h.includes(c)) ? i : -1
        ).filter(i => i !== -1);
        break;
      case 'service':
        columns = headers.map((h, i) => 
          ['handle', 'name', 'military', 'first responder', 'branch'].some(c => h.includes(c)) ? i : -1
        ).filter(i => i !== -1);
        break;
      case 'meetings_q1':
        columns = headers.map((h, i) => 
          ['handle', 'name', 'jan', 'feb', 'mar'].some(c => h.includes(c)) ? i : -1
        ).filter(i => i !== -1);
        break;
      case 'meetings_q2':
        columns = headers.map((h, i) => 
          ['handle', 'name', 'apr', 'may', 'jun'].some(c => h.includes(c)) ? i : -1
        ).filter(i => i !== -1);
        break;
      case 'meetings_q3':
        columns = headers.map((h, i) => 
          ['handle', 'name', 'jul', 'aug', 'sep'].some(c => h.includes(c)) ? i : -1
        ).filter(i => i !== -1);
        break;
      case 'meetings_q4':
        columns = headers.map((h, i) => 
          ['handle', 'name', 'oct', 'nov', 'dec'].some(c => h.includes(c)) ? i : -1
        ).filter(i => i !== -1);
        break;
      default:
        break;
    }
    
    setSelectedColumns(columns);
  };

  const printSelectedColumns = () => {
    if (selectedColumns.length === 0) {
      toast.error("Please select at least one column");
      return;
    }
    
    const filteredData = csvData.map(row => 
      selectedColumns.map(colIndex => row[colIndex] || '')
    );
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Prospects Report</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 12px; }
            th { background-color: #4a5568; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            @media print { 
              body { margin: 0; }
              table { font-size: 10px; }
            }
          </style>
        </head>
        <body>
          <h2>Prospects Report</h2>
          <table>
            <thead>
              <tr>${filteredData[0]?.map(h => `<th>${h}</th>`).join('') || ''}</tr>
            </thead>
            <tbody>
              ${filteredData.slice(1).map(row => 
                `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`
              ).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  const filteredProspects = prospects.filter((prospect) => {
    const search = searchTerm.toLowerCase();
    return (
      prospect.name.toLowerCase().includes(search) ||
      prospect.handle.toLowerCase().includes(search)
    );
  });

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  const headerActions = (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs sm:text-sm text-slate-300">
        {localStorage.getItem("username")} ({userRole})
      </span>
      {userRole === 'admin' && (
        <Button
          onClick={() => navigate("/users")}
          variant="outline"
          size="sm"
          className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
        >
          <Users className="w-3 h-3 sm:w-4 sm:h-4" />
          <span className="hidden sm:inline">Admin</span>
        </Button>
      )}
      <Button
        onClick={onLogout}
        variant="outline"
        size="sm"
        className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
      >
        <LogOut className="w-3 h-3 sm:w-4 sm:h-4" />
        Logout
      </Button>
    </div>
  );

  return (
    <PageLayout
      title="Hangarounds/Prospects"
      icon={UserCheck}
      backTo="/"
      backLabel="Members"
      actions={headerActions}
    >
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
                placeholder="Search by name or handle..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 py-4 sm:py-6 text-sm sm:text-base bg-slate-900 border-2 border-slate-700 text-slate-100 focus:border-slate-600 rounded-lg placeholder:text-white"
              />
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mb-4 sm:mb-6">
            <div className="flex gap-2 flex-wrap">
              <Button
                onClick={handleExportCSV}
                size="sm"
                className="flex items-center justify-center gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </Button>

              <Button
                onClick={openPrintModal}
                size="sm"
                className="flex items-center justify-center gap-2 text-xs sm:text-sm bg-purple-700 text-white hover:bg-purple-800"
              >
                <Printer className="w-4 h-4" />
                Print Custom
              </Button>

              {selectedProspects.length > 0 && (
                <Button
                  onClick={handleBulkPromote}
                  size="sm"
                  className="flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white"
                >
                  <UserPlus className="w-4 h-4" />
                  Bulk Promote ({selectedProspects.length})
                </Button>
              )}

              <Dialog open={dialogOpen} onOpenChange={(open) => {
                setDialogOpen(open);
                if (!open) resetForm();
              }}>
                <DialogTrigger asChild>
                  <Button
                    size="sm"
                    className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-900 text-white"
                  >
                    <Plus className="w-4 h-4" />
                    Add Prospect
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-[95vw] sm:max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">
                    {editingProspect ? "Edit Prospect" : "Add New Prospect"}
                  </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label>Handle</Label>
                      <Input
                        value={formData.handle}
                        onChange={(e) => setFormData({ ...formData, handle: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label>Phone</Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label>Address</Label>
                    <Input
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <Label>Date of Birth (optional)</Label>
                    <Input
                      type="date"
                      value={formData.dob}
                      onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
                    />
                  </div>

                  <div>
                    <Label>Anniversary Date (MM/YYYY)</Label>
                    <Input
                      type="text"
                      placeholder="MM/YYYY"
                      value={formData.join_date}
                      onChange={(e) => {
                        let value = e.target.value.replace(/[^\d/]/g, '');
                        if (value.length === 2 && !value.includes('/') && formData.join_date.length < value.length) {
                          value = value + '/';
                        }
                        if (value.length <= 7) {
                          setFormData({ ...formData, join_date: value });
                        }
                      }}
                    />
                  </div>

                  {/* Military Service Section */}
                  <div className="space-y-3 p-3 bg-slate-800 rounded-lg border border-slate-700">
                    <Label className="text-white font-semibold">🎖️ Military Service</Label>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="prospect_military_service"
                        checked={formData.military_service || false}
                        onCheckedChange={(checked) =>
                          setFormData({ ...formData, military_service: checked, military_branch: checked ? formData.military_branch : "" })
                        }
                      />
                      <label htmlFor="prospect_military_service" className="text-sm text-slate-200 cursor-pointer">
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
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="prospect_is_first_responder"
                        checked={formData.is_first_responder || false}
                        onCheckedChange={(checked) =>
                          setFormData({ ...formData, is_first_responder: checked })
                        }
                      />
                      <label htmlFor="prospect_is_first_responder" className="text-sm text-slate-200 cursor-pointer">
                        Served as First Responder (Police, Fire, or EMS)
                      </label>
                    </div>
                  </div>

                  {/* Collapsible Meeting Attendance Section */}
                  <div className="border border-slate-600 rounded-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setAttendanceExpanded(!attendanceExpanded)}
                      className="w-full flex items-center justify-between p-3 bg-slate-700/50 hover:bg-slate-700 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <Label className="cursor-pointer text-base font-semibold">Meeting Attendance ({selectedYear})</Label>
                        {/* Summary counts */}
                        {(() => {
                          const yearMeetings = formData.meeting_attendance[selectedYear] || [];
                          const total = yearMeetings.length;
                          const present = yearMeetings.filter(m => m?.status === 1).length;
                          const excused = yearMeetings.filter(m => m?.status === 2).length;
                          const absent = yearMeetings.filter(m => m?.status === 0).length;
                          return (
                            <div className="flex gap-2 text-xs">
                              <span className="px-2 py-0.5 bg-slate-600 text-white rounded">{total} total</span>
                              <span className="px-2 py-0.5 bg-green-600 text-white rounded">{present} P</span>
                              <span className="px-2 py-0.5 bg-orange-500 text-white rounded">{excused} E</span>
                              <span className="px-2 py-0.5 bg-red-600/80 text-white rounded">{absent} A</span>
                            </div>
                          );
                        })()}
                      </div>
                      <svg 
                        className={`w-5 h-5 text-slate-400 transition-transform ${attendanceExpanded ? 'rotate-180' : ''}`}
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    
                    {attendanceExpanded && (
                      <div className="p-3 space-y-3 bg-slate-800/50">
                        {/* Year Selector and Add Meeting Button */}
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400">Year:</span>
                            <select
                              value={selectedYear}
                              onChange={(e) => setSelectedYear(e.target.value)}
                              className="bg-slate-700 border border-slate-600 text-white text-xs rounded px-2 py-1"
                            >
                              {[new Date().getFullYear().toString(), ...Object.keys(formData.meeting_attendance).filter(k => k !== new Date().getFullYear().toString())].sort((a, b) => b - a).map(year => (
                                <option key={year} value={year}>{year}</option>
                              ))}
                            </select>
                          </div>
                          <Button
                            type="button"
                            size="sm"
                            onClick={() => setAddMeetingDialogOpen(true)}
                            className="bg-blue-600 hover:bg-blue-700 text-xs h-7"
                          >
                            <Plus className="w-3 h-3 mr-1" />
                            Add Meeting
                          </Button>
                        </div>
                        
                        {/* Legend */}
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-slate-400">Click to cycle status</span>
                          <div className="flex gap-2">
                            <span className="text-green-500">● Present</span>
                            <span className="text-orange-500">● Excused</span>
                            <span className="text-red-500">● Absent</span>
                          </div>
                        </div>
                        
                        {/* Flexible Meetings List */}
                        {(() => {
                          const yearMeetings = formData.meeting_attendance[selectedYear] || [];
                          
                          if (yearMeetings.length === 0) {
                            return (
                              <div className="text-center py-4 text-slate-500 text-sm">
                                No meetings recorded for {selectedYear}
                                <p className="text-xs mt-1">Click &quot;Add Meeting&quot; to add one</p>
                              </div>
                            );
                          }
                          
                          return (
                            <div className="space-y-1 max-h-48 overflow-y-auto">
                              {yearMeetings.map((meeting, idx) => (
                                <div 
                                  key={idx} 
                                  className="flex items-center gap-2 p-2 bg-slate-900/50 rounded"
                                >
                                  <span className="text-xs text-slate-300 w-20 flex-shrink-0">
                                    {formatMeetingDate(meeting.date)}
                                  </span>
                                  
                                  <button
                                    type="button"
                                    onClick={() => handleAttendanceToggle(idx)}
                                    className={`px-2 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                                      meeting.status === 1
                                        ? 'bg-green-600 text-white'
                                        : meeting.status === 2
                                        ? 'bg-orange-500 text-white'
                                        : 'bg-red-600/80 text-white'
                                    }`}
                                  >
                                    {meeting.status === 1 ? 'Present' : meeting.status === 2 ? 'Excused' : 'Absent'}
                                  </button>
                                  
                                  <Input
                                    type="text"
                                    value={meeting.note || ''}
                                    onChange={(e) => handleAttendanceNoteChange(idx, e.target.value)}
                                    placeholder="Note..."
                                    className="flex-1 text-xs h-7 bg-slate-800 border-slate-600 text-white"
                                  />
                                  
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteMeeting(idx)}
                                    className="text-red-400 hover:text-red-300 p-1"
                                    title="Remove meeting"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                </div>
                              ))}
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </div>

                  {/* Add Meeting Dialog */}
                  <Dialog open={addMeetingDialogOpen} onOpenChange={setAddMeetingDialogOpen}>
                    <DialogContent className="bg-slate-800 border-slate-600 max-w-sm">
                      <DialogHeader>
                        <DialogTitle className="text-white">Add Meeting</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label className="text-slate-200">Date</Label>
                          <Input
                            type="date"
                            value={newMeetingDate}
                            onChange={(e) => setNewMeetingDate(e.target.value)}
                            className="mt-1 bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-200">Status</Label>
                          <Select value={newMeetingStatus.toString()} onValueChange={(v) => setNewMeetingStatus(parseInt(v))}>
                            <SelectTrigger className="mt-1 bg-slate-700 border-slate-600 text-white">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-600">
                              <SelectItem value="1" className="text-white hover:bg-slate-700">Present</SelectItem>
                              <SelectItem value="2" className="text-white hover:bg-slate-700">Excused</SelectItem>
                              <SelectItem value="0" className="text-white hover:bg-slate-700">Absent</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label className="text-slate-200">Note (optional)</Label>
                          <Input
                            value={newMeetingNote}
                            onChange={(e) => setNewMeetingNote(e.target.value)}
                            placeholder="e.g., reason for absence"
                            className="mt-1 bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                        <div className="flex gap-3 justify-end pt-2">
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => setAddMeetingDialogOpen(false)}
                            className="text-white border-slate-600"
                          >
                            Cancel
                          </Button>
                          <Button
                            type="button"
                            onClick={handleAddMeeting}
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            Add Meeting
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>

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
                    <Button type="submit" className="bg-slate-800 hover:bg-slate-900 text-white">
                      {editingProspect ? "Update" : "Save"}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
            </div>
          </div>

          {filteredProspects.length === 0 ? (
            <p className="text-center text-slate-400 py-8">No prospects found</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedProspects.length === filteredProspects.length && filteredProspects.length > 0}
                        onCheckedChange={handleSelectAll}
                        aria-label="Select all"
                        className="border-slate-400 data-[state=checked]:bg-green-600 data-[state=checked]:border-green-600"
                      />
                    </TableHead>
                    <TableHead>Handle</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Address</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProspects.map((prospect) => (
                    <TableRow key={prospect.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedProspects.includes(prospect.id)}
                          onCheckedChange={() => handleToggleSelect(prospect.id)}
                          aria-label={`Select ${prospect.handle}`}
                          className="border-slate-400 data-[state=checked]:bg-green-600 data-[state=checked]:border-green-600"
                        />
                      </TableCell>
                      <TableCell className="text-white">{prospect.handle}</TableCell>
                      <TableCell className="text-white">{prospect.name}</TableCell>
                      <TableCell>
                        <a
                          href={`mailto:${prospect.email}`}
                          className="flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline text-sm"
                        >
                          <Mail className="w-3 h-3" />
                          {prospect.email}
                        </a>
                      </TableCell>
                      <TableCell>
                        <a
                          href={`tel:${prospect.phone}`}
                          className="flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline text-sm"
                        >
                          <Phone className="w-3 h-3" />
                          {prospect.phone}
                        </a>
                      </TableCell>
                      <TableCell>
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(prospect.address)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-white hover:text-slate-300 hover:underline text-sm"
                        >
                          <MapPin className="w-3 h-3" />
                          {prospect.address}
                        </a>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1.5">
                          {/* Promote Action */}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-green-600 hover:text-green-700 hover:bg-green-950/50 h-8 w-8 p-0"
                            onClick={() => handlePromote(prospect)}
                            title="Promote to Member"
                          >
                            <UserPlus className="w-4 h-4" />
                          </Button>
                          
                          {/* Info/Edit Group */}
                          <div className="flex gap-1 p-1 bg-slate-700/20 rounded border border-slate-600/30">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-blue-500 hover:text-blue-600 hover:bg-blue-950/50 h-8 w-8 p-0"
                              onClick={() => handleOpenActions(prospect)}
                              title="View/Add Actions"
                            >
                              <FileText className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-slate-300 hover:text-white hover:bg-slate-600 h-8 w-8 p-0"
                              onClick={() => handleEdit(prospect)}
                              title="Edit Prospect"
                            >
                              <Pencil className="w-4 h-4" />
                            </Button>
                          </div>
                          
                          {/* Delete Action */}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-500 hover:text-red-600 hover:bg-red-950/50 h-8 w-8 p-0"
                            onClick={() => handleDelete(prospect)}
                            title="Archive Prospect"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>

        {/* Promote Dialog */}
        <Dialog open={promoteDialogOpen} onOpenChange={setPromoteDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Promote to Member</DialogTitle>
            </DialogHeader>
            {promotingProspect && (
              <form onSubmit={handlePromoteSubmit} className="space-y-4 mt-4">
                <div className="bg-slate-100 p-3 rounded-md">
                  <p className="text-sm text-slate-600">Promoting:</p>
                  <p className="font-semibold text-slate-900">{promotingProspect.handle} - {promotingProspect.name}</p>
                </div>

                <div>
                  <Label>Chapter *</Label>
                  <Select
                    value={promoteFormData.chapter}
                    onValueChange={(value) =>
                      setPromoteFormData({ ...promoteFormData, chapter: value })
                    }
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select chapter" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="National">National</SelectItem>
                      <SelectItem value="AD">AD - Asphalt Demons</SelectItem>
                      <SelectItem value="HA">HA - Highway Asylum</SelectItem>
                      <SelectItem value="HS">HS - Highway Souls</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Title *</Label>
                  <Select
                    value={promoteFormData.title}
                    onValueChange={(value) =>
                      setPromoteFormData({ ...promoteFormData, title: value })
                    }
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select title" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Prez">Prez - President</SelectItem>
                      <SelectItem value="VP">VP - Vice President</SelectItem>
                      <SelectItem value="S@A">S@A - Sergeant at Arms</SelectItem>
                      <SelectItem value="ENF">ENF - Enforcer</SelectItem>
                      <SelectItem value="SEC">SEC - Secretary</SelectItem>
                      <SelectItem value="T">T - Treasurer</SelectItem>
                      <SelectItem value="CD">CD - Club Director</SelectItem>
                      <SelectItem value="CC">CC - Club Chaplain</SelectItem>
                      <SelectItem value="CCLC">CCLC - Club Counselor & Life Coach</SelectItem>
                      <SelectItem value="MD">MD - Media Director</SelectItem>
                      <SelectItem value="PM">PM - Prospect Manager</SelectItem>
                      <SelectItem value="Member">Member</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-3 justify-end pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setPromoteDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    Promote to Member
                  </Button>
                </div>
              </form>
            )}
          </DialogContent>
        </Dialog>

        {/* Actions Dialog */}
        <Dialog open={actionsDialogOpen} onOpenChange={setActionsDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Actions History - {selectedProspect?.handle}</DialogTitle>
            </DialogHeader>
            {selectedProspect && (
              <div className="space-y-6 mt-4">
                {/* Existing Actions List */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-100 mb-3">History</h3>
                  {selectedProspect.actions && selectedProspect.actions.length > 0 ? (
                    <div className="space-y-2">
                      {selectedProspect.actions.sort((a, b) => new Date(b.date) - new Date(a.date)).map((action) => (
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
                          <p className="text-slate-400 text-xs">
                            Added by {action.added_by} on {new Date(action.added_at).toLocaleDateString('en-US', { timeZone: 'America/Chicago' })}
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
              <DialogTitle>Archive Prospect</DialogTitle>
            </DialogHeader>
            {prospectToDelete && (
              <div className="space-y-4 mt-4">
                <p className="text-slate-200">
                  You are about to archive <span className="font-semibold">{prospectToDelete.handle} - {prospectToDelete.name}</span>. 
                  This action will move the prospect to the archived records.
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
                    Archive Prospect
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Bulk Promote Dialog */}
        <Dialog open={bulkPromoteDialogOpen} onOpenChange={setBulkPromoteDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Bulk Promote to Members</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleBulkPromoteSubmit} className="space-y-4 mt-4">
              <div className="bg-slate-100 p-3 rounded-md">
                <p className="text-sm text-slate-600">Promoting {selectedProspects.length} prospects</p>
              </div>

              <div>
                <Label>Chapter *</Label>
                <Select
                  value={promoteFormData.chapter}
                  onValueChange={(value) =>
                    setPromoteFormData({ ...promoteFormData, chapter: value })
                  }
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select chapter" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="National">National</SelectItem>
                    <SelectItem value="AD">AD - Asphalt Demons</SelectItem>
                    <SelectItem value="HA">HA - Highway Asylum</SelectItem>
                    <SelectItem value="HS">HS - Highway Souls</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Title *</Label>
                <Select
                  value={promoteFormData.title}
                  onValueChange={(value) =>
                    setPromoteFormData({ ...promoteFormData, title: value })
                  }
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select title" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Prez">Prez - President</SelectItem>
                    <SelectItem value="VP">VP - Vice President</SelectItem>
                    <SelectItem value="S@A">S@A - Sergeant at Arms</SelectItem>
                    <SelectItem value="ENF">ENF - Enforcer</SelectItem>
                    <SelectItem value="SEC">SEC - Secretary</SelectItem>
                    <SelectItem value="T">T - Treasurer</SelectItem>
                    <SelectItem value="CD">CD - Club Director</SelectItem>
                    <SelectItem value="CC">CC - Club Chaplain</SelectItem>
                    <SelectItem value="CCLC">CCLC - Club Counselor & Life Coach</SelectItem>
                    <SelectItem value="MD">MD - Media Director</SelectItem>
                    <SelectItem value="PM">PM - Prospect Manager</SelectItem>
                    <SelectItem value="Member">Member</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-3 justify-end pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setBulkPromoteDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  Promote {selectedProspects.length} to Members
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
    </PageLayout>
  );
}
