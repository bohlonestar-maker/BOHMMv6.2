import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { Plus, FileText, Upload, Edit2, Eye, EyeOff, ArrowLeft, Menu } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DocumentTemplates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInactive, setShowInactive] = useState(false);
  
  // Create/Edit dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    template_type: 'text',
    text_content: '',
  });
  const [pdfFile, setPdfFile] = useState(null);
  const [saving, setSaving] = useState(false);

  // View template dialog
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [viewingTemplate, setViewingTemplate] = useState(null);

  // Mobile menu state
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchTemplates();
  }, [showInactive]);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/documents/templates`, {
        params: { include_inactive: showInactive },
        headers: { Authorization: `Bearer ${token}` }
      });
      setTemplates(response.data);
    } catch (err) {
      console.error('Error fetching templates:', err);
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTemplate(null);
    setFormData({
      name: '',
      description: '',
      category: '',
      template_type: 'text',
      text_content: '',
    });
    setPdfFile(null);
    setDialogOpen(true);
    setMobileMenuOpen(false);
  };

  const handleEdit = async (template) => {
    try {
      const response = await axios.get(`${API}/documents/templates/${template.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const fullTemplate = response.data;
      
      setEditingTemplate(fullTemplate);
      setFormData({
        name: fullTemplate.name || '',
        description: fullTemplate.description || '',
        category: fullTemplate.category || '',
        template_type: fullTemplate.template_type || 'text',
        text_content: fullTemplate.text_content || '',
      });
      setPdfFile(null);
      setDialogOpen(true);
    } catch (err) {
      console.error('Error fetching template:', err);
      toast.error('Failed to load template details');
    }
  };

  const handleView = async (template) => {
    try {
      const response = await axios.get(`${API}/documents/templates/${template.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setViewingTemplate(response.data);
      setViewDialogOpen(true);
    } catch (err) {
      console.error('Error viewing template:', err);
      toast.error('Failed to load template');
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Template name is required');
      return;
    }
    
    if (formData.template_type === 'text' && !formData.text_content.trim()) {
      toast.error('Text content is required for text templates');
      return;
    }
    
    if (formData.template_type === 'pdf' && !editingTemplate && !pdfFile) {
      toast.error('PDF file is required');
      return;
    }
    
    setSaving(true);
    
    try {
      const data = new FormData();
      data.append('name', formData.name.trim());
      data.append('description', formData.description || '');
      data.append('category', formData.category || '');
      
      if (editingTemplate) {
        if (formData.template_type === 'text') {
          data.append('text_content', formData.text_content);
        }
        if (pdfFile) {
          data.append('pdf_file', pdfFile);
        }
        
        await axios.put(`${API}/documents/templates/${editingTemplate.id}`, data, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        toast.success('Template updated successfully');
      } else {
        data.append('template_type', formData.template_type);
        if (formData.template_type === 'text') {
          data.append('text_content', formData.text_content);
        } else {
          data.append('pdf_file', pdfFile);
        }
        
        await axios.post(`${API}/documents/templates`, data, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        toast.success('Template created successfully');
      }
      
      setDialogOpen(false);
      fetchTemplates();
    } catch (err) {
      console.error('Error saving template:', err);
      toast.error(err.response?.data?.detail || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (template) => {
    try {
      const data = new FormData();
      data.append('is_active', (!template.is_active).toString());
      
      await axios.put(`${API}/documents/templates/${template.id}`, data, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success(template.is_active ? 'Template deactivated' : 'Template activated');
      fetchTemplates();
    } catch (err) {
      console.error('Error toggling template:', err);
      toast.error('Failed to update template');
    }
  };

  const categories = ['Financial Hardship', 'Honorary Application', 'Bylaws', 'SOPs', 'Other'];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header - Responsive */}
      <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-700">
        <div className="max-w-6xl mx-auto px-4 py-4">
          {/* Mobile Header */}
          <div className="flex items-center justify-between md:hidden">
            <button 
              onClick={() => navigate('/')}
              className="p-2 text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-lg font-bold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-purple-400" />
              Templates
            </h1>
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-400 hover:text-white"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>

          {/* Mobile Menu Dropdown */}
          {mobileMenuOpen && (
            <div className="md:hidden mt-3 p-3 bg-slate-800 rounded-lg border border-slate-700 space-y-2">
              <Button
                onClick={handleCreate}
                className="w-full bg-purple-600 hover:bg-purple-700"
                data-testid="create-template-btn-mobile"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Template
              </Button>
              <Button
                variant="outline"
                onClick={() => { setShowInactive(!showInactive); setMobileMenuOpen(false); }}
                className="w-full"
                data-testid="toggle-inactive-btn-mobile"
              >
                {showInactive ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                {showInactive ? 'Hide Inactive' : 'Show Inactive'}
              </Button>
            </div>
          )}

          {/* Desktop Header */}
          <div className="hidden md:flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button 
                onClick={() => navigate('/')}
                className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
                  <FileText className="text-purple-400" />
                  Document Templates
                </h1>
                <p className="text-slate-400 text-sm mt-1">
                  Manage document templates for e-signatures
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowInactive(!showInactive)}
                data-testid="toggle-inactive-btn"
              >
                {showInactive ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                <span className="hidden lg:inline">{showInactive ? 'Hide Inactive' : 'Show Inactive'}</span>
                <span className="lg:hidden">{showInactive ? 'Hide' : 'Show'}</span>
              </Button>
              <Button
                onClick={handleCreate}
                className="bg-purple-600 hover:bg-purple-700"
                data-testid="create-template-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                <span className="hidden lg:inline">Create Template</span>
                <span className="lg:hidden">Create</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Templates Grid - Responsive */}
        {loading ? (
          <div className="text-center py-12 text-slate-400">
            <i className="fas fa-spinner fa-spin text-2xl mb-2"></i>
            <p>Loading templates...</p>
          </div>
        ) : templates.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="text-center py-8 sm:py-12">
              <FileText className="w-12 h-12 sm:w-16 sm:h-16 mx-auto text-slate-600 mb-4" />
              <p className="text-slate-400 mb-4 text-sm sm:text-base">No document templates yet</p>
              <Button onClick={handleCreate} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Template
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <Card 
                key={template.id} 
                className={`bg-slate-800 border-slate-700 ${!template.is_active ? 'opacity-60' : ''}`}
                data-testid={`template-card-${template.id}`}
              >
                <CardHeader className="pb-2 p-4 sm:p-6">
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-white text-base sm:text-lg flex items-center gap-2">
                        {template.template_type === 'pdf' ? (
                          <i className="fas fa-file-pdf text-red-400 flex-shrink-0"></i>
                        ) : (
                          <i className="fas fa-file-alt text-blue-400 flex-shrink-0"></i>
                        )}
                        <span className="truncate">{template.name}</span>
                      </CardTitle>
                      {template.category && (
                        <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded mt-2 inline-block">
                          {template.category}
                        </span>
                      )}
                    </div>
                    {!template.is_active && (
                      <span className="text-xs bg-red-500/20 text-red-300 px-2 py-0.5 rounded flex-shrink-0">
                        Inactive
                      </span>
                    )}
                  </div>
                  {template.description && (
                    <CardDescription className="text-slate-400 text-xs sm:text-sm mt-2 line-clamp-2">
                      {template.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent className="p-4 sm:p-6 pt-0 sm:pt-0">
                  <div className="text-xs text-slate-500 mb-3">
                    <span className="hidden sm:inline">Created </span>
                    {new Date(template.created_at).toLocaleDateString()}
                    <span className="hidden sm:inline"> by {template.created_by}</span>
                  </div>
                  
                  {/* Action Buttons - Stack on mobile, row on tablet+ */}
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleView(template)}
                      className="flex-1 text-xs sm:text-sm"
                      data-testid={`view-template-${template.id}`}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      View
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEdit(template)}
                      className="flex-1 text-xs sm:text-sm"
                      data-testid={`edit-template-${template.id}`}
                    >
                      <Edit2 className="w-3 h-3 mr-1" />
                      Edit
                    </Button>
                    {template.template_type === 'pdf' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => navigate(`/document-templates/${template.id}/edit`)}
                        className="flex-1 text-xs sm:text-sm text-purple-400 hover:text-purple-300"
                        data-testid={`configure-template-${template.id}`}
                      >
                        <i className="fas fa-pen-to-square w-3 h-3 mr-1"></i>
                        Fields
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleToggleActive(template)}
                      className={`flex-1 text-xs sm:text-sm ${template.is_active ? 'text-red-400 hover:text-red-300' : 'text-green-400 hover:text-green-300'}`}
                      data-testid={`toggle-template-${template.id}`}
                    >
                      {template.is_active ? (
                        <>
                          <EyeOff className="w-3 h-3 mr-1" />
                          <span className="hidden sm:inline">Deactivate</span>
                          <span className="sm:hidden">Off</span>
                        </>
                      ) : (
                        <>
                          <Eye className="w-3 h-3 mr-1" />
                          <span className="hidden sm:inline">Activate</span>
                          <span className="sm:hidden">On</span>
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Dialog - Full screen on mobile */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="w-full max-w-full sm:max-w-lg md:max-w-2xl h-full sm:h-auto max-h-screen sm:max-h-[90vh] overflow-y-auto rounded-none sm:rounded-lg">
          <DialogHeader className="sticky top-0 bg-slate-900 pb-4 z-10">
            <DialogTitle className="text-lg sm:text-xl">
              {editingTemplate ? 'Edit Template' : 'Create New Template'}
            </DialogTitle>
            <DialogDescription className="text-sm">
              {editingTemplate 
                ? 'Update the template details below'
                : 'Create a new document template for e-signatures'
              }
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSave} className="space-y-4 pb-20 sm:pb-0">
            <div>
              <Label className="text-slate-200 text-sm">Template Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="e.g., Financial Hardship Application"
                className="bg-slate-700 border-slate-600 text-white mt-1"
                required
                data-testid="template-name-input"
              />
            </div>
            
            <div>
              <Label className="text-slate-200 text-sm">Description</Label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Brief description of this template"
                className="bg-slate-700 border-slate-600 text-white mt-1"
                data-testid="template-description-input"
              />
            </div>
            
            <div>
              <Label className="text-slate-200 text-sm">Category</Label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full mt-1 p-2.5 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                data-testid="template-category-select"
              >
                <option value="">Select a category...</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            
            {!editingTemplate && (
              <div>
                <Label className="text-slate-200 text-sm">Template Type *</Label>
                <div className="flex flex-col sm:flex-row gap-3 mt-2">
                  <label className="flex items-center gap-2 cursor-pointer p-3 rounded-lg border border-slate-600 hover:border-purple-500 transition-colors flex-1">
                    <input
                      type="radio"
                      name="template_type"
                      value="text"
                      checked={formData.template_type === 'text'}
                      onChange={(e) => setFormData({...formData, template_type: e.target.value})}
                      className="text-purple-600"
                    />
                    <span className="text-slate-300 text-sm">
                      <i className="fas fa-file-alt mr-2 text-blue-400"></i>
                      Text Document
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer p-3 rounded-lg border border-slate-600 hover:border-purple-500 transition-colors flex-1">
                    <input
                      type="radio"
                      name="template_type"
                      value="pdf"
                      checked={formData.template_type === 'pdf'}
                      onChange={(e) => setFormData({...formData, template_type: e.target.value})}
                      className="text-purple-600"
                    />
                    <span className="text-slate-300 text-sm">
                      <i className="fas fa-file-pdf mr-2 text-red-400"></i>
                      PDF Upload
                    </span>
                  </label>
                </div>
              </div>
            )}
            
            {(formData.template_type === 'text' || editingTemplate?.template_type === 'text') && (
              <div>
                <Label className="text-slate-200 text-sm">Document Content *</Label>
                <Textarea
                  value={formData.text_content}
                  onChange={(e) => setFormData({...formData, text_content: e.target.value})}
                  placeholder="Enter the document text content..."
                  className="bg-slate-700 border-slate-600 text-white mt-1 min-h-[150px] sm:min-h-[200px] font-mono text-xs sm:text-sm"
                  required={formData.template_type === 'text'}
                  data-testid="template-content-textarea"
                />
              </div>
            )}
            
            {(formData.template_type === 'pdf' || editingTemplate?.template_type === 'pdf') && (
              <div>
                <Label className="text-slate-200 text-sm">
                  PDF File {editingTemplate ? '(upload new to replace)' : '*'}
                </Label>
                <div className="mt-1 border-2 border-dashed border-slate-600 rounded-lg p-4 sm:p-6 text-center">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setPdfFile(e.target.files[0])}
                    className="hidden"
                    id="pdf-upload"
                    data-testid="pdf-file-input"
                  />
                  <label htmlFor="pdf-upload" className="cursor-pointer">
                    <Upload className="w-6 h-6 sm:w-8 sm:h-8 mx-auto text-slate-400 mb-2" />
                    <p className="text-slate-400 text-sm">
                      {pdfFile ? pdfFile.name : 'Tap to upload PDF'}
                    </p>
                  </label>
                </div>
                {editingTemplate?.pdf_filename && !pdfFile && (
                  <p className="text-xs text-slate-400 mt-2">
                    Current file: {editingTemplate.pdf_filename}
                  </p>
                )}
              </div>
            )}
            
            {/* Fixed footer on mobile */}
            <DialogFooter className="fixed sm:relative bottom-0 left-0 right-0 p-4 sm:p-0 bg-slate-900 border-t sm:border-0 border-slate-700 flex gap-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setDialogOpen(false)}
                className="flex-1 sm:flex-none"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={saving}
                className="flex-1 sm:flex-none bg-purple-600 hover:bg-purple-700"
                data-testid="save-template-btn"
              >
                {saving ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    Saving...
                  </>
                ) : (
                  <>
                    <i className="fas fa-save mr-2"></i>
                    {editingTemplate ? 'Update' : 'Create'}
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Template Dialog - Responsive */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="w-full max-w-full sm:max-w-lg md:max-w-2xl h-full sm:h-auto max-h-screen sm:max-h-[90vh] overflow-y-auto rounded-none sm:rounded-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base sm:text-lg">
              {viewingTemplate?.template_type === 'pdf' ? (
                <i className="fas fa-file-pdf text-red-400"></i>
              ) : (
                <i className="fas fa-file-alt text-blue-400"></i>
              )}
              <span className="truncate">{viewingTemplate?.name}</span>
            </DialogTitle>
            {viewingTemplate?.description && (
              <DialogDescription className="text-sm">{viewingTemplate.description}</DialogDescription>
            )}
          </DialogHeader>
          
          <div className="space-y-4">
            {viewingTemplate?.category && (
              <div>
                <Label className="text-slate-400 text-xs sm:text-sm">Category</Label>
                <p className="text-white text-sm sm:text-base">{viewingTemplate.category}</p>
              </div>
            )}
            
            <div>
              <Label className="text-slate-400 text-xs sm:text-sm">Content</Label>
              {viewingTemplate?.template_type === 'text' ? (
                <div className="bg-slate-700/50 rounded-lg p-3 sm:p-4 mt-1 max-h-64 sm:max-h-96 overflow-y-auto">
                  <pre className="text-slate-300 whitespace-pre-wrap font-mono text-xs sm:text-sm">
                    {viewingTemplate?.text_content}
                  </pre>
                </div>
              ) : (
                <div className="bg-slate-700/50 rounded-lg p-3 sm:p-4 mt-1">
                  <p className="text-slate-300 text-sm">
                    <i className="fas fa-file-pdf text-red-400 mr-2"></i>
                    {viewingTemplate?.pdf_filename || 'PDF Document'}
                  </p>
                </div>
              )}
            </div>
            
            <div className="text-xs text-slate-500">
              Created {viewingTemplate && new Date(viewingTemplate.created_at).toLocaleString()} 
              <span className="hidden sm:inline"> by {viewingTemplate?.created_by}</span>
              {viewingTemplate?.updated_at && (
                <span className="block sm:inline sm:ml-1">
                  | Updated {new Date(viewingTemplate.updated_at).toLocaleString()}
                </span>
              )}
            </div>
          </div>
          
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setViewDialogOpen(false)} className="w-full sm:w-auto">
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
