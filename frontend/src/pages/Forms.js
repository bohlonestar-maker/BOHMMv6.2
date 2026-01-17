import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  FileText,
  Upload,
  Download,
  Trash2,
  Plus,
  ArrowLeft,
  File,
  FileSpreadsheet,
  FileImage,
  Search,
  Calendar,
  User
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

// Get icon based on file type
const getFileIcon = (filename) => {
  const ext = filename?.split('.').pop()?.toLowerCase() || '';
  if (['pdf'].includes(ext)) return <FileText className="w-8 h-8 text-red-400" />;
  if (['doc', 'docx'].includes(ext)) return <FileText className="w-8 h-8 text-blue-400" />;
  if (['xls', 'xlsx', 'csv'].includes(ext)) return <FileSpreadsheet className="w-8 h-8 text-green-400" />;
  if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return <FileImage className="w-8 h-8 text-purple-400" />;
  return <File className="w-8 h-8 text-slate-400" />;
};

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes) return 'Unknown size';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

export default function Forms() {
  const [forms, setForms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [selectedForm, setSelectedForm] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [canManage, setCanManage] = useState(false);
  
  // Upload form state
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formFile, setFormFile] = useState(null);
  
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("role");

  useEffect(() => {
    fetchForms();
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    try {
      const response = await axios.get(`${API}/auth/verify`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const permissions = response.data.permissions || {};
      setCanManage(userRole === 'admin' || permissions.manage_forms);
    } catch (error) {
      console.error("Failed to check permissions:", error);
    }
  };

  const fetchForms = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/forms`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setForms(response.data.forms || []);
    } catch (error) {
      console.error("Failed to fetch forms:", error);
      toast.error("Failed to load forms");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!formFile) {
      toast.error("Please select a file to upload");
      return;
    }
    if (!formName.trim()) {
      toast.error("Please enter a form name");
      return;
    }

    try {
      setUploading(true);
      
      const formData = new FormData();
      formData.append("file", formFile);
      formData.append("name", formName.trim());
      formData.append("description", formDescription.trim());

      await axios.post(`${API}/forms/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      toast.success("Form uploaded successfully");
      setUploadDialog(false);
      resetUploadForm();
      fetchForms();
    } catch (error) {
      console.error("Failed to upload form:", error);
      toast.error(error.response?.data?.detail || "Failed to upload form");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedForm) return;

    try {
      await axios.delete(`${API}/forms/${selectedForm.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Form deleted successfully");
      setDeleteDialog(false);
      setSelectedForm(null);
      fetchForms();
    } catch (error) {
      console.error("Failed to delete form:", error);
      toast.error("Failed to delete form");
    }
  };

  const handleDownload = async (form) => {
    try {
      const response = await axios.get(`${API}/forms/${form.id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', form.filename || form.name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Download started");
    } catch (error) {
      console.error("Failed to download form:", error);
      toast.error("Failed to download form");
    }
  };

  const resetUploadForm = () => {
    setFormName("");
    setFormDescription("");
    setFormFile(null);
  };

  const filteredForms = forms.filter(form => 
    form.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    form.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading forms...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-4 sm:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/")}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <FileText className="w-6 h-6 text-blue-400" />
                Forms & Documents
              </h1>
              <p className="text-slate-400 text-sm">Download official forms and documents</p>
            </div>
          </div>
          
          {canManage && (
            <Button
              onClick={() => setUploadDialog(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Form
            </Button>
          )}
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Search forms..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-slate-800 border-slate-700 text-white"
          />
        </div>

        {/* Forms Grid */}
        {filteredForms.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="py-12 text-center">
              <FileText className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">
                {searchTerm ? "No forms match your search" : "No forms available yet"}
              </p>
              {canManage && !searchTerm && (
                <Button
                  onClick={() => setUploadDialog(true)}
                  className="mt-4 bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Upload First Form
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredForms.map((form) => (
              <Card 
                key={form.id} 
                className="bg-slate-800 border-slate-700 hover:border-slate-600 transition-colors"
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 p-3 bg-slate-700/50 rounded-lg">
                      {getFileIcon(form.filename)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white truncate" title={form.name}>
                        {form.name}
                      </h3>
                      {form.description && (
                        <p className="text-sm text-slate-400 mt-1 line-clamp-2">
                          {form.description}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <File className="w-3 h-3" />
                          {formatFileSize(form.file_size)}
                        </span>
                        {form.uploaded_by && (
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {form.uploaded_by}
                          </span>
                        )}
                        {form.uploaded_at && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(form.uploaded_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 mt-4">
                    <Button
                      onClick={() => handleDownload(form)}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                      size="sm"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                    {canManage && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedForm(form);
                          setDeleteDialog(true);
                        }}
                        className="border-red-600 text-red-400 hover:bg-red-600 hover:text-white"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Upload Dialog */}
        <Dialog open={uploadDialog} onOpenChange={setUploadDialog}>
          <DialogContent className="bg-slate-800 border-slate-700 text-white">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-400" />
                Upload New Form
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="formName">Form Name *</Label>
                <Input
                  id="formName"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g., Membership Application"
                  className="bg-slate-700 border-slate-600"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="formDescription">Description</Label>
                <Textarea
                  id="formDescription"
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="Brief description of this form..."
                  className="bg-slate-700 border-slate-600 min-h-[80px]"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="formFile">File *</Label>
                <Input
                  id="formFile"
                  type="file"
                  onChange={(e) => setFormFile(e.target.files[0])}
                  className="bg-slate-700 border-slate-600 file:bg-slate-600 file:text-white file:border-0 file:mr-4 file:py-2 file:px-4"
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.png,.jpg,.jpeg,.gif"
                />
                <p className="text-xs text-slate-400">
                  Supported: PDF, Word, Excel, CSV, Images (Max 10MB)
                </p>
              </div>
            </div>
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setUploadDialog(false);
                  resetUploadForm();
                }}
                className="border-slate-600"
              >
                Cancel
              </Button>
              <Button
                onClick={handleUpload}
                disabled={uploading || !formFile || !formName.trim()}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {uploading ? "Uploading..." : "Upload Form"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialog} onOpenChange={setDeleteDialog}>
          <DialogContent className="bg-slate-800 border-slate-700 text-white">
            <DialogHeader>
              <DialogTitle className="text-red-400">Delete Form</DialogTitle>
            </DialogHeader>
            <p className="text-slate-300">
              Are you sure you want to delete "{selectedForm?.name}"? This action cannot be undone.
            </p>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDeleteDialog(false)}
                className="border-slate-600"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDelete}
                className="bg-red-600 hover:bg-red-700"
              >
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
