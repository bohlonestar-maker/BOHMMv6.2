import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import { ChevronLeft, ChevronRight, Plus, Trash2, Save, Type, PenLine, Calendar, FileText, CheckSquare } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FIELD_TYPES = [
  { value: 'text', label: 'Text Field', icon: Type },
  { value: 'date', label: 'Date Field', icon: Calendar },
  { value: 'textarea', label: 'Text Area', icon: FileText },
  { value: 'initials', label: 'Initials', icon: PenLine },
  { value: 'checkbox', label: 'Checkbox', icon: CheckSquare },
];

const SIGNER_TYPES = [
  { value: 'recipient', label: 'Recipient (Applicant)' },
  { value: 'approver_0', label: 'Approver 1 (e.g., Committee Officer)' },
  { value: 'approver_1', label: 'Approver 2' },
  { value: 'approver_2', label: 'Approver 3' },
  { value: 'approver_3', label: 'Approver 4' },
  { value: 'approver_4', label: 'Approver 5' },
];

export default function TemplateEditor() {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [template, setTemplate] = useState(null);
  const [pagesInfo, setPagesInfo] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageImage, setPageImage] = useState(null);
  const [loadingPage, setLoadingPage] = useState(false);
  
  // Placements state
  const [fieldPlacements, setFieldPlacements] = useState([]);
  const [signaturePlacements, setSignaturePlacements] = useState([]);
  
  // UI state
  const [selectedItem, setSelectedItem] = useState(null); // { type: 'field' | 'signature', id: string }
  const [addMode, setAddMode] = useState(null); // 'field' | 'signature' | null
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newItemConfig, setNewItemConfig] = useState({});
  
  // Image dimensions for coordinate calculation
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    fetchTemplateData();
  }, [templateId]);

  useEffect(() => {
    if (pagesInfo.length > 0) {
      fetchPageImage(currentPage);
    }
  }, [currentPage, pagesInfo]);

  const fetchTemplateData = async () => {
    const token = localStorage.getItem('token');
    try {
      // Get template info
      const templateRes = await axios.get(`${API}/documents/templates/${templateId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTemplate(templateRes.data);
      
      // Get pages info
      const pagesRes = await axios.get(`${API}/documents/templates/${templateId}/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPagesInfo(pagesRes.data.pages || []);
      setFieldPlacements(pagesRes.data.field_placements || []);
      setSignaturePlacements(pagesRes.data.signature_placements || []);
    } catch (error) {
      toast.error('Failed to load template');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPageImage = async (pageNum) => {
    const token = localStorage.getItem('token');
    setLoadingPage(true);
    try {
      const response = await axios.get(
        `${API}/documents/templates/${templateId}/page/${pageNum}/image`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      const imageUrl = URL.createObjectURL(response.data);
      setPageImage(imageUrl);
    } catch (error) {
      toast.error('Failed to load page image');
      console.error(error);
    } finally {
      setLoadingPage(false);
    }
  };

  const handleImageLoad = (e) => {
    setImageDimensions({
      width: e.target.naturalWidth,
      height: e.target.naturalHeight
    });
  };

  const handleCanvasClick = useCallback((e) => {
    if (!addMode || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const img = containerRef.current.querySelector('img');
    if (!img) return;
    
    const imgRect = img.getBoundingClientRect();
    
    // Calculate click position relative to image as percentage
    const x = ((e.clientX - imgRect.left) / imgRect.width) * 100;
    const y = ((e.clientY - imgRect.top) / imgRect.height) * 100;
    
    if (x < 0 || x > 100 || y < 0 || y > 100) return;
    
    // Open dialog to configure the new item
    setNewItemConfig({
      x: Math.round(x * 10) / 10,
      y: Math.round(y * 10) / 10,
      page: currentPage,
      width: addMode === 'signature' ? 20 : 15,
      height: addMode === 'signature' ? 5 : 3,
      field_type: 'text',
      signer_type: 'recipient',
      label: '',
      required: true,
      include_date: true,
    });
    setShowAddDialog(true);
  }, [addMode, currentPage]);

  const handleAddItem = () => {
    const id = `${addMode}_${Date.now()}`;
    
    if (addMode === 'field') {
      const newField = {
        id,
        field_type: newItemConfig.field_type,
        label: newItemConfig.label || 'New Field',
        page: newItemConfig.page,
        x: newItemConfig.x,
        y: newItemConfig.y,
        width: newItemConfig.width,
        height: newItemConfig.height,
        required: newItemConfig.required,
        signer_type: newItemConfig.signer_type,
        placeholder: newItemConfig.placeholder || '',
      };
      setFieldPlacements(prev => [...prev, newField]);
    } else if (addMode === 'signature') {
      const newSig = {
        id,
        label: newItemConfig.label || 'Signature',
        page: newItemConfig.page,
        x: newItemConfig.x,
        y: newItemConfig.y,
        width: newItemConfig.width,
        height: newItemConfig.height,
        signer_type: newItemConfig.signer_type,
        include_date: newItemConfig.include_date,
        date_x: newItemConfig.x + newItemConfig.width + 5,
        date_y: newItemConfig.y,
      };
      setSignaturePlacements(prev => [...prev, newSig]);
    }
    
    setShowAddDialog(false);
    setAddMode(null);
    toast.success(`${addMode === 'field' ? 'Field' : 'Signature'} added`);
  };

  const handleDeleteItem = (type, id) => {
    if (type === 'field') {
      setFieldPlacements(prev => prev.filter(f => f.id !== id));
    } else {
      setSignaturePlacements(prev => prev.filter(s => s.id !== id));
    }
    setSelectedItem(null);
    toast.success('Item removed');
  };

  const handleUpdateItem = (type, id, updates) => {
    if (type === 'field') {
      setFieldPlacements(prev => prev.map(f => f.id === id ? { ...f, ...updates } : f));
    } else {
      setSignaturePlacements(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s));
    }
  };

  const handleSave = async () => {
    const token = localStorage.getItem('token');
    setSaving(true);
    try {
      await axios.put(
        `${API}/documents/templates/${templateId}/placements`,
        {
          field_placements: fieldPlacements,
          signature_placements: signaturePlacements
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Placements saved successfully');
    } catch (error) {
      toast.error('Failed to save placements');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  // Get items for current page
  const currentPageFields = fieldPlacements.filter(f => f.page === currentPage);
  const currentPageSignatures = signaturePlacements.filter(s => s.page === currentPage);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-3xl text-purple-400 mb-4"></i>
          <p className="text-white">Loading template...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/document-templates')}>
              <ChevronLeft className="w-4 h-4 mr-1" /> Back
            </Button>
            <div>
              <h1 className="text-lg font-semibold text-white">{template?.name}</h1>
              <p className="text-sm text-slate-400">Configure form fields and signature placements</p>
            </div>
          </div>
          <Button onClick={handleSave} disabled={saving} className="bg-purple-600 hover:bg-purple-700">
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Save Placements'}
          </Button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-4 flex gap-4">
        {/* Left Panel - Tools */}
        <div className="w-64 flex-shrink-0 space-y-4">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white">Add Elements</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant={addMode === 'field' ? 'default' : 'outline'}
                className="w-full justify-start"
                onClick={() => setAddMode(addMode === 'field' ? null : 'field')}
              >
                <Type className="w-4 h-4 mr-2" />
                Add Form Field
              </Button>
              <Button
                variant={addMode === 'signature' ? 'default' : 'outline'}
                className="w-full justify-start"
                onClick={() => setAddMode(addMode === 'signature' ? null : 'signature')}
              >
                <PenLine className="w-4 h-4 mr-2" />
                Add Signature
              </Button>
              {addMode && (
                <p className="text-xs text-purple-400 mt-2">
                  Click on the PDF to place the {addMode}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Page Navigation */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white">Pages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage(p => p - 1)}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-white text-sm">
                  Page {currentPage} of {pagesInfo.length}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= pagesInfo.length}
                  onClick={() => setCurrentPage(p => p + 1)}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Elements on Current Page */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white">
                Elements on Page {currentPage}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-64 overflow-y-auto">
              {currentPageFields.length === 0 && currentPageSignatures.length === 0 && (
                <p className="text-xs text-slate-500">No elements on this page</p>
              )}
              {currentPageFields.map(field => (
                <div
                  key={field.id}
                  className={`p-2 rounded text-xs cursor-pointer transition-colors ${
                    selectedItem?.id === field.id
                      ? 'bg-purple-600/30 border border-purple-500'
                      : 'bg-slate-700 hover:bg-slate-600'
                  }`}
                  onClick={() => setSelectedItem({ type: 'field', id: field.id })}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-white truncate">{field.label}</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteItem('field', field.id); }}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                  <span className="text-slate-400">{field.field_type} • {field.signer_type}</span>
                </div>
              ))}
              {currentPageSignatures.map(sig => (
                <div
                  key={sig.id}
                  className={`p-2 rounded text-xs cursor-pointer transition-colors ${
                    selectedItem?.id === sig.id
                      ? 'bg-orange-600/30 border border-orange-500'
                      : 'bg-slate-700 hover:bg-slate-600'
                  }`}
                  onClick={() => setSelectedItem({ type: 'signature', id: sig.id })}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-white truncate">{sig.label}</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteItem('signature', sig.id); }}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                  <span className="text-slate-400">signature • {sig.signer_type}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Selected Item Properties */}
          {selectedItem && (
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-white">Properties</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {selectedItem.type === 'field' && (() => {
                  const field = fieldPlacements.find(f => f.id === selectedItem.id);
                  if (!field) return null;
                  return (
                    <>
                      <div>
                        <Label className="text-xs text-slate-400">Label</Label>
                        <Input
                          value={field.label}
                          onChange={(e) => handleUpdateItem('field', field.id, { label: e.target.value })}
                          className="h-8 text-sm bg-slate-700 border-slate-600"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">Field Type</Label>
                        <Select
                          value={field.field_type}
                          onValueChange={(v) => handleUpdateItem('field', field.id, { field_type: v })}
                        >
                          <SelectTrigger className="h-8 text-sm bg-slate-700 border-slate-600">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {FIELD_TYPES.map(ft => (
                              <SelectItem key={ft.value} value={ft.value}>{ft.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">Signer</Label>
                        <Select
                          value={field.signer_type}
                          onValueChange={(v) => handleUpdateItem('field', field.id, { signer_type: v })}
                        >
                          <SelectTrigger className="h-8 text-sm bg-slate-700 border-slate-600">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {SIGNER_TYPES.map(st => (
                              <SelectItem key={st.value} value={st.value}>{st.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  );
                })()}
                {selectedItem.type === 'signature' && (() => {
                  const sig = signaturePlacements.find(s => s.id === selectedItem.id);
                  if (!sig) return null;
                  return (
                    <>
                      <div>
                        <Label className="text-xs text-slate-400">Label</Label>
                        <Input
                          value={sig.label}
                          onChange={(e) => handleUpdateItem('signature', sig.id, { label: e.target.value })}
                          className="h-8 text-sm bg-slate-700 border-slate-600"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">Signer</Label>
                        <Select
                          value={sig.signer_type}
                          onValueChange={(v) => handleUpdateItem('signature', sig.id, { signer_type: v })}
                        >
                          <SelectTrigger className="h-8 text-sm bg-slate-700 border-slate-600">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {SIGNER_TYPES.map(st => (
                              <SelectItem key={st.value} value={st.value}>{st.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Main Canvas Area */}
        <div className="flex-1">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div
                ref={containerRef}
                className={`relative bg-white rounded-lg overflow-hidden ${addMode ? 'cursor-crosshair' : ''}`}
                onClick={handleCanvasClick}
                style={{ minHeight: '600px' }}
              >
                {loadingPage ? (
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-200">
                    <i className="fas fa-spinner fa-spin text-2xl text-slate-500"></i>
                  </div>
                ) : pageImage ? (
                  <>
                    <img
                      src={pageImage}
                      alt={`Page ${currentPage}`}
                      className="w-full h-auto"
                      onLoad={handleImageLoad}
                      draggable={false}
                    />
                    {/* Render field overlays */}
                    {currentPageFields.map(field => (
                      <div
                        key={field.id}
                        className={`absolute border-2 rounded transition-colors ${
                          selectedItem?.id === field.id
                            ? 'border-purple-500 bg-purple-500/20'
                            : 'border-blue-500 bg-blue-500/10 hover:bg-blue-500/20'
                        }`}
                        style={{
                          left: `${field.x}%`,
                          top: `${field.y}%`,
                          width: `${field.width}%`,
                          height: `${field.height}%`,
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (!addMode) setSelectedItem({ type: 'field', id: field.id });
                        }}
                      >
                        <span className="absolute -top-5 left-0 text-xs bg-blue-600 text-white px-1 rounded whitespace-nowrap">
                          {field.label}
                        </span>
                      </div>
                    ))}
                    {/* Render signature overlays */}
                    {currentPageSignatures.map(sig => (
                      <div
                        key={sig.id}
                        className={`absolute border-2 rounded transition-colors ${
                          selectedItem?.id === sig.id
                            ? 'border-orange-500 bg-orange-500/20'
                            : 'border-orange-400 bg-orange-400/10 hover:bg-orange-400/20'
                        }`}
                        style={{
                          left: `${sig.x}%`,
                          top: `${sig.y}%`,
                          width: `${sig.width}%`,
                          height: `${sig.height}%`,
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (!addMode) setSelectedItem({ type: 'signature', id: sig.id });
                        }}
                      >
                        <span className="absolute -top-5 left-0 text-xs bg-orange-600 text-white px-1 rounded whitespace-nowrap">
                          {sig.label}
                        </span>
                      </div>
                    ))}
                  </>
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                    No page to display
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Add Item Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              Add {addMode === 'field' ? 'Form Field' : 'Signature Placement'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Label</Label>
              <Input
                value={newItemConfig.label || ''}
                onChange={(e) => setNewItemConfig(prev => ({ ...prev, label: e.target.value }))}
                placeholder={addMode === 'field' ? 'e.g., First Name' : 'e.g., Applicant Signature'}
              />
            </div>
            {addMode === 'field' && (
              <div>
                <Label>Field Type</Label>
                <Select
                  value={newItemConfig.field_type}
                  onValueChange={(v) => setNewItemConfig(prev => ({ ...prev, field_type: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FIELD_TYPES.map(ft => (
                      <SelectItem key={ft.value} value={ft.value}>{ft.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div>
              <Label>Who fills this?</Label>
              <Select
                value={newItemConfig.signer_type}
                onValueChange={(v) => setNewItemConfig(prev => ({ ...prev, signer_type: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SIGNER_TYPES.map(st => (
                    <SelectItem key={st.value} value={st.value}>{st.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Width (%)</Label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={newItemConfig.width || 15}
                  onChange={(e) => setNewItemConfig(prev => ({ ...prev, width: parseFloat(e.target.value) }))}
                />
              </div>
              <div>
                <Label>Height (%)</Label>
                <Input
                  type="number"
                  min="1"
                  max="20"
                  value={newItemConfig.height || 3}
                  onChange={(e) => setNewItemConfig(prev => ({ ...prev, height: parseFloat(e.target.value) }))}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowAddDialog(false); setAddMode(null); }}>
              Cancel
            </Button>
            <Button onClick={handleAddItem} className="bg-purple-600 hover:bg-purple-700">
              Add {addMode === 'field' ? 'Field' : 'Signature'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
