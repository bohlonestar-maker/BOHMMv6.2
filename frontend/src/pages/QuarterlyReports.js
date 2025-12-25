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
import { toast } from "sonner";
import { ArrowLeft, Download, FileSpreadsheet, Users, DollarSign, UserCheck } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHAPTERS = ["All", "National", "AD", "HA", "HS"];
const QUARTERS = [
  { value: "1", label: "Q1 (Jan-Mar)" },
  { value: "2", label: "Q2 (Apr-Jun)" },
  { value: "3", label: "Q3 (Jul-Sep)" },
  { value: "4", label: "Q4 (Oct-Dec)" },
];

export default function QuarterlyReports() {
  const navigate = useNavigate();
  const currentYear = new Date().getFullYear();
  const currentQuarter = Math.ceil((new Date().getMonth() + 1) / 3);
  
  const [selectedYear, setSelectedYear] = useState(currentYear.toString());
  const [selectedQuarter, setSelectedQuarter] = useState(currentQuarter.toString());
  const [selectedChapter, setSelectedChapter] = useState("All");
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem('token');
  
  // Generate year options (current year and 5 years back)
  const years = Array.from({ length: 6 }, (_, i) => (currentYear - i).toString());

  const downloadReport = async (reportType) => {
    setLoading(true);
    try {
      let url = "";
      let filename = "";
      
      switch (reportType) {
        case "attendance":
          url = `${API}/reports/attendance/quarterly?year=${selectedYear}&quarter=${selectedQuarter}&chapter=${selectedChapter}`;
          filename = `attendance_Q${selectedQuarter}_${selectedYear}${selectedChapter !== 'All' ? `_${selectedChapter}` : ''}.csv`;
          break;
        case "dues":
          url = `${API}/reports/dues/quarterly?year=${selectedYear}&quarter=${selectedQuarter}&chapter=${selectedChapter}`;
          filename = `dues_Q${selectedQuarter}_${selectedYear}${selectedChapter !== 'All' ? `_${selectedChapter}` : ''}.csv`;
          break;
        case "prospects":
          url = `${API}/reports/prospects/attendance/quarterly?year=${selectedYear}&quarter=${selectedQuarter}`;
          filename = `prospects_attendance_Q${selectedQuarter}_${selectedYear}.csv`;
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
            Quarterly Reports
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Download meeting attendance and dues reports by quarter and chapter
          </p>
        </div>

        {/* Filter Controls */}
        <Card className="bg-slate-800 border-slate-700 mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-white text-lg">Report Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Year Select */}
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

              {/* Quarter Select */}
              <div>
                <Label className="text-slate-300 text-sm">Quarter</Label>
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

              {/* Chapter Select */}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
                Meeting attendance by chapter for {QUARTERS.find(q => q.value === selectedQuarter)?.label} {selectedYear}
              </p>
              <Button
                onClick={() => downloadReport('attendance')}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Download CSV
              </Button>
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
                Dues payment status by chapter for {QUARTERS.find(q => q.value === selectedQuarter)?.label} {selectedYear}
              </p>
              <Button
                onClick={() => downloadReport('dues')}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Download CSV
              </Button>
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
                Prospect meeting attendance for {QUARTERS.find(q => q.value === selectedQuarter)?.label} {selectedYear}
              </p>
              <Button
                onClick={() => downloadReport('prospects')}
                disabled={loading}
                className="w-full bg-orange-600 hover:bg-orange-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Download CSV
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Info Note */}
        <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <h3 className="text-sm font-medium text-slate-300 mb-2">Report Details</h3>
          <ul className="text-xs text-slate-400 space-y-1">
            <li>• <strong>Member Attendance:</strong> Shows meeting count, present/excused/absent stats per member</li>
            <li>• <strong>Member Dues:</strong> Shows paid/late/unpaid status for each month in the quarter</li>
            <li>• <strong>Prospect Attendance:</strong> Shows prospect meeting attendance (chapter filter not applicable)</li>
            <li>• Reports are sorted by chapter (National → AD → HA → HS) and then by title</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
