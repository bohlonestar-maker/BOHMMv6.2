import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import { Users, Calendar, DollarSign, CheckCircle, XCircle, Clock, ArrowLeft, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CHAPTERS = ['National', 'AD', 'HA', 'HS'];

// Meeting types based on chapter
const MEETING_TYPES_BY_CHAPTER = {
  National: [
    { value: 'national_board', label: 'National Board' },
    { value: 'national_quarterly', label: 'National Quarterly' },
    { value: 'budget_committee', label: 'Budget Committee' }
  ],
  AD: [
    { value: 'national_quarterly', label: 'National Quarterly' },
    { value: 'joint_officers', label: 'Joint Officers' },
    { value: 'chapter_officers', label: 'Chapter Officers' },
    { value: 'ad_chapter', label: 'AD Chapter' }
  ],
  HA: [
    { value: 'national_quarterly', label: 'National Quarterly' },
    { value: 'joint_officers', label: 'Joint Officers' },
    { value: 'chapter_officers', label: 'Chapter Officers' },
    { value: 'ha_chapter', label: 'HA Chapter' }
  ],
  HS: [
    { value: 'national_quarterly', label: 'National Quarterly' },
    { value: 'joint_officers', label: 'Joint Officers' },
    { value: 'chapter_officers', label: 'Chapter Officers' },
    { value: 'hs_chapter', label: 'HS Chapter' }
  ]
};

// Dues status options with colors
const DUES_STATUSES = [
  { value: 'paid', label: 'Paid', color: 'bg-green-600', icon: CheckCircle },
  { value: 'late', label: 'Late', color: 'bg-orange-500', icon: Clock },
  { value: 'unpaid', label: 'Not Paid', color: 'bg-red-600', icon: XCircle }
];

function OfficerTracking() {
  const navigate = useNavigate();
  const [members, setMembers] = useState({});
  const [attendance, setAttendance] = useState([]);
  const [dues, setDues] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedChapter, setSelectedChapter] = useState('National');
  const [activeTab, setActiveTab] = useState('attendance');
  const [canEdit, setCanEdit] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // View Member Meetings Dialog
  const [viewMeetingsDialog, setViewMeetingsDialog] = useState(false);
  const [viewMeetingsMember, setViewMeetingsMember] = useState(null);
  
  // Attendance Dialog
  const [attendanceDialog, setAttendanceDialog] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [attendanceForm, setAttendanceForm] = useState({
    meeting_date: new Date().toISOString().split('T')[0],
    meeting_type: 'national_officer',
    status: 'present',
    notes: ''
  });
  
  // Dues Dialog - Simplified
  const [duesDialog, setDuesDialog] = useState(false);
  const [duesForm, setDuesForm] = useState({
    status: 'paid',
    notes: ''
  });
  
  const token = localStorage.getItem('token');
  const userTitle = localStorage.getItem('title');
  const userRole = localStorage.getItem('role');
  
  // Check if user can edit (only SEC, NVP, NPrez - admin role does NOT grant edit)
  useEffect(() => {
    const editTitles = ['SEC', 'NVP', 'NPrez'];
    const canUserEdit = editTitles.includes(userTitle);
    setCanEdit(canUserEdit);
  }, [userTitle]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [membersRes, attendanceRes, duesRes, summaryRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/officer-tracking/members`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${BACKEND_URL}/api/officer-tracking/attendance`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${BACKEND_URL}/api/officer-tracking/dues`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${BACKEND_URL}/api/officer-tracking/summary`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setMembers(membersRes.data);
      setAttendance(attendanceRes.data);
      setDues(duesRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Access denied. Officers only.");
        navigate('/');
      } else {
        toast.error("Failed to load data");
      }
    } finally {
      setLoading(false);
    }
  }, [token, navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getAttendanceForMember = (memberId) => {
    return attendance.filter(a => a.member_id === memberId);
  };

  const getDuesForMember = (memberId) => {
    return dues.filter(d => d.member_id === memberId);
  };

  const getAttendanceStats = (memberId) => {
    const records = getAttendanceForMember(memberId);
    const present = records.filter(r => r.status === 'present').length;
    const total = records.length;
    return { present, total, rate: total > 0 ? Math.round(present / total * 100) : 0 };
  };

  // Get current month dues status for a member
  const getCurrentMonthDues = (memberId) => {
    const now = new Date();
    const currentMonth = `${now.toLocaleString('en-US', { month: 'short' })}_${now.getFullYear()}`;
    return dues.find(d => d.member_id === memberId && d.month === currentMonth);
  };

  const openAttendanceDialog = (member) => {
    setSelectedMember(member);
    // Get the first meeting type for the selected chapter as default
    const defaultMeetingType = MEETING_TYPES_BY_CHAPTER[selectedChapter]?.[0]?.value || 'national_board';
    setAttendanceForm({
      meeting_date: new Date().toISOString().split('T')[0],
      meeting_type: defaultMeetingType,
      status: 'present',
      notes: ''
    });
    setAttendanceDialog(true);
  };

  const openViewMeetingsDialog = (member) => {
    setViewMeetingsMember(member);
    setViewMeetingsDialog(true);
  };

  // Get meeting type label from value
  const getMeetingTypeLabel = (value) => {
    const allMeetingTypes = [
      ...MEETING_TYPES_BY_CHAPTER.National,
      ...MEETING_TYPES_BY_CHAPTER.AD,
      ...MEETING_TYPES_BY_CHAPTER.HA,
      ...MEETING_TYPES_BY_CHAPTER.HS
    ];
    const found = allMeetingTypes.find(t => t.value === value);
    return found ? found.label : value;
  };

  const openDuesDialog = (member, preselectedStatus = null) => {
    setSelectedMember(member);
    const existing = getCurrentMonthDues(member.id);
    setDuesForm({
      status: preselectedStatus || existing?.status || 'paid',
      notes: existing?.notes || ''
    });
    setDuesDialog(true);
  };

  const handleAttendanceSubmit = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/officer-tracking/attendance`, {
        member_id: selectedMember.id,
        ...attendanceForm
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      toast.success("Attendance recorded");
      setAttendanceDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to record attendance");
    }
  };

  const handleDuesSubmit = async () => {
    try {
      const now = new Date();
      const currentMonth = `${now.toLocaleString('en-US', { month: 'short' })}_${now.getFullYear()}`;
      
      await axios.post(`${BACKEND_URL}/api/officer-tracking/dues`, {
        member_id: selectedMember.id,
        month: currentMonth,
        status: duesForm.status,
        notes: duesForm.notes
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      toast.success("Dues status updated");
      setDuesDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update dues");
    }
  };

  // Quick dues update without dialog
  const handleQuickDuesUpdate = async (member, status) => {
    try {
      const now = new Date();
      const currentMonth = `${now.toLocaleString('en-US', { month: 'short' })}_${now.getFullYear()}`;
      
      await axios.post(`${BACKEND_URL}/api/officer-tracking/dues`, {
        member_id: member.id,
        month: currentMonth,
        status: status,
        notes: ''
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      toast.success(`Dues marked as ${status}`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update dues");
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      present: <Badge className="bg-green-600"><CheckCircle className="w-3 h-3 mr-1" />Present</Badge>,
      absent: <Badge className="bg-red-600"><XCircle className="w-3 h-3 mr-1" />Absent</Badge>,
      excused: <Badge className="bg-yellow-600"><Clock className="w-3 h-3 mr-1" />Excused</Badge>,
      paid: <Badge className="bg-green-600"><CheckCircle className="w-3 h-3 mr-1" />Paid</Badge>,
      unpaid: <Badge className="bg-red-600"><XCircle className="w-3 h-3 mr-1" />Not Paid</Badge>,
      late: <Badge className="bg-orange-500"><Clock className="w-3 h-3 mr-1" />Late</Badge>
    };
    return badges[status] || <Badge>{status}</Badge>;
  };

  // Filter members by search term
  const filteredMembers = (members[selectedChapter] || []).filter(member => 
    member.handle?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    member.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    member.title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Users className="h-6 w-6" />
              A & D
            </h1>
            <p className="text-muted-foreground text-sm">
              Attendance & Dues Tracking
              {!canEdit && <span className="text-yellow-500 ml-2">(View Only)</span>}
            </p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {CHAPTERS.map(chapter => (
          <Card key={chapter} 
            className={`cursor-pointer transition-all ${selectedChapter === chapter ? 'ring-2 ring-primary' : ''}`}
            onClick={() => setSelectedChapter(chapter)}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">{chapter}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{members[chapter]?.length || 0}</div>
              <div className="text-xs text-muted-foreground">Members</div>
              {summary[chapter] && (
                <div className="mt-2 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span>Attendance:</span>
                    <span className={summary[chapter].attendance_rate >= 80 ? 'text-green-500' : 'text-yellow-500'}>
                      {summary[chapter].attendance_rate}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Dues Paid:</span>
                    <span>{summary[chapter].dues_paid}/{summary[chapter].dues_total}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <CardTitle>{selectedChapter} Chapter</CardTitle>
              <CardDescription>Track attendance and dues for all {selectedChapter} members</CardDescription>
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search members..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Separate View Buttons */}
          <div className="flex gap-4 mb-6">
            <Button
              onClick={() => setActiveTab('attendance')}
              className={`flex-1 h-14 text-lg font-bold ${
                activeTab === 'attendance' 
                  ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
              }`}
            >
              <Calendar className="w-6 h-6 mr-3" />
              Attendance
            </Button>
            <Button
              onClick={() => setActiveTab('dues')}
              className={`flex-1 h-14 text-lg font-bold ${
                activeTab === 'dues' 
                  ? 'bg-green-600 hover:bg-green-700 text-white' 
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
              }`}
            >
              <DollarSign className="w-6 h-6 mr-3" />
              Dues
            </Button>
          </div>

          {/* Attendance Content */}
          {activeTab === 'attendance' && (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Member</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Attendance Rate</TableHead>
                      <TableHead>Last Meeting</TableHead>
                      <TableHead>View</TableHead>
                      {canEdit && <TableHead>Action</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredMembers.map(member => {
                      const stats = getAttendanceStats(member.id);
                      const lastRecord = getAttendanceForMember(member.id).sort((a, b) => 
                        new Date(b.meeting_date) - new Date(a.meeting_date)
                      )[0];
                      
                      return (
                        <TableRow key={member.id}>
                          <TableCell className="font-medium">{member.handle}</TableCell>
                          <TableCell>{member.title || '-'}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span className={stats.rate >= 80 ? 'text-green-500' : stats.rate >= 50 ? 'text-yellow-500' : 'text-red-500'}>
                                {stats.rate}%
                              </span>
                              <span className="text-xs text-muted-foreground">
                                ({stats.present}/{stats.total})
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {lastRecord ? (
                              <div className="flex items-center gap-2">
                                <span className="text-xs">{lastRecord.meeting_date}</span>
                                {getStatusBadge(lastRecord.status)}
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-xs">No records</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button size="sm" variant="outline" onClick={() => openViewMeetingsDialog(member)}>
                              View All
                            </Button>
                          </TableCell>
                          {canEdit && (
                            <TableCell>
                              <Button size="sm" onClick={() => openAttendanceDialog(member)}>
                                Record
                              </Button>
                            </TableCell>
                          )}
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
          )}

          {/* Dues Content */}
          {activeTab === 'dues' && (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Member</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Current Month Status</TableHead>
                      {canEdit && <TableHead>Quick Update</TableHead>}
                      {canEdit && <TableHead>Notes</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredMembers.map(member => {
                      const currentDues = getCurrentMonthDues(member.id);
                      
                      return (
                        <TableRow key={member.id}>
                          <TableCell className="font-medium">{member.handle}</TableCell>
                          <TableCell>{member.title || '-'}</TableCell>
                          <TableCell>
                            {currentDues ? getStatusBadge(currentDues.status) : (
                              <Badge variant="outline">Not Recorded</Badge>
                            )}
                          </TableCell>
                          {canEdit && (
                            <TableCell>
                              <div className="flex gap-1">
                                <Button 
                                  size="sm" 
                                  className="bg-green-600 hover:bg-green-700 h-8 px-2"
                                  onClick={() => handleQuickDuesUpdate(member, 'paid')}
                                  title="Mark as Paid"
                                >
                                  <CheckCircle className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="sm" 
                                  className="bg-orange-500 hover:bg-orange-600 h-8 px-2"
                                  onClick={() => handleQuickDuesUpdate(member, 'late')}
                                  title="Mark as Late"
                                >
                                  <Clock className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="sm" 
                                  className="bg-red-600 hover:bg-red-700 h-8 px-2"
                                  onClick={() => handleQuickDuesUpdate(member, 'unpaid')}
                                  title="Mark as Not Paid"
                                >
                                  <XCircle className="w-4 h-4" />
                                </Button>
                              </div>
                            </TableCell>
                          )}
                          {canEdit && (
                            <TableCell>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => openDuesDialog(member)}
                              >
                                + Note
                              </Button>
                            </TableCell>
                          )}
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
          )}
        </CardContent>
      </Card>

      {/* Attendance Dialog */}
      <Dialog open={attendanceDialog} onOpenChange={setAttendanceDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Attendance</DialogTitle>
            <DialogDescription>
              Recording attendance for {selectedMember?.handle}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Meeting Date</Label>
              <Input 
                type="date" 
                value={attendanceForm.meeting_date}
                onChange={(e) => setAttendanceForm({...attendanceForm, meeting_date: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label>Meeting Type</Label>
              <Select value={attendanceForm.meeting_type} onValueChange={(v) => setAttendanceForm({...attendanceForm, meeting_type: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(MEETING_TYPES_BY_CHAPTER[selectedChapter] || []).map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={attendanceForm.status} onValueChange={(v) => setAttendanceForm({...attendanceForm, status: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="present">Present</SelectItem>
                  <SelectItem value="absent">Absent</SelectItem>
                  <SelectItem value="excused">Excused</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Notes (Optional)</Label>
              <Textarea 
                value={attendanceForm.notes}
                onChange={(e) => setAttendanceForm({...attendanceForm, notes: e.target.value})}
                placeholder="Any additional notes..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAttendanceDialog(false)}>Cancel</Button>
            <Button onClick={handleAttendanceSubmit}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dues Dialog - Simplified */}
      <Dialog open={duesDialog} onOpenChange={setDuesDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Dues</DialogTitle>
            <DialogDescription>
              Update dues status for {selectedMember?.handle}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Status</Label>
              <div className="flex gap-2">
                {DUES_STATUSES.map(status => {
                  const Icon = status.icon;
                  return (
                    <Button
                      key={status.value}
                      type="button"
                      className={`flex-1 ${duesForm.status === status.value ? status.color : 'bg-gray-600'}`}
                      onClick={() => setDuesForm({...duesForm, status: status.value})}
                    >
                      <Icon className="w-4 h-4 mr-1" />
                      {status.label}
                    </Button>
                  );
                })}
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes (Optional)</Label>
              <Textarea 
                value={duesForm.notes}
                onChange={(e) => setDuesForm({...duesForm, notes: e.target.value})}
                placeholder="Any additional notes about this dues status..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDuesDialog(false)}>Cancel</Button>
            <Button onClick={handleDuesSubmit}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default OfficerTracking;
