import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

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
          if (h.includes('name') || h.includes('handle') || h.includes('chapter') || 
              h.includes('title') || h.includes('email') || h.includes('phone') || h.includes('address')) {
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

    const printWindow = window.open('', '_blank');
    const html = generatePrintHTML(filteredData);
    printWindow.document.write(html);
    printWindow.document.close();
    setTimeout(() => printWindow.print(), 500);
    setShowPrintModal(false);
  };

  const generatePrintHTML = (data) => {
    return `
<!DOCTYPE html>
<html>
<head>
  <title>Brothers of the Highway - Custom Print</title>
  <style>
    @page { size: landscape; margin: 0.5cm; }
    body { font-family: Arial, sans-serif; margin: 10px; }
    h1 { text-align: center; color: #8b5cf6; margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #8b5cf6; color: white; padding: 8px; text-align: left; font-size: 0.75rem; }
    td { padding: 6px; border-bottom: 1px solid #ddd; font-size: 0.7rem; }
    tr:nth-child(even) { background: #f5f5f5; }
    @media print {
      .no-print { display: none; }
    }
  </style>
</head>
<body>
  <div class="no-print" style="text-align: center; margin-bottom: 20px;">
    <button onclick="window.print()" style="background: #8b5cf6; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; margin: 5px;">Print</button>
    <button onclick="window.close()" style="background: #64748b; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; margin: 5px;">Close</button>
  </div>
  <h1>Brothers of the Highway - Member Export</h1>
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

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading CSV data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-purple-400">
            <i className="fas fa-file-csv mr-2"></i>
            Brothers of the Highway - Member Export
          </h1>
          <button
            onClick={() => window.close()}
            className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg"
          >
            <i className="fas fa-arrow-left mr-2"></i>
            Back to Dashboard
          </button>
        </div>

        {/* Stats */}
        <div className="bg-slate-800 rounded-lg p-4 mb-6">
          <div className="flex gap-6 text-sm">
            <div>
              <span className="text-slate-400">Total Members:</span>
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
        <div className="flex flex-wrap gap-3 mb-6">
          <button
            onClick={handleDownload}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 px-6 py-3 rounded-lg font-semibold"
          >
            <i className="fas fa-download mr-2"></i>
            Download CSV
          </button>
          <button
            onClick={handleCustomPrint}
            className="bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 px-6 py-3 rounded-lg font-semibold"
          >
            <i className="fas fa-print mr-2"></i>
            Print Custom
          </button>
          <button
            onClick={() => setShowSheetsModal(true)}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 px-6 py-3 rounded-lg font-semibold"
          >
            <i className="fab fa-google mr-2"></i>
            Export to Sheets
          </button>
          <button
            onClick={() => setView(view === 'table' ? 'raw' : 'table')}
            className="bg-slate-700 hover:bg-slate-600 px-6 py-3 rounded-lg font-semibold"
          >
            <i className={`fas fa-${view === 'table' ? 'code' : 'table'} mr-2`}></i>
            {view === 'table' ? 'Raw View' : 'Table View'}
          </button>
        </div>

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search members..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-purple-500"
          />
        </div>

        {/* Content */}
        {view === 'table' ? (
          <div className="bg-slate-800 rounded-lg overflow-auto" style={{ maxHeight: '70vh' }}>
            <table className="w-full">
              <thead className="bg-gradient-to-r from-purple-600 to-purple-700 sticky top-0">
                <tr>
                  {csvData[0]?.map((header, i) => (
                    <th key={i} className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredData.slice(1).map((row, i) => (
                  <tr key={i} className="border-b border-slate-700 hover:bg-slate-700">
                    {row.map((cell, j) => (
                      <td key={j} className="px-4 py-2 text-sm whitespace-nowrap">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <pre className="bg-slate-800 p-6 rounded-lg overflow-auto text-sm" style={{ maxHeight: '70vh' }}>
            {csvText}
          </pre>
        )}
      </div>

      {/* Print Custom Modal */}
      {showPrintModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4" onClick={() => setShowPrintModal(false)}>
          <div className="bg-slate-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold text-purple-400 mb-4">
              <i className="fas fa-print mr-2"></i>
              Customize Print Columns
            </h2>
            
            <div className="mb-4">
              <p className="text-slate-300 mb-3">Select which columns to include in your print:</p>
              <div className="flex flex-wrap gap-2 mb-4">
                <button onClick={() => selectPreset('all')} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm">All Fields</button>
                <button onClick={() => selectPreset('contact')} className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-sm">Contact Info</button>
                <button onClick={() => selectPreset('dues_q1')} className="bg-rose-600 hover:bg-rose-700 px-3 py-2 rounded text-sm">Dues Q1</button>
                <button onClick={() => selectPreset('dues_q2')} className="bg-red-600 hover:bg-red-700 px-3 py-2 rounded text-sm">Dues Q2</button>
                <button onClick={() => selectPreset('dues_q3')} className="bg-orange-600 hover:bg-orange-700 px-3 py-2 rounded text-sm">Dues Q3</button>
                <button onClick={() => selectPreset('dues_q4')} className="bg-amber-600 hover:bg-amber-700 px-3 py-2 rounded text-sm">Dues Q4</button>
                <button onClick={() => selectPreset('meetings_q1')} className="bg-cyan-600 hover:bg-cyan-700 px-3 py-2 rounded text-sm">Meetings Q1</button>
                <button onClick={() => selectPreset('meetings_q2')} className="bg-teal-600 hover:bg-teal-700 px-3 py-2 rounded text-sm">Meetings Q2</button>
                <button onClick={() => selectPreset('meetings_q3')} className="bg-emerald-600 hover:bg-emerald-700 px-3 py-2 rounded text-sm">Meetings Q3</button>
                <button onClick={() => selectPreset('meetings_q4')} className="bg-green-600 hover:bg-green-700 px-3 py-2 rounded text-sm">Meetings Q4</button>
                <button onClick={() => setSelectedColumns([])} className="bg-slate-600 hover:bg-slate-700 px-4 py-2 rounded text-sm">Clear All</button>
              </div>
            </div>

            <div className="bg-slate-700 rounded-lg p-4 mb-4 max-h-64 overflow-y-auto">
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

            <div className="flex gap-3">
              <button
                onClick={() => setShowPrintModal(false)}
                className="flex-1 bg-slate-600 hover:bg-slate-700 px-6 py-3 rounded-lg font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={printSelectedColumns}
                className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 px-6 py-3 rounded-lg font-semibold"
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
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4" onClick={() => setShowSheetsModal(false)}>
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold text-green-400 mb-4">
              <i className="fab fa-google mr-2"></i>
              Export to Google Sheets
            </h2>
            <p className="text-slate-300 mb-6">
              Click below to copy all {csvData.length - 1} members with {csvData[0]?.length} columns to clipboard and open Google Sheets.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowSheetsModal(false)}
                className="flex-1 bg-slate-600 hover:bg-slate-700 px-6 py-3 rounded-lg font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={exportToGoogleSheets}
                className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 px-6 py-3 rounded-lg font-semibold"
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
    </div>
  );
}
