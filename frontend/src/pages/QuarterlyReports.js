import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { ArrowLeft, Download, FileSpreadsheet, Users, DollarSign, UserCheck, Printer, Eye, Calendar } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHAPTERS = ["All", "National", "AD", "HA", "HS"];
const QUARTERS = [
  { value: "all", label: "Full Year" },
  { value: "1", label: "Q1 (Jan-Mar)" },
  { value: "2", label: "Q2 (Apr-Jun)" },
  { value: "3", label: "Q3 (Jul-Sep)" },
  { value: "4", label: "Q4 (Oct-Dec)" },
];

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function QuarterlyReports() {
  const navigate = useNavigate();
  const currentYear = new Date().getFullYear();
  const currentQuarter = Math.ceil((new Date().getMonth() + 1) / 3);
  
  const [selectedYear, setSelectedYear] = useState(currentYear.toString());
  const [selectedQuarter, setSelectedQuarter] = useState(currentQuarter.toString());
  const [selectedChapter, setSelectedChapter] = useState("All");
  const [loading, setLoading] = useState(false);
  
  // Preview state
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewData, setPreviewData] = useState([]);
  const [previewType, setPreviewType] = useState(""); // "dues", "attendance", "prospects"
  const [previewLoading, setPreviewLoading] = useState(false);

  const token = localStorage.getItem('token');
  
  // Generate year options (current year and 10 years back)
  const years = Array.from({ length: 11 }, (_, i) => (currentYear - i).toString());

  // Get months for selected quarter
  const getQuarterMonths = () => {
    if (selectedQuarter === "all") return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
    const q = parseInt(selectedQuarter);
    const start = (q - 1) * 3;
    return [start, start + 1, start + 2];
  };

  const downloadReport = async (reportType) => {
    setLoading(true);
    try {
      let url = "";
      let filename = "";
      const quarterParam = selectedQuarter === "all" ? "all" : selectedQuarter;
      
      switch (reportType) {
        case "attendance":
          url = `${API}/reports/attendance/quarterly?year=${selectedYear}&quarter=${quarterParam}&chapter=${selectedChapter}`;
          filename = selectedQuarter === "all" 
            ? `attendance_${selectedYear}${selectedChapter !== 'All' ? `_${selectedChapter}` : ''}.csv`
            : `attendance_Q${selectedQuarter}_${selectedYear}${selectedChapter !== 'All' ? `_${selectedChapter}` : ''}.csv`;
          break;
        case "dues":
          url = `${API}/reports/dues/quarterly?year=${selectedYear}&quarter=${quarterParam}&chapter=${selectedChapter}`;
          filename = selectedQuarter === "all"
            ? `dues_${selectedYear}${selectedChapter !== 'All' ? `_${selectedChapter}` : ''}.csv`
            : `dues_Q${selectedQuarter}_${selectedYear}${selectedChapter !== 'All' ? `_${selectedChapter}` : ''}.csv`;
          break;
        case "prospects":
          url = `${API}/reports/prospects/attendance/quarterly?year=${selectedYear}&quarter=${quarterParam}`;
          filename = selectedQuarter === "all"
            ? `prospects_attendance_${selectedYear}.csv`
            : `prospects_attendance_Q${selectedQuarter}_${selectedYear}.csv`;
          break;
        default:
          return;
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'text/csv' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success(`${reportType.charAt(0).toUpperCase() + reportType.slice(1)} report downloaded`);
    } catch (error) {
      console.error('Error downloading report:', error);
      toast.error('Failed to download report');
    } finally {
      setLoading(false);
    }
  };

  // Preview Member Dues
  const previewDuesReport = async () => {
    setPreviewLoading(true);
    setPreviewType("dues");
    try {
      // Fetch members and officer_dues data together
      const [membersRes, officerDuesRes, extensionsRes] = await Promise.all([
        axios.get(`${API}/members`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/officer-tracking/dues`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/dues-reminders/extensions`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: { extensions: [] } }))
      ]);
      
      let members = membersRes.data;
      const officerDues = officerDuesRes.data || [];
      const extensions = extensionsRes.data?.extensions || [];
      
      // Build lookup for officer_dues: member_id -> { month_key: status }
      const officerDuesLookup = {};
      officerDues.forEach(record => {
        const memberId = record.member_id;
        const monthKey = record.month; // e.g., "Jan_2026"
        if (!officerDuesLookup[memberId]) {
          officerDuesLookup[memberId] = {};
        }
        officerDuesLookup[memberId][monthKey] = record.status;
      });
      
      // Build set of members with active extensions
      const today = new Date().toISOString().split('T')[0];
      const extendedMemberIds = new Set(
        extensions
          .filter(ext => ext.extension_date >= today)
          .map(ext => ext.member_id)
      );
      
      // Attach lookup and extension info to each member
      members = members.map(m => ({
        ...m,
        _officerDues: officerDuesLookup[m.id] || {},
        _hasExtension: extendedMemberIds.has(m.id)
      }));
      
      if (selectedChapter !== "All") {
        members = members.filter(m => m.chapter === selectedChapter);
      }
      
      const chapterOrder = { "National": 0, "AD": 1, "HA": 2, "HS": 3 };
      members.sort((a, b) => {
        const chapterDiff = (chapterOrder[a.chapter] || 99) - (chapterOrder[b.chapter] || 99);
        if (chapterDiff !== 0) return chapterDiff;
        return (a.handle || '').localeCompare(b.handle || '');
      });
      
      setPreviewData(members);
      setPreviewOpen(true);
    } catch (error) {
      console.error('Error loading preview:', error);
      toast.error('Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  // Preview Member Attendance
  const previewAttendanceReport = async () => {
    setPreviewLoading(true);
    setPreviewType("attendance");
    try {
      const response = await axios.get(`${API}/members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      let members = response.data;
      
      if (selectedChapter !== "All") {
        members = members.filter(m => m.chapter === selectedChapter);
      }
      
      const chapterOrder = { "National": 0, "AD": 1, "HA": 2, "HS": 3 };
      members.sort((a, b) => {
        const chapterDiff = (chapterOrder[a.chapter] || 99) - (chapterOrder[b.chapter] || 99);
        if (chapterDiff !== 0) return chapterDiff;
        return (a.handle || '').localeCompare(b.handle || '');
      });
      
      setPreviewData(members);
      setPreviewOpen(true);
    } catch (error) {
      console.error('Error loading preview:', error);
      toast.error('Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  // Preview Prospect Attendance
  const previewProspectsReport = async () => {
    setPreviewLoading(true);
    setPreviewType("prospects");
    try {
      const response = await axios.get(`${API}/prospects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      let prospects = response.data;
      
      // Sort by name
      prospects.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
      
      setPreviewData(prospects);
      setPreviewOpen(true);
    } catch (error) {
      console.error('Error loading preview:', error);
      toast.error('Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handlePrint = () => {
    const printContent = document.getElementById('preview-table');
    if (!printContent) return;
    
    const quarterLabel = selectedQuarter === "all" 
      ? `Full Year ${selectedYear}` 
      : `${QUARTERS.find(q => q.value === selectedQuarter)?.label} ${selectedYear}`;
    
    const reportTitles = {
      dues: "Dues Report",
      attendance: "Meeting Attendance Report",
      prospects: "Prospect Attendance Report"
    };
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>${reportTitles[previewType]} - ${quarterLabel}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { font-size: 18px; margin-bottom: 5px; }
            h2 { font-size: 14px; color: #666; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; font-size: 10px; }
            th, td { border: 1px solid #333; padding: 3px 5px; text-align: center; }
            th { background-color: #1e293b; color: white; }
            .member-info { text-align: left; }
            .paid { background-color: #dcfce7; color: #166534; }
            .late { background-color: #fef3c7; color: #92400e; }
            .unpaid { background-color: #fee2e2; color: #991b1b; }
            .present { background-color: #dcfce7; color: #166534; }
            .excused { background-color: #fef3c7; color: #92400e; }
            .absent { background-color: #fee2e2; color: #991b1b; }
            @media print {
              body { padding: 10px; }
              table { font-size: 8px; }
              th, td { padding: 2px 3px; }
            }
          </style>
        </head>
        <body>
          <h1>Brothers of the Highway - ${reportTitles[previewType]}</h1>
          <h2>${quarterLabel} ${selectedChapter !== 'All' && previewType !== 'prospects' ? '- ' + selectedChapter + ' Chapter' : previewType !== 'prospects' ? '- All Chapters' : ''}</h2>
          ${printContent.outerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  // Get dues status for a member
  const getDuesStatus = (member, monthIndex) => {
    // Check for non-dues-paying members
    if (member.non_dues_paying) {
      return "exempt";
    }
    
    // Build the month key like "Jan_2026"
    const monthKey = `${MONTHS[monthIndex]}_${selectedYear}`;
    
    // First check officer_dues (A&D page source)
    const officerDuesStatus = member._officerDues?.[monthKey];
    if (officerDuesStatus) {
      return officerDuesStatus;
    }
    
    // Check for extension (only for current/future months)
    const currentMonth = new Date().getMonth();
    if (member._hasExtension && monthIndex >= currentMonth && parseInt(selectedYear) === new Date().getFullYear()) {
      return "extended";
    }
    
    // Fallback to member.dues field
    const yearData = member.dues?.[selectedYear];
    if (!yearData || !yearData[monthIndex]) return "unpaid";
    
    const monthData = yearData[monthIndex];
    if (typeof monthData === 'object') {
      return monthData.status || "unpaid";
    }
    return monthData ? "paid" : "unpaid";
  };

  // Get attendance for a member in a specific month
  const getAttendanceForMonth = (member, monthIndex) => {
    const yearData = member.meeting_attendance?.[selectedYear];
    if (!yearData || !Array.isArray(yearData)) return { present: 0, excused: 0, absent: 0, total: 0 };
    
    // Filter meetings for this month
    const monthMeetings = yearData.filter(meeting => {
      if (!meeting.date) return false;
      const meetingDate = new Date(meeting.date);
      return meetingDate.getMonth() === monthIndex;
    });
    
    let present = 0, excused = 0, absent = 0;
    monthMeetings.forEach(m => {
      const status = m.status || 0;
      if (status === 1) present++;
      else if (status === 2) excused++;
      else absent++;
    });
    
    return { present, excused, absent, total: monthMeetings.length };
  };

  // Get prospect attendance for a month
  const getProspectAttendanceForMonth = (prospect, monthIndex) => {
    const yearData = prospect.meeting_attendance?.[selectedYear];
    if (!yearData || !Array.isArray(yearData)) return { present: 0, total: 0 };
    
    const monthMeetings = yearData.filter(meeting => {
      if (!meeting.date) return false;
      const meetingDate = new Date(meeting.date);
      return meetingDate.getMonth() === monthIndex;
    });
    
    let present = 0;
    monthMeetings.forEach(m => {
      if (m.status === 1) present++;
    });
    
    return { present, total: monthMeetings.length };
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "paid": return "✓";
      case "late": return "L";
      case "exempt": return "—";
      case "extended": return "E";
      default: return "✗";
    }
  };

  const quarterMonths = getQuarterMonths();
  const quarterLabel = selectedQuarter === "all" 
    ? `Full Year ${selectedYear}` 
    : `${QUARTERS.find(q => q.value === selectedQuarter)?.label} ${selectedYear}`;

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <Button
            onClick={() => navigate("/")}
            variant="ghost"
            size="sm"
            className="text-slate-300 hover:text-white mb-4 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Members
          </Button>
          
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileSpreadsheet className="w-6 h-6 text-green-400" />
            Reports
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Download or print meeting attendance and dues reports
          </p>
        </div>

        {/* Filter Controls */}
        <Card className="bg-slate-800 border-slate-700 mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-400" />
              Report Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Label className="text-slate-300 text-sm">Year</Label>
                <Select value={selectedYear} onValueChange={setSelectedYear}>
                  <SelectTrigger className="mt-1 bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-600">
                    {years.map(year => (
                      <SelectItem key={year} value={year} className="text-white hover:bg-slate-700">
                        {year}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-slate-300 text-sm">Period</Label>
                <Select value={selectedQuarter} onValueChange={setSelectedQuarter}>
                  <SelectTrigger className="mt-1 bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-600">
                    {QUARTERS.map(q => (
                      <SelectItem key={q.value} value={q.value} className="text-white hover:bg-slate-700">
                        {q.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-slate-300 text-sm">Chapter</Label>
                <Select value={selectedChapter} onValueChange={setSelectedChapter}>
                  <SelectTrigger className="mt-1 bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-600">
                    {CHAPTERS.map(ch => (
                      <SelectItem key={ch} value={ch} className="text-white hover:bg-slate-700">
                        {ch === "All" ? "All Chapters" : ch}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Report Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Member Attendance Report */}
          <Card className="bg-slate-800 border-slate-700 hover:border-green-500/50 transition-colors">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-base flex items-center gap-2">
                <Users className="w-5 h-5 text-green-400" />
                Member Attendance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-400 text-sm mb-4">
                Meeting attendance for {quarterLabel}
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={previewAttendanceReport}
                  disabled={loading || previewLoading}
                  variant="outline"
                  className="flex-1 border-green-600 text-green-400 hover:bg-green-900/30"
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Preview
                </Button>
                <Button
                  onClick={() => downloadReport('attendance')}
                  disabled={loading}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  <Download className="w-4 h-4 mr-1" />
                  CSV
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Dues Report */}
          <Card className="bg-slate-800 border-slate-700 hover:border-blue-500/50 transition-colors">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-base flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-blue-400" />
                Member Dues
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-400 text-sm mb-4">
                Dues payment status for {quarterLabel}
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={previewDuesReport}
                  disabled={loading || previewLoading}
                  variant="outline"
                  className="flex-1 border-blue-600 text-blue-400 hover:bg-blue-900/30"
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Preview
                </Button>
                <Button
                  onClick={() => downloadReport('dues')}
                  disabled={loading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  <Download className="w-4 h-4 mr-1" />
                  CSV
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Prospects Attendance Report */}
          <Card className="bg-slate-800 border-slate-700 hover:border-orange-500/50 transition-colors">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-base flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-orange-400" />
                Prospect Attendance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-400 text-sm mb-4">
                Prospect meetings for {quarterLabel}
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={previewProspectsReport}
                  disabled={loading || previewLoading}
                  variant="outline"
                  className="flex-1 border-orange-600 text-orange-400 hover:bg-orange-900/30"
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Preview
                </Button>
                <Button
                  onClick={() => downloadReport('prospects')}
                  disabled={loading}
                  className="flex-1 bg-orange-600 hover:bg-orange-700"
                >
                  <Download className="w-4 h-4 mr-1" />
                  CSV
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Legend */}
        <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <h3 className="text-sm font-medium text-slate-300 mb-2">Legend</h3>
          <div className="flex flex-wrap gap-4 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1">
              <span className="w-3 h-3 bg-green-600 rounded"></span> Paid / Present
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="w-3 h-3 bg-yellow-600 rounded"></span> Late / Excused
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="w-3 h-3 bg-red-600 rounded"></span> Unpaid / Absent
            </span>
          </div>
        </div>
      </div>

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-[95vw] max-h-[90vh] overflow-hidden bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                {previewType === "dues" && <DollarSign className="w-5 h-5 text-blue-400" />}
                {previewType === "attendance" && <Users className="w-5 h-5 text-green-400" />}
                {previewType === "prospects" && <UserCheck className="w-5 h-5 text-orange-400" />}
                {previewType === "dues" && "Dues Report"}
                {previewType === "attendance" && "Member Attendance Report"}
                {previewType === "prospects" && "Prospect Attendance Report"}
                {" - "}{quarterLabel}
                {selectedChapter !== 'All' && previewType !== 'prospects' && ` - ${selectedChapter}`}
              </span>
              <Button
                onClick={handlePrint}
                size="sm"
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Printer className="w-4 h-4 mr-2" />
                Print
              </Button>
            </DialogTitle>
          </DialogHeader>
          
          <div className="overflow-auto max-h-[70vh]">
            <Table id="preview-table" className="text-sm">
              <TableHeader>
                <TableRow className="border-slate-700">
                  <TableHead className="text-white bg-slate-800 sticky left-0 z-10">
                    {previewType === "prospects" ? "Prospect" : "Member"}
                  </TableHead>
                  {previewType !== "prospects" && (
                    <TableHead className="text-white bg-slate-800">Chapter</TableHead>
                  )}
                  {quarterMonths.map(monthIndex => (
                    <TableHead key={monthIndex} className="text-white bg-slate-800 text-center px-2">
                      {MONTHS[monthIndex]}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {previewData.map((item, idx) => (
                  <TableRow key={item.id || idx} className="border-slate-700">
                    <TableCell className="text-white font-medium sticky left-0 bg-slate-900 z-10 member-info">
                      {item.handle || item.name}
                    </TableCell>
                    {previewType !== "prospects" && (
                      <TableCell className="text-slate-300">{item.chapter}</TableCell>
                    )}
                    {quarterMonths.map(monthIndex => {
                      if (previewType === "dues") {
                        const status = getDuesStatus(item, monthIndex);
                        return (
                          <TableCell 
                            key={monthIndex} 
                            className={`text-center px-2 ${
                              status === 'paid' ? 'bg-green-900/50 text-green-400 paid' :
                              status === 'late' ? 'bg-yellow-900/50 text-yellow-400 late' :
                              status === 'exempt' ? 'bg-slate-700/50 text-slate-400' :
                              status === 'extended' ? 'bg-blue-900/50 text-blue-400' :
                              'bg-red-900/50 text-red-400 unpaid'
                            }`}
                          >
                            {getStatusIcon(status)}
                          </TableCell>
                        );
                      } else if (previewType === "attendance") {
                        const att = getAttendanceForMonth(item, monthIndex);
                        if (att.total === 0) {
                          return (
                            <TableCell key={monthIndex} className="text-center px-2 text-slate-500">
                              -
                            </TableCell>
                          );
                        }
                        return (
                          <TableCell 
                            key={monthIndex} 
                            className={`text-center px-2 ${
                              att.present === att.total ? 'bg-green-900/50 text-green-400 present' :
                              att.present > 0 ? 'bg-yellow-900/50 text-yellow-400 excused' :
                              'bg-red-900/50 text-red-400 absent'
                            }`}
                          >
                            {att.present}/{att.total}
                          </TableCell>
                        );
                      } else {
                        // Prospects
                        const att = getProspectAttendanceForMonth(item, monthIndex);
                        if (att.total === 0) {
                          return (
                            <TableCell key={monthIndex} className="text-center px-2 text-slate-500">
                              -
                            </TableCell>
                          );
                        }
                        return (
                          <TableCell 
                            key={monthIndex} 
                            className={`text-center px-2 ${
                              att.present === att.total ? 'bg-green-900/50 text-green-400 present' :
                              att.present > 0 ? 'bg-yellow-900/50 text-yellow-400' :
                              'bg-red-900/50 text-red-400 absent'
                            }`}
                          >
                            {att.present}/{att.total}
                          </TableCell>
                        );
                      }
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            
            {previewData.length === 0 && (
              <div className="text-center py-8 text-slate-400">
                No data found for the selected filters
              </div>
            )}
          </div>
          
          <div className="flex items-center justify-between pt-4 border-t border-slate-700">
            <div className="text-xs text-slate-400">
              {previewType === "dues" ? (
                <>
                  <span className="inline-flex items-center gap-1 mr-4">
                    <span className="w-3 h-3 bg-green-600 rounded"></span> Paid
                  </span>
                  <span className="inline-flex items-center gap-1 mr-4">
                    <span className="w-3 h-3 bg-yellow-600 rounded"></span> Late
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 bg-red-600 rounded"></span> Unpaid
                  </span>
                </>
              ) : (
                <>
                  <span className="inline-flex items-center gap-1 mr-4">
                    <span className="w-3 h-3 bg-green-600 rounded"></span> All Present
                  </span>
                  <span className="inline-flex items-center gap-1 mr-4">
                    <span className="w-3 h-3 bg-yellow-600 rounded"></span> Partial
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 bg-red-600 rounded"></span> None
                  </span>
                </>
              )}
            </div>
            <div className="text-xs text-slate-400">
              {previewData.length} {previewType === "prospects" ? "prospects" : "members"}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
