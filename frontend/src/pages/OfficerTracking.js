import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import { Users, Calendar, DollarSign, CheckCircle, XCircle, Clock, ArrowLeft, Search, Printer, CreditCard, Gift, Shield } from "lucide-react";
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
  { value: 'forgiven', label: 'Forgiven', color: 'bg-purple-600', icon: Gift },
  { value: 'extended', label: 'Extended', color: 'bg-blue-600', icon: Shield },
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
  
  // Square Payments State
  const [unmatchedPayments, setUnmatchedPayments] = useState([]);
  const [showPaymentsDialog, setShowPaymentsDialog] = useState(false);
  const [matchingPayment, setMatchingPayment] = useState(null);
  const [matchMemberId, setMatchMemberId] = useState('');
  const [matchYear, setMatchYear] = useState(new Date().getFullYear());
  const [matchMonth, setMatchMonth] = useState(new Date().getMonth());
  
  // View Member Meetings Dialog
  const [viewMeetingsDialog, setViewMeetingsDialog] = useState(false);
  const [viewMeetingsMember, setViewMeetingsMember] = useState(null);
  const [viewMeetingsFilter, setViewMeetingsFilter] = useState('all'); // 'all' or 'YYYY-MM'
  const printRef = useRef(null);
  
  // Dues History Dialog
  const [duesHistoryDialog, setDuesHistoryDialog] = useState(false);
  const [duesHistoryMember, setDuesHistoryMember] = useState(null);
  const [duesHistoryData, setDuesHistoryData] = useState(null);
  const [loadingDuesHistory, setLoadingDuesHistory] = useState(false);
  
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
    notes: '',
    extensionDate: ''
  });
  const [memberExtension, setMemberExtension] = useState(null);
  
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
    setViewMeetingsFilter('all');
    setViewMeetingsDialog(true);
  };

  // Open dues history dialog for a member
  const openDuesHistoryDialog = async (member) => {
    setDuesHistoryMember(member);
    setDuesHistoryDialog(true);
    setLoadingDuesHistory(true);
    setDuesHistoryData(null);
    
    try {
      const response = await axios.get(`${BACKEND_URL}/api/officer-tracking/dues/history/${member.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDuesHistoryData(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to load dues history");
    } finally {
      setLoadingDuesHistory(false);
    }
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

  // Get filtered meetings for view dialog
  const getFilteredMeetings = (memberId) => {
    const allMeetings = getAttendanceForMember(memberId);
    if (viewMeetingsFilter === 'all') {
      return allMeetings.sort((a, b) => new Date(b.meeting_date) - new Date(a.meeting_date));
    }
    // Filter by month (YYYY-MM format)
    return allMeetings
      .filter(m => m.meeting_date && m.meeting_date.startsWith(viewMeetingsFilter))
      .sort((a, b) => new Date(b.meeting_date) - new Date(a.meeting_date));
  };

  // Get unique months from attendance records
  const getAvailableMonths = (memberId) => {
    const meetings = getAttendanceForMember(memberId);
    const months = new Set();
    meetings.forEach(m => {
      if (m.meeting_date) {
        const yearMonth = m.meeting_date.substring(0, 7); // YYYY-MM
        months.add(yearMonth);
      }
    });
    return Array.from(months).sort().reverse();
  };

  // Format month for display
  const formatMonth = (yearMonth) => {
    const [year, month] = yearMonth.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  };

  // Print meetings
  const handlePrintMeetings = () => {
    const content = printRef.current;
    if (!content) return;
    
    const printWindow = window.open('', '_blank');
    const meetings = getFilteredMeetings(viewMeetingsMember?.id || '');
    const stats = getAttendanceStats(viewMeetingsMember?.id || '');
    
    printWindow.document.write(`
      <html>
        <head>
          <title>Meeting Attendance - ${viewMeetingsMember?.handle}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { font-size: 18px; margin-bottom: 5px; }
            h2 { font-size: 14px; color: #666; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f5f5f5; }
            .stats { margin-bottom: 15px; padding: 10px; background: #f9f9f9; border-radius: 5px; }
            .present { color: green; }
            .absent { color: red; }
            .excused { color: orange; }
          </style>
        </head>
        <body>
          <h1>Meeting Attendance Report</h1>
          <h2>${viewMeetingsMember?.handle} (${viewMeetingsMember?.title || 'Member'}) - ${viewMeetingsFilter === 'all' ? 'All Time' : formatMonth(viewMeetingsFilter)}</h2>
          <div class="stats">
            <strong>Attendance Rate:</strong> ${stats.rate}% (${stats.present} present out of ${stats.total} meetings)
          </div>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Meeting Type</th>
                <th>Status</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              ${meetings.map(m => `
                <tr>
                  <td>${m.meeting_date}</td>
                  <td>${getMeetingTypeLabel(m.meeting_type)}</td>
                  <td class="${m.status}">${m.status.charAt(0).toUpperCase() + m.status.slice(1)}</td>
                  <td>${m.notes || '-'}</td>
                </tr>
              `).join('')}
              ${meetings.length === 0 ? '<tr><td colspan="4" style="text-align:center;">No meetings found</td></tr>' : ''}
            </tbody>
          </table>
          <p style="margin-top: 20px; font-size: 12px; color: #999;">Printed on ${new Date().toLocaleDateString()}</p>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  // Fetch unmatched Square payments
  const fetchUnmatchedPayments = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/dues/unmatched-payments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnmatchedPayments(response.data || []);
    } catch (error) {
      console.error("Failed to fetch unmatched payments:", error);
    }
  };

  // Sync subscriptions from Square
  const handleSyncSubscriptions = async () => {
    try {
      toast.info("Syncing subscriptions from Square payment history...");
      const response = await axios.post(`${BACKEND_URL}/api/dues/sync-subscriptions`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = response.data;
      toast.success(`Synced ${data.members_synced} members, marked ${data.months_marked_paid} months as paid`);
      fetchData(); // Refresh dues data
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to sync subscriptions");
    }
  };

  // Sync payment links from Square (one-time dues payments)
  const handleSyncPaymentLinks = async () => {
    try {
      toast.info("Syncing payment links from Square...");
      const response = await axios.post(`${BACKEND_URL}/api/dues/sync-payment-links`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = response.data;
      toast.success(`Synced ${data.orders_synced} payments, marked ${data.months_marked_paid} months as paid`);
      fetchData(); // Refresh dues data
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to sync payment links");
    }
  };

  // Sync all dues (subscriptions + payment links)
  const handleSyncAllDues = async () => {
    try {
      toast.info("Syncing all dues from Square...");
      
      // Run both syncs
      const [subsResponse, linksResponse] = await Promise.all([
        axios.post(`${BACKEND_URL}/api/dues/sync-subscriptions`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.post(`${BACKEND_URL}/api/dues/sync-payment-links`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      const totalMembers = (subsResponse.data.members_synced || 0) + (linksResponse.data.orders_synced || 0);
      const totalMonths = (subsResponse.data.months_marked_paid || 0) + (linksResponse.data.months_marked_paid || 0);
      
      toast.success(`Synced ${totalMembers} payments, marked ${totalMonths} months as paid`);
      fetchData(); // Refresh dues data
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to sync dues");
    }
  };

  // View subscriptions
  const [subscriptions, setSubscriptions] = useState({ matched: [], unmatched: [] });
  const [showSubscriptionsDialog, setShowSubscriptionsDialog] = useState(false);
  const [loadingSubscriptions, setLoadingSubscriptions] = useState(false);
  
  // Manual linking state
  const [allMembersForLinking, setAllMembersForLinking] = useState([]);
  const [linkingSubscription, setLinkingSubscription] = useState(null);
  const [selectedMemberForLink, setSelectedMemberForLink] = useState('');
  const [linkingInProgress, setLinkingInProgress] = useState(false);
  const [cancellingSubscription, setCancellingSubscription] = useState(null);

  const handleViewSubscriptions = async () => {
    setLoadingSubscriptions(true);
    setShowSubscriptionsDialog(true);
    try {
      const [subsResponse, membersResponse] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/dues/subscriptions`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/dues/all-members-for-linking`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setSubscriptions(subsResponse.data);
      setAllMembersForLinking(membersResponse.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to fetch subscriptions");
    } finally {
      setLoadingSubscriptions(false);
    }
  };

  const handleCancelSquareSubscription = async (subscription) => {
    if (!window.confirm(`⚠️ CANCEL SUBSCRIPTION\n\nAre you sure you want to cancel the Square subscription for:\n\n${subscription.customer_name || 'Unknown'} (${subscription.customer_email || 'No email'})\n\nThis will cancel their recurring payment in Square.`)) {
      return;
    }
    
    setCancellingSubscription(subscription.subscription_id);
    try {
      await axios.delete(`${BACKEND_URL}/api/dues/cancel-square-subscription/${subscription.subscription_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success("Square subscription cancelled successfully!");
      
      // Refresh subscriptions
      const response = await axios.get(`${BACKEND_URL}/api/dues/subscriptions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscriptions(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to cancel subscription");
    } finally {
      setCancellingSubscription(null);
    }
  };

  const handleLinkSubscription = async () => {
    if (!linkingSubscription || !selectedMemberForLink) {
      toast.error("Please select a member");
      return;
    }
    
    setLinkingInProgress(true);
    try {
      await axios.post(`${BACKEND_URL}/api/dues/link-subscription`, {
        member_id: selectedMemberForLink,
        square_customer_id: linkingSubscription.customer_id
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success("Subscription linked successfully!");
      setLinkingSubscription(null);
      setSelectedMemberForLink('');
      
      // Refresh subscriptions
      const response = await axios.get(`${BACKEND_URL}/api/dues/subscriptions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscriptions(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to link subscription");
    } finally {
      setLinkingInProgress(false);
    }
  };

  const getMatchTypeLabel = (matchType, score) => {
    if (!matchType) return null;
    const labels = {
      'manual_link': { text: 'Manual', color: 'bg-blue-600' },
      'exact_name': { text: 'Exact', color: 'bg-green-600' },
      'exact_handle': { text: 'Exact', color: 'bg-green-600' },
      'fuzzy_name': { text: `Fuzzy ${score}%`, color: score >= 90 ? 'bg-green-500' : 'bg-yellow-500' },
      'fuzzy_handle': { text: `Fuzzy ${score}%`, color: score >= 90 ? 'bg-green-500' : 'bg-yellow-500' },
      'partial_name': { text: 'Partial', color: 'bg-yellow-600' }
    };
    return labels[matchType] || { text: matchType, color: 'bg-gray-500' };
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

  // Delete attendance record (syncs to member's meeting_attendance)
  const handleDeleteAttendance = async (recordId) => {
    if (!confirm("Are you sure you want to delete this attendance record?")) return;
    
    try {
      await axios.delete(`${BACKEND_URL}/api/officer-tracking/attendance/${recordId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Attendance record deleted");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete attendance");
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
      late: <Badge className="bg-orange-500"><Clock className="w-3 h-3 mr-1" />Late</Badge>,
      forgiven: <Badge className="bg-purple-600"><Gift className="w-3 h-3 mr-1" />Forgiven</Badge>,
      extended: <Badge className="bg-blue-600"><Shield className="w-3 h-3 mr-1" />Extended</Badge>
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4 max-w-7xl">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2 sm:gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate('/')} className="h-8 w-8 sm:h-10 sm:w-10">
                <ArrowLeft className="h-4 w-4 sm:h-5 sm:w-5" />
              </Button>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold flex items-center gap-2 text-white">
                  <Users className="h-5 w-5 sm:h-6 sm:w-6" />
                  A & D
                </h1>
                <p className="text-muted-foreground text-xs sm:text-sm hidden sm:block">
                  Attendance & Dues Tracking
                  {!canEdit && <span className="text-yellow-500 ml-2">(View Only)</span>}
                </p>
              </div>
            </div>
            {!canEdit && <Badge variant="outline" className="text-yellow-500 border-yellow-500 text-xs sm:hidden">View Only</Badge>}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 max-w-7xl">
        {/* Summary Cards - Responsive Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-4 sm:mb-6">
          {CHAPTERS.map(chapter => (
            <Card key={chapter} 
              className={`cursor-pointer transition-all bg-slate-800 border-slate-700 ${selectedChapter === chapter ? 'ring-2 ring-primary' : ''}`}
              onClick={() => setSelectedChapter(chapter)}
            >
              <CardHeader className="p-3 sm:p-4 pb-1 sm:pb-2">
                <CardTitle className="text-sm sm:text-lg text-white">{chapter}</CardTitle>
              </CardHeader>
              <CardContent className="p-3 sm:p-4 pt-0">
                <div className="text-xl sm:text-2xl font-bold text-white">{members[chapter]?.length || 0}</div>
                <div className="text-xs text-muted-foreground">Members</div>
                {summary[chapter] && (
                  <div className="mt-1 sm:mt-2 text-xs space-y-0.5 sm:space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Attend:</span>
                      <span className={summary[chapter].attendance_rate >= 80 ? 'text-green-500' : 'text-yellow-500'}>
                        {summary[chapter].attendance_rate}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Dues:</span>
                      <span className="text-white">{summary[chapter].dues_paid}/{summary[chapter].dues_total}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Card */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="p-3 sm:p-6">
            <div className="flex flex-col gap-3 sm:gap-4">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-4">
                <div>
                  <CardTitle className="text-base sm:text-xl text-white">{selectedChapter} Chapter</CardTitle>
                  <CardDescription className="text-xs sm:text-sm hidden sm:block">Track attendance and dues for {selectedChapter} members</CardDescription>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-8 h-9 sm:h-10 bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>
              
              {/* View Toggle Buttons - Responsive */}
              <div className="flex gap-2 sm:gap-4">
                <Button
                  onClick={() => setActiveTab('attendance')}
                  className={`flex-1 h-10 sm:h-14 text-sm sm:text-lg font-bold ${
                    activeTab === 'attendance' 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                      : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                  }`}
                >
                  <Calendar className="w-4 h-4 sm:w-6 sm:h-6 mr-1 sm:mr-3" />
                  <span className="hidden xs:inline">Attendance</span>
                  <span className="xs:hidden">Attend</span>
                </Button>
                <Button
                  onClick={() => setActiveTab('dues')}
                  className={`flex-1 h-10 sm:h-14 text-sm sm:text-lg font-bold ${
                    activeTab === 'dues' 
                      ? 'bg-green-600 hover:bg-green-700 text-white' 
                      : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                  }`}
                >
                  <DollarSign className="w-4 h-4 sm:w-6 sm:h-6 mr-1 sm:mr-3" />
                  Dues
                </Button>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="p-3 sm:p-6 pt-0">
            {/* Attendance Content */}
            {activeTab === 'attendance' && (
              <div>
                {/* Desktop Table View */}
                <div className="hidden md:block overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-700">
                        <TableHead className="text-slate-400">Member</TableHead>
                        <TableHead className="text-slate-400">Title</TableHead>
                        <TableHead className="text-slate-400">Attendance Rate</TableHead>
                        <TableHead className="text-slate-400">Last Meeting</TableHead>
                        <TableHead className="text-slate-400">View</TableHead>
                        {canEdit && <TableHead className="text-slate-400">Action</TableHead>}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredMembers.map(member => {
                        const stats = getAttendanceStats(member.id);
                        const lastRecord = getAttendanceForMember(member.id).sort((a, b) => 
                          new Date(b.meeting_date) - new Date(a.meeting_date)
                        )[0];
                        
                        return (
                          <TableRow key={member.id} className="border-slate-700">
                            <TableCell className="font-medium text-white">{member.handle}</TableCell>
                            <TableCell className="text-slate-300">{member.title || '-'}</TableCell>
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
                                  <span className="text-xs text-slate-300">{lastRecord.meeting_date}</span>
                                  {getStatusBadge(lastRecord.status)}
                                </div>
                              ) : (
                                <span className="text-muted-foreground text-xs">No records</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Button size="sm" variant="outline" onClick={() => openViewMeetingsDialog(member)} className="text-xs">
                                View All
                              </Button>
                            </TableCell>
                            {canEdit && (
                              <TableCell>
                                <Button size="sm" onClick={() => openAttendanceDialog(member)} className="text-xs">
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

                {/* Mobile Card View for Attendance */}
                <div className="md:hidden space-y-3">
                  {filteredMembers.map(member => {
                    const stats = getAttendanceStats(member.id);
                    const lastRecord = getAttendanceForMember(member.id).sort((a, b) => 
                      new Date(b.meeting_date) - new Date(a.meeting_date)
                    )[0];
                    
                    return (
                      <div key={member.id} className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-medium text-white">{member.handle}</div>
                            <div className="text-xs text-slate-400">{member.title || 'Member'}</div>
                          </div>
                          <div className="text-right">
                            <div className={`text-lg font-bold ${stats.rate >= 80 ? 'text-green-500' : stats.rate >= 50 ? 'text-yellow-500' : 'text-red-500'}`}>
                              {stats.rate}%
                            </div>
                            <div className="text-xs text-slate-400">({stats.present}/{stats.total})</div>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                          <span>Last:</span>
                          {lastRecord ? (
                            <div className="flex items-center gap-1">
                              <span>{lastRecord.meeting_date}</span>
                              {getStatusBadge(lastRecord.status)}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">No records</span>
                          )}
                        </div>
                        
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => openViewMeetingsDialog(member)} className="flex-1 text-xs h-8">
                            View All
                          </Button>
                          {canEdit && (
                            <Button size="sm" onClick={() => openAttendanceDialog(member)} className="flex-1 text-xs h-8">
                              Record
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Dues Content */}
            {activeTab === 'dues' && (
              <div className="space-y-4">
                {/* Square Sync Buttons - Responsive */}
                {canEdit && (
                  <div className="flex flex-col sm:flex-row gap-2 sm:justify-end">
                    <Button variant="outline" onClick={handleViewSubscriptions} className="text-xs sm:text-sm h-9 sm:h-10">
                      <CreditCard className="w-4 h-4 mr-2" />
                      View Subscriptions
                    </Button>
                    <Button onClick={handleSyncAllDues} className="bg-purple-600 hover:bg-purple-700 text-xs sm:text-sm h-9 sm:h-10">
                      <CreditCard className="w-4 h-4 mr-2" />
                      Sync from Square
                    </Button>
                  </div>
                )}
                
                {/* Desktop Table View for Dues */}
                <div className="hidden md:block overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-700">
                        <TableHead className="text-slate-400">Member</TableHead>
                        <TableHead className="text-slate-400">Title</TableHead>
                        <TableHead className="text-slate-400">Current Month Status</TableHead>
                        <TableHead className="text-slate-400">History</TableHead>
                        {canEdit && <TableHead className="text-slate-400">Quick Update</TableHead>}
                        {canEdit && <TableHead className="text-slate-400">Notes</TableHead>}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredMembers.map(member => {
                        const currentDues = getCurrentMonthDues(member.id);
                        const isExempt = member.non_dues_paying;
                        
                        return (
                          <TableRow key={member.id} className="border-slate-700">
                            <TableCell 
                              className="font-medium text-blue-400 hover:text-blue-300 cursor-pointer underline"
                              onClick={() => openDuesHistoryDialog(member)}
                            >
                              {member.handle}
                              {isExempt && (
                                <Badge className="ml-2 bg-amber-600 text-white text-xs">Exempt</Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-slate-300">{member.title || '-'}</TableCell>
                            <TableCell>
                              {isExempt ? (
                                <Badge className="bg-amber-600">Non-Dues Paying</Badge>
                              ) : currentDues ? getStatusBadge(currentDues.status) : (
                                <Badge variant="outline">Not Recorded</Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openDuesHistoryDialog(member)}
                                className="text-xs h-7"
                              >
                                View
                              </Button>
                            </TableCell>
                            {canEdit && (
                              <TableCell>
                                <div className="flex gap-1">
                                  <Button
                                    size="sm"
                                    className="bg-green-600 hover:bg-green-700 h-7 px-2 text-xs"
                                    onClick={() => handleQuickDuesUpdate(member, 'paid')}
                                  >
                                    <CheckCircle className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    className="bg-orange-500 hover:bg-orange-600 h-7 px-2 text-xs"
                                    onClick={() => handleQuickDuesUpdate(member, 'late')}
                                  >
                                    <Clock className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    className="bg-red-600 hover:bg-red-700 h-7 px-2 text-xs"
                                    onClick={() => handleQuickDuesUpdate(member, 'unpaid')}
                                  >
                                    <XCircle className="w-3 h-3" />
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
                                  className="text-xs h-7"
                                >
                                  Edit
                                </Button>
                              </TableCell>
                            )}
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>

                {/* Mobile Card View for Dues */}
                <div className="md:hidden space-y-3">
                  {filteredMembers.map(member => {
                    const currentDues = getCurrentMonthDues(member.id);
                    const isExempt = member.non_dues_paying;
                    
                    return (
                      <div key={member.id} className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
                        <div 
                          className="flex justify-between items-start mb-3 cursor-pointer"
                          onClick={() => openDuesHistoryDialog(member)}
                        >
                          <div>
                            <div className="font-medium text-blue-400 underline">
                              {member.handle}
                              {isExempt && (
                                <Badge className="ml-2 bg-amber-600 text-white text-xs">Exempt</Badge>
                              )}
                            </div>
                            <div className="text-xs text-slate-400">{member.title || 'Brother'}</div>
                          </div>
                          <div>
                            {isExempt ? (
                              <Badge className="bg-amber-600 text-xs">Non-Dues Paying</Badge>
                            ) : currentDues ? getStatusBadge(currentDues.status) : (
                              <Badge variant="outline" className="text-xs">Not Recorded</Badge>
                            )}
                          </div>
                        </div>
                        
                        {canEdit && !isExempt && (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              className="flex-1 bg-green-600 hover:bg-green-700 h-9 text-xs"
                              onClick={() => handleQuickDuesUpdate(member, 'paid')}
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Paid
                            </Button>
                            <Button
                              size="sm"
                              className="flex-1 bg-orange-500 hover:bg-orange-600 h-9 text-xs"
                              onClick={() => handleQuickDuesUpdate(member, 'late')}
                            >
                              <Clock className="w-4 h-4 mr-1" />
                              Late
                            </Button>
                            <Button
                              size="sm"
                              className="flex-1 bg-red-600 hover:bg-red-700 h-9 text-xs"
                              onClick={() => handleQuickDuesUpdate(member, 'unpaid')}
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              Unpaid
                            </Button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Subscriptions Dialog */}
      <Dialog open={showSubscriptionsDialog} onOpenChange={setShowSubscriptionsDialog}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Square Subscriptions</DialogTitle>
            <DialogDescription>
              Active dues subscriptions from Square • {subscriptions.customer_fetch_method === 'batch' && '⚡ Using batch API'}
            </DialogDescription>
          </DialogHeader>
          {loadingSubscriptions ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <span className="ml-3 text-muted-foreground">Loading subscriptions...</span>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Matched Subscriptions */}
              <div>
                <h3 className="font-semibold text-green-500 mb-2">
                  ✓ Matched Subscriptions ({subscriptions.matched?.length || 0})
                </h3>
                {subscriptions.matched?.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Customer Name</TableHead>
                        <TableHead>Matched Member</TableHead>
                        <TableHead>Match</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Paid Through</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {subscriptions.matched.map((sub, idx) => {
                        const matchInfo = getMatchTypeLabel(sub.match_type, sub.match_score);
                        return (
                          <TableRow key={idx}>
                            <TableCell>{sub.customer_name}</TableCell>
                            <TableCell className="text-green-500 font-medium">{sub.matched_member_handle}</TableCell>
                            <TableCell>
                              {matchInfo && (
                                <Badge className={`${matchInfo.color} text-xs`}>{matchInfo.text}</Badge>
                              )}
                            </TableCell>
                            <TableCell><Badge className="bg-green-600">{sub.status}</Badge></TableCell>
                            <TableCell>{sub.charged_through_date}</TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                ) : (
                  <p className="text-muted-foreground text-sm">No matched subscriptions</p>
                )}
              </div>

              {/* Unmatched Subscriptions with Manual Linking */}
              <div>
                <h3 className="font-semibold text-yellow-500 mb-2">
                  ⚠ Unmatched Subscriptions ({subscriptions.unmatched?.length || 0})
                  {subscriptions.unmatched?.length > 0 && canEdit && (
                    <span className="text-xs font-normal text-muted-foreground ml-2">
                      Click "Link" to manually assign a member
                    </span>
                  )}
                </h3>
                {subscriptions.unmatched?.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Customer Name</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Status</TableHead>
                        {canEdit && <TableHead>Actions</TableHead>}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {subscriptions.unmatched.map((sub, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{sub.customer_name || 'Unknown'}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">{sub.customer_email || '-'}</TableCell>
                          <TableCell><Badge variant="outline">{sub.status}</Badge></TableCell>
                          {canEdit && (
                            <TableCell>
                              <div className="flex gap-2">
                                <Button 
                                  size="sm" 
                                  variant="outline"
                                  onClick={() => {
                                    setLinkingSubscription(sub);
                                    setSelectedMemberForLink('');
                                  }}
                                >
                                  Link
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="destructive"
                                  disabled={cancellingSubscription === sub.subscription_id}
                                  onClick={() => handleCancelSquareSubscription(sub)}
                                >
                                  {cancellingSubscription === sub.subscription_id ? 'Cancelling...' : 'Cancel'}
                                </Button>
                              </div>
                            </TableCell>
                          )}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <p className="text-green-500 text-sm">🎉 All subscriptions matched!</p>
                )}
              </div>

              {/* Manual Linking Section */}
              {linkingSubscription && (
                <div className="border rounded-lg p-4 bg-slate-800">
                  <h4 className="font-semibold mb-3">Link Subscription to Member</h4>
                  <div className="space-y-3">
                    <div>
                      <Label className="text-muted-foreground">Customer from Square:</Label>
                      <p className="font-medium">{linkingSubscription.customer_name} ({linkingSubscription.customer_email || 'No email'})</p>
                    </div>
                    <div>
                      <Label>Select Member to Link:</Label>
                      <Select value={selectedMemberForLink} onValueChange={setSelectedMemberForLink}>
                        <SelectTrigger>
                          <SelectValue placeholder="Choose a member..." />
                        </SelectTrigger>
                        <SelectContent>
                          {allMembersForLinking.map(member => (
                            <SelectItem key={member.id} value={member.id}>
                              {member.handle} - {member.name} ({member.chapter})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        onClick={handleLinkSubscription} 
                        disabled={!selectedMemberForLink || linkingInProgress}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {linkingInProgress ? 'Linking...' : 'Confirm Link'}
                      </Button>
                      <Button variant="outline" onClick={() => setLinkingSubscription(null)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSubscriptionsDialog(false)}>Close</Button>
            <Button onClick={handleSyncSubscriptions} className="bg-purple-600 hover:bg-purple-700">
              Sync Now
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Attendance Dialog */}
      <Dialog open={attendanceDialog} onOpenChange={setAttendanceDialog}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-md mx-4 sm:mx-auto">
          <DialogHeader>
            <DialogTitle className="text-white">Record Attendance</DialogTitle>
            <DialogDescription>
              Recording attendance for {selectedMember?.handle}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-300">Meeting Date</Label>
              <Input 
                type="date" 
                value={attendanceForm.meeting_date}
                onChange={(e) => setAttendanceForm({...attendanceForm, meeting_date: e.target.value})}
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Meeting Type</Label>
              <Select value={attendanceForm.meeting_type} onValueChange={(v) => setAttendanceForm({...attendanceForm, meeting_type: v})}>
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  {(MEETING_TYPES_BY_CHAPTER[selectedChapter] || []).map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Status</Label>
              <Select value={attendanceForm.status} onValueChange={(v) => setAttendanceForm({...attendanceForm, status: v})}>
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="present">Present</SelectItem>
                  <SelectItem value="absent">Absent</SelectItem>
                  <SelectItem value="excused">Excused</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Notes (Optional)</Label>
              <Textarea 
                value={attendanceForm.notes}
                onChange={(e) => setAttendanceForm({...attendanceForm, notes: e.target.value})}
                placeholder="Any additional notes..."
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>
          </div>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => setAttendanceDialog(false)} className="w-full sm:w-auto">Cancel</Button>
            <Button onClick={handleAttendanceSubmit} className="w-full sm:w-auto">Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dues Dialog - Simplified */}
      <Dialog open={duesDialog} onOpenChange={setDuesDialog}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-[95vw] sm:max-w-md mx-2 sm:mx-auto p-4 sm:p-6">
          <DialogHeader className="pb-2">
            <DialogTitle className="text-white text-lg">Update Dues</DialogTitle>
            <DialogDescription className="text-sm">
              Update dues status for {selectedMember?.handle}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-300 text-sm">Status</Label>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
                {DUES_STATUSES.map(status => {
                  const Icon = status.icon;
                  return (
                    <Button
                      key={status.value}
                      type="button"
                      size="sm"
                      className={`${duesForm.status === status.value ? status.color : 'bg-gray-600'} text-xs sm:text-sm px-2 py-2`}
                      onClick={() => setDuesForm({...duesForm, status: status.value})}
                    >
                      <Icon className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                      <span className="truncate">{status.label}</span>
                    </Button>
                  );
                })}
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300 text-sm">Notes (Optional)</Label>
              <Textarea 
                value={duesForm.notes}
                onChange={(e) => setDuesForm({...duesForm, notes: e.target.value})}
                placeholder="Any additional notes..."
                className="bg-slate-700 border-slate-600 text-white text-sm min-h-[80px]"
              />
            </div>
          </div>
          <DialogFooter className="flex-col-reverse sm:flex-row gap-2 pt-4">
            <Button variant="outline" onClick={() => setDuesDialog(false)} className="w-full sm:w-auto border-slate-600 text-slate-300">Cancel</Button>
            <Button onClick={handleDuesSubmit} className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700">Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Member Meetings Dialog */}
      <Dialog open={viewMeetingsDialog} onOpenChange={setViewMeetingsDialog}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto bg-slate-800 border-slate-700 mx-2 sm:mx-auto">
          <DialogHeader>
            <DialogTitle className="text-white">Meeting Attendance History</DialogTitle>
            <DialogDescription>
              Meetings attended by {viewMeetingsMember?.handle}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4" ref={printRef}>
            {viewMeetingsMember && (
              <>
                {/* Header with stats */}
                <div className="flex items-center justify-between bg-slate-800 p-3 rounded-lg">
                  <div>
                    <span className="font-bold text-lg">{viewMeetingsMember.handle}</span>
                    <span className="text-muted-foreground ml-2">({viewMeetingsMember.title || 'Member'})</span>
                  </div>
                  <div className="text-right">
                    {(() => {
                      const stats = getAttendanceStats(viewMeetingsMember.id);
                      return (
                        <div>
                          <span className={stats.rate >= 80 ? 'text-green-500' : stats.rate >= 50 ? 'text-yellow-500' : 'text-red-500'}>
                            {stats.rate}% Attendance
                          </span>
                          <span className="text-muted-foreground text-sm ml-2">
                            ({stats.present}/{stats.total} meetings)
                          </span>
                        </div>
                      );
                    })()}
                  </div>
                </div>

                {/* Filter and Print Controls */}
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Label>Filter by Month:</Label>
                    <Select value={viewMeetingsFilter} onValueChange={setViewMeetingsFilter}>
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Time</SelectItem>
                        {getAvailableMonths(viewMeetingsMember.id).map(month => (
                          <SelectItem key={month} value={month}>{formatMonth(month)}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button variant="outline" onClick={handlePrintMeetings}>
                    <Printer className="w-4 h-4 mr-2" />
                    Print
                  </Button>
                </div>
                
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Meeting Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Notes</TableHead>
                      {canEdit && <TableHead>Delete</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {getFilteredMeetings(viewMeetingsMember.id)
                      .map((record, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{record.meeting_date}</TableCell>
                          <TableCell>{getMeetingTypeLabel(record.meeting_type)}</TableCell>
                          <TableCell>{getStatusBadge(record.status)}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">{record.notes || '-'}</TableCell>
                          {canEdit && (
                            <TableCell>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => handleDeleteAttendance(record.id)}
                              >
                                <XCircle className="w-4 h-4" />
                              </Button>
                            </TableCell>
                          )}
                        </TableRow>
                      ))
                    }
                    {getFilteredMeetings(viewMeetingsMember?.id || '').length === 0 && (
                      <TableRow>
                        <TableCell colSpan={canEdit ? 5 : 4} className="text-center text-muted-foreground py-8">
                          {viewMeetingsFilter === 'all' ? 'No meeting records found' : `No meetings found for ${formatMonth(viewMeetingsFilter)}`}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </>
            )}
          </div>
          <DialogFooter>
            <Button onClick={() => setViewMeetingsDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dues History Dialog */}
      <Dialog open={duesHistoryDialog} onOpenChange={setDuesHistoryDialog}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto bg-slate-800 border-slate-700 mx-2 sm:mx-auto">
          <DialogHeader>
            <DialogTitle className="text-white">Dues Payment History</DialogTitle>
            <DialogDescription>
              Payment history for {duesHistoryMember?.handle}
            </DialogDescription>
          </DialogHeader>
          
          {loadingDuesHistory ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <span className="ml-3 text-muted-foreground">Loading history...</span>
            </div>
          ) : duesHistoryData ? (
            <div className="space-y-6">
              {/* Last Paid Summary */}
              <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                <h3 className="font-semibold text-white mb-2">Last Payment</h3>
                {duesHistoryData.last_paid ? (
                  <div className="text-lg">
                    <span className="text-green-400 font-bold">{duesHistoryData.last_paid}</span>
                    {duesHistoryData.last_paid_note && (
                      <span className="text-sm text-slate-400 ml-2">- {duesHistoryData.last_paid_note}</span>
                    )}
                  </div>
                ) : (
                  <span className="text-slate-400">No payment records found</span>
                )}
              </div>

              {/* Subscription Info */}
              {duesHistoryData.subscription_info && (
                <div className="bg-purple-900/30 rounded-lg p-4 border border-purple-700/50">
                  <h3 className="font-semibold text-purple-300 mb-2">Square Subscription</h3>
                  <div className="text-sm space-y-1">
                    <div><span className="text-slate-400">Customer:</span> <span className="text-white">{duesHistoryData.subscription_info.customer_name}</span></div>
                    <div><span className="text-slate-400">Last Synced:</span> <span className="text-white">{duesHistoryData.subscription_info.last_synced ? new Date(duesHistoryData.subscription_info.last_synced).toLocaleString() : 'Never'}</span></div>
                    <div><span className="text-slate-400">Subscription ID:</span> <span className="text-xs text-slate-300 font-mono">{duesHistoryData.subscription_info.square_subscription_id}</span></div>
                  </div>
                </div>
              )}

              {/* Square Payments */}
              {duesHistoryData.square_payments?.length > 0 && (
                <div>
                  <h3 className="font-semibold text-white mb-3">Square Payment History</h3>
                  <div className="space-y-2">
                    {duesHistoryData.square_payments.map((payment, idx) => (
                      <div key={idx} className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="text-green-400 font-bold">${payment.amount?.toFixed(2) || '0.00'} {payment.currency || 'USD'}</div>
                            {payment.paid_at ? (
                              <div className="text-xs text-slate-400">
                                <span className="text-slate-500">Paid:</span> {new Date(payment.paid_at).toLocaleDateString('en-US', { 
                                  year: 'numeric', 
                                  month: 'long', 
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </div>
                            ) : payment.invoice_date && (
                              <div className="text-xs text-slate-400">
                                <span className="text-slate-500">Invoice Date:</span> {new Date(payment.invoice_date).toLocaleDateString('en-US', { 
                                  year: 'numeric', 
                                  month: 'long', 
                                  day: 'numeric'
                                })}
                              </div>
                            )}
                          </div>
                          <Badge className={payment.status === 'PAID' || payment.status === 'COMPLETED' ? 'bg-green-600' : 'bg-yellow-600'}>
                            {payment.status}
                          </Badge>
                        </div>
                        <div className="mt-2 text-xs space-y-1">
                          {payment.payment_id && (
                            <div>
                              <span className="text-slate-400">Transaction ID:</span>
                              <span className="text-slate-300 font-mono ml-1 break-all">{payment.payment_id}</span>
                            </div>
                          )}
                          {payment.invoice_id && (
                            <div>
                              <span className="text-slate-400">Invoice ID:</span>
                              <span className="text-slate-300 font-mono ml-1 break-all">{payment.invoice_id}</span>
                            </div>
                          )}
                        </div>
                        {payment.receipt_url && (
                          <a 
                            href={payment.receipt_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-xs text-blue-400 hover:underline mt-1 inline-block"
                          >
                            View Receipt →
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Dues Records */}
              {duesHistoryData.dues_records?.length > 0 && (
                <div>
                  <h3 className="font-semibold text-white mb-3">Manual Dues Records</h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {duesHistoryData.dues_records.map((record, idx) => (
                      <div key={idx} className="bg-slate-700/50 rounded-lg p-3 border border-slate-600 flex justify-between items-center">
                        <div>
                          <span className="text-white">{record.month}</span>
                          {record.notes && <span className="text-xs text-slate-400 ml-2">- {record.notes}</span>}
                        </div>
                        {getStatusBadge(record.status)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No Data Message */}
              {!duesHistoryData.square_payments?.length && !duesHistoryData.dues_records?.length && !duesHistoryData.last_paid && (
                <div className="text-center py-8 text-slate-400">
                  <DollarSign className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No payment history found for this member.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400">
              <p>Failed to load dues history.</p>
            </div>
          )}
          
          <DialogFooter>
            <Button onClick={() => setDuesHistoryDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default OfficerTracking;
