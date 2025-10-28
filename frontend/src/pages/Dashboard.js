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
import { LogOut, Plus, Pencil, Trash2, Download, Users, Mail, Phone, MapPin } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHAPTERS = ["National", "AD", "HA", "HS"];
const TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM"];

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
  const navigate = useNavigate();

  // Helper to check permissions
  const hasPermission = (permission) => {
    if (userRole === 'admin') return true;
    return userPermissions?.[permission] === true;
  };

  const [formData, setFormData] = useState({
    chapter: "",
    title: "",
    handle: "",
    name: "",
    email: "",
    phone: "",
    address: "",
    dues: {
      year: new Date().getFullYear(),
      months: Array(12).fill(false)
    },
    meeting_attendance: {
      year: new Date().getFullYear(),
      meetings: Array(24).fill(false)
    }
  });

  useEffect(() => {
    fetchMembers();
  }, []);

  const fetchMembers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/members`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const sortedMembers = sortMembers(response.data);
      setMembers(sortedMembers);
    } catch (error) {
      toast.error("Failed to load members");
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
    setFormData({
      chapter: member.chapter,
      title: member.title,
      handle: member.handle,
      name: member.name,
      email: member.email,
      phone: member.phone,
      address: member.address,
      dues: member.dues || {
        year: new Date().getFullYear(),
        months: Array(12).fill(false)
      },
      meeting_attendance: member.meeting_attendance || {
        year: new Date().getFullYear(),
        meetings: Array(24).fill(false)
      }
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      chapter: "",
      title: "",
      handle: "",
      name: "",
      email: "",
      phone: "",
      address: "",
      dues: {
        year: new Date().getFullYear(),
        months: Array(12).fill(false)
      },
      meeting_attendance: {
        year: new Date().getFullYear(),
        meetings: Array(24).fill(false)
      }
    });
    setEditingMember(null);
  };

  const handleDuesToggle = (monthIndex) => {
    const newMonths = [...formData.dues.months];
    newMonths[monthIndex] = !newMonths[monthIndex];
    setFormData({
      ...formData,
      dues: {
        ...formData.dues,
        months: newMonths
      }
    });
  };

  const handleAttendanceToggle = (meetingIndex) => {
    const newMeetings = [...formData.meeting_attendance.meetings];
    newMeetings[meetingIndex] = !newMeetings[meetingIndex];
    setFormData({
      ...formData,
      meeting_attendance: {
        ...formData.meeting_attendance,
        meetings: newMeetings
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <nav className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-slate-900">Brothers of the Highway</h1>
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-600">
                {localStorage.getItem("username")} ({userRole})
              </span>
              {hasPermission('admin_actions') && (
                <Button
                  onClick={() => navigate("/users")}
                  variant="outline"
                  data-testid="user-management-button"
                  className="flex items-center gap-2"
                >
                  <Users className="w-4 h-4" />
                  Manage Users
                </Button>
              )}
              <Button
                onClick={onLogout}
                variant="outline"
                data-testid="logout-button"
                className="flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="mb-6">
            <div className="relative max-w-2xl">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none z-10"
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
                className="w-full pl-10 py-6 text-base border-2 border-slate-300 focus:border-slate-600 rounded-lg"
              />
            </div>
          </div>
          
          {hasPermission('admin_actions') && (
            <div className="flex gap-3 mb-6">
              <Button
                onClick={handleExportCSV}
                variant="outline"
                data-testid="export-csv-button"
                className="flex items-center gap-2"
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
                    className="flex items-center gap-2 bg-slate-800 hover:bg-slate-900"
                  >
                    <Plus className="w-4 h-4" />
                    Add Member
                  </Button>
                </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>
                        {editingMember ? "Edit Member" : "Add New Member"}
                      </DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Chapter</Label>
                          <Select
                            value={formData.chapter}
                            onValueChange={(value) =>
                              setFormData({ ...formData, chapter: value })
                            }
                            required
                          >
                            <SelectTrigger data-testid="chapter-select">
                              <SelectValue placeholder="Select chapter" />
                            </SelectTrigger>
                            <SelectContent>
                              {CHAPTERS.map((ch) => (
                                <SelectItem key={ch} value={ch}>
                                  {ch}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Title</Label>
                          <Select
                            value={formData.title}
                            onValueChange={(value) =>
                              setFormData({ ...formData, title: value })
                            }
                            required
                          >
                            <SelectTrigger data-testid="title-select">
                              <SelectValue placeholder="Select title" />
                            </SelectTrigger>
                            <SelectContent>
                              {TITLES.map((t) => (
                                <SelectItem key={t} value={t}>
                                  {t}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div>
                        <Label>Member Handle</Label>
                        <Input
                          data-testid="handle-input"
                          value={formData.handle}
                          onChange={(e) =>
                            setFormData({ ...formData, handle: e.target.value })
                          }
                          required
                        />
                      </div>

                      <div>
                        <Label>Name</Label>
                        <Input
                          data-testid="name-input"
                          value={formData.name}
                          onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                          }
                          required
                        />
                      </div>

                      <div>
                        <Label>Email</Label>
                        <Input
                          data-testid="email-input"
                          type="email"
                          value={formData.email}
                          onChange={(e) =>
                            setFormData({ ...formData, email: e.target.value })
                          }
                          required
                        />
                      </div>

                      <div>
                        <Label>Phone</Label>
                        <Input
                          data-testid="phone-input"
                          value={formData.phone}
                          onChange={(e) =>
                            setFormData({ ...formData, phone: e.target.value })
                          }
                          required
                        />
                      </div>

                      <div>
                        <Label>Address</Label>
                        <Input
                          data-testid="address-input"
                          value={formData.address}
                          onChange={(e) =>
                            setFormData({ ...formData, address: e.target.value })
                          }
                          required
                        />
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <Label>Dues Tracking - {formData.dues.year}</Label>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setFormData({
                              ...formData,
                              dues: {
                                year: formData.dues.year + 1,
                                months: Array(12).fill(false)
                              }
                            })}
                            data-testid="change-dues-year"
                          >
                            Change Year
                          </Button>
                        </div>
                        <div className="grid grid-cols-6 gap-2">
                          {monthNames.map((month, index) => (
                            <button
                              key={index}
                              type="button"
                              onClick={() => handleDuesToggle(index)}
                              className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                                formData.dues.months[index]
                                  ? 'bg-green-600 text-white hover:bg-green-700'
                                  : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                              }`}
                              data-testid={`dues-month-${index}`}
                            >
                              {month}
                            </button>
                          ))}
                        </div>
                        <p className="text-xs text-slate-600">
                          Click months to mark as paid (green) or unpaid (gray)
                        </p>
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <Label>Meeting Attendance - {formData.meeting_attendance.year}</Label>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setFormData({
                              ...formData,
                              meeting_attendance: {
                                year: formData.meeting_attendance.year + 1,
                                meetings: Array(24).fill(false)
                              }
                            })}
                            data-testid="change-attendance-year"
                          >
                            Change Year
                          </Button>
                        </div>
                        <div className="grid grid-cols-6 gap-2">
                          {monthNames.map((month, monthIndex) => (
                            <>
                              <button
                                key={`${monthIndex}-1st`}
                                type="button"
                                onClick={() => handleAttendanceToggle(monthIndex * 2)}
                                className={`px-2 py-2 rounded text-xs font-medium transition-colors ${
                                  formData.meeting_attendance.meetings[monthIndex * 2]
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                                }`}
                                data-testid={`attendance-${monthIndex}-1st`}
                              >
                                {month}-1st
                              </button>
                              <button
                                key={`${monthIndex}-3rd`}
                                type="button"
                                onClick={() => handleAttendanceToggle(monthIndex * 2 + 1)}
                                className={`px-2 py-2 rounded text-xs font-medium transition-colors ${
                                  formData.meeting_attendance.meetings[monthIndex * 2 + 1]
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                                }`}
                                data-testid={`attendance-${monthIndex}-3rd`}
                              >
                                {month}-3rd
                              </button>
                            </>
                          ))}
                        </div>
                        <p className="text-xs text-slate-600">
                          Click meetings to mark attendance: Present (blue) or Absent (gray). Meetings on 1st & 3rd Wednesday of each month.
                        </p>
                      </div>

                      <div className="flex gap-3 justify-end pt-4">
                        <Button
                          type="button"
                          variant="outline"
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
                          className="bg-slate-800 hover:bg-slate-900"
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
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-slate-600">{member.dues?.year || new Date().getFullYear()}</span>
                            <span className="text-xs font-medium text-slate-700">
                              {member.dues?.months?.filter(p => p).length || 0}/12
                            </span>
                          </div>
                        </TableCell>
                      )}
                      {hasPermission('meeting_attendance') && (
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-slate-600">{member.meeting_attendance?.year || new Date().getFullYear()}</span>
                            <span className="text-xs font-medium text-slate-700">
                              {member.meeting_attendance?.meetings?.filter(p => p).length || 0}/24
                            </span>
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