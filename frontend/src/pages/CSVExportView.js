import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import PageLayout from "@/components/PageLayout";
import { FileSpreadsheet, Users, DollarSign, UserCheck } from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function CSVExportView() {
  const [csvData, setCsvData] = useState([]);
  const [csvText, setCsvText] = useState('');
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('table'); // 'table' or 'raw'
  const [searchTerm, setSearchTerm] = useState('');
  const [showPrintModal, setShowPrintModal] = useState(false);
  const [showSheetsModal, setShowSheetsModal] = useState(false);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [reportYear, setReportYear] = useState(new Date().getFullYear().toString());
  const [reportQuarter, setReportQuarter] = useState(Math.ceil((new Date().getMonth() + 1) / 3).toString());
  const [reportChapter, setReportChapter] = useState('All');
  const [reportLoading, setReportLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCSVData();
  }, []);

  const fetchCSVData = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/');
      return;
    }

    try {
      const response = await axios.get(`${API}/api/members/export/csv`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'text',
      });

      const text = response.data;
      setCsvText(text);
      
      // Parse CSV
      const parsed = parseCSV(text);
      setCsvData(parsed);
      
      // Initialize all columns as selected
      if (parsed.length > 0) {
        setSelectedColumns(Array.from({ length: parsed[0].length }, (_, i) => i));
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching CSV:', error);
      setLoading(false);
    }
  };

  const parseCSV = (text) => {
    const lines = text.split('\n').filter(line => line.trim());
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
  };

  const filteredData = csvData.filter((row, index) => {
    if (index === 0) return true; // Always show header
    return row.some(cell => 
      cell.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const handleDownload = () => {
    const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brothers_of_highway_members_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    // Create optimized print window with all data
    const printWindow = window.open('', '_blank');
    const html = generatePrintHTML(csvData);
    printWindow.document.write(html);
    printWindow.document.close();
    setTimeout(() => printWindow.print(), 500);
  };

  const handleCustomPrint = () => {
    setShowPrintModal(true);
  };

  const selectPreset = (preset) => {
    const headers = csvData[0];
    const indices = [];
    
    console.log('selectPreset called with:', preset);
    console.log('Total headers:', headers.length);
    
    headers.forEach((header, index) => {
      const h = header.toLowerCase();
      
      switch(preset) {
        case 'all':
          indices.push(index);
          break;
        case 'contact':
          // Select: Chapter, Title, Member Handle, Name, Email Address, Phone Number, Mailing Address
          if (h.includes('chapter') || h.includes('title') || h.includes('handle') || 
              h.includes('name') || h.includes('email') || h.includes('phone') || h.includes('address')) {
            console.log('  Matched contact field:', header);
            indices.push(index);
          }
          break;
        case 'service':
          // Select: Handle, Military Service, Military Branch, First Responder
          if (h.includes('handle') || h.includes('military') || h.includes('first responder')) {
            console.log('  Matched service field:', header);
            indices.push(index);
          }
          break;
        case 'dues_q1':
          // Q1: January, February, March
          if (h.includes('handle') || h.includes('dues year') ||
              (h.includes('dues') && (h.includes('january') || h.includes('february') || h.includes('march')))) {
            console.log('  Matched Q1:', header);
            indices.push(index);
          }
          break;
        case 'dues_q2':
          // Q2: April, May, June
          if (h.includes('handle') || h.includes('dues year') ||
              (h.includes('dues') && (h.includes('april') || h.includes('may') || h.includes('june')))) {
            console.log('  Matched Q2:', header);
            indices.push(index);
          }
          break;
        case 'dues_q3':
          // Q3: July, August, September
          if (h.includes('handle') || h.includes('dues year') ||
              (h.includes('dues') && (h.includes('july') || h.includes('august') || h.includes('september')))) {
            console.log('  Matched Q3:', header);
            indices.push(index);
          }
          break;
        case 'dues_q4':
          // Q4: October, November, December
          if (h.includes('handle') || h.includes('dues year') ||
              (h.includes('dues') && (h.includes('october') || h.includes('november') || h.includes('december')))) {
            console.log('  Matched Q4:', header);
            indices.push(index);
          }
          break;
        case 'meetings_q1':
          // Q1: January, February, March meetings
          if (h.includes('handle') ||
              (h.includes('meeting') && (h.includes('january') || h.includes('february') || h.includes('march')))) {
            console.log('  Matched meetings Q1:', header);
            indices.push(index);
          }
          break;
        case 'meetings_q2':
          // Q2: April, May, June meetings
          if (h.includes('handle') ||
              (h.includes('meeting') && (h.includes('april') || h.includes('may') || h.includes('june')))) {
            console.log('  Matched meetings Q2:', header);
            indices.push(index);
          }
          break;
        case 'meetings_q3':
          // Q3: July, August, September meetings
          if (h.includes('handle') ||
              (h.includes('meeting') && (h.includes('july') || h.includes('august') || h.includes('september')))) {
            console.log('  Matched meetings Q3:', header);
            indices.push(index);
          }
          break;
        case 'meetings_q4':
          // Q4: October, November, December meetings
          if (h.includes('handle') ||
              (h.includes('meeting') && (h.includes('october') || h.includes('november') || h.includes('december')))) {
            console.log('  Matched meetings Q4:', header);
            indices.push(index);
          }
          break;
        default:
          break;
      }
    });
    
    console.log('Total indices selected:', indices.length);
    console.log('Indices:', indices);
    setSelectedColumns(indices);
    setSelectedPreset(preset);
  };

  const printSelectedColumns = () => {
    if (selectedColumns.length === 0) {
      alert('Please select at least one column to print.');
      return;
    }

    const filteredData = csvData.map(row => 
      selectedColumns.map(index => row[index])
    );

    // Get user info
    const username = localStorage.getItem('username') || 'Unknown User';
    
    // Get current time in CST
    const now = new Date();
    const cstTime = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/Chicago',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }).format(now);

    const printWindow = window.open('', '_blank');
    const html = generatePrintHTML(filteredData, selectedPreset, username, cstTime);
    printWindow.document.write(html);
    printWindow.document.close();
    setTimeout(() => printWindow.print(), 500);
    setShowPrintModal(false);
  };

  const generatePrintHTML = (data, preset, username, timestamp) => {
    // Convert preset code to readable name
    const presetNames = {
      'dues_q1': 'Dues - Quarter 1 (Jan, Feb, Mar)',
      'dues_q2': 'Dues - Quarter 2 (Apr, May, Jun)',
      'dues_q3': 'Dues - Quarter 3 (Jul, Aug, Sep)',
      'dues_q4': 'Dues - Quarter 4 (Oct, Nov, Dec)',
      'meetings_q1': 'Meetings - Quarter 1 (Jan, Feb, Mar)',
      'meetings_q2': 'Meetings - Quarter 2 (Apr, May, Jun)',
      'meetings_q3': 'Meetings - Quarter 3 (Jul, Aug, Sep)',
      'meetings_q4': 'Meetings - Quarter 4 (Oct, Nov, Dec)',
      'contact': 'Contact Information',
      'service': 'Military & First Responder Service',
      'all': 'All Fields'
    };
    
    const presetName = presetNames[preset] || 'Custom Selection';
    
    return `
<!DOCTYPE html>
<html>
<head>
  <title>Brothers of the Highway - Custom Print</title>
  <style>
    @page { size: landscape; margin: 0.5cm; }
    body { font-family: Arial, sans-serif; margin: 10px; }
    .header-info { background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #8b5cf6; }
    .header-info h1 { text-align: center; color: #8b5cf6; margin: 0 0 10px 0; font-size: 1.5rem; }
    .header-info .meta { display: flex; justify-content: space-between; font-size: 0.875rem; color: #1f2937; }
    .header-info .meta div { margin: 5px 0; }
    .header-info .meta strong { color: #8b5cf6; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #8b5cf6; color: white; padding: 8px; text-align: left; font-size: 0.75rem; }
    td { padding: 6px; border-bottom: 1px solid #ddd; font-size: 0.7rem; }
    tr:nth-child(even) { background: #f5f5f5; }
    @media print {
      .no-print { display: none; }
      .header-info { background: #f3f4f6; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      th { background: #8b5cf6 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  <div class="no-print" style="text-align: center; margin-bottom: 20px;">
    <button onclick="window.print()" style="background: #8b5cf6; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; margin: 5px;">Print</button>
    <button onclick="window.close()" style="background: #64748b; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; margin: 5px;">Close</button>
  </div>
  
  <div class="header-info">
    <h1>Brothers of the Highway - Member Export</h1>
    <div class="meta">
      <div><strong>Report:</strong> ${presetName}</div>
      <div><strong>Printed By:</strong> ${username}</div>
      <div><strong>Date/Time:</strong> ${timestamp} CST</div>
    </div>
  </div>
  
  <table>
    <thead><tr>${data[0].map(h => `<th>${h}</th>`).join('')}</tr></thead>
    <tbody>
      ${data.slice(1).map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')}
    </tbody>
  </table>
</body>
</html>`;
  };

  const exportToGoogleSheets = () => {
    const rows = csvText.split('\n');
    const tsvData = rows.map(row => {
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
      return cells.join('\t');
    }).join('\n');

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(tsvData).then(() => {
        alert('Data copied to clipboard! Opening Google Sheets...');
        window.open('https://sheets.google.com/create', '_blank');
        setShowSheetsModal(false);
      });
    } else {
      handleDownload();
      window.open('https://sheets.google.com/create', '_blank');
      setShowSheetsModal(false);
    }
  };

  const downloadQuarterlyReport = async (reportType) => {
    const token = localStorage.getItem('token');
    if (!token) {
      toast.error('Please login to download reports');
      return;
    }
    
    setReportLoading(true);
    try {
      let url = "";
      let filename = "";
      
      const quarterNames = { '1': 'Q1', '2': 'Q2', '3': 'Q3', '4': 'Q4' };
      const qName = quarterNames[reportQuarter];
      
      switch (reportType) {
        case "attendance":
          url = `${API}/api/reports/attendance/quarterly?year=${reportYear}&quarter=${reportQuarter}&chapter=${reportChapter}`;
          filename = `attendance_${qName}_${reportYear}${reportChapter !== 'All' ? `_${reportChapter}` : ''}.csv`;
          break;
        case "dues":
          url = `${API}/api/reports/dues/quarterly?year=${reportYear}&quarter=${reportQuarter}&chapter=${reportChapter}`;
          filename = `dues_${qName}_${reportYear}${reportChapter !== 'All' ? `_${reportChapter}` : ''}.csv`;
          break;
        case "prospects":
          url = `${API}/api/reports/prospects/attendance/quarterly?year=${reportYear}&quarter=${reportQuarter}`;
          filename = `prospects_attendance_${qName}_${reportYear}.csv`;
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
      setReportLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading CSV data...</div>
      </div>
    );
  }

  return (
    <PageLayout
      title="Member Export"
      icon={FileSpreadsheet}
      backTo="/"
      backLabel="Back"
    >
        {/* Stats */}
        <div className="bg-slate-800 rounded-lg p-3 sm:p-4 mb-4 sm:mb-6">
          <div className="flex flex-wrap gap-3 sm:gap-6 text-xs sm:text-sm">
            <div>
              <span className="text-slate-400">Members:</span>
              <span className="ml-2 font-bold text-purple-400">{csvData.length - 1}</span>
            </div>
            <div>
              <span className="text-slate-400">Columns:</span>
              <span className="ml-2 font-bold text-purple-400">{csvData[0]?.length || 0}</span>
            </div>
            <div>
              <span className="text-slate-400">Filtered:</span>
              <span className="ml-2 font-bold text-purple-400">{filteredData.length - 1}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row flex-wrap gap-2 sm:gap-3 mb-4 sm:mb-6">
          <button
            onClick={handleDownload}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base w-full sm:w-auto"
          >
            <i className="fas fa-download mr-2"></i>
            Download CSV
          </button>
          <button
            onClick={handleCustomPrint}
            className="bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base w-full sm:w-auto"
          >
            <i className="fas fa-print mr-2"></i>
            Print Custom
          </button>
          <button
            onClick={() => setShowSheetsModal(true)}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base w-full sm:w-auto"
          >
            <i className="fab fa-google mr-2"></i>
            Export to Sheets
          </button>
          <button
            onClick={() => setView(view === 'table' ? 'raw' : 'table')}
            className="bg-slate-700 hover:bg-slate-600 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base w-full sm:w-auto"
          >
            <i className={`fas fa-${view === 'table' ? 'code' : 'table'} mr-2`}></i>
            {view === 'table' ? 'Raw View' : 'Table View'}
          </button>
        </div>

        {/* Search */}
        <div className="mb-4 sm:mb-6">
          <input
            type="text"
            placeholder="Search members..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base text-white placeholder-slate-400 focus:outline-none focus:border-purple-500"
          />
        </div>

        {/* Content */}
        {view === 'table' ? (
          <div className="bg-slate-800 rounded-lg overflow-x-auto -mx-3 sm:mx-0" style={{ maxHeight: '70vh' }}>
            <table className="w-full min-w-max">
              <thead className="bg-gradient-to-r from-purple-600 to-purple-700 sticky top-0">
                <tr>
                  {csvData[0]?.map((header, i) => (
                    <th key={i} className="px-2 sm:px-3 md:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-semibold whitespace-nowrap">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredData.slice(1).map((row, i) => (
                  <tr key={i} className="border-b border-slate-700 hover:bg-slate-700">
                    {row.map((cell, j) => (
                      <td key={j} className="px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 text-xs sm:text-sm whitespace-nowrap">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <pre className="bg-slate-800 p-3 sm:p-4 md:p-6 rounded-lg overflow-auto text-xs sm:text-sm" style={{ maxHeight: '70vh' }}>
            {csvText}
          </pre>
        )}

      {/* Print Custom Modal */}
      {showPrintModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-3 sm:p-4" onClick={() => setShowPrintModal(false)}>
          <div className="bg-slate-800 rounded-lg p-4 sm:p-6 max-w-full sm:max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-purple-400 mb-3 sm:mb-4">
              <i className="fas fa-print mr-2"></i>
              Print Custom
            </h2>
            
            {/* Quarterly Reports Section */}
            <div className="mb-4 p-3 sm:p-4 bg-slate-700/50 rounded-lg border border-slate-600">
              <h3 className="text-sm font-semibold text-green-400 mb-3 flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4" />
                Quarterly Reports (CSV Download)
              </h3>
              
              {/* Filters */}
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Year</label>
                  <select
                    value={reportYear}
                    onChange={(e) => setReportYear(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-xs text-white"
                  >
                    {Array.from({ length: 6 }, (_, i) => (new Date().getFullYear() - i).toString()).map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Quarter</label>
                  <select
                    value={reportQuarter}
                    onChange={(e) => setReportQuarter(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-xs text-white"
                  >
                    <option value="1">Q1 (Jan-Mar)</option>
                    <option value="2">Q2 (Apr-Jun)</option>
                    <option value="3">Q3 (Jul-Sep)</option>
                    <option value="4">Q4 (Oct-Dec)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Chapter</label>
                  <select
                    value={reportChapter}
                    onChange={(e) => setReportChapter(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-xs text-white"
                  >
                    <option value="All">All Chapters</option>
                    <option value="National">National</option>
                    <option value="AD">AD</option>
                    <option value="HA">HA</option>
                    <option value="HS">HS</option>
                  </select>
                </div>
              </div>
              
              {/* Report Download Buttons */}
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => downloadQuarterlyReport('attendance')}
                  disabled={reportLoading}
                  className="flex items-center justify-center gap-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 px-2 py-2 rounded text-xs font-medium transition-colors"
                >
                  <Users className="w-3 h-3" />
                  Attendance
                </button>
                <button
                  onClick={() => downloadQuarterlyReport('dues')}
                  disabled={reportLoading}
                  className="flex items-center justify-center gap-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-2 py-2 rounded text-xs font-medium transition-colors"
                >
                  <DollarSign className="w-3 h-3" />
                  Dues
                </button>
                <button
                  onClick={() => downloadQuarterlyReport('prospects')}
                  disabled={reportLoading}
                  className="flex items-center justify-center gap-1 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 px-2 py-2 rounded text-xs font-medium transition-colors"
                >
                  <UserCheck className="w-3 h-3" />
                  Prospects
                </button>
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-slate-600 my-4"></div>
            
            {/* Column Selection Section */}
            <div className="mb-3 sm:mb-4">
              <h3 className="text-sm font-semibold text-purple-400 mb-2">Print by Columns</h3>
              <p className="text-slate-300 mb-2 sm:mb-3 text-sm sm:text-base">Select which columns to include:</p>
              <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-3 sm:mb-4">
                <button onClick={() => selectPreset('all')} className="bg-blue-600 hover:bg-blue-700 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 rounded text-xs sm:text-sm">All Fields</button>
                <button onClick={() => selectPreset('contact')} className="bg-purple-600 hover:bg-purple-700 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Contact</button>
                <button onClick={() => selectPreset('service')} className="bg-indigo-600 hover:bg-indigo-700 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 rounded text-xs sm:text-sm">🎖️ Service</button>
                <button onClick={() => selectPreset('dues_q1')} className="bg-rose-600 hover:bg-rose-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Dues Q1</button>
                <button onClick={() => selectPreset('dues_q2')} className="bg-red-600 hover:bg-red-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Dues Q2</button>
                <button onClick={() => selectPreset('dues_q3')} className="bg-orange-600 hover:bg-orange-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Dues Q3</button>
                <button onClick={() => selectPreset('dues_q4')} className="bg-amber-600 hover:bg-amber-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Dues Q4</button>
                <button onClick={() => selectPreset('meetings_q1')} className="bg-cyan-600 hover:bg-cyan-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Mtgs Q1</button>
                <button onClick={() => selectPreset('meetings_q2')} className="bg-teal-600 hover:bg-teal-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Mtgs Q2</button>
                <button onClick={() => selectPreset('meetings_q3')} className="bg-emerald-600 hover:bg-emerald-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Mtgs Q3</button>
                <button onClick={() => selectPreset('meetings_q4')} className="bg-green-600 hover:bg-green-700 px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Mtgs Q4</button>
                <button onClick={() => setSelectedColumns([])} className="bg-slate-600 hover:bg-slate-700 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 rounded text-xs sm:text-sm">Clear</button>
              </div>
            </div>

            <div className="bg-slate-700 rounded-lg p-3 sm:p-4 mb-3 sm:mb-4 max-h-48 sm:max-h-64 overflow-y-auto">
              {csvData[0]?.map((header, index) => (
                <div key={index} className="flex items-center gap-3 py-2 hover:bg-slate-600 px-2 rounded">
                  <input
                    type="checkbox"
                    id={`col-${index}`}
                    checked={selectedColumns.includes(index)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedColumns([...selectedColumns, index]);
                      } else {
                        setSelectedColumns(selectedColumns.filter(i => i !== index));
                      }
                    }}
                    className="w-5 h-5 accent-purple-600"
                  />
                  <label htmlFor={`col-${index}`} className="cursor-pointer flex-1">
                    {header}
                  </label>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
              <button
                onClick={() => setShowPrintModal(false)}
                className="flex-1 bg-slate-600 hover:bg-slate-700 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base"
              >
                Cancel
              </button>
              <button
                onClick={printSelectedColumns}
                className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base"
              >
                <i className="fas fa-print mr-2"></i>
                Print Selected
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Google Sheets Modal */}
      {showSheetsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-3 sm:p-4" onClick={() => setShowSheetsModal(false)}>
          <div className="bg-slate-800 rounded-lg p-4 sm:p-6 max-w-full sm:max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-green-400 mb-3 sm:mb-4">
              <i className="fab fa-google mr-2"></i>
              Export to Google Sheets
            </h2>
            <p className="text-slate-300 mb-4 sm:mb-6 text-sm sm:text-base">
              Copy all {csvData.length - 1} members with {csvData[0]?.length} columns to clipboard and open Google Sheets.
            </p>
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
              <button
                onClick={() => setShowSheetsModal(false)}
                className="flex-1 bg-slate-600 hover:bg-slate-700 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base"
              >
                Cancel
              </button>
              <button
                onClick={exportToGoogleSheets}
                className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold text-sm sm:text-base"
              >
                <i className="fab fa-google mr-2"></i>
                Export Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Print Styles */}
      <style>{`
        @media print {
          body { background: white !important; }
          .no-print { display: none !important; }
          table { page-break-inside: auto; }
          tr { page-break-inside: avoid; page-break-after: auto; }
          thead { display: table-header-group; }
        }
      `}</style>
    </PageLayout>
  );
}
