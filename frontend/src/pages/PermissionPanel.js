import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { ArrowLeft, Shield, Save, RefreshCw, Check, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom Toggle Switch Component with proper design
const ToggleSwitch = ({ checked, onChange, disabled = false }) => {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className={`
        relative inline-flex h-7 w-12 shrink-0 cursor-pointer rounded-full border-2 border-transparent 
        transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-800
        ${checked ? 'bg-green-500' : 'bg-slate-600'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <span
        className={`
          pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow-lg ring-0 
          transition duration-200 ease-in-out
          ${checked ? 'translate-x-5' : 'translate-x-0'}
        `}
      >
        <span className={`absolute inset-0 flex h-full w-full items-center justify-center transition-opacity ${checked ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in'}`}>
          <X className="h-3 w-3 text-slate-400" />
        </span>
        <span className={`absolute inset-0 flex h-full w-full items-center justify-center transition-opacity ${checked ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out'}`}>
          <Check className="h-3 w-3 text-green-600" />
        </span>
      </span>
    </button>
  );
};

export default function PermissionPanel() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [permissions, setPermissions] = useState({});
  const [availablePermissions, setAvailablePermissions] = useState([]);
  const [titles, setTitles] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState("National");
  const [hasChanges, setHasChanges] = useState(false);
  const [originalPermissions, setOriginalPermissions] = useState({});
  const [expandedTitle, setExpandedTitle] = useState(null);
  
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchPermissions();
  }, []);

  const fetchPermissions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/permissions/all`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      setPermissions(response.data.permissions_by_chapter || {});
      setOriginalPermissions(JSON.parse(JSON.stringify(response.data.permissions_by_chapter || {})));
      setAvailablePermissions(response.data.available_permissions || []);
      setTitles(response.data.titles || []);
      setChapters(response.data.chapters || ["National", "AD", "HA", "HS"]);
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to fetch permissions:", error);
      if (error.response?.status === 403) {
        toast.error("You don't have permission to access this page");
        navigate("/");
      } else {
        toast.error("Failed to load permissions");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (chapter, title, permKey) => {
    setPermissions(prev => {
      const newPerms = JSON.parse(JSON.stringify(prev));
      if (!newPerms[chapter]) {
        newPerms[chapter] = {};
      }
      if (!newPerms[chapter][title]) {
        newPerms[chapter][title] = {};
      }
      newPerms[chapter][title][permKey] = !newPerms[chapter][title]?.[permKey];
      return newPerms;
    });
    setHasChanges(true);
  };

  const saveChanges = async () => {
    try {
      setSaving(true);
      
      for (const chapter of chapters) {
        for (const title of titles) {
          const current = permissions[chapter]?.[title] || {};
          const original = originalPermissions[chapter]?.[title] || {};
          
          let changed = false;
          for (const perm of availablePermissions) {
            if (current[perm.key] !== original[perm.key]) {
              changed = true;
              break;
            }
          }
          
          if (changed) {
            await axios.put(`${API}/permissions/bulk-update`, {
              chapter: chapter,
              title: title,
              permissions: current
            }, {
              headers: { Authorization: `Bearer ${token}` },
            });
          }
        }
      }
      
      toast.success("Permissions saved successfully");
      setOriginalPermissions(JSON.parse(JSON.stringify(permissions)));
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save permissions:", error);
      toast.error(error.response?.data?.detail || "Failed to save permissions");
    } finally {
      setSaving(false);
    }
  };

  const resetChanges = () => {
    setPermissions(JSON.parse(JSON.stringify(originalPermissions)));
    setHasChanges(false);
    toast.info("Changes reset");
  };

  const copyFromChapter = async (sourceChapter) => {
    if (sourceChapter === selectedChapter) return;
    
    setPermissions(prev => {
      const newPerms = JSON.parse(JSON.stringify(prev));
      newPerms[selectedChapter] = JSON.parse(JSON.stringify(prev[sourceChapter] || {}));
      return newPerms;
    });
    setHasChanges(true);
    toast.info(`Copied permissions from ${sourceChapter} to ${selectedChapter}`);
  };

  const countEnabledPermissions = (chapter, title) => {
    const titlePerms = permissions[chapter]?.[title] || {};
    return Object.values(titlePerms).filter(v => v === true).length;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading permissions...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <nav className="bg-slate-800 border-b border-slate-700 shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div className="flex items-center gap-2 sm:gap-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => navigate("/")}
                className="text-slate-400 hover:text-white p-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline ml-2">Back</span>
              </Button>
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-purple-400" />
                <h1 className="text-lg sm:text-xl font-bold text-white">Permission Panel</h1>
              </div>
            </div>
            {hasChanges && (
              <div className="flex items-center gap-2">
                <Badge className="bg-yellow-600 text-xs">Unsaved</Badge>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={resetChanges}
                  className="text-slate-300 border-slate-600 h-8 px-2 sm:px-3"
                >
                  <RefreshCw className="w-4 h-4 sm:mr-2" />
                  <span className="hidden sm:inline">Reset</span>
                </Button>
                <Button 
                  size="sm"
                  onClick={saveChanges}
                  disabled={saving}
                  className="bg-green-600 hover:bg-green-700 h-8 px-2 sm:px-3"
                >
                  <Save className="w-4 h-4 sm:mr-2" />
                  <span className="hidden sm:inline">{saving ? "Saving..." : "Save"}</span>
                </Button>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6">
        {/* Chapter Tabs */}
        <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700 overflow-hidden mb-4">
          <div className="p-3 sm:p-4 border-b border-slate-700">
            <p className="text-slate-400 text-xs sm:text-sm mb-3">
              Configure permissions for each title within each chapter.
            </p>
            
            {/* Chapter Selector */}
            <div className="flex flex-wrap gap-2">
              {chapters.map((chapter) => (
                <button
                  key={chapter}
                  onClick={() => setSelectedChapter(chapter)}
                  className={`
                    px-4 py-2 rounded-lg font-medium text-sm transition-all
                    ${selectedChapter === chapter 
                      ? 'bg-purple-600 text-white shadow-lg' 
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}
                  `}
                >
                  {chapter}
                </button>
              ))}
            </div>
            
            {/* Copy From */}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-500">Copy from:</span>
              {chapters.filter(c => c !== selectedChapter).map((chapter) => (
                <button
                  key={chapter}
                  onClick={() => copyFromChapter(chapter)}
                  className="text-xs px-2 py-1 rounded border border-slate-600 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
                >
                  {chapter}
                </button>
              ))}
            </div>
          </div>

          {/* Desktop/Tablet View - Table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-800/50">
                  <th className="text-left text-slate-300 font-semibold p-3 sticky left-0 bg-slate-800 z-10 min-w-[100px]">
                    Title
                  </th>
                  {availablePermissions.map((perm) => (
                    <th 
                      key={perm.key} 
                      className="text-center text-slate-300 font-medium p-3 min-w-[90px]"
                      title={perm.description}
                    >
                      <span className="text-xs leading-tight block">{perm.label}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {titles.map((title) => (
                  <tr 
                    key={title} 
                    className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
                  >
                    <td className="p-3 sticky left-0 bg-slate-800 z-10">
                      <Badge variant="outline" className="border-slate-600 text-slate-200 text-xs">
                        {title}
                      </Badge>
                    </td>
                    {availablePermissions.map((perm) => (
                      <td key={perm.key} className="p-3 text-center">
                        <div className="flex justify-center">
                          <ToggleSwitch
                            checked={permissions[selectedChapter]?.[title]?.[perm.key] || false}
                            onChange={() => handleToggle(selectedChapter, title, perm.key)}
                          />
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile View - Card/Accordion Style */}
          <div className="md:hidden">
            {titles.map((title) => {
              const enabledCount = countEnabledPermissions(selectedChapter, title);
              const isExpanded = expandedTitle === title;
              
              return (
                <div key={title} className="border-b border-slate-700/50">
                  {/* Title Header - Clickable */}
                  <button
                    onClick={() => setExpandedTitle(isExpanded ? null : title)}
                    className="w-full p-4 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="border-slate-600 text-slate-200 text-sm">
                        {title}
                      </Badge>
                      <span className="text-xs text-slate-400">
                        {enabledCount}/{availablePermissions.length} enabled
                      </span>
                    </div>
                    <svg 
                      className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {/* Expanded Permissions */}
                  {isExpanded && (
                    <div className="px-4 pb-4 space-y-3 bg-slate-700/20">
                      {availablePermissions.map((perm) => (
                        <div 
                          key={perm.key} 
                          className="flex items-center justify-between py-2 border-b border-slate-700/30 last:border-0"
                        >
                          <div className="flex-1 pr-4">
                            <div className="text-sm text-white font-medium">{perm.label}</div>
                            <div className="text-xs text-slate-400">{perm.description}</div>
                          </div>
                          <ToggleSwitch
                            checked={permissions[selectedChapter]?.[title]?.[perm.key] || false}
                            onChange={() => handleToggle(selectedChapter, title, perm.key)}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Legend - Desktop/Tablet Only */}
        <div className="hidden sm:block bg-slate-800 rounded-xl shadow-sm border border-slate-700 p-4">
          <h3 className="text-white font-semibold mb-3 text-sm">Permission Descriptions</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {availablePermissions.map((perm) => (
              <div key={perm.key} className="bg-slate-700/50 rounded p-3">
                <div className="text-xs font-medium text-slate-200">{perm.label}</div>
                <div className="text-xs text-slate-400 mt-1">{perm.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
