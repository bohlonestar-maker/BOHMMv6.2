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
import { Plus, FileText, Upload, Edit2, Trash2, Eye, EyeOff } from 'lucide-react';

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
  };

  const handleEdit = async (template) => {
    try {
      // Fetch full template details
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
        // Update existing
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
        // Create new
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

  const handleDelete = async (template) => {
    if (!window.confirm(`Are you sure you want to deactivate "${template.name}"?`)) {
      return;
    }
    
    try {
      await axios.delete(`${API}/documents/templates/${template.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Template deactivated');
      fetchTemplates();
    } catch (err) {
      console.error('Error deleting template:', err);
      toast.error(err.response?.data?.detail || 'Failed to deactivate template');
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
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <FileText className="text-purple-400" />
              Document Templates
            </h1>
            <p className="text-slate-400 mt-1">
              Manage document templates for e-signatures
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setShowInactive(!showInactive)}
              data-testid="toggle-inactive-btn"
            >
              {showInactive ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
              {showInactive ? 'Hide Inactive' : 'Show Inactive'}
            </Button>
            <Button
              onClick={handleCreate}
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="create-template-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Template
            </Button>
          </div>
        </div>

        {/* Templates Grid */}
        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading templates...</div>
        ) : templates.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto text-slate-600 mb-4" />
              <p className="text-slate-400 mb-4">No document templates yet</p>
              <Button onClick={handleCreate} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Template
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <Card 
                key={template.id} 
                className={`bg-slate-800 border-slate-700 ${!template.is_active ? 'opacity-60' : ''}`}
                data-testid={`template-card-${template.id}`}
              >
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-white text-lg flex items-center gap-2">
                        {template.template_type === 'pdf' ? (
                          <i className="fas fa-file-pdf text-red-400"></i>
                        ) : (
                          <i className="fas fa-file-alt text-blue-400"></i>
                        )}
                        {template.name}
                      </CardTitle>
                      {template.category && (
                        <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded mt-1 inline-block">
                          {template.category}
                        </span>
                      )}
                    </div>
                    {!template.is_active && (
                      <span className="text-xs bg-red-500/20 text-red-300 px-2 py-0.5 rounded">
                        Inactive
                      </span>
                    )}
                  </div>
                  {template.description && (
                    <CardDescription className="text-slate-400 text-sm mt-2">
                      {template.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="text-xs text-slate-500 mb-3">
                    Created {new Date(template.created_at).toLocaleDateString()} by {template.created_by}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleView(template)}
                      data-testid={`view-template-${template.id}`}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      View
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEdit(template)}
                      data-testid={`edit-template-${template.id}`}
                    >
                      <Edit2 className="w-3 h-3 mr-1" />
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleToggleActive(template)}
                      className={template.is_active ? 'text-red-400 hover:text-red-300' : 'text-green-400 hover:text-green-300'}
                      data-testid={`toggle-template-${template.id}`}
                    >
                      {template.is_active ? (
                        <>
                          <EyeOff className="w-3 h-3 mr-1" />
                          Deactivate
                        </>
                      ) : (
                        <>
                          <Eye className="w-3 h-3 mr-1" />
                          Activate
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingTemplate ? 'Edit Template' : 'Create New Template'}
              </DialogTitle>
              <DialogDescription>
                {editingTemplate 
                  ? 'Update the template details below'
                  : 'Create a new document template for e-signatures'
                }
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <Label className="text-slate-200">Template Name *</Label>
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
                <Label className="text-slate-200">Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Brief description of this template"
                  className="bg-slate-700 border-slate-600 text-white mt-1"
                  data-testid="template-description-input"
                />
              </div>
              
              <div>
                <Label className="text-slate-200">Category</Label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  className="w-full mt-1 p-2 bg-slate-700 border border-slate-600 rounded text-white"
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
                  <Label className="text-slate-200">Template Type *</Label>
                  <div className="flex gap-4 mt-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="template_type"
                        value="text"
                        checked={formData.template_type === 'text'}
                        onChange={(e) => setFormData({...formData, template_type: e.target.value})}
                        className="text-purple-600"
                      />
                      <span className="text-slate-300">
                        <i className="fas fa-file-alt mr-1"></i>
                        Text Document
                      </span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="template_type"
                        value="pdf"
                        checked={formData.template_type === 'pdf'}
                        onChange={(e) => setFormData({...formData, template_type: e.target.value})}
                        className="text-purple-600"
                      />
                      <span className="text-slate-300">
                        <i className="fas fa-file-pdf mr-1"></i>
                        PDF Upload
                      </span>
                    </label>
                  </div>
                </div>
              )}
              
              {(formData.template_type === 'text' || editingTemplate?.template_type === 'text') && (
                <div>
                  <Label className="text-slate-200">Document Content *</Label>
                  <Textarea
                    value={formData.text_content}
                    onChange={(e) => setFormData({...formData, text_content: e.target.value})}
                    placeholder="Enter the document text content..."
                    className="bg-slate-700 border-slate-600 text-white mt-1 min-h-[200px] font-mono text-sm"
                    required={formData.template_type === 'text'}
                    data-testid="template-content-textarea"
                  />
                </div>
              )}
              
              {(formData.template_type === 'pdf' || editingTemplate?.template_type === 'pdf') && (
                <div>
                  <Label className="text-slate-200">
                    PDF File {editingTemplate ? '(upload new to replace)' : '*'}
                  </Label>
                  <div className="mt-1 border-2 border-dashed border-slate-600 rounded-lg p-6 text-center">
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setPdfFile(e.target.files[0])}
                      className="hidden"
                      id="pdf-upload"
                      data-testid="pdf-file-input"
                    />
                    <label htmlFor="pdf-upload" className="cursor-pointer">
                      <Upload className="w-8 h-8 mx-auto text-slate-400 mb-2" />
                      <p className="text-slate-400">
                        {pdfFile ? pdfFile.name : 'Click to upload PDF'}
                      </p>
                    </label>
                  </div>
                  {editingTemplate?.pdf_filename && !pdfFile && (
                    <p className="text-sm text-slate-400 mt-2">
                      Current file: {editingTemplate.pdf_filename}
                    </p>
                  )}
                </div>
              )}
              
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={saving}
                  className="bg-purple-600 hover:bg-purple-700"
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
                      {editingTemplate ? 'Update Template' : 'Create Template'}
                    </>
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* View Template Dialog */}
        <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {viewingTemplate?.template_type === 'pdf' ? (
                  <i className="fas fa-file-pdf text-red-400"></i>
                ) : (
                  <i className="fas fa-file-alt text-blue-400"></i>
                )}
                {viewingTemplate?.name}
              </DialogTitle>
              {viewingTemplate?.description && (
                <DialogDescription>{viewingTemplate.description}</DialogDescription>
              )}
            </DialogHeader>
            
            <div className="space-y-4">
              {viewingTemplate?.category && (
                <div>
                  <Label className="text-slate-400 text-sm">Category</Label>
                  <p className="text-white">{viewingTemplate.category}</p>
                </div>
              )}
              
              <div>
                <Label className="text-slate-400 text-sm">Content</Label>
                {viewingTemplate?.template_type === 'text' ? (
                  <div className="bg-slate-700/50 rounded-lg p-4 mt-1 max-h-96 overflow-y-auto">
                    <pre className="text-slate-300 whitespace-pre-wrap font-mono text-sm">
                      {viewingTemplate?.text_content}
                    </pre>
                  </div>
                ) : (
                  <div className="bg-slate-700/50 rounded-lg p-4 mt-1">
                    <p className="text-slate-300">
                      <i className="fas fa-file-pdf text-red-400 mr-2"></i>
                      {viewingTemplate?.pdf_filename || 'PDF Document'}
                    </p>
                  </div>
                )}
              </div>
              
              <div className="text-xs text-slate-500">
                Created {viewingTemplate && new Date(viewingTemplate.created_at).toLocaleString()} by {viewingTemplate?.created_by}
                {viewingTemplate?.updated_at && (
                  <span> | Updated {new Date(viewingTemplate.updated_at).toLocaleString()}</span>
                )}
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
