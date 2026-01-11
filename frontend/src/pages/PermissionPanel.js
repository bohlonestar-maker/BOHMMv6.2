import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { ArrowLeft, Shield, Save, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PermissionPanel() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [permissions, setPermissions] = useState({});
  const [availablePermissions, setAvailablePermissions] = useState([]);
  const [titles, setTitles] = useState([]);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalPermissions, setOriginalPermissions] = useState({});
  
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
      
      setPermissions(response.data.permissions_by_title || {});
      setOriginalPermissions(JSON.parse(JSON.stringify(response.data.permissions_by_title || {})));
      setAvailablePermissions(response.data.available_permissions || []);
      setTitles(response.data.titles || []);
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

  const handleToggle = (title, permKey) => {
    setPermissions(prev => {
      const newPerms = { ...prev };
      if (!newPerms[title]) {
        newPerms[title] = {};
      }
      newPerms[title] = {
        ...newPerms[title],
        [permKey]: !newPerms[title]?.[permKey]
      };
      return newPerms;
    });
    setHasChanges(true);
  };

  const saveChanges = async () => {
    try {
      setSaving(true);
      
      // Find which titles have changed
      for (const title of titles) {
        const current = permissions[title] || {};
        const original = originalPermissions[title] || {};
        
        // Check if this title's permissions changed
        let changed = false;
        for (const perm of availablePermissions) {
          if (current[perm.key] !== original[perm.key]) {
            changed = true;
            break;
          }
        }
        
        if (changed) {
          await axios.put(`${API}/permissions/bulk-update`, {
            title: title,
            permissions: current
          }, {
            headers: { Authorization: `Bearer ${token}` },
          });
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
      <nav className="bg-slate-800 border-b border-slate-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => navigate("/")}
                className="text-slate-400 hover:text-white"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div className="flex items-center gap-2">
                <Shield className="w-6 h-6 text-purple-400" />
                <h1 className="text-xl font-bold text-white">Permission Panel</h1>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={resetChanges}
                    className="text-slate-300 border-slate-600"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Reset
                  </Button>
                  <Button 
                    size="sm"
                    onClick={saveChanges}
                    disabled={saving}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? "Saving..." : "Save Changes"}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-700">
            <p className="text-slate-400 text-sm">
              Configure permissions for each title. Changes are saved when you click "Save Changes".
            </p>
            {hasChanges && (
              <Badge className="mt-2 bg-yellow-600">Unsaved changes</Badge>
            )}
          </div>
          
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700 hover:bg-slate-700/50">
                  <TableHead className="text-slate-300 font-semibold sticky left-0 bg-slate-800 z-10 min-w-[120px]">
                    Title
                  </TableHead>
                  {availablePermissions.map((perm) => (
                    <TableHead 
                      key={perm.key} 
                      className="text-slate-300 text-center min-w-[100px]"
                      title={perm.description}
                    >
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-xs">{perm.label}</span>
                      </div>
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {titles.map((title) => (
                  <TableRow 
                    key={title} 
                    className="border-slate-700 hover:bg-slate-700/30"
                  >
                    <TableCell className="font-medium text-white sticky left-0 bg-slate-800 z-10">
                      <Badge variant="outline" className="border-slate-600 text-slate-200">
                        {title}
                      </Badge>
                    </TableCell>
                    {availablePermissions.map((perm) => (
                      <TableCell key={perm.key} className="text-center">
                        <Switch
                          checked={permissions[title]?.[perm.key] || false}
                          onCheckedChange={() => handleToggle(title, perm.key)}
                          className="data-[state=checked]:bg-green-600"
                        />
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-6 bg-slate-800 rounded-xl shadow-sm border border-slate-700 p-4">
          <h3 className="text-white font-semibold mb-3">Permission Descriptions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {availablePermissions.map((perm) => (
              <div key={perm.key} className="bg-slate-700/50 rounded p-3">
                <div className="text-sm font-medium text-slate-200">{perm.label}</div>
                <div className="text-xs text-slate-400 mt-1">{perm.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
