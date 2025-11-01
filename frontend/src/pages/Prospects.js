import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { LogOut, Plus, Pencil, Trash2, Download, Users, Mail, Phone, MapPin, MessageCircle, UserPlus, FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";

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
  const [actionsDialogOpen, setActionsDialogOpen] = useState(false);
  const [editingProspect, setEditingProspect] = useState(null);
  const [promotingProspect, setPromotingProspect] = useState(null);
  const [selectedProspect, setSelectedProspect] = useState(null);
  const [actionForm, setActionForm] = useState({ type: "merit", date: "", description: "" });
  const [searchTerm, setSearchTerm] = useState("");
  const [meetingDates, setMeetingDates] = useState([]);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    handle: "",
    name: "",
    email: "",
    phone: "",
    address: "",
    dob: "",
    join_date: "",
    meeting_attendance: {
      year: new Date().getFullYear(),
      meetings: Array(24).fill(null).map(() => ({ status: 0, note: "" }))
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
    const attendanceData = prospect.meeting_attendance || {
      year: new Date().getFullYear(),
      meetings: Array(24).fill(null).map(() => ({ status: 0, note: "" }))
    };

    const meetings = attendanceData.meetings.map((meeting) => {
      if (typeof meeting === 'object' && meeting !== null) {
        return {
          status: meeting.status || 0,
          note: meeting.note || ""
        };
      }
      return { status: meeting || 0, note: "" };
    });

    setFormData({
      handle: prospect.handle,
      name: prospect.name,
      email: prospect.email,
      phone: prospect.phone,
      address: prospect.address,
      meeting_attendance: {
        year: attendanceData.year || new Date().getFullYear(),
        meetings: meetings
      }
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this prospect?")) return;

    const token = localStorage.getItem("token");
    try {
      await axios.delete(`${API}/prospects/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Prospect deleted successfully");
      fetchProspects();
    } catch (error) {
      toast.error("Failed to delete prospect");
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

  const resetForm = () => {
    setFormData({
      handle: "",
      name: "",
      email: "",
      phone: "",
      address: "",
      meeting_attendance: {
        year: new Date().getFullYear(),
        meetings: Array(24).fill(null).map(() => ({ status: 0, note: "" }))
      }
    });
    setEditingProspect(null);
  };

  const handleAttendanceToggle = (index) => {
    setFormData(prevData => {
      const newMeetings = [...prevData.meeting_attendance.meetings];
      const currentStatus = newMeetings[index].status;
      
      if (currentStatus === 0) {
        newMeetings[index] = { status: 1, note: "" };
      } else if (currentStatus === 1) {
        newMeetings[index] = { status: 2, note: "" };
      } else {
        newMeetings[index] = { status: 0, note: "" };
      }
      
      return {
        ...prevData,
        meeting_attendance: {
          ...prevData.meeting_attendance,
          meetings: newMeetings
        }
      };
    });
  };

  const handleAttendanceNoteChange = (index, note) => {
    setFormData(prevData => {
      const newMeetings = [...prevData.meeting_attendance.meetings];
      newMeetings[index] = { ...newMeetings[index], note };
      
      return {
        ...prevData,
        meeting_attendance: {
          ...prevData.meeting_attendance,
          meetings: newMeetings
        }
      };
    });
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <nav className="bg-slate-800 border-b border-slate-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-100">Hangarounds/Prospects</h1>
            <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
              <span className="text-xs sm:text-sm text-slate-300">
                {localStorage.getItem("username")} ({userRole})
              </span>
              <Button
                onClick={() => navigate("/")}
                variant="outline"
                size="sm"
                className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
              >
                <Users className="w-3 h-3 sm:w-4 sm:h-4" />
                <span className="hidden sm:inline">Members</span>
                <span className="sm:hidden">Members</span>
              </Button>
              {userRole === 'admin' && (
                <Button
                  onClick={() => navigate("/users")}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm bg-slate-700 text-slate-200 border-slate-600 hover:bg-slate-600"
                >
                  <Users className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="hidden sm:inline">Admin</span>
                  <span className="sm:hidden">Admin</span>
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
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 sm:p-6">
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
                className="w-full pl-10 py-4 sm:py-6 text-sm sm:text-base border-2 border-slate-300 focus:border-slate-600 rounded-lg"
              />
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mb-4 sm:mb-6">
            <Button
              onClick={handleExportCSV}
              size="sm"
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
                  size="sm"
                  className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-900 text-white w-full sm:w-auto"
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

                  <div className="border-t pt-4">
                    <div className="flex justify-between items-center mb-3">
                      <Label className="text-base font-semibold">Meeting Attendance</Label>
                      <div className="flex items-center gap-2">
                        <Label className="text-sm">Year:</Label>
                        <Input
                          type="number"
                          value={formData.meeting_attendance.year}
                          onChange={(e) => setFormData({
                            ...formData,
                            meeting_attendance: {
                              ...formData.meeting_attendance,
                              year: parseInt(e.target.value)
                            }
                          })}
                          className="w-24"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
                      {["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map((month, monthIndex) => (
                        <div key={month} className="border rounded p-3">
                          <p className="text-sm font-medium mb-2">{month}</p>
                          <div className="space-y-2">
                            <div>
                              <button
                                type="button"
                                onClick={() => handleAttendanceToggle(monthIndex * 2)}
                                className={`w-full px-2 py-2 rounded text-xs font-medium transition-colors ${
                                  formData.meeting_attendance.meetings[monthIndex * 2].status === 1
                                    ? 'bg-green-600 text-white hover:bg-green-700'
                                    : formData.meeting_attendance.meetings[monthIndex * 2].status === 2
                                    ? 'bg-orange-500 text-white hover:bg-orange-600'
                                    : 'bg-red-600 text-white hover:bg-red-700'
                                }`}
                              >
                                {month}-1st {meetingDates[monthIndex * 2] && `(${formatMeetingDate(meetingDates[monthIndex * 2])})`}
                              </button>
                              {(formData.meeting_attendance.meetings[monthIndex * 2].status === 0 || formData.meeting_attendance.meetings[monthIndex * 2].status === 2) && (
                                <Input
                                  placeholder={`${month}-1st note (${formData.meeting_attendance.meetings[monthIndex * 2].status === 2 ? 'excused' : 'unexcused'} absence)`}
                                  value={formData.meeting_attendance.meetings[monthIndex * 2].note}
                                  onChange={(e) => handleAttendanceNoteChange(monthIndex * 2, e.target.value)}
                                  className="mt-1 text-xs"
                                />
                              )}
                            </div>
                            <div>
                              <button
                                type="button"
                                onClick={() => handleAttendanceToggle(monthIndex * 2 + 1)}
                                className={`w-full px-2 py-2 rounded text-xs font-medium transition-colors ${
                                  formData.meeting_attendance.meetings[monthIndex * 2 + 1].status === 1
                                    ? 'bg-green-600 text-white hover:bg-green-700'
                                    : formData.meeting_attendance.meetings[monthIndex * 2 + 1].status === 2
                                    ? 'bg-orange-500 text-white hover:bg-orange-600'
                                    : 'bg-red-600 text-white hover:bg-red-700'
                                }`}
                              >
                                {month}-3rd {meetingDates[monthIndex * 2 + 1] && `(${formatMeetingDate(meetingDates[monthIndex * 2 + 1])})`}
                              </button>
                              {(formData.meeting_attendance.meetings[monthIndex * 2 + 1].status === 0 || formData.meeting_attendance.meetings[monthIndex * 2 + 1].status === 2) && (
                                <Input
                                  placeholder={`${month}-3rd note (${formData.meeting_attendance.meetings[monthIndex * 2 + 1].status === 2 ? 'excused' : 'unexcused'} absence)`}
                                  value={formData.meeting_attendance.meetings[monthIndex * 2 + 1].note}
                                  onChange={(e) => handleAttendanceNoteChange(monthIndex * 2 + 1, e.target.value)}
                                  className="mt-1 text-xs"
                                />
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
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
                    <Button type="submit" className="bg-slate-800 hover:bg-slate-900 text-white">
                      {editingProspect ? "Update" : "Save"}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {filteredProspects.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No prospects found</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
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
                      <TableCell>{prospect.handle}</TableCell>
                      <TableCell>{prospect.name}</TableCell>
                      <TableCell>
                        <a
                          href={`mailto:${prospect.email}`}
                          className="flex items-center gap-1 text-blue-600 hover:underline text-sm"
                        >
                          <Mail className="w-3 h-3" />
                          {prospect.email}
                        </a>
                      </TableCell>
                      <TableCell>
                        <a
                          href={`tel:${prospect.phone}`}
                          className="flex items-center gap-1 text-blue-600 hover:underline text-sm"
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
                          className="flex items-center gap-1 text-blue-600 hover:underline text-sm"
                        >
                          <MapPin className="w-3 h-3" />
                          {prospect.address}
                        </a>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-green-600 hover:text-green-700 hover:bg-green-50"
                            onClick={() => handlePromote(prospect)}
                            title="Promote to Member"
                          >
                            <UserPlus className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(prospect)}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => handleDelete(prospect.id)}
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
                      <SelectItem value="CD">CD - Club Doctor</SelectItem>
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
      </div>
    </div>
  );
}
